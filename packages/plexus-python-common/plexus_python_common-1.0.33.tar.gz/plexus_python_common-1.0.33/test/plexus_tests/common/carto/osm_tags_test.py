import unittest

import ddt
from iker.common.utils.dtutils import dt_utc, dt_utc_epoch

from plexus.common.carto import OSMTags


@ddt.ddt
class OSMTagsTest(unittest.TestCase):
    data_from_any_tags = [
        (
            {
                "dummy_int": "1",
                "dummy_float": "1.0",
                "dummy_boolean": "False",
                "dummy_datetime": "1970-01-01T00:00:00",
                "dummy_str": "dummy",
            },
            {
                "dummy_int": 1,
                "dummy_float": 1.0,
                "dummy_boolean": False,
                "dummy_datetime": dt_utc(1970, 1, 1, 0, 0, 0),
                "dummy_str": "dummy",
            },
        ),
        (
            {
                "dummy_int": 100,
                "dummy_float": 100.0,
                "dummy_boolean": True,
                "dummy_datetime": dt_utc(2020, 1, 1, 12, 30, 45),
                "dummy_str": "dummy",
            },
            {
                "dummy_int": 100,
                "dummy_float": 100.0,
                "dummy_boolean": True,
                "dummy_datetime": dt_utc(2020, 1, 1, 12, 30, 45),
                "dummy_str": "dummy",
            }
        ),
    ]

    @ddt.idata(data_from_any_tags)
    @ddt.unpack
    def test_from_any_tags(self, data, expect):
        tags = OSMTags.from_any_tags(data)
        self.assertEqual(expect, tags.tags)

    data_builtin_iter = [
        (
            {
                "dummy_int": "1",
                "dummy_float": "1.0",
                "dummy_boolean": "False",
                "dummy_datetime": "1970-01-01T00:00:00",
                "dummy_str": "dummy",
            },
        ),
        (
            {
                "dummy_int": 100,
                "dummy_float": 100.0,
                "dummy_boolean": True,
                "dummy_datetime": dt_utc(2020, 1, 1, 12, 30, 45),
                "dummy_str": "dummy",
            },
        ),
    ]

    @ddt.idata(data_builtin_iter)
    @ddt.unpack
    def test_builtin_iter(self, data):
        tags = OSMTags.from_any_tags(data)
        for item in data:
            self.assertIn(item, tags)

    data_builtin_getitem = [
        (
            {
                "dummy_int": "1",
                "dummy_float": "1.0",
                "dummy_boolean": "False",
                "dummy_datetime": "1970-01-01T00:00:00",
                "dummy_str": "dummy",
            },
            {
                "dummy_int": 1,
                "dummy_float": 1.0,
                "dummy_boolean": False,
                "dummy_datetime": dt_utc(1970, 1, 1, 0, 0, 0),
                "dummy_str": "dummy",
            }
        ),
        (
            {
                "dummy_int": 100,
                "dummy_float": 100.0,
                "dummy_boolean": True,
                "dummy_datetime": dt_utc(2020, 1, 1, 12, 30, 45),
                "dummy_str": "dummy",
            },
            {
                "dummy_int": 100,
                "dummy_float": 100.0,
                "dummy_boolean": True,
                "dummy_datetime": dt_utc(2020, 1, 1, 12, 30, 45),
                "dummy_str": "dummy",
            }
        ),
    ]

    @ddt.idata(data_builtin_getitem)
    @ddt.unpack
    def test_builtin_getitem(self, data, expected):
        tags = OSMTags.from_any_tags(data)
        for item, _ in data.items():
            self.assertEqual(expected[item], tags[item])

    data_getint = [
        ({"dummy": "1"}, 100, 1),
        ({"dummy": "-1"}, 100, -1),
        ({"dummy": "1.0"}, 100, 100),
        ({"dummy": "-1.0"}, 100, 100),
        ({"dummy": "False"}, 100, 100),
        ({"dummy": "True"}, 100, 100),
        ({"dummy": "1970-01-01T00:00:00"}, 100, 100),
        ({"dummy": "dummy"}, 100, 100),
        ({}, 100, 100),
        ({}, None, None),
    ]

    @ddt.idata(data_getint)
    @ddt.unpack
    def test_getint(self, data, default, expected):
        tags = OSMTags.from_any_tags(data)
        self.assertEqual(expected, tags.getint("dummy", default))

    data_getfloat = [
        ({"dummy": "1"}, 100.0, 100.0),
        ({"dummy": "-1"}, 100.0, 100.0),
        ({"dummy": "1.0"}, 100.0, 1.0),
        ({"dummy": "-1.0"}, 100.0, -1.0),
        ({"dummy": "False"}, 100.0, 100.0),
        ({"dummy": "True"}, 100.0, 100.0),
        ({"dummy": "1970-01-01T00:00:00"}, 100.0, 100.0),
        ({"dummy": "dummy"}, 100.0, 100.0),
        ({}, 100.0, 100.0),
        ({}, None, None),
    ]

    @ddt.idata(data_getfloat)
    @ddt.unpack
    def test_getfloat(self, data, default, expected):
        tags = OSMTags.from_any_tags(data)
        self.assertEqual(expected, tags.getfloat("dummy", default))

    data_getboolean = [
        ({"dummy": "1"}, False, False),
        ({"dummy": "-1"}, False, False),
        ({"dummy": "1.0"}, False, False),
        ({"dummy": "-1.0"}, False, False),
        ({"dummy": "False"}, False, False),
        ({"dummy": "True"}, False, True),
        ({"dummy": "1970-01-01T00:00:00"}, False, False),
        ({"dummy": "dummy"}, False, False),
        ({}, False, False),
        ({}, None, None),
    ]

    @ddt.idata(data_getboolean)
    @ddt.unpack
    def test_getboolean(self, data, default, expected):
        tags = OSMTags.from_any_tags(data)
        self.assertEqual(expected, tags.getboolean("dummy", default))

    data_getdatetime = [
        ({"dummy": "1"}, dt_utc_epoch(), dt_utc_epoch()),
        ({"dummy": "-1"}, dt_utc_epoch(), dt_utc_epoch()),
        ({"dummy": "1.0"}, dt_utc_epoch(), dt_utc_epoch()),
        ({"dummy": "-1.0"}, dt_utc_epoch(), dt_utc_epoch()),
        ({"dummy": "False"}, dt_utc_epoch(), dt_utc_epoch()),
        ({"dummy": "True"}, dt_utc_epoch(), dt_utc_epoch()),
        ({"dummy": "2020-01-01T00:00:00"}, dt_utc_epoch(), dt_utc(2020, 1, 1, 0, 0, 0)),
        ({"dummy": "dummy"}, dt_utc_epoch(), dt_utc_epoch()),
        ({}, dt_utc_epoch(), dt_utc_epoch()),
        ({}, None, None),
    ]

    @ddt.idata(data_getdatetime)
    @ddt.unpack
    def test_getdatetime(self, data, default, expected):
        tags = OSMTags.from_any_tags(data)
        self.assertEqual(expected, tags.getdatetime("dummy", default))
