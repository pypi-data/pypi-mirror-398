from abc import ABC, abstractmethod

from machinelogic.decorators.undocumented import undocumented

from ..ivention.types.robot_types import JointAnglesDegrees


class IJointTargetConfiguration(ABC):
    """
    A representation of the configuration of a Joint Target instance.
    This configuration defines what the Joint Target is and how it
    is defined in the context of the scene.
    """

    def __init__(self, uuid: str, name: str, joint_angles: JointAnglesDegrees) -> None:
        self._uuid: str = uuid
        self._name: str = name
        self._joint_angles: JointAnglesDegrees = joint_angles

    @property
    def uuid(self) -> str:
        """The Joint Target's ID"""
        return self._uuid

    @property
    def name(self) -> str:
        """The Joint Target's name"""
        return self._name

    @property
    def joint_angles(self) -> JointAnglesDegrees:
        """The nominal value of the Joint Target in degrees."""
        return self._joint_angles


class IJointTarget(ABC):
    """
    A joint target is a representation of a target position for a robot's joints.
    It is defined by the joint angles in degrees.
    """

    @property
    @undocumented
    @abstractmethod
    def _configuration(self) -> IJointTargetConfiguration:
        pass

    @abstractmethod
    def get_joint_angles(self) -> JointAnglesDegrees:
        """Gets the joint target's default values.

        Raises:
            SceneException: If failed to get the default value

        Returns:
            JointAnglesDegrees [j1_deg, j2_deg, j3_deg, j4_deg, j5_deg, j6_deg]: The nominal value of the joint target in degrees.
        """
