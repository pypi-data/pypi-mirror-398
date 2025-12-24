from __future__ import annotations

from typing import Any

from scipy.spatial.transform import Rotation as scipyR

from ..ivention.icamera import ICamera, ICameraConfiguration
from ..ivention.types.robot_types import CartesianPose
from ..ivention.util.inheritance import inherit_docstrings  # type: ignore
from .api import Api


@inherit_docstrings
class CameraConfiguration(ICameraConfiguration):
    def __init__(
        self,
        uuid: str,
        name: str,
    ) -> None:
        super().__init__(uuid=uuid, name=name)


@inherit_docstrings
class Camera(ICamera):
    def __init__(self, configuration: ICameraConfiguration, api: Api):
        super().__init__(configuration)
        self._configuration = configuration
        self._api = api

    def start(self) -> dict[str, Any] | str:
        return self._api.camera_start()

    def grab(self) -> dict[str, Any] | str:
        return self._api.camera_grab()

    def stop(self) -> dict[str, Any] | str:
        return self._api.camera_stop()

    def calibrate(self) -> dict[str, Any] | str:
        return self._api.camera_calibrate()

    def calibration_save(self) -> str:
        return self._api.camera_calibration_save()

    def calibration_pose(self, cartesian_pose: CartesianPose) -> dict[str, Any] | str:
        actual_tcp_pose = self.__euler_yzy_to_rotvec(cartesian_pose)
        return self._api.camera_calibration_pose(actual_tcp_pose)

    def calibration_reset(self, new_calibration_file: str | None = None) -> dict[str, Any] | str:
        return self._api.camera_calibration_reset(new_calibration_file)

    def _play(self, filename: str) -> dict[str, Any] | str:
        return self._api.camera_play(filename)

    def _record(self) -> dict[str, Any] | str:
        return self._api.camera_record()

    def target_get_position(self, actual_tcp_pose: CartesianPose | None = None) -> dict[str, Any] | str:
        return self._api.camera_target_get_position(actual_tcp_pose)

    def versions(self) -> dict[str, Any] | str:
        json_dict: dict[str, Any] | str = self._api.camera_get_versions()
        return json_dict

    def __euler_yzy_to_rotvec(self, pos: CartesianPose) -> list[float]:
        """
        Convert coordinates from Euler('zyz') to rotation vector: a 3 dimensional vector
        which is co-directional to the axis of rotation and whose norm gives
        the angle of rotation

        Args:
            pos (_type_): CartesianPose as retrieve from the robot state

        Returns:
            _type_: position and rotation vector
        """
        rotation_euler = scipyR.from_euler("zyz", pos[3:], degrees=True)
        rv = rotation_euler.as_rotvec()
        return [pos[0], pos[1], pos[2], rv[0], rv[1], rv[2]]
