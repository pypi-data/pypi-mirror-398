import concurrent.futures
import contextlib
import dataclasses
import datetime
import functools
import io
import mimetypes
import os
import os.path
import shutil
import tempfile
import typing
import zipfile
import zlib
from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any, Literal

import boto3
import fsspec
import fsspec.utils
from cloudpathlib import CloudPath, S3Client, S3Path
from iker.common.utils.sequtils import chunk_between, head, last
from iker.common.utils.shutils import glob_match, listfile, path_depth
from iker.common.utils.strutils import is_empty, trim_to_none
from rich.progress import BarColumn, DownloadColumn, Progress, TaskID, TextColumn, TransferSpeedColumn

__all__ = [
    "S3ObjectMeta",
    "s3_make_client",
    "s3_list_objects",
    "s3_listfile",
    "s3_cp_download",
    "s3_cp_upload",
    "s3_sync_download",
    "s3_sync_upload",
    "s3_pull_text",
    "s3_push_text",
    "S3TransferCallbackClient",
    "ArchiveMemberChunk",
    "s3_make_progress_callback",
    "s3_make_progressed_client",
    "s3_archive_member_tree",
    "s3_archive_listfile",
    "s3_archive_open_member",
    "s3_archive_use_ranged_requests",
    "s3_archive_use_chunked_reads",
    "s3_archive_open_members",
]


@dataclasses.dataclass(frozen=True, eq=True)
class S3ObjectMeta(object):
    key: str
    last_modified: datetime.datetime
    size: int


if typing.TYPE_CHECKING:
    def s3_make_client(
        access_key_id: str = None,
        secret_access_key: str = None,
        region_name: str = None,
        endpoint_url: str = None,
    ) -> contextlib.AbstractContextManager[S3Client]: ...


@contextlib.contextmanager
def s3_make_client(
    access_key_id: str = None,
    secret_access_key: str = None,
    region_name: str = None,
    endpoint_url: str = None,
) -> Generator[S3Client, None, None]:
    """
    Creates an S3 client as a context manager for safe resource handling.

    :param access_key_id: AWS access key ID.
    :param secret_access_key: AWS secret access key.
    :param region_name: AWS service region name.
    :param endpoint_url: AWS service endpoint URL.
    :return: An instance of ``S3Client``.
    """
    session = boto3.Session(aws_access_key_id=trim_to_none(access_key_id),
                            aws_secret_access_key=trim_to_none(secret_access_key),
                            region_name=trim_to_none(region_name))
    client = S3Client(boto3_session=session, endpoint_url=trim_to_none(endpoint_url))
    try:
        yield client
    finally:
        if hasattr(client, "close"):
            client.close()


def s3_list_objects(
    client: S3Client,
    bucket: str,
    prefix: str,
    limit: int = None,
) -> Generator[S3ObjectMeta, None, None]:
    """
    Lists all objects from the given S3 ``bucket`` and ``prefix``.

    :param client: An instance of ``S3Client``.
    :param bucket: Bucket name.
    :param prefix: Object keys prefix.
    :param limit: Maximum number of objects to return (``None`` for all).
    :return: An iterable of ``S3ObjectMeta`` objects representing the S3 objects.
    """
    continuation_token = None
    count = 0
    while True:
        if is_empty(continuation_token):
            response = client.client.list_objects_v2(MaxKeys=1000, Bucket=bucket, Prefix=prefix)
        else:
            response = client.client.list_objects_v2(MaxKeys=1000,
                                                     Bucket=bucket,
                                                     Prefix=prefix,
                                                     ContinuationToken=continuation_token)

        contents = response.get("Contents", [])
        count += len(contents)
        if limit is not None and count > limit:
            contents = contents[:limit - count]

        yield from (S3ObjectMeta(key=e["Key"], last_modified=e["LastModified"], size=e["Size"]) for e in contents)

        if not response.get("IsTruncated") or (limit is not None and count >= limit):
            break

        continuation_token = response.get("NextContinuationToken")


