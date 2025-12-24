"""_summary_"""

from abc import abstractmethod

from machinelogic.ivention.icartesian_target import ICartesianTarget
from machinelogic.ivention.ijoint_target import IJointTarget
from machinelogic.ivention.ireference_frame import IReferenceFrame

from ..ivention.icalibration_frame import ICalibrationFrame


class IScene:
    """
    A software representation of the scene containing assets
    that describe and define reference frames and targets for robots.

    Only a single instance of this object should exist in your program.
    """

    @abstractmethod
    def get_calibration_frame(self, name: str) -> ICalibrationFrame:
        """Gets a calibration frame from scene assets by name

        Args:
            name (str): Friendly name of the calibration frame asset

        Raises:
            SceneException: If the scene asset is not found

        Returns:
            ICalibrationFrame: The found calibration frame
        """

    @abstractmethod
    def get_reference_frame(self, name: str) -> IReferenceFrame:
        """Gets a reference frame from scene assets by name

        Args:
            name (str): Friendly name of the reference frame asset

        Raises:
            SceneException: If the scene asset is not found

        Returns:
            IReferenceFrame: The found reference frame
        """

    @abstractmethod
    def get_cartesian_target(self, name: str) -> ICartesianTarget:
        """Gets a cartesian target from scene assets by name

        Args:
            name (str): Friendly name of the cartesian target asset

        Raises:
            SceneException: If the scene asset is not found

        Returns:
            ICartesianTarget: The found cartesian target
        """

    @abstractmethod
    def get_joint_target(self, name: str) -> IJointTarget:
        """Gets a joint target from scene assets by name

        Args:
            name (str): Friendly name of the joint target asset

        Raises:
            SceneException: If the scene asset is not found

        Returns:
            IJointTarget: The found joint target
        """
