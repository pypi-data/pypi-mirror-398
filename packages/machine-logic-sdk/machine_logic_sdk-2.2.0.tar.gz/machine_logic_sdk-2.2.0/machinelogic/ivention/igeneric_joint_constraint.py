from abc import ABC


class IGenericJointConstraint(ABC):
    """
    A representation of a generic joint constraint.
    """

    def __init__(
        self,
        joint_index: int,
        position: float,
        tolerance_above: float,
        tolerance_below: float,
        weighting_factor: float,
    ) -> None:
        self._joint_index: int = joint_index
        self._position: float = position
        self._tolerance_above: float = tolerance_above
        self._tolerance_below: float = tolerance_below
        self._weighting_factor: float = weighting_factor

    @property
    def joint_index(self) -> int:
        """The 1-based index of the robot joint"""
        return self._joint_index

    @property
    def position(self) -> float:
        """The angle of the joint in degrees"""
        return self._position

    @property
    def tolerance_above(self) -> float:
        """The tolerance above the position in degrees"""
        return self._tolerance_above

    @property
    def tolerance_below(self) -> float:
        """The tolerance below the position in degrees"""
        return self._tolerance_below

    @property
    def weighting_factor(self) -> float:
        """A weighting factor for this constraint
        (denotes relative importance to other constraints, closer to zero means less important).
        """
        return self._weighting_factor
