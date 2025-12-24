from abc import ABC
from typing import Callable, Optional, Union

from ..decorators.future_api import future_api
from .event_listener import EventListenerManager
from .idigital_io_shared import DigitalIOConfiguration, DigitalIOState
from .util.inheritance import inherit_docstrings  # type: ignore


@inherit_docstrings
class DigitalInputState(DigitalIOState):
    pass


@inherit_docstrings
class DigitalInputConfiguration(DigitalIOConfiguration):
    pass


OnStateChangeFn = Callable[[bool, "IDigitalInput"], None]


class IDigitalInput(ABC):
    """
    A software representation of an DigitalInput. It is not recommended that you
    construct this object yourself. Rather, you should query it from a Machine instance.
    """

    def __init__(self, configuration: DigitalInputConfiguration) -> None:
        """
        Args:
            configuration (DigitalInputConfiguration): The configuration of this DigitalInput.
        """
        self._configuration: DigitalInputConfiguration = configuration
        self._state: DigitalInputState = DigitalInputState(self._configuration)

        self._event_listener_manager: EventListenerManager = EventListenerManager()

        self._on_state_change: Union[None, OnStateChangeFn] = None

        def wrapped_callback(
            topic: str,
            message: Optional[str],  # pylint: disable=unused-argument
        ) -> None:
            if self._on_state_change is None:
                return
            self._on_state_change(self.state.value, self)

        self._event_listener_manager.add_event_listener("onchange", wrapped_callback)

    @property
    def state(self) -> DigitalInputState:
        """
        The state of the DigitalInput.
        """
        return self._state

    @property
    def configuration(self) -> DigitalInputConfiguration:
        """
        The configuration of the DigitalInput.
        """
        return self._configuration

    @future_api
    def on_state_change(self, callback: OnStateChangeFn) -> None:
        """
        Adds a change listener to execute when the DigitalInput state changes.

        Args:
            callback (Callable[[bool, IDigitalInput], None]): The callback to be called when the DigitalInput state changes.
              The first argument is the new value and the second argument is the DigitalInput itself.

        """
        self._on_state_change = callback

    def _set_value(self, new_value: bool) -> None:
        """
        Sets the DigitalInput state to the provided new_value. Listeners
        will be notified.

        Args:
            new_value (bool): The new value for the DigitalInput state.
        """
        # move honest new_value into the state object.
        self._state._value = bool(new_value)  # pylint: disable=protected-access
        self._event_listener_manager.notify_listeners("onchange")
