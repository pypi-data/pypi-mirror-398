from abc import ABC, abstractmethod
from typing import Literal

from machinelogic.decorators.undocumented import undocumented

from ..ivention.types.robot_types import CartesianPose


class IReferenceFrameConfiguration(ABC):
    """
    A representation of the configuration of a Reference Frame instance.
    This configuration defines what the Reference Frame is and how it
    is defined in the context of the scene.
    """

    def __init__(
        self,
        uuid: str,
        name: str,
        default_position: CartesianPose,
        parent_reference_frame_id: str,
    ) -> None:
        self._uuid: str = uuid
        self._name: str = name
        self._default_position: CartesianPose = default_position
        self._parent_reference_frame_id: str = parent_reference_frame_id

    @property
    def uuid(self) -> str:
        """The Reference Frame's ID"""
        return self._uuid

    @property
    def name(self) -> str:
        """The Reference Frame's name"""
        return self._name

    @property
    def default_position(self) -> CartesianPose:
        """The nominal value (without calibration) of the Reference Frame's position with respect to its parent reference frame,
        in mm and degrees, where the angles are extrinsic Euler angles in XYZ order."""
        return self._default_position

    @property
    def parent_reference_frame_id(self) -> str:
        """The ID of the parent reference frame, if it exists."""
        return self._parent_reference_frame_id


class IReferenceFrame(ABC):
    """
    A reference frame, as defined in the scene assets pane, is represented in software.
    It is measured in millimeters and degrees, with angles given
    as extrinsic Euler angles in XYZ order.
    """

    @property
    @undocumented
    @abstractmethod
    def _configuration(self) -> IReferenceFrameConfiguration:
        pass

    @abstractmethod
    def get_position(self, relative_to: Literal["robot_base", "parent"] = "robot_base") -> CartesianPose:
        """Gets the reference frame's position. If the reference frame underwhich the position is requested is calibrated,
        the position is returned in the calibrated reference frame's position.

        Args:
            relative_to (Literal["robot_base", "parent"]): The reference frame's position
                relative to the robot base or its parent reference frame.
                Defaults to "parent".

        Raises:
            SceneException: If failed to get the position

        Returns:
            CartesianPose: The position of the reference frame
                in mm and degrees, where the angles are extrinsic Euler angles in XYZ order.
        """
