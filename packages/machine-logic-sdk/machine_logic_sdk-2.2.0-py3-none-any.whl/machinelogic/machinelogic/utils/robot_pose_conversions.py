from typing import List, Literal, cast

from ...ivention.types.robot_pose import Pose, Position, Rotation
from ...ivention.types.robot_types import CartesianPose
from ...measurements.angle import Angle, UnitOfAngle, convert_angle
from ...measurements.distance import Distance, UnitOfDistance, convert_distance


def convert_pose_to_cartesian_pose(
    pose: Pose,
    distance_units: UnitOfDistance = UnitOfDistance.MILLIMETERS,
    angle_units: UnitOfAngle = UnitOfAngle.DEGREE,
) -> CartesianPose:
    """Converts a Pose made up of Position (x:Distance, y:Distance, z:Distance)
        and Rotation (i:Angle, j:Angle, k:Angle) types
        into a simple list of length 6 [x,y,z,i,j,k] of defined units.

    Args:
        pose (Pose): Pose to convert
        distance_units (UnitOfDistance, optional): Unit of distance to convert to.
            Defaults to UnitOfDistance.MILLIMETERS.
        angle_units (UnitOfAngle, optional): Unit of angle to convert to.
            Defaults to UnitOfAngle.DEGREE.

    Returns:
        CartesianPose: _description_
    """
    position = pose["position"]
    rotation = pose["rotation"]

    distance_axes: List[Literal["x", "y", "z"]] = ["x", "y", "z"]
    rotation_axes: List[Literal["i", "j", "k"]] = ["i", "j", "k"]
    return [
        convert_distance(
            position[axis]["value"],
            distance_units,
            UnitOfDistance(position[axis]["unit"]),
        )["value"]
        for axis in distance_axes
    ] + [
        convert_angle(
            rotation[axis]["value"],
            angle_units,
            UnitOfAngle(rotation[axis]["unit"]),
        )["value"]
        for axis in rotation_axes
    ]


def convert_cartesian_pose_to_pose(
    cartesian_pose: CartesianPose,
) -> Pose:
    """Converts a CartesianPose list [x,y,z,i,j,k] into a Pose with Position and Rotation.
        Assumes for now that CartesianPose has units mm and deg

    Args:
        cartesian_pose (CartesianPose): CartesianPose to convert

    Returns:
        Pose: A dictionary representing the Pose with Position and Rotation.
    """
    if len(cartesian_pose) != 6:
        raise ValueError("CartesianPose must have exactly 6 elements [x,y,z,i,j,k].")

    distance_axes: List[str] = ["x", "y", "z"]
    rotation_axes: List[str] = ["i", "j", "k"]

    # CartesianPoses only can be used in mm and deg, so we create a Pose with these units
    position = {axis: Distance(value=cartesian_pose[i], unit=UnitOfDistance.MILLIMETERS) for i, axis in enumerate(distance_axes)}

    rotation = {axis: Angle(value=cartesian_pose[i + 3], unit=UnitOfAngle.DEGREE) for i, axis in enumerate(rotation_axes)}
    cast_position = cast(Position, position)
    cast_rotation = cast(Rotation, rotation)
    pose = Pose(position=cast_position, rotation=cast_rotation)

    return pose
