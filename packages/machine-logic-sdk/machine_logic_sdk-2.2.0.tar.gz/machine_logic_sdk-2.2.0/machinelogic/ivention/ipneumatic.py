# pylint: disable=duplicate-code
"""_summary_"""

from abc import ABC, abstractmethod
from typing import Literal, Optional

PneumaticState = Literal["pushed", "pulled", "transition", "unknown"]


class PneumaticConfiguration:
    """Representation of a Pneumatic configuration."""

    def __init__(
        self,
        uuid: str,
        name: str,
        controller_id: str,
        device_id: int,
        controller_port: int,
        output_pin_push: int,
        output_pin_pull: int,
        input_pin_push: Optional[int],
        input_pin_pull: Optional[int],
    ) -> None:
        self._uuid: str = uuid
        self._name: str = name
        self._controller_id: str = controller_id
        self._device_id: int = device_id
        self._controller_port: int = controller_port
        self._output_pin_push: int = output_pin_push
        self._output_pin_pull: int = output_pin_pull
        self._input_pin_push: Optional[int] = input_pin_push
        self._input_pin_pull: Optional[int] = input_pin_pull

    @property
    def uuid(self) -> str:
        """The ID of the Pneumatic."""
        return self._uuid

    @property
    def name(self) -> str:
        """The name of the Pneumatic."""
        return self._name

    @property
    def controller_id(self) -> str:
        """The MachineMotion controller id."""
        return self._controller_id

    @property
    def device_id(self) -> int:
        """The device id of the io module that controls the pneumatic axis."""
        return self._device_id

    @property
    def controller_port(self) -> int:
        """The MachineMotion controller port of the io module that controls the pneumatic axis."""
        return self._controller_port

    @property
    def output_pin_push(self) -> int:
        """The push out pin of the axis."""
        return self._output_pin_push

    @property
    def output_pin_pull(self) -> int:
        """The pull out pin of the axis."""
        return self._output_pin_pull

    @property
    def input_pin_push(self) -> Optional[int]:
        """The optional push in pin."""
        return self._input_pin_push

    @property
    def input_pin_pull(self) -> Optional[int]:
        """The optional pull in pin."""
        return self._input_pin_pull


class IPneumatic(ABC):
    """
    A software representation of a Pneumatic. It is not recommended that you
    construct this object yourself. Rather, you should query it from a Machine instance:

    E.g.:
        machine = Machine()
        my_pneumatic = machine.get_pneumatic("Pneumatic")

    In this example, "Pneumatic" is the friendly name assigned to a Pneumatic in the
    MachineLogic configuration page.
    """

    def __init__(self, configuration: PneumaticConfiguration) -> None:
        """
        Args:
            configuration (PneumaticConfiguration): Configuration of the Pneumatic.
        """
        self._state: PneumaticState = "unknown"
        self._configuration: PneumaticConfiguration = configuration

    @property
    def state(self) -> PneumaticState:
        """
        The state of the actuator.
        """
        return self._state

    @property
    def configuration(self) -> PneumaticConfiguration:
        """
        The configuration of the actuator.
        """
        return self._configuration

    @abstractmethod
    def pull_async(self) -> None:
        """
        Pulls the Pneumatic.

        Raises:
            PneumaticException: If the pull was unsuccessful.
        """

    @abstractmethod
    def push_async(self) -> None:
        """
        Pushes the Pneumatic.

        Raises:
            PneumaticException: If the push was unsuccessful.
        """

    @abstractmethod
    def idle_async(self) -> None:
        """
        Idles the Pneumatic.

        Raises:
            PneumaticException: If the idle was unsuccessful.
        """
