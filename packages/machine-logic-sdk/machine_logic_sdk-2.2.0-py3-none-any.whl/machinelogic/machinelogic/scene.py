import logging
from typing import List, TypeVar, Union, cast

from machinelogic.ivention.icalibration_frame import ICalibrationFrame
from machinelogic.ivention.icartesian_target import ICartesianTarget
from machinelogic.ivention.ijoint_target import IJointTarget
from machinelogic.ivention.ireference_frame import IReferenceFrame
from machinelogic.machinelogic.reference_frame import ReferenceFrame
from machinelogic.measurements.angle import UnitOfAngle, convert_angle

from ..ivention.exception import SceneException
from ..ivention.iscene import IScene
from ..ivention.types.robot_pose import Pose
from ..ivention.types.scene_assets import (
    AssetList,
    AssetMapping,
    CalibrationFrameAsset,
    CartesianTargetAsset,
    JointTargetAsset,
    ReferenceFrameAsset,
)
from ..ivention.util.inheritance import inherit_docstrings  # type: ignore
from .api import Api
from .calibration_frame import CalibrationFrame
from .cartesian_target import CartesianTarget
from .joint_target import JointTarget
from .utils.robot_pose_conversions import convert_pose_to_cartesian_pose


@inherit_docstrings
class Scene(IScene):
    def __init__(self, api: Api) -> None:
        self._calibration_frame_list: List[CalibrationFrame] = []
        self._joint_target_list: List[JointTarget] = []
        self._reference_frame_list: List[ReferenceFrame] = []
        self._cartesian_target_list: List[CartesianTarget] = []
        self._initialize_assets(api)

    def get_calibration_frame(self, name: str) -> CalibrationFrame:
        return _find_asset_in_list_by_name(
            self._calibration_frame_list,
            name,
            f"Failed to find calibration frame with name: {name}",
            "Multiple calibration frames found with name: {}, using first one found with id: {}.",
        )

    def get_reference_frame(self, name: str) -> ReferenceFrame:
        return _find_asset_in_list_by_name(
            self._reference_frame_list,
            name,
            f"Failed to find reference frame with name: {name}",
            "Multiple reference frames found with name: {}, using first one found with id: {}.",
        )

    def get_cartesian_target(self, name: str) -> CartesianTarget:
        """Gets a cartesian target from scene assets by name

        Args:
            name (str): Friendly name of the cartesian target asset

        Raises:
            SceneException: If the scene asset is not found

        Returns:
            CartesianTarget: The found cartesian target
        """
        return _find_asset_in_list_by_name(
            self._cartesian_target_list,
            name,
            f"Failed to find cartesian target with name: {name}",
            "Multiple cartesian targets found with name: {}, using first one found with id: {}.",
        )

    def get_joint_target(self, name: str) -> JointTarget:
        return _find_asset_in_list_by_name(
            self._joint_target_list,
            name,
            f"Failed to find joint target with name: {name}",
            "Multiple joint targets found with name: {}, using first one found with id: {}.",
        )

    def _initialize_assets(self, api: Api) -> None:
        scene_assets_json = api.get_scene_assets()
        for scene_asset_json in scene_assets_json["assets"]:
            scene_asset_type = scene_asset_json["type"]
            if scene_asset_type == AssetMapping.CALIBRATION_FRAME:
                calibration_frame_asset = cast(CalibrationFrameAsset, scene_asset_json)
                self._calibration_frame_list.append(_create_calibration_frame(calibration_frame_asset, api))
            if scene_asset_type == AssetMapping.JOINT_TARGET:
                joint_target_asset = cast(JointTargetAsset, scene_asset_json)
                self._joint_target_list.append(_create_joint_target(joint_target_asset, api))
            if scene_asset_type == AssetMapping.CARTESIAN_TARGET:
                cartesian_target_asset = cast(CartesianTargetAsset, scene_asset_json)
                self._cartesian_target_list.append(_create_cartesian_target(cartesian_target_asset, api))
            if scene_asset_type == AssetMapping.REFERENCE_FRAME:
                reference_frame_asset = cast(ReferenceFrameAsset, scene_asset_json)
                self._reference_frame_list.append(_create_reference_frame(reference_frame_asset, api))

        asset_list = self._get_all_assets()
        for ref_frame in self._reference_frame_list:
            ref_frame._set_asset_list(asset_list)
        for cartesian_target in self._cartesian_target_list:
            cartesian_target._set_asset_list(asset_list)

    def _get_all_assets(
        self,
    ) -> AssetList:
        """Returns a list of all assets in the scene."""

        asset_list: AssetList = []
        asset_list.extend(self._calibration_frame_list)
        asset_list.extend(self._joint_target_list)
        asset_list.extend(self._reference_frame_list)
        asset_list.extend(self._cartesian_target_list)
        return asset_list


