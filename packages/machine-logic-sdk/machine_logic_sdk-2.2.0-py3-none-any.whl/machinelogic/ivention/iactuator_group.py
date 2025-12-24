"""_summary_"""

from abc import ABC, abstractmethod
from typing import Tuple, TypeVar

from machinelogic.machinelogic.motion_profile import MotionProfile

from .exception import ActuatorGroupException
from .iactuator import ActuatorState, IActuator

DEFAULT_MOVEMENT_TIMEOUT_SECONDS = 300


class ActuatorGroupState:
    """Representation of the state of an ActuatorGroup."""

    _move_in_progress: bool

    def __init__(self, *actuator_states: ActuatorState) -> None:
        self._actuator_states = actuator_states
        self._move_in_progress = False

    @property
    def move_in_progress(self) -> bool:
        """The boolean is True if the ActuatorGroup has at least one Actuator in progress"""
        for actuator_state in self._actuator_states:
            if actuator_state.move_in_progress:
                return True
        return False


T = TypeVar("T")


class IActuatorGroup(ABC):
    """
    A helper class used to group N-many Actuator instances together
    so that they can be acted upon as a group. An ActuatorGroup
    may only contain Actuators that are on the same MachineMotion controller.

    E.g.:
        machine = Machine()
        my_actuator_1 = machine.get_actuator("Actuator 1")
        my_actuator_2 = machine.get_actuator("Actuator 2")
        actuator_group = ActuatorGroup(my_actuator_1, my_actuator_2)
    """

    def __init__(self, *actuators: IActuator):
        """
        Args:
            actuators (IActuator): The variable number of Actuators.
        """
        if len(actuators) == 0:
            raise ActuatorGroupException("Actuators must have length of at least one")

        for actuator in actuators:
            if not isinstance(actuator, IActuator):
                raise ActuatorGroupException("Must only pass Actuators to the ActuatorGroup constructor")

        controller_id = None
        for actuator in actuators:
            if controller_id is None:
                controller_id = actuator.configuration.controller_id
                continue

            if controller_id != actuator.configuration.controller_id:
                raise ActuatorGroupException(
                    f"""
                    Actuators in an ActuatorGroup must be on the same controller,
                    found an Actuator on controller={controller_id} and another on controller={actuator.configuration.controller_id}
                    """
                )

        self._actuators: Tuple[IActuator, ...] = actuators
        self._length: int = len(self._actuators)
        self._state: ActuatorGroupState = ActuatorGroupState(*[actuator.state for actuator in actuators])

    @property
    def state(self) -> ActuatorGroupState:
        """The state of the ActuatorGroup."""
        return self._state

    def _does_tuple_match_axes_length(self, value: Tuple[T, ...]) -> bool:
        """
        Internal helper method that will check if an arbitrary argument tuple
        matches the length of the Actuators in the group.

        Args:
            value (Tuple[T, ...]): An arbitrary argument tuple.

        Returns:
            bool: True if the lengths match, otherwise False.
        """
        return len(value) == self._length

    @abstractmethod
    def move_relative(
        self,
        distance: Tuple[float, ...],
        motion_profile: MotionProfile,
    ) -> None:
        """
        Moves relative synchronously by the tuple of distances.

        Args:
            distance (Tuple[float, ...]): The distances to move each Actuator. Each value corresponds 1-to-1 with the actuators tuple provided to the constructor.
            motion_profile (MotionProfile): The motion profile to move with. See MotionProfile class.
        Raises:
            ActuatorGroupException: If the request fails or the timeout occurs
        """

    @abstractmethod
    def move_relative_async(
        self,
        distance: Tuple[float, ...],
        motion_profile: MotionProfile,
    ) -> None:
        """
        Moves relative asynchronously by the tuple of distances.

        Args:
            distance (Tuple[float, ...]): The distances to move each Actuator. Each value corresponds 1-to-1 with the actuators tuple provided to the constructor.
            motion_profile (MotionProfile): The motion profile to move with. See MotionProfile class.

        Raises:
            ActuatorGroupException: If the request fails.
        """

    @abstractmethod
    def move_absolute(
        self,
        position: Tuple[float, ...],
        motion_profile: MotionProfile,
    ) -> None:
        """
        Moves absolute synchronously to the tuple of positions.

        Args:
            position (Tuple[float, ...]): The positions to move to. Each value corresponds 1-to-1 with the actuators tuple provided to the constructor.
            motion_profile (MotionProfile): The motion profile to move with. See MotionProfile class.

        Raises:
            ActuatorGroupException: If the request fails or the timeout occurs.
        """

    @abstractmethod
    def move_absolute_async(
        self,
        position: Tuple[float, ...],
        motion_profile: MotionProfile,
    ) -> None:
        """
        Moves absolute asynchronously to the tuple of positions.

        Args:
            distance (Tuple[float, ...]): The positions to move to. Each value corresponds 1-to-1 with the actuators tuple provided to the constructor.
            motion_profile (MotionProfile): The motion profile to move with. See MotionProfile class.

        Raises:
            ActuatorGroupException: If the request fails.
        """

    @abstractmethod
    def wait_for_move_completion(self, timeout: float = DEFAULT_MOVEMENT_TIMEOUT_SECONDS) -> None:
        """
        Waits for motion to complete on all Actuators in the group.

        Args:
            timeout (float): The timeout in seconds, after which an exception will be thrown.

        Raises:
            ActuatorGroupException: If the request fails or the move did not complete in the allocated amount of time.
        """

    @abstractmethod
    def stop(self) -> None:
        """
        Stops movement on all Actuators in the group.

        Raises:
            ActuatorGroupException: If any of the Actuators in the group failed to stop.
        """
