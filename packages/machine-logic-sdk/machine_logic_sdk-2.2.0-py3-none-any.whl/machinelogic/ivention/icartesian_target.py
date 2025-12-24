from abc import ABC, abstractmethod
from typing import Literal

from machinelogic.decorators.undocumented import undocumented

from ..ivention.types.robot_types import CartesianPose


class ICartesianTargetConfiguration(ABC):
    """
    Interface for the cartesian target configuration.
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
        """The Cartesian Target's ID"""
        return self._uuid

    @property
    def name(self) -> str:
        """The Cartesian Target's name"""
        return self._name

    @property
    def default_position(self) -> CartesianPose:
        """The nominal cartesian pose of the target (without calibration) with respect to its parent reference frame,
        in mm and degrees, where the angles are extrinsic Euler angles in XYZ order."""
        return self._default_position

    @property
    def parent_reference_frame_id(self) -> str:
        """The ID of the parent reference frame, if it exists."""
        return self._parent_reference_frame_id


class ICartesianTarget(ABC):
    """
    A cartesian target, as defined in the scene assets pane, is represented in software.
    It is measured in millimeters and degrees, with angles given
    as extrinsic Euler angles in XYZ order.
    """

    @property
    @undocumented
    @abstractmethod
    def _configuration(self) -> ICartesianTargetConfiguration:
        pass

    @abstractmethod
    def get_position(self, relative_to: Literal["robot_base", "parent"] = "parent") -> CartesianPose:
        """Gets the cartesian target's pose values. If the reference frame underwich the position is requested is calibrated,
        the position is returned in the calibrated reference frame's position.

        Args:
            relative_to (Literal["robot_base", "parent"]): The reference frame to which the position is relative.
                Defaults to "parent".

        Raises:
            SceneException: If failed to get the default value

        Returns:
            CartesianPose: The pose of the cartesian target
                in mm and degrees, where the angles are extrinsic Euler angles in XYZ order.
        """
