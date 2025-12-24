import unittest

from machinelogic.ivention.types.robot_types import CartesianPose, Matrix


class MatrixAssertionsMixin(unittest.TestCase):
    def _assert_matrices_close(self, matrix1: Matrix, matrix2: Matrix) -> None:
        self.assertEqual(matrix1.shape, matrix2.shape)
        # Handle 1D arrays
        if len(matrix1.shape) == 1:
            for i in range(matrix1.shape[0]):
                self.assertAlmostEqual(
                    matrix1[i],
                    matrix2[i],
                    places=5,
                    msg=f"Arrays differ at position [{i}]: {matrix1[i]} != {matrix2[i]}",
                )
        # Handle 2D arrays
        else:
            for i in range(matrix1.shape[0]):
                for j in range(matrix1.shape[1]):
                    self.assertAlmostEqual(
                        matrix1[i, j],
                        matrix2[i, j],
                        places=5,
                        msg=f"Matrices differ at position [{i}, {j}]: {matrix1[i, j]} != {matrix2[i, j]}",
                    )

    def _assert_poses_close(self, pose1: CartesianPose, pose2: CartesianPose) -> None:
        self.assertEqual(len(pose1), len(pose2))
        for i, (val1, val2) in enumerate(zip(pose1, pose2)):
            self.assertAlmostEqual(val1, val2, places=5, msg=f"Poses differ at index {i}: {val1} != {val2}")
