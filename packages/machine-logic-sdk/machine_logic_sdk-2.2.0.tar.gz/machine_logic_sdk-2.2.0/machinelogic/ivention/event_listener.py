"""Module for managing generic events"""

from typing import Callable, Optional

import paho.mqtt.client as mqtt

from .handle import Handle

EventCallback = Callable[[str, Optional[str]], None]


class EventListener:
    """A listener on a topic"""

    def __init__(self, handle: Handle, topic: str, callback: EventCallback):
        """_summary_

        Args:
            handle (Handle): Handle for the vent
            topic (str): Topic to wait for
            callback (EventCallback): Callback to trigger
        """
        self.handle = handle
        self.topic = topic
        self.callback = callback


class EventListenerManager:
    """
    Generic mechanism for adding, removing, and notifying event listeners.
    """

    _listeners: list[EventListener]
    _handle_count: int

    def __init__(self) -> None:
        self._listeners = []
        self._handle_count = 0

    def add_event_listener(self, topic: str, callback: EventCallback) -> Handle:
        """Add a listener for a topic.

        Args:
            topic (str): The topic to listen on
            callback (EventCallback): A callback where the first argument is the topic and the second is the message

        Returns:
            Handle: Provide to 'remove_event_listener' to remove this event
        """
        handle = Handle(self._handle_count)
        self._handle_count = self._handle_count + 1
        self._listeners.append(EventListener(handle, topic, callback))
        return handle

    def remove_event_listener(self, handle: Handle) -> bool:
        """Remove an active event listener

        Args:
            handle (Handle): The handle of the listener that you want to remove

        Returns:
            bool: True if the handle was removed, otherwise False
        """
        for listener in self._listeners:
            if listener.handle is handle:
                self._listeners.remove(listener)
                return True

        return False

    def notify_listeners(self, topic: str, message: Optional[str] = None) -> None:
        """Calls the callback on all event listeners interested in the provided topic

        Args:
            topic (str): Topic
            message (str): Message
        """
        for listener in self._listeners:
            if mqtt.topic_matches_sub(listener.topic, topic):
                listener.callback(topic, message)
