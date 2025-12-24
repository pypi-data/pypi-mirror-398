# pylint: disable=duplicate-code
import json
from typing import List, Optional

from ..ivention.ipneumatic import IPneumatic, PneumaticConfiguration
from ..ivention.mqtt_client import MqttClient
from ..ivention.util.inheritance import inherit_docstrings  # type: ignore
from .api import Api


@inherit_docstrings
class Pneumatic(IPneumatic):
    def __init__(self, configuration: PneumaticConfiguration, api: Api, mqtt_client: MqttClient) -> None:
        super().__init__(configuration)
        self._api = api
        self._pin_state: dict[str, Optional[bool]] = {
            "input_pin_push": None,
            "input_pin_pull": None,
        }
        mqtt_client.internal_subscribe(
            f"execution-engine/controller/{self.configuration._controller_id}/io",
            lambda _, payload: self._on_digital_input(payload),
        )

    def _on_digital_input(self, payload: Optional[str]) -> None:
        if payload is None:
            return
        payload_json = json.loads(payload)
        filtered_for_device = [
            deviceState
            for deviceState in payload_json
            if (deviceState["device"] == f"{self.configuration.controller_port}/{self.configuration.device_id}")
            and (deviceState["deviceType"] == "io-expander")
        ]
        if len(filtered_for_device) == 0:
            return
        pin_states = filtered_for_device[0]["pinStates"]
        self._update_pin_state(pin_states)

    def _update_pin_state(self, pin_states: List[int]) -> None:
        if self.configuration.input_pin_pull is not None:
            self._pin_state["input_pin_pull"] = bool(pin_states[self.configuration.input_pin_pull])
        if self.configuration.input_pin_push is not None:
            self._pin_state["input_pin_push"] = bool(pin_states[self.configuration.input_pin_push])
        self._update_pneumatic_state()

    def _update_pneumatic_state(self) -> None:
        pin_pull = self._pin_state["input_pin_pull"]
        pin_push = self._pin_state["input_pin_push"]

        # https://github.com/VentionCo/mm-programmatic-sdk/issues/473#issue-1823142657
        if pin_push is False and pin_pull is False:
            self._state = "unknown"
        elif pin_push is True and pin_pull is True:
            self._state = "transition"
        elif pin_push is False:
            self._state = "pushed"
        elif pin_pull is False:
            self._state = "pulled"
        else:
            self._state = "unknown"

    def idle_async(self) -> None:
        self._api.pneumatic_idle(self.configuration.uuid)

    def push_async(self) -> None:
        self._api.pneumatic_push(self.configuration.uuid, False)

    def pull_async(self) -> None:
        self._api.pneumatic_pull(self.configuration.uuid, False)
