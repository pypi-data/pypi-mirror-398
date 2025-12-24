from ..ivention.imachine_motion import IMachineMotion, MachineMotionConfiguration
from ..ivention.util.inheritance import inherit_docstrings  # type: ignore
from .api import Api


@inherit_docstrings
class MachineMotion(IMachineMotion):
    def __init__(
        self,
        configuration: MachineMotionConfiguration,
        api: Api,
    ):
        super().__init__(configuration)
        self._api = api
