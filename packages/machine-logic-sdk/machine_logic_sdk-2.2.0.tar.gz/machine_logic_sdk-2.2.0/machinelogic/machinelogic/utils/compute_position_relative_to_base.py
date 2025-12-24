from typing import Union

from machinelogic.ivention.exception import SceneException
from machinelogic.ivention.icalibration_frame import ICalibrationFrame
from machinelogic.ivention.icartesian_target import ICartesianTarget
from machinelogic.ivention.ireference_frame import IReferenceFrame
from machinelogic.ivention.types.robot_types import CartesianPose
from machinelogic.ivention.types.scene_assets import AssetList
from machinelogic.machinelogic.utils.robot_transforms import (
    euler_to_homogeneous_transform_matrix,
    homogeneous_transform_matrix_to_euler,
)


def compute_position_relative_to_base(
    child_asset: Union[IReferenceFrame, ICalibrationFrame, ICartesianTarget],
    asset_list: AssetList,
) -> CartesianPose:
    """
    Computes the transform matrix from parent and converts to CartesianPose.

    Args:
        child_asset: The child asset for which the position is computed.
        asset_list: List of all assets in the scene.
    Raises:
        SceneException: If no parent asset is found with the specified ID.
    Returns:
        CartesianPose: Position in [x, y, z, rx, ry, rz] format (mm and degrees)
    """

    if isinstance(child_asset, ICalibrationFrame):
        calibrated_value = child_asset.get_calibrated_value()
        return calibrated_value if calibrated_value is not None else child_asset.get_default_value()

    child_position = child_asset._configuration.default_position

    transform_matrix = euler_to_homogeneous_transform_matrix(child_position)

    parent_id = child_asset._configuration.parent_reference_frame_id
    parent_asset = None
    valid_parents = (
        IReferenceFrame,
        ICalibrationFrame,
    )
    for asset in asset_list:
        if isinstance(asset, valid_parents) and asset._configuration.uuid == parent_id:
            parent_asset = asset
            break

    if parent_asset is None:
        raise SceneException(f"No asset found with id {parent_id}")

    # Recursive call to get parent transform matrix
    parent_position = compute_position_relative_to_base(parent_asset, asset_list)
    parent_matrix = euler_to_homogeneous_transform_matrix(parent_position)

    result_matrix = parent_matrix @ transform_matrix

    return homogeneous_transform_matrix_to_euler(result_matrix)
