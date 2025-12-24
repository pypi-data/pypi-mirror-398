from enum import Enum
from typing import TypedDict, Union

from machinelogic.ivention.icalibration_frame import ICalibrationFrame
from machinelogic.ivention.icartesian_target import ICartesianTarget
from machinelogic.ivention.ijoint_target import IJointTarget
from machinelogic.ivention.ireference_frame import IReferenceFrame

from ...measurements.angle import Angle
from .robot_pose import Position, Rotation


class AssetMapping(str, Enum):
    CALIBRATION_FRAME = "RobotCalibrationFrame"
    REFERENCE_FRAME = "ReferenceFrame"
    CARTESIAN_TARGET = "RobotWaypoint"
    JOINT_TARGET = "RobotJointPosition"


class AssetParametersBase(TypedDict):
    name: str
    scope: str
    scopeId: str


class AssetBase(TypedDict):
    """Dictionary representing a typical asset structure"""

    id: str
    type: AssetMapping


class CalibrationFrameParameters(AssetParametersBase):
    position: Position
    rotation: Rotation


class JointTargetParameters(AssetParametersBase):
    jointAngles: list[Angle]


class CartesianTargetParameters(AssetParametersBase):
    position: Position
    rotation: Rotation
    parentReferenceFrameId: str


class ReferenceFrameParameters(AssetParametersBase):
    position: Position
    rotation: Rotation
    parentReferenceFrameId: str


class CalibrationFrameAsset(AssetBase):
    parameters: CalibrationFrameParameters


class JointTargetAsset(AssetBase):
    parameters: JointTargetParameters


class CartesianTargetAsset(AssetBase):
    parameters: CartesianTargetParameters


class ReferenceFrameAsset(AssetBase):
    parameters: ReferenceFrameParameters


SceneAssets = Union[CalibrationFrameAsset, JointTargetAsset, CartesianTargetAsset, ReferenceFrameAsset]
AssetList = list[Union[ICalibrationFrame, IJointTarget, ICartesianTarget, IReferenceFrame]]
