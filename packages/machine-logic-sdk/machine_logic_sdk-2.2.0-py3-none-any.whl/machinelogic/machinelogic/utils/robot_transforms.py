import warnings

import numpy
from scipy.spatial.transform import Rotation as scipy_rotation

from machinelogic.ivention.types.robot_types import CartesianPose, Matrix


def euler_to_rotation_matrix(cartesian_pose: CartesianPose, euler_angle_order: str = "XYZ") -> Matrix:
    """
    Converts a Cartesian pose (position and orientation) to a rotation matrix.
    Args:
        cartesian_pose: A list of 6 elements representing the Cartesian pose in the format [x, y, z, i, j, k] in mm and deg.
        euler_angle_order: A sting representing the order of Euler angles (default is "XYZ").
    Returns:
        Matrix: A 3x3 numpy array representing the rotation matrix.
    """
    rotation_matrix_rad: Matrix = scipy_rotation.from_euler(euler_angle_order, cartesian_pose[3:], degrees=True).as_matrix()
    return rotation_matrix_rad


def euler_to_homogeneous_transform_matrix(
    cartesian_pose: CartesianPose,
    euler_angle_order: str = "XYZ",
) -> Matrix:
    """
    Converts a Cartesian pose (position and orientation) to a homogeneous transformation matrix.
    Args:
        cartesian_pose: A list of 6 elements representing the Cartesian pose in the format [x, y, z, i, j, k] in mm and deg.
        euler_angle_order: A string representing the order of Euler angles (default is "XYZ").
    Returns:
        Matrix: A 4x4 numpy array representing the homogeneous transformation matrix.
    """
    rotation_matrix_rad = euler_to_rotation_matrix(cartesian_pose, euler_angle_order=euler_angle_order)
    homogeneous_transform_matrix = numpy.zeros((4, 4))
    for row_index in range(3):
        # copy cartesian positions to the last column
        homogeneous_transform_matrix[row_index, 3] = cartesian_pose[row_index]
        # fill out rotation matrix elements
        for col_index in range(3):
            homogeneous_transform_matrix[row_index, col_index] = rotation_matrix_rad[row_index, col_index]
    # one inside of 4,4 position.
    homogeneous_transform_matrix[3, 3] = 1.0
    return homogeneous_transform_matrix


def homogeneous_transform_matrix_to_euler(
    homogeneous_matrix: Matrix,
    euler_angle_order: str = "XYZ",
) -> CartesianPose:
    """
    Converts a homogeneous transformation matrix (4x4 matrix representing position and orientation) to a Cartesian pose.

    Args:
        homogeneous_matrix: A 4x4 numpy array representing the homogeneous transformation matrix.
        euler_angle_order: A string representing the order of Euler angles (default is "XYZ").

    Returns:
        CartesianPose: A list of 6 elements representing the Cartesian pose in the format [x, y, z, i, j, k] in mm and deg.
    """
    pose_result = [0.0] * 6
    rotation_matrix_rad = homogeneous_matrix[:3, :3]
    rotation_object = scipy_rotation.from_matrix(rotation_matrix_rad)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        euler_angles_degrees = rotation_object.as_euler(euler_angle_order, degrees=True)
    for i in range(3):
        pose_result[i] = homogeneous_matrix[i, 3]
        pose_result[3 + i] = euler_angles_degrees[i]
    return pose_result


def transform_position_between_ref_frames(
    position: CartesianPose,
    from_reference_frame: CartesianPose = [0.0] * 6,
    to_reference_frame: CartesianPose = [0.0] * 6,
    euler_angle_order: str = "XYZ",
) -> CartesianPose:
    """
    Transforms a position vector from one reference frame to another.
    Args:
        position: A list of 6 elements representing the Cartesian pose in the format [x, y, z, i, j, k] in mm and deg.
        from_reference_frame: A list of 6 elements representing the reference frame to transform from (default is [0.0] * 6).
        to_reference_frame: A list of 6 elements representing the reference frame to transform to (default is [0.0] * 6).
        euler_angle_order: A string representing the order of Euler angles (default is "XYZ").
    Returns:
        CartesianPose: A list of 6 elements representing the transformed Cartesian pose in the format [x, y, z, i, j, k] in mm and deg.
    """
    position_matrix = euler_to_homogeneous_transform_matrix(position, euler_angle_order=euler_angle_order)
    from_reference_matrix = euler_to_homogeneous_transform_matrix(from_reference_frame, euler_angle_order=euler_angle_order)
    to_reference_matrix = euler_to_homogeneous_transform_matrix(to_reference_frame, euler_angle_order=euler_angle_order)
    transform_matrix = numpy.linalg.inv(to_reference_matrix) @ from_reference_matrix @ position_matrix
    return homogeneous_transform_matrix_to_euler(transform_matrix)
