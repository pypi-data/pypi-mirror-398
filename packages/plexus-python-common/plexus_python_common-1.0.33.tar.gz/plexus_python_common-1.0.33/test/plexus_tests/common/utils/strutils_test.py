import unittest

import ddt
import pyparsing as pp
from iker.common.utils.dtutils import dt_parse_iso

from plexus.common.utils.strutils import BagName, UserEmail, UserName, VehicleName
from plexus.common.utils.strutils import colon_tag_parser, colon_tag_pattern, slash_tag_parser, slash_tag_pattern
from plexus.common.utils.strutils import dot_case_parser, dot_case_pattern
from plexus.common.utils.strutils import email_address_parser, email_address_pattern, semver_parser, semver_pattern
from plexus.common.utils.strutils import hex_string_parser, hex_string_pattern
from plexus.common.utils.strutils import kebab_case_parser, kebab_case_pattern
from plexus.common.utils.strutils import parse_bag_name, parse_user_email, parse_user_name, parse_vehicle_name
from plexus.common.utils.strutils import snake_case_parser, snake_case_pattern
from plexus.common.utils.strutils import strict_abspath_parser, strict_abspath_pattern
from plexus.common.utils.strutils import strict_archive_abspath_parser, strict_archive_abspath_pattern
from plexus.common.utils.strutils import strict_archive_relpath_parser, strict_archive_relpath_pattern
from plexus.common.utils.strutils import strict_relpath_parser, strict_relpath_pattern
from plexus.common.utils.strutils import topic_parser, topic_pattern
from plexus.common.utils.strutils import vin_code_parser, vin_code_pattern


