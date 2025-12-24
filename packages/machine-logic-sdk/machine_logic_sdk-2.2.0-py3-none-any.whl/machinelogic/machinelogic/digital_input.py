from ..ivention.idigital_input import DigitalInputConfiguration, IDigitalInput
from ..ivention.util.inheritance import inherit_docstrings  # type: ignore
from .api import Api


@inherit_docstrings
class DigitalInput(IDigitalInput):
    def __init__(self, configuration: DigitalInputConfiguration, api: Api):
        super().__init__(configuration)
        self._api = api
