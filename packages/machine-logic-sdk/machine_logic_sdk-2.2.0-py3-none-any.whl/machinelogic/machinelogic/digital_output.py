from ..ivention.exception import DigitalOutputException
from ..ivention.idigital_output import DigitalOutputConfiguration, IDigitalOutput
from ..ivention.util.inheritance import inherit_docstrings  # type: ignore
from .api import Api


@inherit_docstrings
class DigitalOutput(IDigitalOutput):
    """Representation of a Vention Output"""

    def __init__(self, configuration: DigitalOutputConfiguration, api: Api):
        super().__init__(configuration)
        self._api = api

    def _internal_write(self, proper_value: bool) -> None:
        if not self._api.write_output(self.configuration.uuid, 1 if proper_value else 0):
            raise DigitalOutputException(f"Failed to write output with name {self.configuration.name}")
