from ..ivention.ijoint_target import IJointTarget, IJointTargetConfiguration
from ..ivention.types.robot_types import JointAnglesDegrees
from ..ivention.util.inheritance import inherit_docstrings  # type: ignore
from .api import Api


class JointTargetConfiguration(IJointTargetConfiguration):
    def __init__(
        self,
        api: Api,
        uuid: str,
        name: str,
        joint_angles: JointAnglesDegrees,
    ) -> None:
        super().__init__(uuid, name, joint_angles)
        self._api = api


@inherit_docstrings
class JointTarget(IJointTarget):
    """
    A software representation of a Joint Target as defined within the scene assets pane.
    A joint target is defined by the joint angles in degrees.
    """

    def __init__(self, uuid: str, name: str, joint_angles: JointAnglesDegrees, api: Api) -> None:
        self.__configuration = JointTargetConfiguration(api, uuid, name, joint_angles)
        self._api = api

    @property
    def _configuration(self) -> JointTargetConfiguration:
        return self.__configuration

    def get_joint_angles(self) -> JointAnglesDegrees:
        return self._configuration.joint_angles
