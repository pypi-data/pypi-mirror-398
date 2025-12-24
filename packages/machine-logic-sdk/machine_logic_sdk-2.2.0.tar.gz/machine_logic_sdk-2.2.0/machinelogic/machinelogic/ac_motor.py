from ..ivention.exception import ACMotorException
from ..ivention.iac_motor import ACMotorConfiguration, IACMotor
from ..ivention.util.inheritance import inherit_docstrings  # type: ignore
from .api import Api


@inherit_docstrings
class ACMotor(IACMotor):
    def __init__(self, configuration: ACMotorConfiguration, api: Api) -> None:
        super().__init__(configuration)
        self._api = api

    def move_forward(self) -> None:
        if not self._api.move_ac_motor(self.configuration.uuid, "forward"):
            raise ACMotorException(f"Failed to move AC motor with name {self.configuration.name}")

    def move_reverse(self) -> None:
        if not self._api.move_ac_motor(self.configuration.uuid, "reverse"):
            raise ACMotorException(f"Failed to move AC motor with name {self.configuration.name}")

    def stop(self) -> None:
        if not self._api.stop_ac_motor(self.configuration.uuid):
            raise ACMotorException(f"Failed to stop AC motor with name {self.configuration.name}")
