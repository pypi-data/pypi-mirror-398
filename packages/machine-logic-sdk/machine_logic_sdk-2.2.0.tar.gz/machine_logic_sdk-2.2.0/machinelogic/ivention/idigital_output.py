from abc import ABC, abstractmethod

from ..decorators.future_api import future_api
from .idigital_io_shared import DigitalIOConfiguration, DigitalIOState
from .util.inheritance import inherit_docstrings  # type: ignore


@inherit_docstrings
class DigitalOutputState(DigitalIOState):
    pass


@inherit_docstrings
class DigitalOutputConfiguration(DigitalIOConfiguration):
    pass


class IDigitalOutput(ABC):
    """
    A software representation of an Output. It is not recommended that you
    construct this object yourself. Rather, you should query it from a Machine instance.
    """

    def __init__(self, configuration: DigitalOutputConfiguration) -> None:
        """
        Args:
            configuration (OutputConfiguration): Configuration of the Output.
        """
        self._configuration = configuration
        self._state = DigitalOutputState(self._configuration)

    # see: https://github.com/VentionCo/mm-programmatic-sdk/issues/416
    @future_api
    def state(self) -> DigitalOutputState:
        """
        The state of the Output.
        """
        return self._state

    @property
    def configuration(self) -> DigitalOutputConfiguration:
        """
        The configuration of the Output.
        """
        return self._configuration

    def write(self, value: bool) -> None:
        """
        Writes the value into the Output, with True being high and False being low.

        Args:
            value (bool): The value to write to the Output.

        Raises:
            DigitalOutputException: If we fail to write the value to the Output.
        """

        proper_value = value
        if not self.configuration.active_high:
            proper_value = not proper_value
        self._internal_write(proper_value)
        self._set_value(proper_value)

    @abstractmethod
    def _internal_write(self, proper_value: bool) -> None:
        # proper_value is the correct value to write, active_high configuration taken into account.
        # this is so that "backend" implementers don't have to remember this step.
        # and just have tofill-in this method.
        pass

    def _set_value(self, new_value: bool) -> None:
        """
        Sets the Output state to the provided new_value.
        Args:
            new_value (bool): The new value for the Output state.
        """
        self._state._value = new_value  # pylint: disable=protected-access
