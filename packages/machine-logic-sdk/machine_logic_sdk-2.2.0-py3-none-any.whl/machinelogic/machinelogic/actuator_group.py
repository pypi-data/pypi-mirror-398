# pylint: disable=protected-access
from typing import List, Tuple, Union

from machinelogic.ivention.types.batch_move import (
    BatchMove,
    ContinuousMove,
    TorqueMove,
    TrapezoidalMotion,
    TrapezoidalMove,
)
from machinelogic.machinelogic.motion_profile import MotionProfile

from ..ivention.exception import ActuatorGroupException
from ..ivention.iactuator_group import DEFAULT_MOVEMENT_TIMEOUT_SECONDS, IActuatorGroup
from ..ivention.util.inheritance import inherit_docstrings  # type: ignore
from .actuator import Actuator
from .api import Api


@inherit_docstrings
class ActuatorGroup(IActuatorGroup):
    def __init__(self, *axes: Actuator):
        super().__init__(*axes)
        self._api: Api = axes[0]._api  # pylint: disable=protected-access

    def move_absolute(
        self,
        position: Tuple[float, ...],
        motion_profile: MotionProfile,
    ) -> None:
        self.move_absolute_async(position, motion_profile)
        self.wait_for_move_completion()

    def move_relative(
        self,
        distance: Tuple[float, ...],
        motion_profile: MotionProfile,
    ) -> None:
        self.move_relative_async(distance, motion_profile)
        self.wait_for_move_completion()

    def move_absolute_async(self, position: Tuple[float, ...], motion_profile: MotionProfile) -> None:
        motions = self._build_trapezoidal_motions(position)

        trapezoidal_move = TrapezoidalMove(
            motions=motions,
            use_relative_reference=False,
            motion_profile=motion_profile.strip_out_none_and_to_dict(),
            ignore_synchronization=False,
        )

        self._batch_move([trapezoidal_move], "Unable to move absolute on ActuatorGroup")

    def move_relative_async(self, distance: Tuple[float, ...], motion_profile: MotionProfile) -> None:
        motions = self._build_trapezoidal_motions(distance)

        trapezoidal_move = TrapezoidalMove(
            motions=motions,
            use_relative_reference=True,
            motion_profile=motion_profile.strip_out_none_and_to_dict(),
            ignore_synchronization=False,
        )

        self._batch_move([trapezoidal_move], "Unable to move relative on ActuatorGroup")

    def wait_for_move_completion(self, timeout: float = DEFAULT_MOVEMENT_TIMEOUT_SECONDS) -> None:
        wait_for_move_completion_payload: list[str] = []

        for axis in self._actuators:
            wait_for_move_completion_payload.append(axis.configuration.uuid)
        if not self._api.wait_for_motion_completion(wait_for_move_completion_payload, timeout=timeout):
            raise ActuatorGroupException("Failed to wait_for_move_completion")

    def stop(self) -> None:
        actuator_uuids_to_stop = [actuator.configuration.uuid for actuator in self._actuators]

        if not self._api.stop_motion_combined(actuator_uuids_to_stop):
            raise ActuatorGroupException("Unable to stop on ActuatorGroup")

    def _build_trapezoidal_motions(self, positions: Tuple[float, ...]) -> List[TrapezoidalMotion]:
        if not self._does_tuple_match_axes_length(positions):
            raise ActuatorGroupException("The length of the provided positions tuple does not match the number of actuators in the group")

        motions = []
        for i in range(0, self._length):
            axis = self._actuators[i]
            axis_position = positions[i]
            motions.append(
                TrapezoidalMotion(
                    motor_address=axis.configuration.uuid,
                    position_target=axis_position,
                )
            )
        return motions

    def _batch_move(
        self,
        moves: List[Union[TrapezoidalMove, ContinuousMove, TorqueMove]],
        error_message: str,
    ) -> None:
        if not self._api.batch_move(BatchMove(moves=moves)):
            raise ActuatorGroupException(error_message)
        for actuator in self._actuators:
            actuator.state._move_in_progress = not self._api.get_axis_motion_completion(actuator._configuration.uuid)
