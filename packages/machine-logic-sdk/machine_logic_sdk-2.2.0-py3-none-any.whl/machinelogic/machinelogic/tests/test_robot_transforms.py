import unittest

import numpy as np

from machinelogic.machinelogic.tests.MatrixAssertionsMixin import MatrixAssertionsMixin
from machinelogic.machinelogic.utils.robot_transforms import (
    euler_to_homogeneous_transform_matrix,
    euler_to_rotation_matrix,
    homogeneous_transform_matrix_to_euler,
    transform_position_between_ref_frames,
)

IDENTITY_POSE = [0.0] * 6
CARTESIAN_POSE = [100.0, 200.0, 300.0, 30.0, 45.0, 60.0]
TRANSLATION_POSE = [50.0, 75.0, 100.0, 0.0, 0.0, 0.0]


class TestEulerToRotationMatrix(MatrixAssertionsMixin):
    def setUp(self) -> None:
        self.cartesian_pose = list(CARTESIAN_POSE)
        self.identity_pose = list(IDENTITY_POSE)

    def test_identity_rotation(self) -> None:
        result = euler_to_rotation_matrix(self.identity_pose)
        self._assert_matrices_close(result, np.eye(3))

    def test_rotation_matrix_properties(self) -> None:
        result = euler_to_rotation_matrix(self.cartesian_pose)
        self.assertAlmostEqual(np.linalg.det(result), 1.0, places=5)
        # matrix multiplication between the transpose and the original should yield the identity matrix
        self._assert_matrices_close(result.T @ result, np.eye(3))


class TestEulerToHomogeneousMatrix(MatrixAssertionsMixin):
    def setUp(self) -> None:
        self.cartesian_pose = list(CARTESIAN_POSE)
        self.identity_pose = list(IDENTITY_POSE)
        self.translation_pose = list(TRANSLATION_POSE)

    def test_identity_homogeneous(self) -> None:
        result = euler_to_homogeneous_transform_matrix(self.identity_pose)
        self._assert_matrices_close(result, np.eye(4))

    def test_bottom_row_and_translation(self) -> None:
        result = euler_to_homogeneous_transform_matrix(self.cartesian_pose)
        self.assertEqual(result.shape, (4, 4))
        self._assert_matrices_close(result[3:], np.array([[0, 0, 0, 1]]))
        for i in range(3):
            self.assertAlmostEqual(result[i, 3], self.cartesian_pose[i])

    def test_pure_translation_matrix(self) -> None:
        result = euler_to_homogeneous_transform_matrix(self.translation_pose)
        self._assert_matrices_close(result[:3, :3], np.eye(3))
        for i in range(3):
            self.assertAlmostEqual(result[i, 3], self.translation_pose[i])


class TestHomogeneousToEuler(MatrixAssertionsMixin):
    def setUp(self) -> None:
        self.cartesian_pose = list(CARTESIAN_POSE)

    def test_roundtrip_conversion(self) -> None:
        transform = euler_to_homogeneous_transform_matrix(self.cartesian_pose)
        result = homogeneous_transform_matrix_to_euler(transform)
        self._assert_poses_close(result, self.cartesian_pose)

    def test_identity_matrix(self) -> None:
        result = homogeneous_transform_matrix_to_euler(np.eye(4))
        self._assert_poses_close(result, [0.0] * 6)


class TestReferenceFrameTransforms(MatrixAssertionsMixin):
    def test_identity_transform(self) -> None:
        pose = [1.0, 2.0, 3.0, 10.0, 20.0, 30.0]
        result = transform_position_between_ref_frames(pose, [0.0] * 6, [0.0] * 6)
        self._assert_poses_close(result, pose)

    def test_translation_only(self) -> None:
        frame1 = [10.0, 20.0, 30.0, 0.0, 0.0, 0.0]
        frame2 = [5.0, 10.0, 15.0, 0.0, 0.0, 0.0]
        position = [1.0, 2.0, 3.0, 0.0, 0.0, 0.0]
        expected = [6.0, 12.0, 18.0, 0.0, 0.0, 0.0]
        result = transform_position_between_ref_frames(position, frame1, frame2)
        self._assert_poses_close(result, expected)

    def test_rotation_transform(self) -> None:
        frame_a = [100.0, 200.0, 300.0, 0.0, 0.0, 90.0]
        frame_b = [50.0, 50.0, 50.0, 0.0, 0.0, 0.0]
        test_pos = [10.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        expected_pos = [50.0, 160.0, 250.0, 0.0, 0.0, 90.0]
        result = transform_position_between_ref_frames(test_pos, frame_a, frame_b)
        self._assert_poses_close(result, expected_pos)

    def test_transform_roundtrip(self) -> None:
        frame1 = [10.0, 20.0, 30.0, 10.0, 20.0, 30.0]
        frame2 = [5.0, 15.0, 25.0, 5.0, 15.0, 25.0]
        position = [1.0, 2.0, 3.0, 40.0, 50.0, 60.0]
        out = transform_position_between_ref_frames(position, frame1, frame2)
        back = transform_position_between_ref_frames(out, frame2, frame1)
        self._assert_poses_close(back, position)


if __name__ == "__main__":
    unittest.main()