@ddt.ddt
class StrUtilsTest(unittest.TestCase):
    data_hex_string_pattern = [
        ("0",),
        ("a",),
        ("0123456789abcdef",),
    ]

    @ddt.idata(data_hex_string_pattern)
    @ddt.unpack
    def test_hex_string_pattern(self, data):
        self.assertIsNotNone(hex_string_pattern.match(data))
        self.assertIsNotNone(hex_string_parser.parse_string(data, parse_all=True))

    data_hex_string_pattern__bad_cases = [
        ("",),
        ("A",),
        ("g",),
        ("0123456789ABCDEF",),
        (" 0123456789abcdef",),
        ("0123456789abcdef ",),
        ("!",),
    ]

    @ddt.idata(data_hex_string_pattern__bad_cases)
    @ddt.unpack
    def test_hex_string_pattern__bad_cases(self, data):
        self.assertIsNone(hex_string_pattern.match(data))
        with self.assertRaises(pp.ParseException):
            hex_string_parser.parse_string(data, parse_all=True)

    data_snake_case_pattern = [
        ("d",),
        ("0",),
        ("dummy",),
        ("12345",),
        ("dummy12345",),
        ("12345dummy",),
        ("dummy12345dummy",),
        ("12345dummy12345",),
        ("dummy_dummy",),
        ("dummy_12345",),
        ("12345_dummy",),
        ("12345_12345",),
        ("dummy12345dummy_12345dummy12345",),
        ("dummy_dummy_dummy",),
        ("12345_12345_12345",),
        ("dummy_12345_dummy",),
        ("12345_dummy_12345",),
    ]

    @ddt.idata(data_snake_case_pattern)
    @ddt.unpack
    def test_snake_case_pattern(self, data):
        self.assertIsNotNone(snake_case_pattern.match(data))
        self.assertIsNotNone(snake_case_parser.parse_string(data, parse_all=True))

    data_snake_case_pattern__bad_cases = [
        ("",),
        ("_",),
        ("dummy_",),
        ("_dummy",),
        ("_dummy_",),
        ("12345_",),
        ("_12345",),
        ("_12345_",),
        ("dummy_dummy_",),
        ("_dummy_dummy",),
        ("_dummy_dummy_",),
        ("dummy__dummy",),
        ("Dummy_Dummy",),
        ("dummy+dummy",),
        ("dummy-dummy",),
        ("dummy.dummy",),
        (" dummy_12345_dummy ",),
        (" 12345_dummy_12345 ",),
    ]

    @ddt.idata(data_snake_case_pattern__bad_cases)
    @ddt.unpack
    def test_snake_case_pattern__bad_cases(self, data):
        self.assertIsNone(snake_case_pattern.match(data))
        with self.assertRaises(pp.ParseException):
            snake_case_parser.parse_string(data, parse_all=True)

    data_kebab_case_pattern = [
        ("d",),
        ("0",),
        ("dummy",),
        ("12345",),
        ("dummy12345",),
        ("12345dummy",),
        ("dummy12345dummy",),
        ("12345dummy12345",),
        ("dummy-dummy",),
        ("dummy-12345",),
        ("12345-dummy",),
        ("12345-12345",),
        ("dummy12345dummy-12345dummy12345",),
        ("dummy-dummy-dummy",),
        ("12345-12345-12345",),
        ("dummy-12345-dummy",),
        ("12345-dummy-12345",),
    ]

    @ddt.idata(data_kebab_case_pattern)
    @ddt.unpack
    def test_kebab_case_pattern(self, data):
        self.assertIsNotNone(kebab_case_pattern.match(data))
        self.assertIsNotNone(kebab_case_parser.parse_string(data, parse_all=True))

    data_kebab_case_pattern__bad_cases = [
        ("",),
        ("-",),
        ("dummy-",),
        ("-dummy",),
        ("-dummy-",),
        ("12345-",),
        ("-12345",),
        ("-12345-",),
        ("dummy-dummy-",),
        ("-dummy-dummy",),
        ("-dummy-dummy-",),
        ("dummy--dummy",),
        ("Dummy-Dummy",),
        ("dummy+dummy",),
        ("dummy_dummy",),
        ("dummy.dummy",),
        (" dummy-12345-dummy ",),
        (" 12345-dummy-12345 ",),
    ]

    @ddt.idata(data_kebab_case_pattern__bad_cases)
    @ddt.unpack
    def test_kebab_case_pattern__bad_cases(self, data):
        self.assertIsNone(kebab_case_pattern.match(data))
        with self.assertRaises(pp.ParseException):
            kebab_case_parser.parse_string(data, parse_all=True)

    data_dot_case_pattern = [
        ("d",),
        ("0",),
        ("dummy",),
        ("12345",),
        ("dummy12345",),
        ("12345dummy",),
        ("dummy12345dummy",),
        ("12345dummy12345",),
        ("dummy.dummy",),
        ("dummy.12345",),
        ("12345.dummy",),
        ("12345.12345",),
        ("dummy12345dummy.12345dummy12345",),
        ("dummy.dummy.dummy",),
        ("12345.12345.12345",),
        ("dummy.12345.dummy",),
        ("12345.dummy.12345",),
    ]

    @ddt.idata(data_dot_case_pattern)
    @ddt.unpack
    def test_dot_case_pattern(self, data):
        self.assertIsNotNone(dot_case_pattern.match(data))
        self.assertIsNotNone(dot_case_parser.parse_string(data, parse_all=True))

    data_dot_case_pattern__bad_cases = [
        ("",),
        (".",),
        ("dummy.",),
        (".dummy",),
        (".dummy.",),
        ("12345.",),
        (".12345",),
        (".12345.",),
        ("dummy.dummy.",),
        (".dummy.dummy",),
        (".dummy.dummy.",),
        ("dummy..dummy",),
        ("Dummy.Dummy",),
        ("dummy+dummy",),
        ("dummy_dummy",),
        ("dummy-dummy",),
        (" dummy.12345.dummy ",),
        (" 12345.dummy.12345 ",),
    ]

    @ddt.idata(data_dot_case_pattern__bad_cases)
    @ddt.unpack
    def test_dot_case_pattern__bad_cases(self, data):
        self.assertIsNone(dot_case_pattern.match(data))
        with self.assertRaises(pp.ParseException):
            dot_case_parser.parse_string(data, parse_all=True)

    data_strict_relpath_pattern = [
        ("",),
        ("directory",),
        ("directory/",),
        ("directory/dummy",),
        ("directory/dummy/",),
        ("directory/dummy/path",),
        ("directory/dummy/path/",),
        ("directory/dummy/path/to",),
        ("directory/dummy/path/to/",),
        ("directory/dummy/path/to/file",),
        ("directory/dummy/path/to/file/",),
        ("directory/dummy/path_to-file.1",),
        ("directory/dummy/path_to-file.1/",),
        ("directory/dummy/path_to-file.1.",),
        ("directory/dummy/path_to-file.1./",),
        ("directory/dummy/.path_to-file.1",),
        ("directory/dummy/.path_to-file.1/",),
        ("directory/dummy/..path_to-file..1..",),
        ("directory/dummy/..path_to-file..1../",),
    ]

    @ddt.idata(data_strict_relpath_pattern)
    @ddt.unpack
    def test_strict_relpath_pattern(self, data):
        self.assertIsNotNone(strict_relpath_pattern.match(data))
        self.assertIsNotNone(strict_relpath_parser.parse_string(data, parse_all=True))

    data_strict_relpath_pattern__bad_cases = [
        ("/",),
        (".",),
        ("..",),
        ("./",),
        ("../",),
        ("/.",),
        ("/..",),
        ("//",),
        ("/directory",),
        ("directory//",),
        ("directory//dummy",),
        ("directory/@dummy",),
        ("directory/#dummy",),
        ("directory/$dummy",),
        ("directory/%dummy",),
        ("directory/^dummy",),
        ("directory/&dummy",),
        ("directory/*dummy",),
        ("directory/!dummy",),
        ("directory/?dummy",),
        ("directory/<dummy",),
        ("directory/>dummy",),
        ("directory/,dummy",),
        ("directory/|dummy",),
        ("directory/\\dummy",),
        ("directory/[dummy",),
        ("directory/]dummy",),
        ("directory/(dummy",),
        ("directory/)dummy",),
        ("directory/{dummy",),
        ("directory/}dummy",),
        ("directory/:dummy",),
        ("directory/;dummy",),
        ('directory/"dummy',),
        ("directory/'dummy",),
        ("directory/ dummy",),
        ("directory/\tdummy",),
        ("directory/\rdummy",),
        ("directory/\ndummy",),
        ("directory/./",),
        ("directory/../",),
        ("directory/.../",),
        ("directory/./dummy/path/to/file",),
        ("directory/../dummy/path/to/file",),
        ("directory/.../dummy/path/to/file",),
    ]

    @ddt.idata(data_strict_relpath_pattern__bad_cases)
    @ddt.unpack
    def test_strict_relpath_pattern__bad_cases(self, data):
        self.assertIsNone(strict_relpath_pattern.match(data))
        with self.assertRaises(pp.ParseException):
            strict_relpath_parser.parse_string(data, parse_all=True)

    data_strict_abspath_pattern = [
        ("/",),
        ("/directory",),
        ("/directory/",),
        ("/directory/dummy",),
        ("/directory/dummy/",),
        ("/directory/dummy/path",),
        ("/directory/dummy/path/",),
        ("/directory/dummy/path/to",),
        ("/directory/dummy/path/to/",),
        ("/directory/dummy/path/to/file",),
        ("/directory/dummy/path/to/file/",),
        ("/directory/dummy/path_to-file.1",),
        ("/directory/dummy/path_to-file.1/",),
        ("/directory/dummy/path_to-file.1.",),
        ("/directory/dummy/path_to-file.1./",),
        ("/directory/dummy/.path_to-file.1",),
        ("/directory/dummy/.path_to-file.1/",),
        ("/directory/dummy/..path_to-file..1..",),
        ("/directory/dummy/..path_to-file..1../",),
    ]

    @ddt.idata(data_strict_abspath_pattern)
    @ddt.unpack
    def test_strict_abspath_pattern(self, data):
        self.assertIsNotNone(strict_abspath_pattern.match(data))
        self.assertIsNotNone(strict_abspath_parser.parse_string(data, parse_all=True))

    data_strict_abspath_pattern__bad_cases = [
        ("",),
        (".",),
        ("..",),
        ("./",),
        ("../",),
        ("/.",),
        ("/..",),
        ("//",),
        ("directory",),
        ("/directory//",),
        ("/directory//dummy",),
        ("/directory/@dummy",),
        ("/directory/#dummy",),
        ("/directory/$dummy",),
        ("/directory/%dummy",),
        ("/directory/^dummy",),
        ("/directory/&dummy",),
        ("/directory/*dummy",),
        ("/directory/!dummy",),
        ("/directory/?dummy",),
        ("/directory/<dummy",),
        ("/directory/>dummy",),
        ("/directory/,dummy",),
        ("/directory/|dummy",),
        ("/directory/\\dummy",),
        ("/directory/[dummy",),
        ("/directory/]dummy",),
        ("/directory/(dummy",),
        ("/directory/)dummy",),
        ("/directory/{dummy",),
        ("/directory/}dummy",),
        ("/directory/:dummy",),
        ("/directory/;dummy",),
        ('/directory/"dummy',),
        ("/directory/'dummy",),
        ("/directory/ dummy",),
        ("/directory/\tdummy",),
        ("/directory/\rdummy",),
        ("/directory/\ndummy",),
        ("/directory/./",),
        ("/directory/../",),
        ("/directory/.../",),
        ("/directory/./dummy/path/to/file",),
        ("/directory/../dummy/path/to/file",),
        ("/directory/.../dummy/path/to/file",),
    ]

    @ddt.idata(data_strict_abspath_pattern__bad_cases)
    @ddt.unpack
    def test_strict_abspath_pattern__bad_cases(self, data):
        self.assertIsNone(strict_abspath_pattern.match(data))
        with self.assertRaises(pp.ParseException):
            strict_abspath_parser.parse_string(data, parse_all=True)

    data_strict_archive_relpath_pattern = [
        ("archive.zip",),
        ("directory/archive.zip",),
        ("directory/dummy/archive.zip",),
        ("directory/dummy/path/archive.zip",),
        ("directory/dummy/path/to/archive.zip",),
        ("directory/dummy/path_to-archive.zip",),
        ("directory/dummy/.path_to-archive.zip",),
        ("archive.zip#",),
        ("archive.zip#directory",),
        ("archive.zip#directory/",),
        ("directory/archive.zip#directory/dummy",),
        ("directory/archive.zip#directory/dummy/",),
        ("directory/dummy/archive.zip#directory/dummy/path",),
        ("directory/dummy/path/archive.zip#directory/dummy/path/to",),
        ("directory/dummy/path/to/archive.zip#directory/dummy/path/to/file.txt",),
        ("directory/dummy/path_to-archive.zip#directory/dummy/path_to-file.txt.",),
        ("directory/dummy/.path_to-archive.zip#directory/dummy/.path_to-file.txt",),
    ]

    @ddt.idata(data_strict_archive_relpath_pattern)
    @ddt.unpack
    def test_strict_archive_relpath_pattern(self, data):
        self.assertIsNotNone(strict_archive_relpath_pattern.match(data))
        self.assertIsNotNone(strict_archive_relpath_parser.parse_string(data, parse_all=True))

    data_strict_archive_relpath_pattern__bad_cases = [
        ("/archive.zip",),
        ("/directory/archive.zip",),
        ("/directory/dummy/archive.zip",),
        ("/directory/dummy/path/archive.zip",),
        ("/directory/dummy/path/to/archive.zip",),
        ("/directory/dummy/path_to-archive.zip",),
        ("/directory/dummy/.path_to-archive.zip",),
        ("/archive.zip#directory",),
        ("/archive.zip#directory/",),
        ("/directory/archive.zip#directory/dummy",),
        ("/directory/archive.zip#directory/dummy/",),
        ("/directory/dummy/archive.zip#directory/dummy/path",),
        ("/directory/dummy/path/archive.zip#directory/dummy/path/to",),
        ("/directory/dummy/path/to/archive.zip#directory/dummy/path/to/file.txt",),
        ("/directory/dummy/path_to-archive.zip#directory/dummy/path_to-file.txt.",),
        ("/directory/dummy/.path_to-archive.zip#directory/dummy/.path_to-file.txt",),
        ("archive.zip/",),
        ("directory/archive.zip/",),
        ("directory/dummy/archive.zip/",),
        ("directory/dummy/path/archive.zip/",),
        ("directory/dummy/path/to/archive.zip/",),
        ("directory/dummy/path_to-archive.zip/",),
        ("directory/dummy/.path_to-archive.zip/",),
        ("archive.zip#/directory",),
        ("archive.zip#/directory/",),
        ("directory/archive.zip#/directory/dummy",),
        ("directory/archive.zip#/directory/dummy/",),
        ("directory/dummy/archive.zip#/directory/dummy/path",),
        ("directory/dummy/path/archive.zip#/directory/dummy/path/to",),
        ("directory/dummy/path/to/archive.zip#/directory/dummy/path/to/file.txt",),
        ("directory/dummy/path_to-archive.zip#/directory/dummy/path_to-file.txt.",),
        ("directory/dummy/.path_to-archive.zip#/directory/dummy/.path_to-file.txt",),
        ("directory/archive.zip#directory/./dummy",),
        ("directory/archive.zip#directory/../dummy",),
        ("directory/archive.zip#directory/.../dummy",),
        ("directory/archive.zip#directory/\t/dummy",),
        ("directory/archive.zip#directory/\r/dummy",),
        ("directory/archive.zip#directory/\n/dummy",),
    ]

    @ddt.idata(data_strict_archive_relpath_pattern__bad_cases)
    @ddt.unpack
    def test_strict_archive_relpath_pattern__bad_cases(self, data):
        self.assertIsNone(strict_archive_relpath_pattern.match(data))
        with self.assertRaises(pp.ParseException):
            strict_archive_relpath_parser.parse_string(data, parse_all=True)

    data_strict_archive_abspath_pattern = [
        ("/archive.zip",),
        ("/directory/archive.zip",),
        ("/directory/dummy/archive.zip",),
        ("/directory/dummy/path/archive.zip",),
        ("/directory/dummy/path/to/archive.zip",),
        ("/directory/dummy/path_to-archive.zip",),
        ("/directory/dummy/.path_to-archive.zip",),
        ("/archive.zip#",),
        ("/archive.zip#directory",),
        ("/archive.zip#directory/",),
        ("/directory/archive.zip#directory/dummy",),
        ("/directory/archive.zip#directory/dummy/",),
        ("/directory/dummy/archive.zip#directory/dummy/path",),
        ("/directory/dummy/path/archive.zip#directory/dummy/path/to",),
        ("/directory/dummy/path/to/archive.zip#directory/dummy/path/to/file.txt",),
        ("/directory/dummy/path_to-archive.zip#directory/dummy/path_to-file.txt.",),
        ("/directory/dummy/.path_to-archive.zip#directory/dummy/.path_to-file.txt",),
    ]

    @ddt.idata(data_strict_archive_abspath_pattern)
    @ddt.unpack
    def test_strict_archive_abspath_pattern(self, data):
        self.assertIsNotNone(strict_archive_abspath_pattern.match(data))
        self.assertIsNotNone(strict_archive_abspath_parser.parse_string(data, parse_all=True))

    data_strict_archive_abspath_pattern__bad_cases = [
        ("archive.zip",),
        ("directory/archive.zip",),
        ("directory/dummy/archive.zip",),
        ("directory/dummy/path/archive.zip",),
        ("directory/dummy/path/to/archive.zip",),
        ("directory/dummy/path_to-archive.zip",),
        ("directory/dummy/.path_to-archive.zip",),
        ("archive.zip#directory",),
        ("archive.zip#directory/",),
        ("directory/archive.zip#directory/dummy",),
        ("directory/archive.zip#directory/dummy/",),
        ("directory/dummy/archive.zip#directory/dummy/path",),
        ("directory/dummy/path/archive.zip#directory/dummy/path/to",),
        ("directory/dummy/path/to/archive.zip#directory/dummy/path/to/file.txt",),
        ("directory/dummy/path_to-archive.zip#directory/dummy/path_to-file.txt.",),
        ("directory/dummy/.path_to-archive.zip#directory/dummy/.path_to-file.txt",),
        ("/archive.zip/",),
        ("/directory/archive.zip/",),
        ("/directory/dummy/archive.zip/",),
        ("/directory/dummy/path/archive.zip/",),
        ("/directory/dummy/path/to/archive.zip/",),
        ("/directory/dummy/path_to-archive.zip/",),
        ("/directory/dummy/.path_to-archive.zip/",),
        ("/archive.zip#/directory",),
        ("/archive.zip#/directory/",),
        ("/directory/archive.zip#/directory/dummy",),
        ("/directory/archive.zip#/directory/dummy/",),
        ("/directory/dummy/archive.zip#/directory/dummy/path",),
        ("/directory/dummy/path/archive.zip#/directory/dummy/path/to",),
        ("/directory/dummy/path/to/archive.zip#/directory/dummy/path/to/file.txt",),
        ("/directory/dummy/path_to-archive.zip#/directory/dummy/path_to-file.txt.",),
        ("/directory/dummy/.path_to-archive.zip#/directory/dummy/.path_to-file.txt",),
        ("/directory/archive.zip#directory/./dummy",),
        ("/directory/archive.zip#directory/../dummy",),
        ("/directory/archive.zip#directory/.../dummy",),
        ("/directory/archive.zip#directory/\t/dummy",),
        ("/directory/archive.zip#directory/\r/dummy",),
        ("/directory/archive.zip#directory/\n/dummy",),
    ]

    @ddt.idata(data_strict_archive_abspath_pattern__bad_cases)
    @ddt.unpack
    def test_strict_archive_abspath_pattern__bad_cases(self, data):
        self.assertIsNone(strict_archive_abspath_pattern.match(data))
        with self.assertRaises(pp.ParseException):
            strict_archive_abspath_parser.parse_string(data, parse_all=True)

    data_email_address_pattern = [
        ("someone@dummy.com",),
        ("some.one@dummy.com",),
        ("some.1@dummy.com",),
        ("some-one@dummy.com",),
        ("someone-@dummy.com",),
        ("someone@dummy.company.com",),
        ("some.one@dummy-company.com",),
        ("some.1@dummy.company-company.com",),
        ("some_one@dummy-1st-company.co-ltd.com",),
    ]

    @ddt.idata(data_email_address_pattern)
    @ddt.unpack
    def test_email_address_pattern(self, data):
        self.assertIsNotNone(email_address_pattern.match(data))
        self.assertIsNotNone(email_address_parser.parse_string(data, parse_all=True))

    data_email_address_pattern__bad_cases = [
        ("",),
        ("some.one",),
        ("@dummy.com",),
        ("someone@dummy",),
        ("someone@dummy.methionylthreonylthreonylglutaminylarginyltyrosylglutamylserylleucine",),
        ("someone+one@dummy.com",),
        ("someone.@dummy.com",),
        ("someone@.dummy.com",),
        ("someone@dummy-.com",),
    ]

    @ddt.idata(data_email_address_pattern__bad_cases)
    @ddt.unpack
    def test_email_address_pattern__bad_cases(self, data):
        self.assertIsNone(email_address_pattern.match(data))
        with self.assertRaises(pp.ParseException):
            email_address_parser.parse_string(data, parse_all=True)

    data_semver_pattern = [
        ("0.0.0",),
        ("1.2.3",),
        ("10.20.30",),
        ("0.1.0-alpha",),
        ("1.0.0+build.1",),
        ("1.0.0-alpha+build.1",),
        ("1.0.0-0.3.7",),
        ("1.0.0-x.7.z.92",),
    ]

    @ddt.idata(data_semver_pattern)
    @ddt.unpack
    def test_semver_pattern(self, data):
        self.assertIsNotNone(semver_pattern.match(data))
        self.assertIsNotNone(semver_parser.parse_string(data, parse_all=True))

    data_semver_pattern__bad_cases = [
        ("",),
        ("dummy",),
        ("1",),
        ("1.0",),
        ("01.0.0",),
        ("0.01.0",),
        ("0.0.01",),
        ("1.0.0-",),
        ("1.0.0+",),
        ("1.0.0-alpha+",),
        ("1.0.0-alpha+beta-",),
    ]

    @ddt.idata(data_semver_pattern__bad_cases)
    @ddt.unpack
    def test_semver_pattern__bad_cases(self, data):
        self.assertIsNone(semver_pattern.match(data))
        with self.assertRaises(pp.ParseException):
            semver_parser.parse_string(data, parse_all=True)

    data_colon_tag_pattern = [
        ("dummy",),
        ("dummy:dummy",),
        ("dummy:dummy:dummy",),
        ("dummy_12345:dummy_12345:dummy_12345",),
    ]

    @ddt.idata(data_colon_tag_pattern)
    @ddt.unpack
    def test_colon_tag_pattern(self, data):
        self.assertIsNotNone(colon_tag_pattern.match(data))
        self.assertIsNotNone(colon_tag_parser.parse_string(data, parse_all=True))

    data_colon_tag_pattern__bad_cases = [
        ("",),
        (":",),
        ("dummy_",),
        ("_dummy",),
        ("dummy_:",),
        ("_dummy:",),
        ("dummy:dummy_",),
        ("dummy:_dummy",),
    ]

    @ddt.idata(data_colon_tag_pattern__bad_cases)
    @ddt.unpack
    def test_colon_tag_pattern__bad_cases(self, data):
        self.assertIsNone(colon_tag_pattern.match(data))
        with self.assertRaises(pp.ParseException):
            colon_tag_parser.parse_string(data, parse_all=True)

    data_slash_tag_pattern = [
        ("dummy",),
        ("dummy/dummy",),
        ("dummy/dummy/dummy",),
        ("dummy_12345/dummy_12345/dummy_12345",),
    ]

    @ddt.idata(data_slash_tag_pattern)
    @ddt.unpack
    def test_slash_tag_pattern(self, data):
        self.assertIsNotNone(slash_tag_pattern.match(data))
        self.assertIsNotNone(slash_tag_parser.parse_string(data, parse_all=True))

    data_slash_tag_pattern__bad_cases = [
        ("",),
        ("/",),
        ("dummy_",),
        ("_dummy",),
        ("dummy_/",),
        ("_dummy/",),
        ("dummy/dummy_",),
        ("dummy/_dummy",),
    ]

    @ddt.idata(data_slash_tag_pattern__bad_cases)
    @ddt.unpack
    def test_slash_tag_pattern__bad_cases(self, data):
        self.assertIsNone(slash_tag_pattern.match(data))
        with self.assertRaises(pp.ParseException):
            slash_tag_parser.parse_string(data, parse_all=True)

    data_topic_pattern = [
        ("/dummy_sensor",),
        ("/dummy/sensor",),
        ("/dummy/layout/sensor",),
        ("/dummy/heading_lateral/sensor",),
        ("/dummy/heading_lateral/sensor/001",),
    ]

    @ddt.idata(data_topic_pattern)
    @ddt.unpack
    def test_topic_pattern(self, data):
        self.assertIsNotNone(topic_pattern.match(data))
        self.assertIsNotNone(topic_parser.parse_string(data, parse_all=True))

    data_topic_pattern__bad_cases = [
        ("",),
        ("/",),
        ("/dummy_sensor/",),
        ("/DUMMY_SENSOR",),
        ("/DUMMY/SENSOR",),
        ("/Dummy/Layout/Sensor",),
        ("/dummy/heading-lateral/sensor",),
        ("/dummy/heading/sensor//",),
    ]

    @ddt.idata(data_topic_pattern__bad_cases)
    @ddt.unpack
    def test_topic_pattern__bad_cases(self, data):
        self.assertIsNone(topic_pattern.match(data))
        with self.assertRaises(pp.ParseException):
            topic_parser.parse_string(data, parse_all=True)

    data_vin_code_pattern = [
        ("00000000000000000",),
        ("AAAAAAAAAAAAAAAAA",),
        ("0123456789ABCDEFG",),
        ("HJKLMNPRSTUVWXYZ0",),
    ]

    @ddt.idata(data_vin_code_pattern)
    @ddt.unpack
    def test_vin_code_pattern(self, data):
        self.assertIsNotNone(vin_code_pattern.match(data))
        self.assertIsNotNone(vin_code_parser.parse_string(data, parse_all=True))

    data_vin_code_pattern__bad_cases = [
        ("",),
        ("0",),
        ("0000000000000000",),
        ("000000000000000000",),
        ("00000000I00000000",),
        ("00000000O00000000",),
        ("00000000Q00000000",),
    ]

    @ddt.idata(data_vin_code_pattern__bad_cases)
    @ddt.unpack
    def test_vin_code_pattern__bad_cases(self, data):
        self.assertIsNone(vin_code_pattern.match(data))
        with self.assertRaises(pp.ParseException):
            vin_code_parser.parse_string(data, parse_all=True)

    data_parse_user_name = [
        ("dummy.person", UserName("dummy", "person", 0)),
        ("dummy1.person", UserName("dummy", "person", 1)),
        ("dummy999999.person", UserName("dummy", "person", 999999)),
    ]

    @ddt.idata(data_parse_user_name)
    @ddt.unpack
    def test_parse_user_name(self, data, expect):
        self.assertEqual(parse_user_name(data), expect)
        self.assertEqual(data, str(expect))

    data_parse_user_name__bad_cases = [
        ("dummy",),
        ("0.dummy",),
        ("dummy.0",),
        ("Dummy.Dummy",),
        ("dummy-dummy.dummy",),
        ("0dummy.dummy",),
        ("0dummy0.dummy",),
        ("dummy01.dummy",),
    ]

    @ddt.idata(data_parse_user_name__bad_cases)
    @ddt.unpack
    def test_parse_user_name__bad_cases(self, data):
        with self.assertRaises(pp.ParseException):
            parse_user_name(data)

    data_parse_user_email = [
        ("dummy.person@some.company", UserEmail(UserName("dummy", "person", 0), "some.company")),
        ("dummy1.person@another.company", UserEmail(UserName("dummy", "person", 1), "another.company")),
        ("dummy1.person@yet-another.company", UserEmail(UserName("dummy", "person", 1), "yet-another.company")),
        ("dummy1.person@yet-yet.another.company", UserEmail(UserName("dummy", "person", 1), "yet-yet.another.company")),
        ("dummy999999.person@good.company", UserEmail(UserName("dummy", "person", 999999), "good.company")),
        ("dummy.person@better.or.even-better.company",
         UserEmail(UserName("dummy", "person", 0), "better.or.even-better.company")),
    ]

    @ddt.idata(data_parse_user_email)
    @ddt.unpack
    def test_parse_user_email(self, data, expect):
        self.assertEqual(parse_user_email(data), expect)
        self.assertEqual(data, str(expect))

    data_parse_user_email__bad_cases = [
        ("dummy",),
        ("0.dummy",),
        ("dummy.0",),
        ("Dummy.Dummy",),
        ("dummy-dummy.dummy",),
        ("0dummy.dummy",),
        ("0dummy0.dummy",),
        ("dummy01.dummy",),
        ("dummy@some.company",),
        ("0.dummy@some.company",),
        ("dummy.0@some.company",),
        ("Dummy.Dummy@some.company",),
        ("dummy-dummy.dummy@some.company",),
        ("0dummy.dummy@some.company",),
        ("0dummy0.dummy@some.company",),
        ("dummy01.dummy@some.company",),
        ("dummy.person@BAD.COMPANY",),
        ("dummy1.person@worse.company.",),
        ("dummy1.person@even.worse-company",),
        ("dummy1.person#worst.company",),
    ]

    @ddt.idata(data_parse_user_email__bad_cases)
    @ddt.unpack
    def test_parse_user_email__bad_cases(self, data):
        with self.assertRaises(pp.ParseException):
            parse_user_email(data)

    data_parse_vehicle_name = [
        ("brand_alias",
         VehicleName("brand", "alias", None, None)),
        ("brand_alias_00001",
         VehicleName("brand", "alias", "00001", None)),
        ("brand_alias_V00000000000000000",
         VehicleName("brand", "alias", None, "00000000000000000")),
        ("brand_alias_V0123456789ABCDEFG",
         VehicleName("brand", "alias", None, "0123456789ABCDEFG")),
        ("brand_alias_yet_another_alias_00001",
         VehicleName("brand", "alias_yet_another_alias", "00001", None)),
        ("brand_alias_yet_another_alias_V00000000000000000",
         VehicleName("brand", "alias_yet_another_alias", None, "00000000000000000")),
        ("brand_alias_yet_another_alias_V0123456789ABCDEFG",
         VehicleName("brand", "alias_yet_another_alias", None, "0123456789ABCDEFG")),
        ("brand_alias_00001_V00000000000000000",
         VehicleName("brand", "alias", "00001", "00000000000000000")),
        ("brand_alias_00001_V0123456789ABCDEFG",
         VehicleName("brand", "alias", "00001", "0123456789ABCDEFG")),
        ("brand_alias_yet_another_alias_00001_V00000000000000000",
         VehicleName("brand", "alias_yet_another_alias", "00001", "00000000000000000")),
        ("brand_alias_yet_another_alias_00001_V0123456789ABCDEFG",
         VehicleName("brand", "alias_yet_another_alias", "00001", "0123456789ABCDEFG")),
    ]

    @ddt.idata(data_parse_vehicle_name)
    @ddt.unpack
    def test_parse_vehicle_name(self, data, expect):
        self.assertEqual(parse_vehicle_name(data), expect)
        self.assertEqual(data, str(expect))

    data_parse_vehicle_name__bad_cases = [
        ("brand",),
        ("brand_00001",),
        ("brand_V00000000000000000",),
        ("brand_V0123456789ABCDEFG",),
        ("BRAND_alias",),
        ("BRAND_alias_00001",),
        ("BRAND_alias_V00000000000000000",),
        ("BRAND_alias_V0123456789ABCDEFG",),
        ("brand_ALIAS",),
        ("brand_ALIAS_00001",),
        ("brand_ALIAS_V00000000000000000",),
        ("brand_ALIAS_V0123456789ABCDEFG",),
        ("brand-alias",),
        ("brand-alias_00001",),
        ("brand-alias_V00000000000000000",),
        ("brand-alias_V0123456789ABCDEFG",),
        ("brand_alias_V00001",),
        ("brand_alias_V00001",),
        ("brand_alias_VV00000000000000000",),
        ("brand_alias_VV0123456789ABCDEFG",),
    ]

    @ddt.idata(data_parse_vehicle_name__bad_cases)
    @ddt.unpack
    def test_parse_vehicle_name__bad_cases(self, data):
        with self.assertRaises(pp.ParseException):
            parse_vehicle_name(data)

    data_parse_bag_name = [
        ("20250101T123045-brand_alias-0",
         BagName(VehicleName("brand", "alias", None, None),
                 dt_parse_iso("2025-01-01T12:30:45"),
                 0)),
        ("20250101T123045-brand_alias_00001-0",
         BagName(VehicleName("brand", "alias", "00001", None),
                 dt_parse_iso("2025-01-01T12:30:45"),
                 0)),
        ("20250101T123045-brand_alias_V00000000000000000-0",
         BagName(VehicleName("brand", "alias", None, "00000000000000000"),
                 dt_parse_iso("2025-01-01T12:30:45"),
                 0)),
        ("20250101T123045-brand_alias_V0123456789ABCDEFG-0",
         BagName(VehicleName("brand", "alias", None, "0123456789ABCDEFG"),
                 dt_parse_iso("2025-01-01T12:30:45"),
                 0)),
        ("20250101T123045-brand_alias_yet_another_alias_00001-0",
         BagName(VehicleName("brand", "alias_yet_another_alias", "00001", None),
                 dt_parse_iso("2025-01-01T12:30:45"),
                 0)),
        ("20250101T123045-brand_alias_yet_another_alias_V00000000000000000-0",
         BagName(VehicleName("brand", "alias_yet_another_alias", None, "00000000000000000"),
                 dt_parse_iso("2025-01-01T12:30:45"),
                 0)),
        ("20250101T123045-brand_alias_yet_another_alias_V0123456789ABCDEFG-0",
         BagName(VehicleName("brand", "alias_yet_another_alias", None, "0123456789ABCDEFG"),
                 dt_parse_iso("2025-01-01T12:30:45"),
                 0)),
        ("20250101T123045-brand_alias_00001_V00000000000000000-0",
         BagName(VehicleName("brand", "alias", "00001", "00000000000000000"),
                 dt_parse_iso("2025-01-01T12:30:45"),
                 0)),
        ("20250101T123045-brand_alias_00001_V0123456789ABCDEFG-0",
         BagName(VehicleName("brand", "alias", "00001", "0123456789ABCDEFG"),
                 dt_parse_iso("2025-01-01T12:30:45"),
                 0)),
        ("20250101T123045-brand_alias_yet_another_alias_00001_V00000000000000000-0",
         BagName(VehicleName("brand", "alias_yet_another_alias", "00001", "00000000000000000"),
                 dt_parse_iso("2025-01-01T12:30:45"),
                 0)),
        ("20250101T123045-brand_alias_yet_another_alias_00001_V0123456789ABCDEFG-0",
         BagName(VehicleName("brand", "alias_yet_another_alias", "00001", "0123456789ABCDEFG"),
                 dt_parse_iso("2025-01-01T12:30:45"),
                 0)),
        ("20250101T123045-brand_alias_yet_another_alias_00001_V0123456789ABCDEFG-1",
         BagName(VehicleName("brand", "alias_yet_another_alias", "00001", "0123456789ABCDEFG"),
                 dt_parse_iso("2025-01-01T12:30:45"),
                 1)),
        ("20250101T123045-brand_alias_yet_another_alias_00001_V0123456789ABCDEFG-999999",
         BagName(VehicleName("brand", "alias_yet_another_alias", "00001", "0123456789ABCDEFG"),
                 dt_parse_iso("2025-01-01T12:30:45"),
                 999999)),

        ("20250101T123045-brand_alias-0.bag",
         BagName(VehicleName("brand", "alias", None, None),
                 dt_parse_iso("2025-01-01T12:30:45"),
                 0)),
        ("20250101T123045-brand_alias_00001-0.bag",
         BagName(VehicleName("brand", "alias", "00001", None),
                 dt_parse_iso("2025-01-01T12:30:45"),
                 0)),
        ("20250101T123045-brand_alias_V00000000000000000-0.bag",
         BagName(VehicleName("brand", "alias", None, "00000000000000000"),
                 dt_parse_iso("2025-01-01T12:30:45"),
                 0)),
        ("20250101T123045-brand_alias_V0123456789ABCDEFG-0.bag",
         BagName(VehicleName("brand", "alias", None, "0123456789ABCDEFG"),
                 dt_parse_iso("2025-01-01T12:30:45"),
                 0)),
        ("20250101T123045-brand_alias_yet_another_alias_00001-0.bag",
         BagName(VehicleName("brand", "alias_yet_another_alias", "00001", None),
                 dt_parse_iso("2025-01-01T12:30:45"),
                 0)),
        ("20250101T123045-brand_alias_yet_another_alias_V00000000000000000-0.bag",
         BagName(VehicleName("brand", "alias_yet_another_alias", None, "00000000000000000"),
                 dt_parse_iso("2025-01-01T12:30:45"),
                 0)),
        ("20250101T123045-brand_alias_yet_another_alias_V0123456789ABCDEFG-0.bag",
         BagName(VehicleName("brand", "alias_yet_another_alias", None, "0123456789ABCDEFG"),
                 dt_parse_iso("2025-01-01T12:30:45"),
                 0)),
        ("20250101T123045-brand_alias_00001_V00000000000000000-0.bag",
         BagName(VehicleName("brand", "alias", "00001", "00000000000000000"),
                 dt_parse_iso("2025-01-01T12:30:45"),
                 0)),
        ("20250101T123045-brand_alias_00001_V0123456789ABCDEFG-0.bag",
         BagName(VehicleName("brand", "alias", "00001", "0123456789ABCDEFG"),
                 dt_parse_iso("2025-01-01T12:30:45"),
                 0)),
        ("20250101T123045-brand_alias_yet_another_alias_00001_V00000000000000000-0.bag",
         BagName(VehicleName("brand", "alias_yet_another_alias", "00001", "00000000000000000"),
                 dt_parse_iso("2025-01-01T12:30:45"),
                 0)),
        ("20250101T123045-brand_alias_yet_another_alias_00001_V0123456789ABCDEFG-0.bag",
         BagName(VehicleName("brand", "alias_yet_another_alias", "00001", "0123456789ABCDEFG"),
                 dt_parse_iso("2025-01-01T12:30:45"),
                 0)),
        ("20250101T123045-brand_alias_yet_another_alias_00001_V0123456789ABCDEFG-1.bag",
         BagName(VehicleName("brand", "alias_yet_another_alias", "00001", "0123456789ABCDEFG"),
                 dt_parse_iso("2025-01-01T12:30:45"),
                 1)),
        ("20250101T123045-brand_alias_yet_another_alias_00001_V0123456789ABCDEFG-999999.bag",
         BagName(VehicleName("brand", "alias_yet_another_alias", "00001", "0123456789ABCDEFG"),
                 dt_parse_iso("2025-01-01T12:30:45"),
                 999999)),
    ]

    @ddt.idata(data_parse_bag_name)
    @ddt.unpack
    def test_parse_bag_name(self, data, expect):
        self.assertEqual(parse_bag_name(data), expect)
        if data.endswith(".bag"):
            self.assertEqual(data, str(expect))
        else:
            self.assertEqual(data + ".bag", str(expect))
