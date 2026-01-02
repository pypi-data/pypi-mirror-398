import math
import unittest

import ddt
import numpy as np
import pyquaternion as pyquat
from iker.common.utils.randutils import randomizer

from plexus.common.pose import Pose


@ddt.ddt
class PoseTest(unittest.TestCase):

    @staticmethod
    def random_pose() -> Pose:
        q = pyquat.Quaternion(axis=randomizer().random_unit_vector(3),
                              angle=math.pi * randomizer().next_float(0.0, 0.5))
        return Pose(0, np.array(randomizer().random_unit_vector(3)), q.normalised.elements)

    def assert_array_almost_equal(self, xs: np.ndarray, ys: np.ndarray, delta: float):
        self.assertEqual(len(xs), len(ys))
        for x, y in zip(xs, ys):
            self.assertAlmostEqual(x, y, delta=delta)

    def test_builtin_init(self):
        for _ in range(0, 10000):
            expect = PoseTest.random_pose()
            actual = Pose(0, expect.p, expect.q)

            self.assert_array_almost_equal(expect.p, actual.p, delta=1e-9)
            self.assert_array_almost_equal(expect.q, actual.q, delta=1e-9)

    def test_add_sub(self):
        for _ in range(0, 10000):
            pose = PoseTest.random_pose()
            delta = PoseTest.random_pose()

            result = Pose.sub(Pose.add(pose, delta), pose)

            self.assert_array_almost_equal(delta.p, result.p, delta=1e-9)
            self.assert_array_almost_equal(delta.q, result.q, delta=1e-9)

    def test_interpolate(self):
        for _ in range(0, 10000):
            t = randomizer().next_float()

            pose1 = PoseTest.random_pose()
            pose2 = PoseTest.random_pose()

            inter1 = Pose.interpolate(pose1, pose2, t)
            inter2 = Pose.interpolate(pose2, pose1, 1.0 - t)

            self.assert_array_almost_equal(inter1.p, inter2.p, delta=1e-9)
            self.assert_array_almost_equal(inter1.q, inter2.q, delta=1e-9)

    def test_matrix(self):
        for _ in range(0, 10000):
            point = np.array(randomizer().random_unit_vector(3))

            pose = PoseTest.random_pose()

            expect = pose.translate(pose.rotate(point))
            result = np.matmul(pose.matrix(), np.array([*point, 1.0])[:, None]).transpose()[0][:3]

            self.assert_array_almost_equal(expect, result, delta=1e-9)
