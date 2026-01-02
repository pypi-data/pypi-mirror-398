from abc import ABC
from abc import abstractmethod
from typing import Annotated, Self

import numpy as np
import pydantic as pdt
import pyproj
from iker.common.utils.funcutils import singleton
from iker.common.utils.strutils import parse_params_string, repr_data, str_conv

from plexus.common.pose import Pose


class Proj(ABC):
    @classmethod
    @abstractmethod
    def typename(cls) -> str:
        pass

    def __init__(self, spec):
        self.spec = spec

    def __str__(self):
        return self.to_string()

    def method(self) -> str:
        return self.typename()

    @abstractmethod
    def ellipsoid(self) -> str:
        pass

    @abstractmethod
    def from_latlon(self, lat: float, lon: float) -> tuple[float, float]:
        """
        Performs forward projection from latitude/longitude to projection coordinate system

        :param lat: latitude
        :param lon: longitude

        :return: tuple of x and y in projection coordinate system
        """
        pass

    @abstractmethod
    def to_latlon(self, x: float, y: float) -> tuple[float, float]:
        """
        Performs inverse projection from projection coordinate system to latitude/longitude

        :param x: x in projection coordinate system
        :param y: y in projection coordinate system

        :return: tuple of latitude and longitude
        """
        pass

    @abstractmethod
    def to_string(self) -> str:
        pass


class EQDCProj(Proj):
    """
    Equidistant conic projection
    Please refer to https://en.wikipedia.org/wiki/Equidistant_conic_projection
    """

    class Spec(pdt.BaseModel):
        lat_1: Annotated[float, pdt.Strict(), pdt.AllowInfNan(False)]
        lat_2: Annotated[float, pdt.Strict(), pdt.AllowInfNan(False)]
        lon_0: Annotated[float, pdt.Strict(), pdt.AllowInfNan(False)] = 0.0

    @classmethod
    def typename(cls) -> str:
        return "eqdc"

    def __init__(self, **kwargs):
        super(EQDCProj, self).__init__(EQDCProj.Spec(**kwargs))
        self.proj = self.make_proj()

    def ellipsoid(self) -> str:
        return "WGS84"

    def from_latlon(self, lat: float, lon: float) -> tuple[float, float]:
        x, y = self.proj(lon, lat)
        return x, y

    def to_latlon(self, x: float, y: float) -> tuple[float, float]:
        lon, lat = self.proj(x, y, inverse=True)
        return lat, lon

    def to_string(self) -> str:
        return "{method}:lat_1={},lat_2={},lon_0={}".format(
            self.spec.lat_1,
            self.spec.lat_2,
            self.spec.lon_0,
            method=self.method(),
        )

    def make_proj(self):
        return pyproj.Proj(
            "+proj={method} +ellps={ellipsoid} +datum={ellipsoid} +units=m +no_defs +lat_1={} +lat_2={} +lon_0={}".format(
                self.spec.lat_1,
                self.spec.lat_2,
                self.spec.lon_0,
                method=self.method(),
                ellipsoid=self.ellipsoid(),
            )
        )


class UTMProj(Proj):
    """
    Universal Transverse Mercator coordinate system
    Please refer to https://en.wikipedia.org/wiki/Universal_Transverse_Mercator_coordinate_system
    """

    class Spec(pdt.BaseModel):
        zone: Annotated[int, pdt.Strict()]
        south: Annotated[bool, pdt.Strict()] = False

    @classmethod
    def typename(cls) -> str:
        return "utm"

    def __init__(self, **kwargs):
        super(UTMProj, self).__init__(UTMProj.Spec(**kwargs))
        self.proj = self.make_proj()

    def ellipsoid(self) -> str:
        return "WGS84"

    def from_latlon(self, lat: float, lon: float) -> tuple[float, float]:
        x, y = self.proj(lon, lat)
        return x, y

    def to_latlon(self, x: float, y: float) -> tuple[float, float]:
        lon, lat = self.proj(x, y, inverse=True)
        return lat, lon

    def to_string(self) -> str:
        return "{method}:zone={},south={}".format(self.spec.zone, self.spec.south, method=self.method())

    def make_proj(self):
        return pyproj.Proj(
            "+proj={method} +ellps={ellipsoid} +datum={ellipsoid} +units=m +no_defs +zone={} {}".format(
                self.spec.zone,
                "+south" if self.spec.south else "",
                method=self.method(),
                ellipsoid=self.ellipsoid(),
            )
        )


