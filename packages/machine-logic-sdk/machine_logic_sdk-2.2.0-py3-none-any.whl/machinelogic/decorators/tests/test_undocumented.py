# pylint: disable=missing-function-docstring
import unittest

from machinelogic.decorators.undocumented import undocumented, undocumented_property


class DecoratedClass:
    def __init__(self, value: int):
        self.__value = value

    @undocumented_property
    def undocumented_value(self) -> int:
        """This is an undocumented property"""
        return self.__value

    @property
    def value(self) -> int:
        """This is a documented property"""
        return self.__value

    @undocumented
    def get_value(self) -> int:
        """This is an undocumented method"""
        return self.__value


class TestUndocumentedDecorator(unittest.TestCase):
    def setUp(self) -> None:
        self.expected_value = 1
        self.instance = DecoratedClass(self.expected_value)

    def test_get_property_value_when_using_undocumented_property_then_returns_value(
        self,
    ) -> None:
        # @property should return the expected value. This test is added for reference
        self.assertEqual(self.expected_value, self.instance.value)

        # @undocumented_property should return the value
        self.assertEqual(self.expected_value, self.instance.undocumented_value)

    def test_get_value_when_using_undocumented_method_then_returns_value(
        self,
    ) -> None:
        # @undocumented method should still return the value
        self.assertEqual(self.expected_value, self.instance.get_value())

    def test_undocumnented_attributed_should_be_set_to_true(self) -> None:
        # @undocumented should have '__undocumented__' attribute
        self.assertTrue(hasattr(DecoratedClass.undocumented_value, "__undocumented__"))

        # @undocumented should have '__undocumented__' attribute set to True
        self.assertTrue(DecoratedClass.undocumented_value.__undocumented__)

    def test_undocumnented_property_attributed_should_be_set_to_true(self) -> None:
        # @undocumented_property should have '__undocumented__' attribute
        self.assertTrue(hasattr(DecoratedClass.undocumented_value, "__undocumented__"))

        # @undocumented_property should have '__undocumented__' attribute set to True
        self.assertTrue(DecoratedClass.undocumented_value.__undocumented__)

    def test_documentation_should_be_set_when_using_undocumented_property(self) -> None:
        # @undocumented_property should have '__doc__' attribute set to the expected value
        self.assertEqual(
            "This is an undocumented property",
            DecoratedClass.undocumented_value.__doc__,
        )

    def test_documentation_should_be_set_when_using_undocumented(self) -> None:
        # @undocumented should have '__doc__' attribute set to the expected value
        self.assertEqual(
            "This is an undocumented method",
            DecoratedClass.get_value.__doc__,
        )