def s3_listfile(
    client: S3Client,
    bucket: str,
    prefix: str,
    *,
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
    depth: int = 0,
) -> Generator[S3ObjectMeta, None, None]:
    """
    Lists all objects from the given S3 ``bucket`` and ``prefix``, filtered by patterns and directory depth.

    :param client: An instance of ``S3Client``.
    :param bucket: Bucket name.
    :param prefix: Object keys prefix.
    :param include_patterns: Inclusive glob patterns applied to filenames.
    :param exclude_patterns: Exclusive glob patterns applied to filenames.
    :param depth: Maximum depth of subdirectories to include in the scan (``0`` for unlimited depth).
    :return: An iterable of ``S3ObjectMeta`` objects representing the filtered S3 objects.
    """

    # We add trailing slash "/" to the prefix if it is absent
    if not prefix.endswith("/"):
        prefix = prefix + "/"

    def filter_object_meta(object_meta: S3ObjectMeta) -> bool:
        if 0 < depth <= path_depth(prefix, os.path.dirname(object_meta.key)):
            return False
        if len(glob_match([os.path.basename(object_meta.key)], include_patterns, exclude_patterns)) == 0:
            return False
        return True

    yield from filter(filter_object_meta, s3_list_objects(client, bucket, prefix))


def s3_cp_download(client: S3Client, bucket: str, key: str, file_path: str | os.PathLike[str]):
    """
    Downloads an object from the given S3 ``bucket`` and ``key`` to a local file path.

    :param client: An instance of ``S3Client``.
    :param bucket: Bucket name.
    :param key: Object key.
    :param file_path: Local file path to save the object.
    """
    client.client.download_file(bucket, key, file_path)


def s3_cp_upload(client: S3Client, file_path: str | os.PathLike[str], bucket: str, key: str):
    """
    Uploads a local file to the given S3 ``bucket`` and ``key``.

    :param client: An instance of ``S3Client``.
    :param file_path: Local file path to upload.
    :param bucket: Bucket name.
    :param key: Object key for the uploaded file.
    """
    t, _ = mimetypes.MimeTypes().guess_type(file_path)
    client.client.upload_file(file_path,
                              bucket,
                              key,
                              ExtraArgs={"ContentType": "binary/octet-stream" if t is None else t})


def s3_sync_download(
    client: S3Client,
    bucket: str,
    prefix: str,
    dir_path: str | os.PathLike[str],
    *,
    max_workers: int = None,
    include_patterns: list[str] = None,
    exclude_patterns: list[str] = None,
    depth: int = 0,
):
    """
    Recursively downloads all objects from the given S3 ``bucket`` and ``prefix`` to a local directory path, using a thread pool.

    :param client: An instance of ``S3Client``.
    :param bucket: Bucket name.
    :param prefix: Object keys prefix.
    :param dir_path: Local directory path to save objects.
    :param max_workers: Maximum number of worker threads.
    :param include_patterns: Inclusive glob patterns applied to filenames.
    :param exclude_patterns: Exclusive glob patterns applied to filenames.
    :param depth: Maximum depth of subdirectories to include in the scan (``0`` for unlimited depth).
    """

    # We add trailing slash "/" to the prefix if it is absent
    if not prefix.endswith("/"):
        prefix = prefix + "/"

    objects = s3_listfile(client,
                          bucket,
                          prefix,
                          include_patterns=include_patterns,
                          exclude_patterns=exclude_patterns,
                          depth=depth)

    def download_file(key: str):
        file_path = os.path.join(dir_path, key[len(prefix):])
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        s3_cp_download(client, bucket, key, file_path)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(download_file, obj.key) for obj in objects]
        done_futures, not_done_futures = concurrent.futures.wait(futures,
                                                                 return_when=concurrent.futures.FIRST_EXCEPTION)
        if len(not_done_futures) > 0:
            for future in not_done_futures:
                future.cancel()
        for future in done_futures:
            exc = future.exception()
            if exc is not None:
                raise exc
        if len(not_done_futures) > 0:
            raise RuntimeError("download did not complete due to errors in some threads")