class WebMercProj(Proj):
    """
    Web Mercator projection
    Please refer to https://en.wikipedia.org/wiki/Web_Mercator_projection
    """

    class Spec(pdt.BaseModel):
        lon_0: Annotated[float, pdt.Strict(), pdt.AllowInfNan(False)] = 0.0

    @classmethod
    def typename(cls) -> str:
        return "webmerc"

    def __init__(self, **kwargs):
        super(WebMercProj, self).__init__(WebMercProj.Spec(**kwargs))
        self.proj = self.make_proj()

    def ellipsoid(self) -> str:
        return "WGS84"

    def from_latlon(self, lat: float, lon: float) -> tuple[float, float]:
        x, y = self.proj(lon, lat)
        return x, y

    def to_latlon(self, x: float, y: float) -> tuple[float, float]:
        lon, lat = self.proj(x, y, inverse=True)
        return lat, lon

    def to_string(self) -> str:
        return "{method}:lon_0={}".format(self.spec.lon_0, method=self.method())

    def make_proj(self):
        return pyproj.Proj(
            "+proj={method} +ellps={ellipsoid} +datum={ellipsoid} +units=m +no_defs +lon_0={}".format(
                self.spec.lon_0,
                method=self.method(),
                ellipsoid=self.ellipsoid(),
            ),
        )


@singleton
def default_proj() -> Proj:
    return make_proj("eqdc:lat_1=30.0,lat_2=50.0")


def make_proj(spec_str: str) -> Proj | None:
    """
    Constructs cartographic projection from the given name and arguments

    :param spec_str: projection spec string

    :return: projection
    """

    if spec_str is None:
        return None

    match spec_str.split(":", maxsplit=1):
        case [name]:
            kwargs = {}
        case [name, args]:
            kwargs = parse_params_string(args, str_parser=str_conv)
        case _:
            raise ValueError("bad spec string")

    if name.lower() == UTMProj.typename():
        return UTMProj(**kwargs)
    if name.lower() == EQDCProj.typename():
        return EQDCProj(**kwargs)
    if name.lower() == WebMercProj.typename():
        return WebMercProj(**kwargs)

    return None


class Coord(object):
    @classmethod
    def from_pose(cls, pose: Pose, proj: Proj | None) -> Self:
        """
        Creates a coord from given pose

        :param pose: pose based on which the coord is created
        :param proj: cartographic projection

        :return: generated coord
        """
        return cls.from_xy(pose.p[0], pose.p[1], pose.p[2], proj, pose.ts)

    @classmethod
    def from_latlon(cls, lat: float, lon: float, ele: float, proj: Proj | None, ts: float = 0) -> Self:
        """
        Creates a coord from latitude/longitude

        :param lat: latitude
        :param lon: longitude
        :param ele: elevation
        :param proj: cartographic projection
        :param ts: timestamp

        :return: generated coord
        """
        if proj is None:
            return Coord(ts, lat, lon, ele, 0.0, 0.0, pdt.BaseModel())

        x, y = proj.from_latlon(lat, lon)
        return Coord(ts, lat, lon, ele, x, y, proj.spec)

    @classmethod
    def from_xy(cls, x: float, y: float, ele: float, proj: Proj | None, ts: float = 0) -> Self:
        """
        Creates a coord from coordinate in cartographic projection

        :param x: x coordinate in cartographic projection
        :param y: y coordinate in cartographic projection
        :param ele: elevation
        :param proj: cartographic projection
        :param ts: timestamp

        :return: a coord
        """
        if proj is None:
            return Coord(ts, 0.0, 0.0, ele, x, y, pdt.BaseModel())

        lat, lon = proj.to_latlon(x, y)
        return Coord(ts, lat, lon, ele, x, y, proj.spec)

    def __init__(self, ts: float, lat: float, lon: float, ele: float, x: float, y: float, spec: pdt.BaseModel):
        """
        Represents a coordinate

        :param ts: timestamp
        :param lat: latitude
        :param lon: longitude
        :param ele: elevation
        :param x: x in projection coordinate system
        :param y: y in projection coordinate system
        :param spec: projection specification
        """
        self.ts = ts
        self.lat = lat
        self.lon = lon
        self.x = x
        self.y = y
        self.spec = spec
        self.ele = ele
        self.xy = np.array([x, y], dtype=np.float64)
        self.xyz = np.array([x, y, ele], dtype=np.float64)

    def __str__(self):
        return repr_data(self)
