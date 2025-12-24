from abc import ABC


class DigitalIOState:
    """
    Representation of the current state of an DigitalInput/DigitalOutput instance.
    """

    def __init__(self, configuration: "DigitalIOConfiguration") -> None:
        # we pass a ref to configuration, so that we can access the active high
        # attribute (and have it work throughout the application).
        self._configuration = configuration
        self._value: bool = False  # honest value, ignoring "active_high" flips.

    @property
    def value(self) -> bool:
        """
        The current value of the IO pin. True means high, while False means low. This is different from
        active/inactive, which depends on the active_high configuration.
        """
        if not self._configuration.active_high:
            return not self._value
        return self._value


class DigitalIOConfiguration(ABC):
    """
    Representation of the configuration of an DigitalInput/DigitalOutput. This
    configuration is established by the configuration page in
    MachineLogic.
    """

    def __init__(
        self,
        uuid: str,
        name: str,
        device_id: int,
        controller_id: str,
        controller_port: int,
        pin: int,
        active_high: bool,
    ) -> None:
        self._uuid: str = uuid
        self._name: str = name
        self._device_id: int = device_id
        self._controller_id: str = controller_id
        self._controller_port: int = controller_port
        self._pin: int = pin
        self._active_high: bool = active_high

    @property
    def name(self) -> str:
        """The name of the DigitalInput/DigitalOutput."""
        return self._name

    @property
    def active_high(self) -> bool:
        """The value that needs to be set to consider the DigitalInput/DigitalOutput as active."""
        return self._active_high

    @active_high.setter
    def active_high(self, active_high: bool) -> None:
        """Set active high to true/false on the DigitalInput/DigitalOutput."""
        self._active_high = active_high

    @property
    def device_id(self) -> int:
        """The device number of the DigitalInput/DigitalOutput."""
        return self._device_id

    @property
    def controller_id(self) -> str:
        """The MachineMotion controller id of the DigitalInput/DigitalOutput."""
        return self._controller_id

    @property
    def controller_port(self) -> int:
        """The MachineMotion controller port of the DigitalInput/DigitalOutput."""
        return self._controller_port

    @property
    def pin(self) -> int:
        """The pin number of the DigitalInput/DigitalOutput."""
        return self._pin

    @property
    def uuid(self) -> str:
        """The unique ID of the DigitalInput/DigitalOutput."""
        return self._uuid