def s3_sync_upload(
    client: S3Client,
    dir_path: str | os.PathLike[str],
    bucket: str,
    prefix: str,
    *,
    max_workers: int = None,
    include_patterns: list[str] = None,
    exclude_patterns: list[str] = None,
    depth: int = 0,
):
    """
    Recursively uploads all files from a local directory to the given S3 ``bucket`` and ``prefix``, using a thread pool.

    :param client: An instance of ``S3Client``.
    :param dir_path: Local directory path to upload from.
    :param bucket: Bucket name.
    :param prefix: Object keys prefix for uploaded files.
    :param max_workers: Maximum number of worker threads.
    :param include_patterns: Inclusive glob patterns applied to filenames.
    :param exclude_patterns: Exclusive glob patterns applied to filenames.
    :param depth: Maximum depth of subdirectories to include in the scan (``0`` for unlimited depth).
    """

    # We add trailing slash "/" to the prefix if it is absent
    if not prefix.endswith("/"):
        prefix = prefix + "/"

    file_paths = listfile(dir_path,
                          include_patterns=include_patterns,
                          exclude_patterns=exclude_patterns,
                          depth=depth)

    def upload_file(file_path: str):
        s3_cp_upload(client, file_path, bucket, prefix + os.path.relpath(file_path, dir_path))

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(upload_file, file_path) for file_path in file_paths]
        done_futures, not_done_futures = concurrent.futures.wait(futures,
                                                                 return_when=concurrent.futures.FIRST_EXCEPTION)
        if len(not_done_futures) > 0:
            for future in not_done_futures:
                future.cancel()
        for future in done_futures:
            exc = future.exception()
            if exc is not None:
                raise exc
        if len(not_done_futures) > 0:
            raise RuntimeError("upload did not complete due to errors in some threads")


def s3_pull_text(client: S3Client, bucket: str, key: str, encoding: str = None) -> str:
    """
    Downloads and decodes text content stored as an object in the given S3 ``bucket`` and ``key``.

    :param client: An instance of ``S3Client``.
    :param bucket: Bucket name.
    :param key: Object key storing the text.
    :param encoding: String encoding to use (defaults to UTF-8).
    :return: The decoded text content.
    """
    with tempfile.TemporaryFile() as fp:
        client.client.download_fileobj(bucket, key, fp)
        fp.seek(0)
        return fp.read().decode(encoding or "utf-8")


def s3_push_text(client: S3Client, text: str, bucket: str, key: str, encoding: str = None):
    """
    Uploads the given text as an object to the specified S3 ``bucket`` and ``key``.

    :param client: An instance of ``S3Client``.
    :param text: Text content to upload.
    :param bucket: Bucket name.
    :param key: Object key to store the text.
    :param encoding: String encoding to use (defaults to UTF-8).
    """
    with tempfile.TemporaryFile() as fp:
        fp.write(text.encode(encoding or "utf-8"))
        fp.seek(0)
        client.client.upload_fileobj(fp, bucket, key)


TransferDirection = Literal["download", "upload"]
TransferState = Literal["start", "update", "stop"]


@contextlib.contextmanager
def make_transfer_callback(
    callback: Callable[[CloudPath, TransferDirection, TransferState, int], None],
    path: Path | CloudPath,
    direction: TransferDirection,
):
    if callback is None:
        yield None
        return

    callback(path, direction, "start", 0)
    try:
        yield functools.partial(callback, path, direction, "update")
    finally:
        callback(path, direction, "stop", 0)


