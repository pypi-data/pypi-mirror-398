from typing import Self

import numpy as np
import pyquaternion as pyquat
from iker.common.utils.strutils import repr_data


class Pose(object):
    @classmethod
    def from_numbers(
        cls,
        px: float,
        py: float,
        pz: float,
        qx: float,
        qy: float,
        qz: float,
        qw: float,
        ts: float = 0,
    ) -> Self:
        """
        Constructs a pose from numbers representing position and orientation
        """
        return Pose(ts, np.array([px, py, pz], dtype=np.float64), np.array([qw, qx, qy, qz], dtype=np.float64))

    @classmethod
    def add(cls, x: Self, d: Self) -> Self:
        """
        Performs pose SE3 addition, as x + d = y
        """
        xq = pyquat.Quaternion(x.q)
        dq = pyquat.Quaternion(d.q)

        yp = x.p + xq.rotate(d.p)
        yq = xq * dq

        return Pose(0, yp, yq.normalised.elements)

    @classmethod
    def sub(cls, y: Self, x: Self) -> Self:
        """
        Performs pose SE3 subtraction, as x + d = y => d = y - x
        """
        xq = pyquat.Quaternion(x.q)
        yq = pyquat.Quaternion(y.q)

        dp = xq.inverse.rotate(y.p - x.p)
        dq = xq.inverse * yq

        return Pose(0, dp, dq.normalised.elements)

    @classmethod
    def interpolate(cls, a: Self, b: Self, t: float) -> Self:
        """
        Interpolates between two given poses, as a * t + b * (1 - t)

        :return: interpolated pose
        """
        ts = a.ts + (b.ts - a.ts) * t
        p = a.p + (b.p - a.p) * t
        q = pyquat.Quaternion.slerp(pyquat.Quaternion(a.q), pyquat.Quaternion(b.q), t)
        return Pose(ts, p, q.normalised.elements)

    def __init__(self, ts: float, p: np.ndarray, q: np.ndarray):
        """
        Represents a pose

        :param ts: timestamp
        :param p: position vector
        :param q: orientation quaternion
        """
        self.ts = ts
        self.p = p
        self.q = q

    def matrix(self) -> np.ndarray:
        """
        Returns the transformation matrix of this pose

        :return: transformation matrix
        """
        r = pyquat.Quaternion(self.q).rotation_matrix
        t = self.p[:, None]
        return np.block([[r, t], [np.zeros((1, 3), dtype=np.float64), np.ones((1, 1), dtype=np.float64)]])

    def translate(self, v: np.ndarray) -> np.ndarray:
        """
        Translate the given vector with the pose position

        :param v: the vector to be translated

        :return: translated vector
        """
        return self.p + v

    def rotate(self, v: np.ndarray) -> np.ndarray:
        """
        Rotates the given vector with the pose orientation

        :param v: the vector to be rotated

        :return: rotated vector
        """
        return pyquat.Quaternion(self.q).rotate(v)

    def __str__(self):
        return repr_data(self)
