import unittest

from machinelogic.ivention.event_listener import EventListenerManager


class TestEventListenerManager(unittest.TestCase):
    def test_given_nothing_when_add_event_listener_then_adds_the_event_listener(
        self,
    ) -> None:
        # Arrange
        event_listener_manager = EventListenerManager()

        # Act
        event_listener_manager.add_event_listener("topic", None)  # type: ignore

        # Assert
        self.assertEqual(
            len(event_listener_manager._listeners),
            1,
        )