class S3TransferCallbackClient(S3Client):
    def __init__(
        self,
        *args,
        transfer_callback: Callable[[Path | CloudPath, TransferDirection, TransferState, int], None],
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.transfer_callback = transfer_callback

    def _download_file(self, cloud_path: S3Path, local_path: str | os.PathLike[str]) -> Path:
        local_path = Path(local_path)

        obj = self.s3.Object(cloud_path.bucket, cloud_path.key)

        with make_transfer_callback(self.transfer_callback, cloud_path, "download") as callback:
            obj.download_file(
                str(local_path),
                Config=self.boto3_transfer_config,
                ExtraArgs=self.boto3_dl_extra_args,
                Callback=callback,
            )
        return local_path

    def _upload_file(self, local_path: str | os.PathLike[str], cloud_path: S3Path) -> S3Path:
        local_path = Path(local_path)

        obj = self.s3.Object(cloud_path.bucket, cloud_path.key)

        extra_args = self.boto3_ul_extra_args.copy()

        if self.content_type_method is not None:
            content_type, content_encoding = self.content_type_method(str(local_path))
            if content_type is not None:
                extra_args["ContentType"] = content_type
            if content_encoding is not None:
                extra_args["ContentEncoding"] = content_encoding

        with make_transfer_callback(self.transfer_callback, local_path, "upload") as callback:
            obj.upload_file(
                str(local_path),
                Config=self.boto3_transfer_config,
                ExtraArgs=extra_args,
                Callback=callback,
            )
        return cloud_path


def s3_make_progress_callback(
    progress: Progress,
) -> Callable[[Path | CloudPath, TransferDirection, TransferState, int], None]:
    task_ids: dict[Path | CloudPath, TaskID] = {}

    def progress_callback(path: Path | CloudPath, direction: TransferDirection, state: TransferState, bytes_sent: int):
        if state == "start":
            size = path.stat().st_size
            task_ids[path] = progress.add_task(direction, total=size, filename=path.name)
        elif state == "stop":
            if path in task_ids:
                progress.remove_task(task_ids[path])
                del task_ids[path]
        else:
            progress.update(task_ids[path], advance=bytes_sent)

    return progress_callback


if typing.TYPE_CHECKING:
    def s3_make_progressed_client(
        access_key_id: str = None,
        secret_access_key: str = None,
        region_name: str = None,
        endpoint_url: str = None,
    ) -> contextlib.AbstractContextManager[S3Client]: ...


@contextlib.contextmanager
def s3_make_progressed_client(
    access_key_id: str = None,
    secret_access_key: str = None,
    region_name: str = None,
    endpoint_url: str = None,
) -> Generator[S3Client, None, None]:
    """
    Creates an S3 client with progress callback as a context manager for safe resource handling.

    :param access_key_id: AWS access key ID.
    :param secret_access_key: AWS secret access key.
    :param region_name: AWS service region name.
    :param endpoint_url: AWS service endpoint URL.
    :return: An instance of ``S3TransferCallbackClient``.
    """
    with Progress(
        TextColumn("[blue]{task.fields[filename]}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
    ) as progress:
        session = boto3.Session(aws_access_key_id=trim_to_none(access_key_id),
                                aws_secret_access_key=trim_to_none(secret_access_key),
                                region_name=trim_to_none(region_name))
        yield S3TransferCallbackClient(boto3_session=session,
                                       endpoint_url=trim_to_none(endpoint_url),
                                       transfer_callback=s3_make_progress_callback(progress))


def s3_options_from_s3_client(client: S3Client) -> dict[str, Any]:
    """
    Extracts S3 connection options from an existing S3Client instance for use with ``fsspec``.

    :param client: An instance of ``S3Client``.
    :return: A dictionary of S3 connection options.
    """
    if client.sess is None:
        return {}

    s3_options: dict[str, Any] = {}

    credentials = client.sess.get_credentials()
    if credentials is not None:
        if credentials.access_key:
            s3_options["key"] = credentials.access_key
        if credentials.secret_key:
            s3_options["secret"] = credentials.secret_key
        if credentials.token:
            s3_options["token"] = credentials.token

    client_kwargs = {}
    if client.sess.region_name or client.client.meta.region_name:
        client_kwargs["region_name"] = client.sess.region_name or client.client.meta.region_name
    if client.client.meta.endpoint_url:
        client_kwargs["endpoint_url"] = client.client.meta.endpoint_url

    if client_kwargs:
        s3_options["client_kwargs"] = client_kwargs

    return s3_options


type ArchiveMemberTree = dict[str, tuple[zipfile.ZipInfo, ArchiveMemberTree | None]]


def s3_archive_member_tree(
    client: S3Client,
    bucket: str,
    key: str,
) -> ArchiveMemberTree:
    """
    Builds a tree structure of members in a ZIP archive stored in S3 for efficient lookup.
    Directories have ZipInfo and a nested dict; files have ZipInfo and None.
    Directory members are recognized by names ending with a trailing slash ("/").

    Example:
    {
      "dir1/": (ZipInfo, {
          "file1.txt": (ZipInfo, None),
          "subdir/": (ZipInfo, {
              "file2.txt": (ZipInfo, None)
          })
      }),
      "file3.txt": (ZipInfo, None)
    }

    :param client: An instance of ``S3Client``.
    :param bucket: Bucket name.
    :param key: Object key of the ZIP archive.
    :return: A tree structure of members in the ZIP archive.
    """
    s3_options = s3_options_from_s3_client(client)

    archive_url = f"s3://{bucket}/{key}"

    with fsspec.open(archive_url, "rb", s3=s3_options) as s3_fh, zipfile.ZipFile(s3_fh) as archive:
        member_zip_infos = archive.infolist()

    root_member_tree: ArchiveMemberTree = {}

    def build_member_tree(info: zipfile.ZipInfo):
        *parts, last_part = info.filename.rstrip("/").split("/")
        current_member_tree = root_member_tree
        for part in parts:
            _, current_member_tree = current_member_tree.setdefault(part + "/", (None, {}))
        if info.is_dir():
            current_member_tree[last_part + "/"] = info, {}
        else:
            current_member_tree[last_part] = info, None

    # Sort by filename to ensure directories are created before their contents
    for info in sorted(member_zip_infos, key=lambda x: x.filename):
        build_member_tree(info)

    return root_member_tree


def s3_archive_listfile(
    client: S3Client,
    bucket: str,
    key: str,
    members: list[str] | None = None,
) -> tuple[int, list[zipfile.ZipInfo], list[str]]:
    """
    Lists members of a ZIP archive stored in S3, optionally filtering by specific member names. When filtering,
    if a member is a directory, it must end with a trailing slash ("/") to be recognized as such, and all files
    under that directory will be included in the results.

    Example usage:
    >>> archive_size, member_zip_infos, missed_members = s3_archive_listfile(client, bucket, key, members=["file1.txt", "dir1/"])
    >>> for info in member_zip_infos:
    ...     print(info.filename, info.file_size)
    >>> if missed_members:
    ...     print("Members not found:", missed_members)

    :param client: An instance of ``S3Client``.
    :param bucket: Bucket name.
    :param key: Object key of the ZIP archive.
    :param members: Optional list of member names to filter; if ``None``, all members are returned.
    :return: A tuple containing:
             - The size of the archive in bytes.
             - A list of ``zipfile.ZipInfo`` objects for the included members.
             - A list of member names that were not found in the archive.
    """
    s3_options = s3_options_from_s3_client(client)

    archive_url = f"s3://{bucket}/{key}"

    fs = fsspec.filesystem("s3", **s3_options)
    archive_size = fs.size(archive_url)

    root_member_tree = s3_archive_member_tree(client, bucket, key)

    def search_members_tree(member: str) -> tuple[zipfile.ZipInfo | None, dict | None]:
        *parts, last_part = member.rstrip("/").split("/")
        current_member_tree = root_member_tree
        for part in parts:
            _, current_member_tree = current_member_tree.get(part + "/", (None, None))
            if current_member_tree is None:
                return None, None
        if member.endswith("/"):  # Directory member recognized by trailing slash
            return current_member_tree.get(last_part + "/", (None, None))
        else:
            return current_member_tree.get(last_part, (None, None))

    def collect_member_zip_infos(tree: ArchiveMemberTree) -> Generator[zipfile.ZipInfo, None, None]:
        for member_zip_info, member_tree in tree.values():
            if member_zip_info is None:
                continue
            if member_zip_info.is_dir():
                yield from collect_member_zip_infos(member_tree)
            else:
                yield member_zip_info

    if members is None:
        return archive_size, list(collect_member_zip_infos(root_member_tree)), []

    included_member_zip_infos = []
    missed_members = []

    for member in members:
        member_zip_info, member_tree = search_members_tree(member)
        if member_zip_info is None:
            missed_members.append(member)
            continue
        if not member_zip_info.is_dir():
            included_member_zip_infos.append(member_zip_info)
        else:
            included_member_zip_infos.extend(collect_member_zip_infos(member_tree or {}))

    return archive_size, included_member_zip_infos, missed_members


if typing.TYPE_CHECKING:
    def s3_archive_open_member(
        client: S3Client,
        bucket: str,
        key: str,
        member: str,
        mode: Literal["r", "rb"] = "r",
    ) -> contextlib.AbstractContextManager[typing.IO]: ...


@contextlib.contextmanager
def s3_archive_open_member(
    client: S3Client,
    bucket: str,
    key: str,
    member: str,
    mode: Literal["r", "rb"] = "r",
) -> Generator[typing.IO, None, None]:
    """
    Opens a specific member file from a ZIP archive stored in S3.

    :param client: An instance of ``S3Client``.
    :param bucket: Bucket name.
    :param key: Object key of the ZIP archive.
    :param member: The member file name to open from the archive.
    :param mode: File mode for opening the member ("r" for text, "rb" for binary).

    :return: A file-like object for the specified member within the ZIP archive.
    """
    if mode not in ("r", "rb"):
        raise ValueError("mode must be either 'r' or 'rb'")

    s3_options = s3_options_from_s3_client(client)

    with fsspec.open(f"zip://{member}::s3://{bucket}/{key}", mode, s3=s3_options) as s3_fh:
        yield s3_fh


ZIP_CENTRAL_DIR_ESTIMATED_SIZE = 64 * 1024
ZIP_INFO_HDR_MIN_SIZE = 30
ZIP_INFO_HDR_ESTIMATED_SIZE = 128
ZIP_INFO_HDR_FN_LEN_OFFSET = 26
ZIP_INFO_HDR_EX_LEN_OFFSET = 28


@dataclasses.dataclass(frozen=True)
class ArchiveMemberChunk(object):
    name: str
    header_offset: int
    compress_size: int
    compress_type: int
    header_overhead: int = ZIP_INFO_HDR_ESTIMATED_SIZE

    @property
    def begin(self) -> int:
        return self.header_offset

    @property
    def end(self) -> int:
        return self.header_offset + self.header_overhead + self.compress_size


def s3_archive_use_ranged_requests(
    threshold: float = 0.5,
    central_directory_overhead: int = 64 * ZIP_CENTRAL_DIR_ESTIMATED_SIZE,
    zip_info_header_overhead: int = ZIP_INFO_HDR_ESTIMATED_SIZE,
) -> Callable[[int, list[zipfile.ZipInfo]], bool]:
    """
    Decide whether to use ranged requests for accessing members of a ZIP archive in S3
    based on estimated transfer size ratio.

    :param threshold: If (estimated ranged transfer bytes / archive bytes) <= threshold, use ranged per-member access;
                      otherwise download the whole archive.
    :param central_directory_overhead: Estimated overhead size for the central directory in bytes.
    :param zip_info_header_overhead: Estimated overhead size for each member's ``ZipInfo`` header in bytes.
    :return: A callable that takes (``archive_size``, ``member_zip_infos``) and returns a boolean
             indicating whether to use ranged requests.
    """

    if zip_info_header_overhead < ZIP_INFO_HDR_MIN_SIZE:
        raise ValueError(f"zip_info_header_overhead must be at least {ZIP_INFO_HDR_MIN_SIZE} bytes")

    def use_ranged_requests(
        archive_size: int,
        member_zip_infos: list[zipfile.ZipInfo],
    ) -> bool:
        estimated_ranged_total_size = central_directory_overhead + sum(info.compress_size + zip_info_header_overhead
                                                                       for info in member_zip_infos)

        # Avoid division by zero; prefer ranged if archive size is zero (degenerate case)
        return (estimated_ranged_total_size / archive_size) <= threshold if archive_size > 0 else True

    return use_ranged_requests


def s3_archive_use_chunked_reads(
    zip_info_header_overhead: int = ZIP_INFO_HDR_ESTIMATED_SIZE,
) -> Callable[[zipfile.ZipInfo], ArchiveMemberChunk]:
    """
    Map each ``ZipInfo`` to an ``ArchiveMemberChunk`` for grouping adjacent members into single ranged reads.

    :param zip_info_header_overhead: Estimated overhead size for each member's ``ZipInfo`` header in bytes.
    :return: A callable that takes a ``ZipInfo`` and returns an ``ArchiveMemberChunk``.
    """

    if zip_info_header_overhead < ZIP_INFO_HDR_MIN_SIZE:
        raise ValueError(f"zip_info_header_overhead must be at least {ZIP_INFO_HDR_MIN_SIZE} bytes")

    def use_chunked_reads(
        zip_info: zipfile.ZipInfo,
    ) -> ArchiveMemberChunk:
        return ArchiveMemberChunk(zip_info.filename,
                                  zip_info.header_offset,
                                  zip_info.compress_size,
                                  zip_info.compress_type,
                                  header_overhead=zip_info_header_overhead)

    return use_chunked_reads


def s3_archive_open_members(
    client: S3Client,
    bucket: str,
    key: str,
    members: list[str] | None = None,
    mode: Literal["r", "rb"] = "r",
    *,
    use_ranged_requests: bool | Callable[[int, list[zipfile.ZipInfo]], bool] = True,
    use_chunked_reads: bool | Callable[[zipfile.ZipInfo], ArchiveMemberChunk] = False,
) -> Generator[tuple[str, Callable[[], typing.IO]], None, None]:
    """
    Choose the best transfer strategy (ranged requests per-member vs full archive transfer)
    based on estimated transfer size ratio and yield callables to open each requested member.

    The callables return file-like objects for each member when invoked. Due to lazy evaluation,
    the actual data transfer occurs when the member is opened by the corresponding callable.
    Thus, the callables must be used immediately after being yielded, to avoid issues with temporary
    file lifetimes.

    Example usage:

    >>> for member, opener in s3_archive_open_members(client, bucket, key, members):
    ...     with opener() as fh:
    ...         data = fh.read()

    Incorrect usage that may lead to errors due to temporary file cleanup:

    >>> openers = []
    >>> for member, opener in s3_archive_open_members(client, bucket, key, members):
    ...     openers.append((member, opener))
    >>> for member, opener in openers:
    ...     with opener() as fh:  # May fail if temporary files have been cleaned up
    ...         data = fh.read()

    :param client: An instance of ``S3Client``.
    :param bucket: Bucket name.
    :param key: Object key of the ZIP archive.
    :param members: List of member names to stream.
    :param mode: File mode for opening members ("r" for text, "rb" for binary).
    :param use_ranged_requests: If ``True``, always use ranged requests to access the archive; if callable, use it as
                                custom logic to decide based on the archive size and member infos; if ``False``, always
                                download the whole archive.
    :param use_chunked_reads: If ``True``, group adjacent members into single ranged reads using default ``ZipInfo``
                              to ``ArchiveMemberChunk`` mapping; if callable, use it as custom mapping from
                              ``ZipInfo`` to ``ArchiveMemberChunk`` for grouping adjacent members; if ``False``,
                              read each member with individual ranged requests. If ``use_ranged_requests`` is ``False``,
                              this parameter is ignored.

    :return: An iterable of callables that return file-like objects for each requested member.
    """
    if mode not in ("r", "rb"):
        raise ValueError("mode must be either 'r' or 'rb'")

    s3_options = s3_options_from_s3_client(client)

    archive_size, member_zip_infos, missed_members = s3_archive_listfile(client, bucket, key, members)
    if missed_members:
        raise FileNotFoundError(f"Archive members not found: {', '.join(missed_members)}")

    if callable(use_ranged_requests):
        use_ranged_requests = use_ranged_requests(archive_size, member_zip_infos)

    if use_ranged_requests and not use_chunked_reads:
        for info in member_zip_infos:
            opener = functools.partial(s3_archive_open_member, client, bucket, key, info.filename, mode)
            yield info.filename, opener
        return

    archive_url = f"s3://{bucket}/{key}"

    if use_ranged_requests and use_chunked_reads:

        fn_len_slice = lambda index: slice(index + ZIP_INFO_HDR_FN_LEN_OFFSET, index + ZIP_INFO_HDR_FN_LEN_OFFSET + 2)
        ex_len_slice = lambda index: slice(index + ZIP_INFO_HDR_EX_LEN_OFFSET, index + ZIP_INFO_HDR_EX_LEN_OFFSET + 2)

        # Open archive once to read central directory and gather ZipInfo for requested members.
        # We will group adjacent members (by local header offsets) and issue one ranged read per group,
        # then extract each member from the group's bytes to avoid many small ranged requests.
        with fsspec.open(archive_url, "rb", s3=s3_options) as s3_fh, zipfile.ZipFile(s3_fh) as archive:
            if callable(use_chunked_reads):
                chunks = [use_chunked_reads(info) for info in member_zip_infos]
            else:
                chunks = [ArchiveMemberChunk(info.filename, info.header_offset, info.compress_size, info.compress_type)
                          for info in member_zip_infos]

            chunks_groups = chunk_between(sorted(chunks, key=lambda x: x.begin),
                                          chunk_func=lambda x, y: y.begin > x.end)

            # For each group, create openers for members inside the group.
            for group in chunks_groups:
                group_offset = head(group).header_offset
                group_size = last(group).end - group_offset

                # Read group's bytes from remote (single ranged read)
                s3_fh.seek(group_offset)
                group_bytes = s3_fh.read(group_size)

                def make_opener(chunk: ArchiveMemberChunk) -> Callable[[], typing.IO]:

                    def opener() -> typing.IO:
                        index = chunk.header_offset - group_offset

                        if index + ZIP_INFO_HDR_MIN_SIZE > len(group_bytes):
                            raise IOError("unexpected short read of member header")

                        fn_len = int.from_bytes(group_bytes[fn_len_slice(index)], "little")
                        ex_len = int.from_bytes(group_bytes[ex_len_slice(index)], "little")

                        raw_data_begin = index + ZIP_INFO_HDR_MIN_SIZE + fn_len + ex_len
                        raw_data_end = raw_data_begin + chunk.compress_size

                        if raw_data_end > len(group_bytes):
                            raise IOError("unexpected short read of compressed data")

                        raw_data = group_bytes[raw_data_begin:raw_data_end]

                        if chunk.compress_type == zipfile.ZIP_STORED:
                            pass
                        elif chunk.compress_type == zipfile.ZIP_DEFLATED:
                            raw_data = zlib.decompress(raw_data, -zlib.MAX_WBITS)
                        else:
                            raise NotImplementedError(f"unsupported compression '{chunk.compress_type}'")

                        if mode == "r":
                            return io.TextIOWrapper(io.BytesIO(raw_data), encoding="utf-8")
                        else:
                            return io.BytesIO(raw_data)

                    return opener

                yield from ((chunk.name, make_opener(chunk)) for chunk in group)
        return

    # Download full archive once and serve members from it (read member bytes into memory)
    with fsspec.open(archive_url, "rb", s3=s3_options) as s3_fh, tempfile.TemporaryFile() as temp_fh:
        shutil.copyfileobj(s3_fh, temp_fh)
        temp_fh.seek(0)
        with zipfile.ZipFile(temp_fh) as archive:
            for info in member_zip_infos:
                try:
                    if mode == "r":
                        opener = lambda fn=info.filename: io.TextIOWrapper(archive.open(fn), encoding="utf-8")
                    else:
                        opener = lambda fn=info.filename: archive.open(fn)
                    yield info.filename, opener
                except KeyError as e:
                    # Shouldn't happen due to earlier check, but guard anyway
                    raise FileNotFoundError(info.filename) from e
