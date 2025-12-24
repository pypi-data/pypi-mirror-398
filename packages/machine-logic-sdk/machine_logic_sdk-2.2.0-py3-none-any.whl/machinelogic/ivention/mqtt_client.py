# pylint: disable=unused-argument
import _thread
from multiprocessing.pool import ThreadPool
from traceback import print_exception
from typing import Any, Callable, Optional, Union
from urllib.parse import urlparse

import paho.mqtt.client as mqtt

from .handle import Handle

THREAD_POOL_SIZE = 1


class MqttCallbackHandle:
    """Callback handle for MQTT"""

    def __init__(self, handle: Handle, callback: Callable[[str, Optional[str]], None]):
        self.handle: Handle = handle
        self.callback: Callable[[str, Optional[str]], None] = callback


class MqttClient:
    """Wrapper around the MQTT client"""

    def __init__(self, connection_string: str):
        parsed_url = urlparse(connection_string)
        transport = "tcp"
        if parsed_url.scheme in ("ws", "wss"):
            transport = "websockets"

        # "internal" handlers used in the implementation that should not be changed
        # by users
        self._internal_callback_dict: dict[str, list[MqttCallbackHandle]] = {}
        self._callback_handle_counter = 0

        # "user" callbacks (1 topic per callback)
        self._user_callback_dict: dict[str, Callable[[str, Optional[str]], None]] = {}

        self._client = mqtt.Client(transport=transport)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect
        self._client.connect(parsed_url.hostname, parsed_url.port)
        self._client.loop_start()
        self._callback_thread_pool = ThreadPool(processes=THREAD_POOL_SIZE)

    def _on_connect(
        self,
        client: mqtt.Client,
        user_data: Any,
        flags: int,
        return_code: int,
    ) -> None:
        """
        Args:
            client (mqtt.Client):
            userData (Any):
            flags (int):
            rc (int):
        """
        if return_code != 0:
            print(f"MQTT client failed to connect: {return_code}")

    def _on_message(
        self,
        client: mqtt.Client,
        user_data: Any,
        msg: mqtt.MQTTMessage,
    ) -> None:
        """
        Args:
            client (mqtt.Client):
            userData (Any):
            msg (mqtt.MQTTMessage):
        """
        topic = msg.topic
        value = msg.payload.decode("utf-8") if msg.payload else None

        def error_callback(exc: BaseException) -> None:
            print(f"Error while dispatching MQTT message for topic: '{topic}': {exc}")
            print_exception(type(exc), exc, exc.__traceback__)
            _thread.interrupt_main()

        for subscribed_topic, callback_handles in self._internal_callback_dict.items():
            if mqtt.topic_matches_sub(subscribed_topic, topic):
                for handle in callback_handles:
                    self._callback_thread_pool.apply_async(
                        handle.callback,
                        args=(topic, value),
                        error_callback=error_callback,
                    )

        for subscribed_topic, callback in self._user_callback_dict.items():
            if mqtt.topic_matches_sub(subscribed_topic, topic):
                self._callback_thread_pool.apply_async(
                    callback,
                    args=(topic, value),
                    error_callback=error_callback,
                )

    def _on_disconnect(self, client: mqtt.Client, user_data: Any, return_code: int) -> None:  # pylint: disable=unused-argument
        """
        Args:
            client (mqtt.Client):
            userData: (Any):
            rc (int):
        """
        print(f"MQTT client disconnected: {return_code}")

    def internal_subscribe(self, topic: str, callback: Callable[[str, Optional[str]], None]) -> Handle:
        """
        For use in internal services.
        Args:
            topic (str): The topic to subscribe to
            callback (Callable[[str, str] None]): Callback for the topic

        Returns:
            Handle: A handle that can be used to unsubscribe later
        """
        already_subscribed = topic in self._internal_callback_dict
        if not already_subscribed:
            self._internal_callback_dict[topic] = []

        handle = Handle(self._callback_handle_counter)
        self._internal_callback_dict[topic].append(MqttCallbackHandle(handle, callback))

        if not already_subscribed:
            self._client.subscribe(topic)
        self._callback_handle_counter = self._callback_handle_counter + 1
        return handle

    def subscribe(self, topic: str, callback: Union[Callable[[str, Optional[str]], None], None]) -> None:
        """
        Public/User facing MQTT subscribe function.
        Args:
            topic (str): The topic to subscribe to
            callback (Union[Callable[[str, str] None], None]): Callback for the topic, set to Nne to remove callback.
        """
        if callback is not None:
            self._user_callback_dict[topic] = callback
            self._client.subscribe(topic)
            return
        # None -> remove existing callbacks.
        if topic in self._user_callback_dict:
            del self._user_callback_dict[topic]

    def publish(self, topic: str, message: Optional[str] = None) -> bool:
        """
        Args:
            topic (str): The topic to publish to
            message (str): The message to publish, default=None
        """

        self._client.publish(topic, message)
        return True

    def unsubscribe(self, handle: Handle) -> bool:
        """
        For internal use.
        Args:
            handle (Handle): The handle that you want to remove

        Returns:
            bool: True if it was removed, otherwise False
        """
        for topic, callback_handlers in self._internal_callback_dict.items():
            for idx, handler in enumerate(callback_handlers):
                if handler.handle == handle:
                    # Remove the callback
                    del callback_handlers[idx]

                    # If its the final callback, remove the dictionary and unsubscribe
                    if len(callback_handlers) == 0:
                        del self._internal_callback_dict[topic]
                        self._client.unsubscribe(topic)
                    return True
        return False

    def dispose(self) -> None:
        """
        Dispose of the MqttClient.
        You should call this method when you stop using the MqttClient to ensure that the underlying resources are freed properly.
        """
        self._callback_thread_pool.close()
