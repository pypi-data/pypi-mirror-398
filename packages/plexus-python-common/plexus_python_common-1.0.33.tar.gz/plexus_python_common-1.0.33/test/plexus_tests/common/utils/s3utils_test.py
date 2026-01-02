import contextlib
import itertools
import os
import tempfile
import unittest

import ddt
import moto
import moto.server
from iker.common.utils.randutils import randomizer
from iker.common.utils.shutils import listfile
from iker.common.utils.testutils import norm_path

from plexus.common.utils.s3utils import *
from plexus_tests import resources_directory


@contextlib.contextmanager
def moto_server_endpoint_url():
    server = moto.server.ThreadedMotoServer(port=0)  # random free port
    try:
        server.start()
        host, port = server.get_host_and_port()
        yield f"http://{host}:{port}"
    finally:
        server.stop()


@ddt.ddt
class S3UtilsTest(unittest.TestCase):

    def test_s3_list_object__random_text_files(self):
        with moto.mock_aws(), s3_make_client() as client:
            client.client.create_bucket(Bucket="dummy-bucket")

            data = []
            for i in range(0, 2000):
                text = randomizer().random_alphanumeric(randomizer().next_int(1000, 2000))
                key = "dummy_prefix/%04d" % i
                data.append((key, text))

            for key, text in data:
                s3_push_text(client, text, "dummy-bucket", key)

            result = list(s3_list_objects(client, "dummy-bucket", "dummy_prefix/"))

            for key, text in data:
                self.assertTrue(any(o.key == key for o in result))
                self.assertEqual(s3_pull_text(client, "dummy-bucket", key), text)

        with moto.mock_aws(), s3_make_progressed_client() as client:
            client.client.create_bucket(Bucket="dummy-bucket")

            data = []
            for i in range(0, 2000):
                text = randomizer().random_alphanumeric(randomizer().next_int(1000, 2000))
                key = "dummy_prefix/%04d" % i
                data.append((key, text))

            for key, text in data:
                client.CloudPath("s3://dummy-bucket/", key).write_text(text)

            result = list(s3_list_objects(client, "dummy-bucket", "dummy_prefix/"))

            for key, text in data:
                self.assertTrue(any(o.key == key for o in result))
                self.assertEqual(client.CloudPath("s3://dummy-bucket", key).read_text(), text)

    def test_s3_listfile__random_text_files(self):
        with moto.mock_aws(), s3_make_client() as client:
            client.client.create_bucket(Bucket="dummy-bucket")

            data = []
            for i in range(0, 2000):
                text = randomizer().random_alphanumeric(randomizer().next_int(1000, 2000))
                key = "dummy_prefix/%04d" % i
                data.append((key, text))

            for key, text in data:
                s3_push_text(client, text, "dummy-bucket", key)

            result = list(s3_listfile(client, "dummy-bucket", "dummy_prefix/"))

            for key, text in data:
                self.assertTrue(any(o.key == key for o in result))
                self.assertEqual(s3_pull_text(client, "dummy-bucket", key), text)

        with moto.mock_aws(), s3_make_progressed_client() as client:
            client.client.create_bucket(Bucket="dummy-bucket")

            data = []
            for i in range(0, 2000):
                text = randomizer().random_alphanumeric(randomizer().next_int(1000, 2000))
                key = "dummy_prefix/%04d" % i
                data.append((key, text))

            for key, text in data:
                client.CloudPath("s3://dummy-bucket/", key).write_text(text)

            result = list(s3_listfile(client, "dummy-bucket", "dummy_prefix/"))

            for key, text in data:
                self.assertTrue(any(o.key == key for o in result))
                self.assertEqual(client.CloudPath("s3://dummy-bucket", key).read_text(), text)

    data_s3_listfile = [
        (
            "unittest/s3utils/",
            "dummy-bucket",
            "unittest/s3utils/",
            [],
            [],
            0,
            [
                "unittest/s3utils/dir.baz/file.foo.bar",
                "unittest/s3utils/dir.baz/file.foo.baz",
                "unittest/s3utils/dir.baz/file.bar.baz",
                "unittest/s3utils/dir.foo/file.bar",
                "unittest/s3utils/dir.foo/file.baz",
                "unittest/s3utils/dir.foo/file.foo",
                "unittest/s3utils/dir.foo/dir.foo.bar/file.foo.bar",
                "unittest/s3utils/dir.foo/dir.foo.bar/file.foo.baz",
                "unittest/s3utils/dir.foo/dir.foo.bar/file.bar.baz",
                "unittest/s3utils/dir.foo/dir.foo.bar/dir.foo.bar.baz/file.foo.bar.baz",
            ],
        ),
        (
            "unittest/s3utils",
            "dummy-bucket",
            "unittest/s3utils/",
            [],
            [],
            0,
            [
                "unittest/s3utils/dir.baz/file.foo.bar",
                "unittest/s3utils/dir.baz/file.foo.baz",
                "unittest/s3utils/dir.baz/file.bar.baz",
                "unittest/s3utils/dir.foo/file.bar",
                "unittest/s3utils/dir.foo/file.baz",
                "unittest/s3utils/dir.foo/file.foo",
                "unittest/s3utils/dir.foo/dir.foo.bar/file.foo.bar",
                "unittest/s3utils/dir.foo/dir.foo.bar/file.foo.baz",
                "unittest/s3utils/dir.foo/dir.foo.bar/file.bar.baz",
                "unittest/s3utils/dir.foo/dir.foo.bar/dir.foo.bar.baz/file.foo.bar.baz",
            ],
        ),
        (
            "unittest/s3utils/dir.foo",
            "dummy-bucket",
            "unittest/s3utils/dir.foo",
            [],
            [],
            0,
            [
                "unittest/s3utils/dir.foo/file.bar",
                "unittest/s3utils/dir.foo/file.baz",
                "unittest/s3utils/dir.foo/file.foo",
                "unittest/s3utils/dir.foo/dir.foo.bar/file.foo.bar",
                "unittest/s3utils/dir.foo/dir.foo.bar/file.foo.baz",
                "unittest/s3utils/dir.foo/dir.foo.bar/file.bar.baz",
                "unittest/s3utils/dir.foo/dir.foo.bar/dir.foo.bar.baz/file.foo.bar.baz",
            ],
        ),
        (
            "unittest/s3utils/dir.baz",
            "dummy-bucket",
            "unittest/s3utils/dir.baz",
            [],
            [],
            0,
            [
                "unittest/s3utils/dir.baz/file.foo.bar",
                "unittest/s3utils/dir.baz/file.foo.baz",
                "unittest/s3utils/dir.baz/file.bar.baz",
            ],
        ),
        (
            "unittest/s3utils",
            "dummy-bucket",
            "unittest/s3utils/",
            ["*.foo", "*.bar"],
            ["*.foo.bar"],
            0,
            [
                "unittest/s3utils/dir.foo/file.bar",
                "unittest/s3utils/dir.foo/file.foo",
            ],
        ),
        (
            "unittest/s3utils",
            "dummy-bucket",
            "unittest/s3utils/",
            ["*.foo", "*.bar"],
            [],
            0,
            [
                "unittest/s3utils/dir.baz/file.foo.bar",
                "unittest/s3utils/dir.foo/file.bar",
                "unittest/s3utils/dir.foo/file.foo",
                "unittest/s3utils/dir.foo/dir.foo.bar/file.foo.bar",
            ],
        ),
        (
            "unittest/s3utils",
            "dummy-bucket",
            "unittest/s3utils/",
            [],
            ["*.baz"],
            0,
            [
                "unittest/s3utils/dir.baz/file.foo.bar",
                "unittest/s3utils/dir.foo/file.bar",
                "unittest/s3utils/dir.foo/file.foo",
                "unittest/s3utils/dir.foo/dir.foo.bar/file.foo.bar",
            ],
        ),
        (
            "unittest/s3utils",
            "dummy-bucket",
            "unittest/s3utils",
            [],
            [],
            2,
            [
                "unittest/s3utils/dir.baz/file.foo.bar",
                "unittest/s3utils/dir.baz/file.foo.baz",
                "unittest/s3utils/dir.baz/file.bar.baz",
                "unittest/s3utils/dir.foo/file.bar",
                "unittest/s3utils/dir.foo/file.baz",
                "unittest/s3utils/dir.foo/file.foo",
            ],
        ),
    ]

    @ddt.idata(data_s3_listfile)
    @ddt.unpack
    def test_s3_listfile(self, src, bucket, prefix, include_patterns, exclude_patterns, depth, expect):
        with moto.mock_aws(), s3_make_client() as client:
            client.client.create_bucket(Bucket=bucket)

            s3_sync_upload(client,
                           os.path.join(resources_directory, src),
                           bucket,
                           prefix)

            object_metas = s3_listfile(client,
                                       bucket,
                                       prefix,
                                       include_patterns=include_patterns,
                                       exclude_patterns=exclude_patterns,
                                       depth=depth)

            self.assertSetEqual(set(map(lambda x: norm_path(x.key), object_metas)),
                                set(map(lambda x: norm_path(x), expect)))

    data_s3_sync = [
        (
            "unittest/s3utils/",
            "unittest/s3utils/",
            "dummy-bucket",
            "unittest/s3utils/",
            [],
            [],
            0,
            [
                "unittest/s3utils/dir.baz/file.foo.bar",
                "unittest/s3utils/dir.baz/file.foo.baz",
                "unittest/s3utils/dir.baz/file.bar.baz",
                "unittest/s3utils/dir.foo/file.bar",
                "unittest/s3utils/dir.foo/file.baz",
                "unittest/s3utils/dir.foo/file.foo",
                "unittest/s3utils/dir.foo/dir.foo.bar/file.foo.bar",
                "unittest/s3utils/dir.foo/dir.foo.bar/file.foo.baz",
                "unittest/s3utils/dir.foo/dir.foo.bar/file.bar.baz",
                "unittest/s3utils/dir.foo/dir.foo.bar/dir.foo.bar.baz/file.foo.bar.baz",
            ],
        ),
        (
            "unittest/s3utils",
            "unittest/s3utils",
            "dummy-bucket",
            "unittest/s3utils/",
            [],
            [],
            0,
            [
                "unittest/s3utils/dir.baz/file.foo.bar",
                "unittest/s3utils/dir.baz/file.foo.baz",
                "unittest/s3utils/dir.baz/file.bar.baz",
                "unittest/s3utils/dir.foo/file.bar",
                "unittest/s3utils/dir.foo/file.baz",
                "unittest/s3utils/dir.foo/file.foo",
                "unittest/s3utils/dir.foo/dir.foo.bar/file.foo.bar",
                "unittest/s3utils/dir.foo/dir.foo.bar/file.foo.baz",
                "unittest/s3utils/dir.foo/dir.foo.bar/file.bar.baz",
                "unittest/s3utils/dir.foo/dir.foo.bar/dir.foo.bar.baz/file.foo.bar.baz",
            ],
        ),
        (
            "unittest/s3utils/dir.foo",
            "unittest/s3utils/dir.foo",
            "dummy-bucket",
            "unittest/s3utils/dir.foo",
            [],
            [],
            0,
            [
                "unittest/s3utils/dir.foo/file.bar",
                "unittest/s3utils/dir.foo/file.baz",
                "unittest/s3utils/dir.foo/file.foo",
                "unittest/s3utils/dir.foo/dir.foo.bar/file.foo.bar",
                "unittest/s3utils/dir.foo/dir.foo.bar/file.foo.baz",
                "unittest/s3utils/dir.foo/dir.foo.bar/file.bar.baz",
                "unittest/s3utils/dir.foo/dir.foo.bar/dir.foo.bar.baz/file.foo.bar.baz",
            ],
        ),
        (
            "unittest/s3utils/dir.baz",
            "unittest/s3utils/dir.baz",
            "dummy-bucket",
            "unittest/s3utils/dir.baz",
            [],
            [],
            0,
            [
                "unittest/s3utils/dir.baz/file.foo.bar",
                "unittest/s3utils/dir.baz/file.foo.baz",
                "unittest/s3utils/dir.baz/file.bar.baz",
            ],
        ),
        (
            "unittest/s3utils",
            "unittest/s3utils",
            "dummy-bucket",
            "unittest/s3utils/",
            ["*.foo", "*.bar"],
            ["*.foo.bar"],
            0,
            [
                "unittest/s3utils/dir.foo/file.bar",
                "unittest/s3utils/dir.foo/file.foo",
            ],
        ),
        (
            "unittest/s3utils",
            "unittest/s3utils",
            "dummy-bucket",
            "unittest/s3utils/",
            ["*.foo", "*.bar"],
            [],
            0,
            [
                "unittest/s3utils/dir.baz/file.foo.bar",
                "unittest/s3utils/dir.foo/file.bar",
                "unittest/s3utils/dir.foo/file.foo",
                "unittest/s3utils/dir.foo/dir.foo.bar/file.foo.bar",
            ],
        ),
        (
            "unittest/s3utils",
            "unittest/s3utils",
            "dummy-bucket",
            "unittest/s3utils/",
            [],
            ["*.baz"],
            0,
            [
                "unittest/s3utils/dir.baz/file.foo.bar",
                "unittest/s3utils/dir.foo/file.bar",
                "unittest/s3utils/dir.foo/file.foo",
                "unittest/s3utils/dir.foo/dir.foo.bar/file.foo.bar",
            ],
        ),
        (
            "unittest/s3utils",
            "unittest/s3utils",
            "dummy-bucket",
            "unittest/s3utils",
            [],
            [],
            2,
            [
                "unittest/s3utils/dir.baz/file.foo.bar",
                "unittest/s3utils/dir.baz/file.foo.baz",
                "unittest/s3utils/dir.baz/file.bar.baz",
                "unittest/s3utils/dir.foo/file.bar",
                "unittest/s3utils/dir.foo/file.baz",
                "unittest/s3utils/dir.foo/file.foo",
            ],
        ),
    ]

    @ddt.idata(data_s3_sync)
    @ddt.unpack
    def test_s3_sync(self, src, dst, bucket, prefix, include_patterns, exclude_patterns, depth, expect):
        with moto.mock_aws(), s3_make_client() as client:
            client.client.create_bucket(Bucket=bucket)

            s3_sync_upload(client,
                           os.path.join(resources_directory, src),
                           bucket,
                           prefix,
                           include_patterns=include_patterns,
                           exclude_patterns=exclude_patterns,
                           depth=depth)

            with tempfile.TemporaryDirectory() as temp_directory:
                s3_sync_download(client,
                                 bucket,
                                 prefix,
                                 os.path.join(temp_directory, dst))

                self.assertSetEqual(set(map(lambda x: norm_path(x), listfile(os.path.join(temp_directory, dst)))),
                                    set(map(lambda x: norm_path(os.path.join(temp_directory, x)), expect)))

        with moto.mock_aws(), s3_make_client() as client:
            client.client.create_bucket(Bucket=bucket)

            s3_sync_upload(client,
                           os.path.join(resources_directory, src),
                           bucket,
                           prefix)

            with tempfile.TemporaryDirectory() as temp_directory:
                s3_sync_download(client,
                                 bucket,
                                 prefix,
                                 os.path.join(temp_directory, dst),
                                 include_patterns=include_patterns,
                                 exclude_patterns=exclude_patterns,
                                 depth=depth)

                self.assertSetEqual(set(map(lambda x: norm_path(x), listfile(os.path.join(temp_directory, dst)))),
                                    set(map(lambda x: norm_path(os.path.join(temp_directory, x)), expect)))

        with moto.mock_aws(), s3_make_client() as client:
            client.client.create_bucket(Bucket=bucket)

            s3_sync_upload(client,
                           os.path.join(resources_directory, src),
                           bucket,
                           prefix,
                           include_patterns=include_patterns,
                           depth=depth)

            with tempfile.TemporaryDirectory() as temp_directory:
                s3_sync_download(client,
                                 bucket,
                                 prefix,
                                 os.path.join(temp_directory, dst),
                                 exclude_patterns=exclude_patterns,
                                 depth=depth)

                self.assertSetEqual(set(map(lambda x: norm_path(x), listfile(os.path.join(temp_directory, dst)))),
                                    set(map(lambda x: norm_path(os.path.join(temp_directory, x)), expect)))

    data_s3_text = [
        ("dummy-bucket", "dummy/key", "dummy content", None),
        ("dummy-bucket", "dummy/key.alpha", "Old MacDonald had a farm", None),
        ("dummy-bucket", "dummy/key.beta", "Ee-i-ee-i-o", None),
        ("dummy-bucket", "dummy/key", "dummy content", "ascii"),
        ("dummy-bucket", "dummy/key.alpha", "Old MacDonald had a farm", "ascii"),
        ("dummy-bucket", "dummy/key.beta", "Ee-i-ee-i-o", "ascii"),
    ]

    @ddt.idata(data_s3_text)
    @ddt.unpack
    def test_s3_text(self, bucket, key, text, encoding):
        with moto.mock_aws(), s3_make_client() as client:
            client.client.create_bucket(Bucket=bucket)

            s3_push_text(client, text, bucket, key, encoding=encoding)
            self.assertEqual(s3_pull_text(client, bucket, key, encoding=encoding), text)

    def test_s3_archive_listfile(self):
        with (
            moto.mock_aws(),
            moto_server_endpoint_url() as endpoint_url,
            s3_make_client(endpoint_url=endpoint_url) as client,
        ):
            client.client.create_bucket(Bucket="dummy-bucket")

            s3_sync_upload(client,
                           os.path.join(resources_directory, "unittest", "s3utils_archive"),
                           "dummy-bucket",
                           "s3utils_archive")

            local_root = os.path.join(resources_directory, "unittest", "s3utils")
            local_members = [os.path.relpath(file_path, local_root) for file_path in listfile(local_root)]

            for archive_key, members in itertools.product(
                ["s3utils_archive/archive.uncompressed.zip", "s3utils_archive/archive.compressed.zip"],
                [local_members, None],
            ):
                archive_size, member_zip_infos, missed_members = s3_archive_listfile(client,
                                                                                     "dummy-bucket",
                                                                                     archive_key,
                                                                                     members)

                self.assertEqual(archive_size - sum(info.compress_size for info in member_zip_infos), 2470)
                self.assertEqual(set(info.filename for info in member_zip_infos), set(local_members))
                self.assertEqual(len(missed_members), 0)

            for archive_key, (members, members_expect) in itertools.product(
                ["s3utils_archive/archive.uncompressed.zip", "s3utils_archive/archive.compressed.zip"],
                [(local_members, local_members),
                 (None, local_members),
                 (["dir.baz/", "dir.foo/"],
                  [os.path.relpath(file_path, local_root)
                   for file_path in
                   listfile(os.path.join(local_root, "dir.baz")) + listfile(os.path.join(local_root, "dir.foo"))],
                  ),
                 (["dir.foo/"],
                  [os.path.relpath(file_path, local_root)
                   for file_path in listfile(os.path.join(local_root, "dir.foo"))],
                  ),
                 (["dir.foo/"] * 3,  # Duplicate entries, the result should repeat them as well
                  [os.path.relpath(file_path, local_root)
                   for file_path in (listfile(os.path.join(local_root, "dir.foo")) * 3)],
                  ),
                 (["dir.foo/dir.foo.bar/"],
                  [os.path.relpath(file_path, local_root)
                   for file_path in listfile(os.path.join(local_root, "dir.foo", "dir.foo.bar"))],
                  ),
                 ],
            ):
                archive_size, member_zip_infos, missed_members = s3_archive_listfile(client,
                                                                                     "dummy-bucket",
                                                                                     archive_key,
                                                                                     members)

                self.assertEqual(sorted(list(info.filename for info in member_zip_infos)), sorted(members_expect))
                self.assertEqual(len(missed_members), 0)

    def test_s3_archive_open_member(self):
        with (
            moto.mock_aws(),
            moto_server_endpoint_url() as endpoint_url,
            s3_make_client(endpoint_url=endpoint_url) as client,
        ):
            client.client.create_bucket(Bucket="dummy-bucket")

            s3_sync_upload(client,
                           os.path.join(resources_directory, "unittest", "s3utils_archive"),
                           "dummy-bucket",
                           "s3utils_archive")

            local_root = os.path.join(resources_directory, "unittest", "s3utils")
            local_members = [os.path.relpath(file_path, local_root) for file_path in listfile(local_root)]

            for archive_key, mode in itertools.product(
                ["s3utils_archive/archive.uncompressed.zip", "s3utils_archive/archive.compressed.zip"],
                ["r", "rb"],
            ):
                for local_member in local_members:
                    with (
                        open(os.path.join(local_root, local_member), mode) as local_fh,
                        s3_archive_open_member(client, "dummy-bucket", archive_key, local_member, mode) as s3_fh,
                    ):
                        self.assertEqual(local_fh.read(), s3_fh.read())

    def test_s3_archive_open_members(self):
        with (
            moto.mock_aws(),
            moto_server_endpoint_url() as endpoint_url,
            s3_make_client(endpoint_url=endpoint_url) as client,
        ):
            client.client.create_bucket(Bucket="dummy-bucket")

            s3_sync_upload(client,
                           os.path.join(resources_directory, "unittest", "s3utils_archive"),
                           "dummy-bucket",
                           "s3utils_archive")

            local_root = os.path.join(resources_directory, "unittest", "s3utils")
            local_members = [os.path.relpath(file_path, local_root) for file_path in listfile(local_root)]

            for archive_key, members, mode, use_ranged_requests, use_chunked_reads in itertools.product(
                ["s3utils_archive/archive.uncompressed.zip", "s3utils_archive/archive.compressed.zip"],
                [local_members, None],
                ["r", "rb"],
                [False, True, s3_archive_use_ranged_requests()],
                [False, True, s3_archive_use_chunked_reads()],
            ):
                for member, opener in s3_archive_open_members(
                    client,
                    "dummy-bucket",
                    archive_key,
                    members,
                    mode,
                    use_ranged_requests=use_ranged_requests,
                    use_chunked_reads=use_chunked_reads,
                ):
                    with open(os.path.join(local_root, member), mode) as local_fh, opener() as s3_fh:
                        self.assertEqual(local_fh.read(), s3_fh.read())
