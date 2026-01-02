import unittest

import ddt

from plexus.common.utils.datautils import random_vin_code, validate_vin_code


@ddt.ddt
class DataUtilsTest(unittest.TestCase):
    data_validate_vin_code = [
        ("00000000000000000",),
        ("MYKDB5B29544W3JVM",),
        ("3M56ZC619SRYJ95B7",),
        ("93D479KA82VTCRZT0",),
        ("S5S3ADS145NRMHB79",),
        ("SV737FCBXCW3KWPMS",),
    ]

    @ddt.idata(data_validate_vin_code)
    @ddt.unpack
    def test_validate_vin_code(self, data):
        validate_vin_code(data)

    def test_validate_vin_code__random_generation(self):
        for _ in range(1000):
            validate_vin_code(random_vin_code())

    data_validate_vin_code__bad_case = [
        ("AAAAAAAAAAAAAAAAA",),
        ("0123456789ABCDEFG",),
        ("HJKLMNPRSTUVWXYZ0",),
    ]

    @ddt.idata(data_validate_vin_code__bad_case)
    @ddt.unpack
    def test_validate_vin_code__bad_case(self, data):
        with self.assertRaises(ValueError):
            validate_vin_code(data)
