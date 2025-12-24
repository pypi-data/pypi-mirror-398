from abc import ABC, abstractmethod
from typing import Union

from machinelogic.decorators.undocumented import undocumented

from ..ivention.types.robot_types import CartesianPose


class ICalibrationFrameConfiguration(ABC):
    """
    A representation of the configuration of a Calibration Frame instance.
    This configuration defines what the Calibration Frame is and how it
    is defined in the context of the scene.
    """

    def __init__(
        self,
        uuid: str,
        name: str,
        default_value: CartesianPose,
    ) -> None:
        self._uuid: str = uuid
        self._name: str = name
        self._default_value: CartesianPose = default_value

    @property
    def uuid(self) -> str:
        """The Calibration Frame's ID"""
        return self._uuid

    @property
    def name(self) -> str:
        """The Calibration Frame's name"""
        return self._name

    @property
    def default_value(self) -> CartesianPose:
        """The nominal value of the Calibration Frame,
        in mm and degrees, where the angles are extrinsic Euler angles in XYZ order."""
        return self._default_value

    @property
    @abstractmethod
    def calibrated_value(self) -> Union[CartesianPose, None]:
        """The calibrated value of the Calibration Frame,
        in mm and degrees, where the angles are extrinsic Euler angles in XYZ order."""


class ICalibrationFrame(ABC):
    """
    A calibration frame, as defined in the scene assets pane, is represented in software.
    It is measured in millimeters and degrees, with angles given
    as extrinsic Euler angles in XYZ order.
    """

    @property
    @undocumented
    @abstractmethod
    def _configuration(self) -> ICalibrationFrameConfiguration:
        pass

    @abstractmethod
    def get_default_value(self) -> CartesianPose:
        """Gets the calibration frame's default values.

        Raises:
            SceneException: If failed to get the default value

        Returns:
            CartesianPose: The nominal value of the calibration frame
                in mm and degrees, where the angles are extrinsic Euler angles in XYZ order.
        """

    @abstractmethod
    def get_calibrated_value(self) -> Union[CartesianPose, None]:
        """Gets the calibration frame's calibrated values.

        Raises:
            SceneException: If failed to get the calibrated value

        Returns:
            CartesianPose: The calibrated value of the calibration frame
                in mm and degrees, where the angles are extrinsic Euler angles in XYZ order.
        """

    @abstractmethod
    def set_calibrated_value(self, frame: CartesianPose) -> None:
        """Sets the calibration frame's calibrated values.

        Args:
            frame (CartesionPose): The calibrated values of the Calibration Frame in mm and degrees,
                where the angles are extrinsic Euler angles in XYZ order.

        Raises:
            SceneException: If failed to set the calibrated value
        """
