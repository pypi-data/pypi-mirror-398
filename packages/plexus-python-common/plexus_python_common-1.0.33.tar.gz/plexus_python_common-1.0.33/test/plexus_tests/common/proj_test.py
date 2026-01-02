import random
import unittest

import ddt
import pydantic as pdt

from plexus.common.proj import Coord, EQDCProj, UTMProj, WebMercProj
from plexus.common.proj import make_proj


@ddt.ddt
class ProjTest(unittest.TestCase):

    @ddt.data(
        ("eqdc:lat_1=0.0,lat_2=10.0", EQDCProj(lat_1=0.0, lat_2=10.0, lon_0=0.0)),
        ("eqdc:lat_1=0.0,lat_2=10.0,lon_0=0.0", EQDCProj(lat_1=0.0, lat_2=10.0, lon_0=0.0)),
        ("eqdc:lat_1=0.0,lat_2=10.0,lon_0=180.0", EQDCProj(lat_1=0.0, lat_2=10.0, lon_0=180.0)),
        ("eqdc:lat_1=0,lat_2=10,lon_0=180", EQDCProj(lat_1=0.0, lat_2=10.0, lon_0=180.0)),
        ("utm:zone=1", UTMProj(zone=1, south=False)),
        ("utm:zone=1,south=false", UTMProj(zone=1, south=False)),
        ("utm:zone=1,south=False", UTMProj(zone=1, south=False)),
        ("utm:zone=1,south=true", UTMProj(zone=1, south=True)),
        ("utm:zone=1,south=True", UTMProj(zone=1, south=True)),
        ("webmerc", WebMercProj(lon_0=0.0)),
        ("webmerc:lon_0=0.0", WebMercProj(lon_0=0.0)),
        ("webmerc:lon_0=180.0", WebMercProj(lon_0=180.0)),
        ("webmerc:lon_0=180", WebMercProj(lon_0=180.0)),
    )
    @ddt.unpack
    def test_make_proj(self, spec_str, expect):
        actual = make_proj(spec_str)
        self.assertEqual(actual.spec, expect.spec)

    @ddt.data(
        ("eqdc",),
        ("eqdc:lat_1=0.0",),
        ("eqdc:lat_1=0.0,lon_0=0.0",),
        ("eqdc:lat_1=0.0,lat_2=bad-value",),
        ("eqdc:lat_1=inf,lat_2=inf,lon_0=nan",),
        ("utm",),
        ("utm:zone=1,south=0",),
        ("utm:zone=1,south=1",),
        ("utm:zone=1.0,south=True",),
        ("utm:south=True",),
        ("webmerc:lon_0=bad-value",),
        ("webmerc:lon_0=nan",),
    )
    @ddt.unpack
    def test_make_proj__bad_spec_str(self, spec_str):
        with self.assertRaises(pdt.ValidationError):
            make_proj(spec_str)


@ddt.ddt
class EQDCProjTest(unittest.TestCase):

    def test_builtin_init(self):
        proj = EQDCProj(lat_1=0.0, lat_2=10.0)

        self.assertEqual(proj.spec.lat_1, 0.0)
        self.assertEqual(proj.spec.lat_2, 10.0)
        self.assertEqual(proj.spec.lon_0, 0.0)

    def test_to_string(self):
        proj = EQDCProj(lat_1=0.0, lat_2=10.0)

        self.assertEqual(proj.to_string(), "eqdc:lat_1=0.0,lat_2=10.0,lon_0=0.0")

    @ddt.data(
        (dict(),),
        (dict(lat_1=0.0),),
        (dict(lat_1="0.0", lat_2=10.0),),
        (dict(lat_1=0.0, lat_2="10.0"),),
        (dict(lat_1=0.0, lat_2=10.0, lon_0="0.0"),),
    )
    @ddt.unpack
    def test_builtin_init__with_exception(self, args):
        with self.assertRaises(pdt.ValidationError):
            EQDCProj(**args)

    def test_proj(self):
        proj = make_proj("eqdc:lat_1=0.0,lat_2=10.0")

        for _ in range(0, 1000000):
            lat = random.uniform(-80.0, 80.0)
            lon = random.uniform(-180.0, 180.0)

            x, y = proj.from_latlon(lat, lon)
            new_lat, new_lon = proj.to_latlon(x, y)

            coord = Coord.from_latlon(new_lat, new_lon, 0.0, proj)

            self.assertAlmostEqual(lat, new_lat, delta=1e-9)
            self.assertAlmostEqual(lon, new_lon, delta=1e-9)
            self.assertAlmostEqual(x, coord.x, delta=1e-3)
            self.assertAlmostEqual(y, coord.y, delta=1e-3)
            self.assertEqual(new_lat, coord.lat)
            self.assertEqual(new_lon, coord.lon)


@ddt.ddt
class UTMProjTest(unittest.TestCase):

    def test_builtin_init(self):
        proj = UTMProj(zone=31)

        self.assertEqual(proj.spec.zone, 31)
        self.assertEqual(proj.spec.south, False)

    def test_to_string(self):
        proj = UTMProj(zone=31)

        self.assertEqual(proj.to_string(), "utm:zone=31,south=False")

    @ddt.data(
        (dict(),),
        (dict(zone=31.0),),
        (dict(zone=31, south="false"),),
        (dict(zone="31", south=True),),
    )
    @ddt.unpack
    def test_builtin_init__with_exception(self, args):
        with self.assertRaises(pdt.ValidationError):
            UTMProj(**args)

    def test_proj(self):
        proj = make_proj("utm:zone=31")

        for _ in range(0, 1000000):
            lat = random.uniform(-80.0, 80.0)
            lon = random.uniform(0.0, 6.0)

            x, y = proj.from_latlon(lat, lon)
            new_lat, new_lon = proj.to_latlon(x, y)

            coord = Coord.from_latlon(new_lat, new_lon, 0.0, proj)

            self.assertAlmostEqual(lat, new_lat, delta=1e-9)
            self.assertAlmostEqual(lon, new_lon, delta=1e-9)
            self.assertAlmostEqual(x, coord.x, delta=1e-3)
            self.assertAlmostEqual(y, coord.y, delta=1e-3)
            self.assertEqual(new_lat, coord.lat)
            self.assertEqual(new_lon, coord.lon)


@ddt.ddt
class WebMercProjTest(unittest.TestCase):

    def test_builtin_init(self):
        proj = WebMercProj()

        self.assertEqual(proj.spec.lon_0, 0.0)

    def test_to_string(self):
        proj = WebMercProj()

        self.assertEqual(proj.to_string(), "webmerc:lon_0=0.0")

    @ddt.data(
        (dict(lon_0="0.0"),),
    )
    @ddt.unpack
    def test_builtin_init__with_exception(self, args):
        with self.assertRaises(pdt.ValidationError):
            WebMercProj(**args)

    def test_proj(self):
        proj = make_proj("webmerc")

        for _ in range(0, 1000000):
            lat = random.uniform(-80.0, 80.0)
            lon = random.uniform(-180.0, 180.0)

            x, y = proj.from_latlon(lat, lon)
            new_lat, new_lon = proj.to_latlon(x, y)

            coord = Coord.from_latlon(new_lat, new_lon, 0.0, proj)

            self.assertAlmostEqual(lat, new_lat, delta=1e-9)
            self.assertAlmostEqual(lon, new_lon, delta=1e-9)
            self.assertAlmostEqual(x, coord.x, delta=1e-3)
            self.assertAlmostEqual(y, coord.y, delta=1e-3)
            self.assertEqual(new_lat, coord.lat)
            self.assertEqual(new_lon, coord.lon)
