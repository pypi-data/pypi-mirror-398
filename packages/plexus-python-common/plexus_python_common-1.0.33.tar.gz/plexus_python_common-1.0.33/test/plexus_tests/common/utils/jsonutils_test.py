import os.path
import unittest

import ddt

from plexus.common.utils.jsonutils import read_chunked_jsonl
from plexus_test import resources_directory


@ddt.ddt
class JsonUtilsTest(unittest.TestCase):

    def test_read_chunked_jsonl(self):
        for data, path in read_chunked_jsonl(
            os.path.join(resources_directory, "unittest/jsonutils", "dummy.{{}}.jsonl")):
            self.assertEqual(data["file"], os.path.basename(path))
