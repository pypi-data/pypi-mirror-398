from machinelogic.ivention.igeneric_joint_constraint import IGenericJointConstraint
from machinelogic.ivention.types.robot_types import Degrees


class GenericJointConstraint(IGenericJointConstraint):
    """
    A representation of a generic joint constraint. To be used within the compute_inverse_kinematics method of a robot.
    """

    def __init__(
        self,
        joint_index: int,
        position: Degrees,
        tolerance_above: Degrees,
        tolerance_below: Degrees,
        weighting_factor: float,
    ) -> None:
        super().__init__(joint_index, position, tolerance_above, tolerance_below, weighting_factor)
