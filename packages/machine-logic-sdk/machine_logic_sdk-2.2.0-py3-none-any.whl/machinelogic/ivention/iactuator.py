"""_summary_"""

from abc import ABC, abstractmethod
from typing import Callable, Literal, Optional, Tuple

from machinelogic.machinelogic.motion_profile import MotionProfile

from .types.actuator_details import ActuatorType

DEFAULT_MOVEMENT_TIMEOUT_SECONDS = 300


class ActuatorState:
    """
    Representation of the current state of an Actuator instance. The values
    in this class are updated in real time to match the physical reality
    of the Actuator.
    """

    def __init__(self) -> None:
        self._position: float = 0
        self._speed: float = 0
        self._desired_position: float = 0
        self._desired_speed: float = 0
        self._output_torque: dict[str, float] = {}
        self._end_sensors: Tuple[bool, bool] = (False, False)
        self._move_in_progress: bool = False

    @property
    def position(self) -> float:
        """The current position of the Actuator."""
        return self._position

    @property
    def speed(self) -> float:
        """The current speed of the Actuator."""
        return self._speed

    @property
    def output_torque(self) -> dict[str, float]:
        """The current torque output of the Actuator."""
        return self._output_torque

    @property
    def end_sensors(self) -> Tuple[bool, bool]:
        """A tuple representing the state of the [ home, end ] sensors."""
        return self._end_sensors

    @property
    def move_in_progress(self) -> bool:
        """The boolean is True if a move is in progress, otherwise False."""
        return self._move_in_progress


class ActuatorConfiguration:
    """
    Representation of the configuration of an Actuator instance.
    This configuration defines what your Actuator is and how it
    should behave when work is requested from it.
    """

    def __init__(
        self,
        uuid: str,
        name: str,
        actuator_type: ActuatorType,
        home_sensor: Literal["A", "B"],
        units: Literal["mm", "deg"],
        controller_id: str,
    ) -> None:
        self._uuid: str = uuid
        self._name: str = name
        self._actuator_type: ActuatorType = actuator_type
        self._units: Literal["mm", "deg"] = units
        self._home_sensor: Literal["A", "B"] = home_sensor
        self._controller_id: str = controller_id
        self.sensor_event_listener: Optional[Callable[[Tuple[bool, bool]], None]] = None
        self.drive_error_event_listener: Optional[Callable[[int, str], None]] = None

    @property
    def uuid(self) -> str:
        """The Actuator's ID."""
        return self._uuid

    @property
    def actuator_type(self) -> ActuatorType:
        """The type of the Actuator."""
        return self._actuator_type

    @property
    def name(self) -> str:
        """The name of the Actuator."""
        return self._name

    @property
    def home_sensor(self) -> Literal["A", "B"]:
        """The home sensor port, either A or B."""
        return self._home_sensor

    @property
    def units(self) -> Literal["deg", "mm"]:
        """The units that the Actuator functions in."""
        return self._units

    @property
    def controller_id(self) -> str:
        """The controller id of the Actuator"""
        return self._controller_id


class IActuator(ABC):
    """
    A software representation of an Actuator. An Actuator is defined as a motorized
    axis that can move by discrete distances. It is not recommended that you
    construct this object yourself. Rather, you should query it from a Machine instance:

    E.g.:
        machine = Machine()
        my_actuator = machine.get_actuator("Actuator")

    In this example, "New actuator" is the friendly name assigned to the Actuator in the
    MachineLogic configuration page.
    """

    def __init__(self, configuration: ActuatorConfiguration) -> None:
        """
        Args:
            configuration (ActuatorConfiguration): Configuration for this Actuator.
        """
        self._state = ActuatorState()
        self._configuration = configuration

    @property
    def state(self) -> ActuatorState:
        """The representation of the current state of this MachineMotion."""
        return self._state

    @property
    def configuration(self) -> ActuatorConfiguration:
        """The representation of the configuration associated with this MachineMotion."""
        return self._configuration

    @abstractmethod
    def move_relative(
        self,
        distance: float,
        motion_profile: MotionProfile,
    ) -> None:
        """
        Moves relative synchronously by the specified distance.

        Args:
            distance (float): The distance to move.
            motion_profile (MotionProfile): The motion profile to move with. See MotionProfile class.

        Raises:
            ActuatorException: If the move was unsuccessful.
        """

    @abstractmethod
    def move_relative_async(
        self,
        distance: float,
        motion_profile: MotionProfile,
    ) -> None:
        """
        Moves relative asynchronously by the specified distance.

        Args:
            distance (float): The distance to move.
            motion_profile (MotionProfile): The motion profile to move with. See MotionProfile class.

        Raises:
            ActuatorException: If the move was unsuccessful.
        """

    @abstractmethod
    def move_absolute(
        self,
        position: float,
        motion_profile: MotionProfile,
    ) -> None:
        """
        Moves absolute synchronously to the specified position.

        Args:
            position (float): The position to move to.
            motion_profile (MotionProfile): The motion profile to move with. See MotionProfile class.

        Raises:
            ActuatorException: If the move was unsuccessful.
        """

    @abstractmethod
    def move_absolute_async(
        self,
        position: float,
        motion_profile: MotionProfile,
    ) -> None:
        """
        Moves absolute asynchronously.

        Args:
            position (float): The position to move to.
            motion_profile (MotionProfile): The motion profile to move with. See MotionProfile class.

        Raises:
            ActuatorException: If the move was unsuccessful.
        """

    @abstractmethod
    def move_continuous_async(
        self,
        motion_profile: MotionProfile,
    ) -> None:
        """
        Starts a continuous move. The Actuator will keep moving until it is stopped.

        Args:
            motion_profile (MotionProfile): The motion profile to move with. See MotionProfile class.
                Note: Actuator.move_continuous_async does not support jerk.
                If jerk is provided in the MotionProfile, a warning will be raised and the move will continue without jerk.

        Raises:
            ActuatorException: If the move was unsuccessful.
        """

    @abstractmethod
    def wait_for_move_completion(self, timeout: float = DEFAULT_MOVEMENT_TIMEOUT_SECONDS) -> None:
        """
        Waits for motion to complete before commencing the next action.

        Args:
            timeout (float): The timeout in seconds, after which an exception will be thrown.

        Raises:
            ActuatorException: If the request fails or the move did not complete in the allocated amount of time.
        """

    @abstractmethod
    def home(self, timeout: float = DEFAULT_MOVEMENT_TIMEOUT_SECONDS) -> None:
        """
        Home the Actuator synchronously.

        Args:
            timeout (float): The timeout in seconds.

        Raises:
            ActuatorException: If the home was unsuccessful or request timed out.
        """

    @abstractmethod
    def stop(self) -> None:
        """
        Stops movement on this Actuator as quickly as possible.

        Raises:
            ActuatorException: If the Actuator failed to stop.
        """
