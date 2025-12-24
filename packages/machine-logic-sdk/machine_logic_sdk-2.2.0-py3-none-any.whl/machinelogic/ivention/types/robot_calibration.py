from typing import TypedDict

from .robot_pose import Pose


class RobotCalibration(TypedDict):
    """Dictionary representing a robot calibration"""

    calibrated: Pose


class RobotCalibrationWithID(RobotCalibration):
    """Dictionary representing a robot calibration with id"""

    id: str
