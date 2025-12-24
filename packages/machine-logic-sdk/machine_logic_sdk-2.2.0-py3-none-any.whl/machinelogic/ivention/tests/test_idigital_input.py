import itertools
import unittest
from unittest.mock import MagicMock

from machinelogic.ivention.idigital_input import (
    DigitalInputConfiguration,
    IDigitalInput,
)


class DummyDigitalInput(IDigitalInput):
    def __init__(self, active_high: bool = True):
        dic = DigitalInputConfiguration(
            "uuid",
            "name",
            1,
            "controllerId",
            2,
            2,
            active_high,
        )
        super().__init__(dic)


class TestIOutput(unittest.TestCase):
    def test_given_default_input_and_change_listener_when_set_value_with_new_value_then_calls_change_listener_once_with_new_value(
        self,
    ) -> None:
        # Arrange
        inp = DummyDigitalInput()
        change_listener_spy = MagicMock()

        # Act
        inp.on_state_change(change_listener_spy)
        inp._set_value(not inp.state.value)

        # Assert
        change_listener_spy.assert_called_once_with(inp.state.value, inp)

    def test_given_starting_value_when_set_value_then_sets_new_value(
        self,
    ) -> None:
        for starting_value, new_value, active_high in itertools.product([False, True], repeat=3):
            with self.subTest(
                starting_value=starting_value,
                new_value=new_value,
                active_high=active_high,
            ):
                # Arrange
                inp = DummyDigitalInput(active_high)
                inp._state._value = starting_value

                # Act
                inp._set_value(new_value)  # "raw value" (not inverted with active high)

                translated_value = new_value if active_high else not new_value

                # Assert
                self.assertEqual(translated_value, inp.state.value)

                # now, we flip active_high and make sure that things still line up.
                active_high = not active_high

                inp.configuration.active_high = active_high
                translated_value = new_value if active_high else not new_value

                self.assertEqual(translated_value, inp.state.value)


if __name__ == "__main__":
    unittest.main()
