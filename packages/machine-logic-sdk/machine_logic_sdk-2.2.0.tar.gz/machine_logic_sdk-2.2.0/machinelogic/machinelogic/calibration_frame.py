from typing import Union, cast

from ..ivention.exception import SceneException
from ..ivention.icalibration_frame import (
    ICalibrationFrame,
    ICalibrationFrameConfiguration,
)
from ..ivention.types import robot_calibration
from ..ivention.types.robot_types import CartesianPose
from ..ivention.util.inheritance import inherit_docstrings  # type: ignore
from .api import Api
from .utils.robot_pose_conversions import (
    convert_cartesian_pose_to_pose,
    convert_pose_to_cartesian_pose,
)


class CalibrationFrameConfiguration(ICalibrationFrameConfiguration):
    def __init__(
        self,
        api: Api,
        uuid: str,
        name: str,
        default_value: CartesianPose,
    ) -> None:
        super().__init__(uuid, name, default_value)
        self._api = api

    @property
    def calibrated_value(self) -> Union[CartesianPose, None]:
        calibration_frame_json = self._api.get_calibration_frame(self.uuid)["robotCalibration"]
        if calibration_frame_json is None:
            return calibration_frame_json
        calibrated_pose = calibration_frame_json["calibrated"]
        calibrated_value = convert_pose_to_cartesian_pose(calibrated_pose)
        return calibrated_value


@inherit_docstrings
class CalibrationFrame(ICalibrationFrame):
    """
    A software representation of a Calibration Frame as defined within the scene assets pane
    A calibration frame is defined in mm and degrees, where the angles are extrinsic Euler
    angles in XYZ order.
    """

    def __init__(self, uuid: str, name: str, default_value: CartesianPose, api: Api) -> None:
        self.__configuration = CalibrationFrameConfiguration(api, uuid, name, default_value)
        self._api = api

    @property
    def _configuration(self) -> CalibrationFrameConfiguration:
        return self.__configuration

    def get_default_value(self) -> CartesianPose:
        return self._configuration.default_value

    def get_calibrated_value(self) -> Union[CartesianPose, None]:
        return self._configuration.calibrated_value

    def set_calibrated_value(self, frame: CartesianPose) -> None:
        robot_calibrated_pose = convert_cartesian_pose_to_pose(frame)
        robot_calibration_values = cast(
            robot_calibration.RobotCalibration,
            {
                "calibrated": robot_calibrated_pose,
            },
        )

        if not self._api.set_calibration_frame(self._configuration.uuid, robot_calibration_values):
            raise SceneException(
                f"""
                Failed to set calibrated value of calibrationFrame with
                name: {self._configuration.name} and id: {self._configuration.uuid}
                """
            )
        print(f"Successfully set calibrated values to: {frame}")
