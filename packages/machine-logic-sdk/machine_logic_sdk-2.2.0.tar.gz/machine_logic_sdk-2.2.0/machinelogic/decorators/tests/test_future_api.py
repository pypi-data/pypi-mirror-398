# pylint: disable=missing-function-docstring
import unittest

from machinelogic.decorators.future_api import future_api


class DecoratedClass:
    def __init__(self, value: int):
        self.__value = value

    # You cannot wrap @property :(
    @property
    @future_api
    def value(self) -> int:
        return self.__value

    @future_api
    def get_value(self) -> int:
        return self.__value


class TestFutureApi(unittest.TestCase):
    def test_given_value_when_getting_future_api_value_property_then_returns_value(
        self,
    ) -> None:
        # Arrange
        expected_value = 1
        instance = DecoratedClass(expected_value)

        # Act
        actual_value = instance.value

        # Assert
        self.assertEqual(expected_value, actual_value)

    def test_given_value_when_setting_future_api_value_property_then_raises_attribute_error(
        self,
    ) -> None:
        # Arrange
        instance = DecoratedClass(1)

        # Act & Assert
        with self.assertRaises(AttributeError):
            instance.value = 2  # type: ignore

    def test_future_api_on_top_of_property_does_not_work(
        self,
    ) -> None:
        # Assert
        self.assertFalse(getattr(DecoratedClass.value, "__future_api__", False))
