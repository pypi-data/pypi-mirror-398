# pylint: disable=missing-function-docstring
import unittest
import warnings

from machinelogic.decorators.deprecated import deprecated


class DecoratedClass:
    def __init__(self, value: int):
        self.__value = value

    @deprecated
    def deprecated_value(self) -> int:
        """This is a deprecated property"""
        return self.__value

    @property
    def value(self) -> int:
        """This is a documented property"""
        return self.__value

    @deprecated
    def get_value(self) -> int:
        """This is an deprecated method"""
        return self.__value


class TestDeprecatedDecorator(unittest.TestCase):
    def test_deprecated_value_method(self) -> None:
        # Arrange
        instance = DecoratedClass(1)

        # Act & Assert
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = instance.deprecated_value()
            assert result == 1
            assert len(w) == 1
            assert issubclass(w[-1].category, DeprecationWarning)
            assert "deprecated_value is deprecated" in str(w[-1].message)

    def test_get_value_method(self) -> None:
        # Arrange
        instance = DecoratedClass(1)

        # Act & Assert
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = instance.get_value()
            assert result == 1
            assert len(w) == 1
            assert issubclass(w[-1].category, DeprecationWarning)
            assert "get_value is deprecated" in str(w[-1].message)

    def test_value_property(self) -> None:
        # Arrange
        instance = DecoratedClass(1)

        # Act
        result = instance.value

        # Assert
        assert result == 1

    def test_deprecated_decorator_attribute(self) -> None:
        # Assert
        assert getattr(DecoratedClass.deprecated_value, "__deprecated__", False)
        assert getattr(DecoratedClass.get_value, "__deprecated__", False)
