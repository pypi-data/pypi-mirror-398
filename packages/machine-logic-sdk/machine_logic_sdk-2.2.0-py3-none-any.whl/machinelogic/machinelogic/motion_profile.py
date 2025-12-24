from dataclasses import asdict, dataclass
from typing import Optional

from machinelogic.decorators.undocumented import undocumented


@dataclass
class MotionProfile:
    """MotionProfile:
    A dataclass that represents the motion profile of a move.
    args:
        velocity (float): The velocity of the move in mm/s
        acceleration (float): The acceleration of the move in mm/s^2
        jerk (float | None): The jerk of the move in mm/s^3. Defaults to None

    If used in a continuous_move, only velocity and acceleration are required.

    If jerk is defined, an s-curve profile will be generated.
    Jerk option is commonly used to limit vibration due to sharp changes in motion profile.
    """

    velocity: float
    acceleration: float
    jerk: Optional[float] = None

    @undocumented
    def strip_out_none_and_to_dict(self) -> dict[str, float]:
        """Convert to dict, excluding None values."""
        return {key: value for key, value in asdict(self).items() if value is not None}
