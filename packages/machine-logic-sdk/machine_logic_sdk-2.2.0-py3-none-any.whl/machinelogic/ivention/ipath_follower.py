"""_summary_"""

from abc import ABC, abstractmethod
from typing import Union

from .exception import PathFollowingException
from .iactuator import IActuator
from .idigital_output import IDigitalOutput


class PathFollowerState:
    """
    PathFollower State
    """

    def __init__(self) -> None:
        self._running = False
        self._line_number = 0
        self._current_command: Union[str, None] = None
        self._gcode_error: Union[str, None] = None
        self._speed: float = 0.0
        self._acceleration: float = 0.0

    @property
    def speed(self) -> float:
        """The current tool speed in millimeters/second"""
        return self._speed

    @property
    def acceleration(self) -> float:
        """The current tool acceleration in millimeters/second^2"""
        return self._acceleration

    @property
    def running(self) -> bool:
        """
        True if path following in progress.
        """
        return self._running

    @property
    def line_number(self) -> int:
        """
        Current line number in gcode script.
        """
        return self._line_number

    @property
    def current_command(self) -> Union[str, None]:
        """
        In-progress command of gcode script.
        """
        return self._current_command

    @property
    def error(self) -> Union[str, None]:
        """
        A description of errors encountered during path execution.
        """
        return self._gcode_error


class IPathFollower(ABC):
    """Path Follower:  A Path Follower Object is a group of Actuators,
    Digital Inputs and Digital Outputs that enable execution of smooth predefined paths.
    These paths are defined with G-Code instructions. See Vention's G-code interface documentation
    for a list of supported commands:
    https://vention.io/resources/guides/path-following-interface-391#parser-configuration
    """

    def __init__(
        self,
        x_axis: Union[IActuator, None],
        y_axis: Union[IActuator, None],
        z_axis: Union[IActuator, None],
    ) -> None:
        """Create a Path Follower object.

        Args:
            x_axis (Union[IActuator, None]): Optional, Actuator mapping to X axis in gcode
            y_axis (Union[IActuator, None]): Optional, Actuator mapping to Y axis in gcode
            z_axis (Union[IActuator, None]): Optional, Actuator mapping to Z axis in gcode

        Raises:
            PathFollowingException: If Actuators are on different controllers
            PathFollowingException: If PathFollower does not contain at least one Actuator
        """

        controller_id = None
        for actuator in [x_axis, y_axis, z_axis]:
            if actuator is None:
                continue
            next_controller_id = actuator.configuration.controller_id
            if controller_id and next_controller_id != controller_id:
                raise PathFollowingException("PathFollower Axes must be on the same controller")
            controller_id = next_controller_id
        if controller_id is None:
            raise PathFollowingException("PathFollower object must contain at least one actuator")

        self._x_axis = x_axis
        self._y_axis = y_axis
        self._z_axis = z_axis
        self._controller_id = controller_id
        self._state: PathFollowerState = PathFollowerState()

    @property
    def state(self) -> PathFollowerState:
        """Current state of the path follower"""
        return self._state

    @abstractmethod
    def add_tool(
        self,
        tool_id: int,
        m3_output: IDigitalOutput,
        m4_output: Union[IDigitalOutput, None],
    ) -> None:
        """
        Add a tool to be referenced by the M(3-5) $[tool_id] commands

        Args:
            tool_id (int): Unique integer defining tool id.
            m3_output (IDigitalOutput): Output to map to the M3 Gcode command
            m4_output (Union[IDigitalOutput, None]): Optional, Output to map to the M4 Gcode command

        Raises:
            PathFollowerException: If the tool was not properly added.
        """

    @abstractmethod
    def start_path(self, gcode: str) -> None:
        """
        Start the path, returns when path is complete

        Args:
            gcode (str): Gcode path

        Raises:
            PathFollowerException: If failed to run start_path
        """

    @abstractmethod
    def start_path_async(self, gcode: str) -> None:
        """
        Start the path, nonblocking, returns immediately

        Args:
            gcode (str): Gcode path

        Raises:
            PathFollowerException: If failed to run start_path_async
        """

    @abstractmethod
    def stop_path(self) -> None:
        """Abruptly stop the path following procedure.
        Affects all actuators in the PathFollower instance

        Raises:
            PathFollowerException: If failed to stop path
        """

    @abstractmethod
    def wait_for_path_completion(self) -> None:
        """Wait for the path to complete"""
