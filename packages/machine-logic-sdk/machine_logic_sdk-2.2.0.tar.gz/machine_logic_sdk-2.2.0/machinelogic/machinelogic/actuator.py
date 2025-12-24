# pylint: disable=protected-access

import warnings
from typing import List, Union

from machinelogic.ivention.types.batch_move import (
    BatchMove,
    ContinuousMove,
    TorqueMove,
    TrapezoidalMotion,
    TrapezoidalMove,
)
from machinelogic.machinelogic.motion_profile import MotionProfile

from ..ivention.exception import ActuatorException
from ..ivention.iactuator import (
    DEFAULT_MOVEMENT_TIMEOUT_SECONDS,
    ActuatorConfiguration,
    ActuatorState,
    IActuator,
)
from ..ivention.util.inheritance import inherit_docstrings  # type: ignore
from .api import Api

# TODO: One day, we will have high-speed streams in the execution
# engine, and then we can just update the ModifiedAxisState without
# a worry in the world, a cold beer in our hands.

# We purposefully override the traditional ActuatorState while we do
# not yet have access to the "high-powered streams" that Doug knows
# and loves


@inherit_docstrings
class ModifiedActuatorState(ActuatorState):
    def __init__(self, configuration: ActuatorConfiguration, api: Api):
        super().__init__()
        self._configuration = configuration
        self._api = api

    @property
    def speed(self) -> float:
        return self._api.get_speed(self._configuration.uuid)

    @property
    def position(self) -> float:
        return self._api.get_axis_position(self._configuration.uuid)

    def _sync_move_in_progress(self) -> None:
        # get updated values after starting moves.
        # _move_in_progress gets updated again through mqtt when motion is complete (see Machine.py)
        self._move_in_progress = not self._api.get_axis_motion_completion(self._configuration.uuid)

    @property
    def output_torque(self) -> dict[str, float]:
        return self._api.get_axis_actual_torque(self._configuration.uuid)


@inherit_docstrings
class Actuator(IActuator):
    """Representation of a Vention Actuator"""

    def __init__(self, configuration: ActuatorConfiguration, api: Api):
        super().__init__(configuration)
        self._api = api
        self._state: ModifiedActuatorState = ModifiedActuatorState(configuration, api)

    def move_relative(
        self,
        distance: float,
        motion_profile: MotionProfile,
    ) -> None:
        self.move_relative_async(distance, motion_profile)
        self.wait_for_move_completion()

    def move_relative_async(
        self,
        distance: float,
        motion_profile: MotionProfile,
    ) -> None:
        trapezoidal_move = TrapezoidalMove(
            motions=[
                TrapezoidalMotion(
                    motor_address=self.configuration.uuid,
                    position_target=distance,
                )
            ],
            use_relative_reference=True,
            motion_profile=motion_profile.strip_out_none_and_to_dict(),
            ignore_synchronization=False,
        )
        self._batch_move(
            moves=[trapezoidal_move],
            error_message=f"Failed to move relative on actuator with name {self.configuration.name} by a distance of {distance}",
        )

    def move_absolute(
        self,
        position: float,
        motion_profile: MotionProfile,
    ) -> None:
        self.move_absolute_async(position, motion_profile)
        self.wait_for_move_completion()

    def move_absolute_async(
        self,
        position: float,
        motion_profile: MotionProfile,
    ) -> None:
        trapezoidal_move = TrapezoidalMove(
            motions=[
                TrapezoidalMotion(
                    motor_address=self.configuration.uuid,
                    position_target=position,
                )
            ],
            use_relative_reference=False,
            motion_profile=motion_profile.strip_out_none_and_to_dict(),
            ignore_synchronization=False,
        )
        self._batch_move(
            moves=[trapezoidal_move],
            error_message=f"Failed to move absolute on actuator with name {self.configuration.name} to a position of {position}",
        )

    def move_continuous_async(
        self,
        motion_profile: MotionProfile,
    ) -> None:
        if motion_profile.jerk is not None:
            warnings.warn(
                """
                Jerk is not supported for continuous moves.
                Continuing with continuous motion without jerk.
                """
            )
        continuous_move = ContinuousMove(
            motor_address=self.configuration.uuid,
            motion_profile=motion_profile.strip_out_none_and_to_dict(),
        )
        self._batch_move(
            moves=[continuous_move],
            error_message=f"Failed to move continuous on actuator with name {self.configuration.name}",
        )

    def wait_for_move_completion(self, timeout: float = DEFAULT_MOVEMENT_TIMEOUT_SECONDS) -> None:
        if not self._api.wait_for_motion_completion(self.configuration.uuid, timeout=timeout):
            raise ActuatorException(f"Failed to wait_for_move_completion on actuator with name {self.configuration.name}")

    def home(self, timeout: float = DEFAULT_MOVEMENT_TIMEOUT_SECONDS) -> None:
        if not self._api.home(self.configuration.uuid, True, timeout):
            raise ActuatorException(f"Failed to home on actuator with name {self.configuration.name}")

    def stop(self) -> None:
        was_motion_stopped = self._api.stop_motion(self.configuration.uuid)

        if not was_motion_stopped:
            raise ActuatorException(f"Failed to stop on actuator with name {self.configuration.name}")

    def _batch_move(
        self,
        moves: List[Union[TrapezoidalMove, ContinuousMove, TorqueMove]],
        error_message: str,
    ) -> None:
        if not self._api.batch_move(BatchMove(moves=moves)):
            raise ActuatorException(error_message)
        self._state._sync_move_in_progress()