TAsset = TypeVar(
    "TAsset",
    bound=Union[ICalibrationFrame, IJointTarget, IReferenceFrame, ICartesianTarget],
)


def _find_asset_in_list_by_name(
    asset_list: List[TAsset],
    name: str,
    exception_message: str,
    warning_message: str = "",
) -> TAsset:
    """Helper function to find an asset by name in a list.

    Args:
        asset_list (Union[CalibrationFrame, JointTarget, ReferenceFrame]): The list of assets to search.
        name (str): The name of the asset to find.
        exception_message (str): The message for the exception if not found.
        warning_message (str): The message for the warning if multiple found.

    Returns:
        CalibrationFrame | JointTarget | ReferenceFrame: The found asset.

    Raises:
        SceneException: If no asset is found with the given name.
    """
    matching_assets = [asset for asset in asset_list if asset._configuration.name == name]
    if len(matching_assets) == 0:
        raise SceneException(exception_message.format(name))
    if len(matching_assets) > 1 and warning_message:
        logging.warning(warning_message.format(name, matching_assets[0]._configuration.uuid))
    return matching_assets[0]


def _create_calibration_frame(calibration_frame_json: CalibrationFrameAsset, api: Api) -> CalibrationFrame:
    """Takes a calibration frame configuration in JSON format and
        converts it to a CalibrationFrame

    Args:
        calibration_frame_json (CalibrationFrameAsset): The calibration frame in JSON format
        api: The machinelogic api
    Returns:
        CalibrationFrame: An instance of a calibration frame
    """
    calibration_frame_parameters = calibration_frame_json["parameters"]
    uuid = calibration_frame_json["id"]
    name = calibration_frame_parameters["name"]

    # makes sure values are in mm and deg because that's all we can handle right now
    position = calibration_frame_parameters["position"]
    rotation = calibration_frame_parameters["rotation"]
    pose = Pose(position=position, rotation=rotation)
    default_value = convert_pose_to_cartesian_pose(pose)
    return CalibrationFrame(uuid, name, default_value, api)


def _create_joint_target(joint_target_json: JointTargetAsset, api: Api) -> JointTarget:
    """Takes a joint target configuration in JSON format and
        converts it to a JointTarget

    Args:
        joint_target_json (JointTargetAsset): The joint target in JSON format
        api: The machinelogic api

    Returns:
        JointTarget: An instance of a joint target
    """
    joint_target_parameters = joint_target_json["parameters"]
    uuid = joint_target_json["id"]
    name = joint_target_parameters["name"]

    # Extract the joint angles from the JSON
    joint_angles = joint_target_parameters["jointAngles"]
    joint_angles_deg = [
        (
            convert_angle(joint_angle["value"], joint_angle["unit"], UnitOfAngle.DEGREE)["value"]
            if "unit" in joint_angle and joint_angle["unit"] != UnitOfAngle.DEGREE
            else joint_angle["value"]
        )
        for joint_angle in joint_angles
    ]

    return JointTarget(uuid, name, joint_angles_deg, api)


def _create_reference_frame(reference_frame_json: ReferenceFrameAsset, api: Api) -> ReferenceFrame:
    """Takes a reference frame configuration in JSON format and
        converts it to a ReferenceFrame

    Args:
        reference_frame_json (ReferenceFrameAsset): The reference frame in JSON format
        api: The machinelogic api

    Returns:
        ReferenceFrame: An instance of a reference frame
    """
    reference_frame_parameters = reference_frame_json["parameters"]
    uuid = reference_frame_json["id"]
    name = reference_frame_parameters["name"]
    position = reference_frame_parameters["position"]
    rotation = reference_frame_parameters["rotation"]
    parent_reference_frame_id = reference_frame_parameters["parentReferenceFrameId"]

    pose = Pose(position=position, rotation=rotation)
    default_position = convert_pose_to_cartesian_pose(pose)

    return ReferenceFrame(
        uuid,
        name,
        default_position,
        api,
        parent_reference_frame_id=parent_reference_frame_id,
    )


def _create_cartesian_target(cartesian_target_json: CartesianTargetAsset, api: Api) -> CartesianTarget:
    """Takes a cartesian target configuration in JSON format and
        converts it to a CartesianTarget

    Args:
        cartesian_target_json (CartesianTargetAsset): The cartesian target in JSON format
        api: The machinelogic api

    Returns:
        CartesianTarget: An instance of a cartesian target
    """
    cartesian_target_parameters = cartesian_target_json["parameters"]
    uuid = cartesian_target_json["id"]
    name = cartesian_target_parameters["name"]
    position = cartesian_target_parameters["position"]
    rotation = cartesian_target_parameters["rotation"]
    parent_reference_frame_id = cartesian_target_parameters["parentReferenceFrameId"]
    pose = Pose(position=position, rotation=rotation)
    default_position = convert_pose_to_cartesian_pose(pose)
    return CartesianTarget(uuid, name, default_position, api, parent_reference_frame_id)
