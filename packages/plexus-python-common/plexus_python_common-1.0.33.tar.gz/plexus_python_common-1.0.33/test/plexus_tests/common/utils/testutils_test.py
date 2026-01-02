import unittest

import ddt

from plexus.common.utils.testutils import generate_dummy_uuid_str, generate_dummy_vin_code


@ddt.ddt
class TestUtilsTest(unittest.TestCase):
    data_generate_dummy_uuid_str = [
        ((), "00000000-0000-0000-0000-000000000000"),
        ((0,), "00000000-0000-0000-0000-000000000000"),
        ((0, 0,), "00000000-0000-0000-0000-000000000000"),
        ((0, 0, 0, 0, 0, 0, 0, 0,), "00000000-0000-0000-0000-000000000000"),
        ((1,), "00010000-0000-0000-0000-000000000000"),
        ((1, 2, 3, 4, 5, 6, 7, 8,), "00010002-0003-0004-0005-000600070008"),
        ((0x1, 0x10, 0x100, 0x1000, 0xF, 0xFF, 0xFFF, 0xFFFF,), "00010010-0100-1000-000f-00ff0fffffff"),
    ]

    @ddt.idata(data_generate_dummy_uuid_str)
    @ddt.unpack
    def test_generate_dummy_uuid_str(self, nums, expect):
        self.assertEqual(generate_dummy_uuid_str(*nums), expect)

    data_generate_dummy_uuid_str__bad_case = [
        ((0, 0, 0, 0, 0, 0, 0, 0, 0,),),
        ((-1,),),
        ((0x10000,),),
    ]

    @ddt.idata(data_generate_dummy_uuid_str__bad_case)
    @ddt.unpack
    def test_generate_dummy_uuid_str__bad_case(self, nums):
        with self.assertRaises(ValueError):
            generate_dummy_uuid_str(*nums)

    data_generate_dummy_vin_code = [
        ((), "00000000000000000"),
        ((0,), "00000000000000000"),
        ((0, 0,), "00000000000000000"),
        ((0, 0, 0, 0,), "00000000000000000"),
        ((1,), "00010000500000000"),
        ((1, 2, 3, 4,), "00010002700030004"),
        ((1, 23, 456, 7890,), "00010023504567890"),
    ]

    @ddt.idata(data_generate_dummy_vin_code)
    @ddt.unpack
    def test_generate_dummy_vin_code(self, nums, expect):
        self.assertEqual(generate_dummy_vin_code(*nums), expect)
