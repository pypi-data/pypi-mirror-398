import itertools
import unittest

from machinelogic.ivention.idigital_output import (
    DigitalOutputConfiguration,
    IDigitalOutput,
)


class DummyDigitalOutput(IDigitalOutput):
    def __init__(self, active_high: bool = True):
        doc = DigitalOutputConfiguration(
            "uuid",
            "name",
            1,
            "controllerId",
            2,
            2,
            active_high,
        )
        super().__init__(doc)

    def _internal_write(self, proper_value: bool) -> None:
        pass


class TestIDigitalOutput(unittest.TestCase):
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
                dop = DummyDigitalOutput(active_high)
                dop._state._value = starting_value

                dop.write(new_value)

                self.assertEqual(dop._state.value, new_value)

                # flip active high and make sure that readback is inverted.

                active_high = not active_high
                dop.configuration.active_high = active_high

                self.assertEqual(dop._state.value, not new_value)


if __name__ == "__main__":
    unittest.main()
