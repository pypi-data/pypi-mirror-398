"""Queue abstraction with both sync and async support."""
import functools
import logging
import typing as tp
from types import ModuleType

import aio_pika
from aio_pika import DeliveryMode

from connection import AsyncConnection, RequeueMessage, SyncConnection

log = logging.getLogger(__name__)

# Type aliases for clarity
AMMessage = tp.TypeVar("AMMessage")  # Your message type
Message = tp.TypeVar("Message")  # Your base message type


class AsyncQueue:
    """Async message queue backed by RabbitMQ.

    Example:
        queue = AsyncQueue(topic)
        await queue.publish(message)
        await queue.subscribe(callback)
    """

    def __init__(self, topic: "Topic", connection: AsyncConnection):
        """Initialize async queue.

        Args:
            topic: a Topic value object
            connection: AsyncConnection instance
        """
        self.topic = topic.name
        self.shared_queue = topic.is_task_queue
        self.connection = connection
        self.subscription: str | None = None
        self.result_subscription: str | None = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self.topic == other.topic and self.shared_queue == other.shared_queue

    @property
    def result_topic(self) -> str:
        """Get the result topic for this queue."""
        return f"{self.topic}.result"

    async def publish(self, message: AMMessage) -> None:
        """Publish a message to the queue.

        Args:
            message: a protobuf message
        """
        await self._send_message(self.topic, bytes(message))

    async def _receive(
        self, callback: tp.Callable[[AMMessage], tp.Any], message: aio_pika.IncomingMessage
    ) -> None:
        """Handle a message from the queue.

        Args:
            callback: Function to process the message
            message: Incoming message from RabbitMQ
        """
        if not message.routing_key:
            raise ValueError("Routing key was not set. Invalid topic")

        # Skip result messages - they're handled separately
        if message.routing_key == self.result_topic or message.routing_key.endswith(".result"):
            return

        msg: AMMessage = deserialize_message(message.routing_key, message.body)
        try:
            result = callback(msg)
            # Handle async callbacks
            if tp.iscoroutine(result):
                await result
        except RequeueMessage:
            raise
        except Exception as exc:
            log.exception("Could not process message: %s", str(message.body))
            result = msg.make_result(return_code=pb.results.ReturnCode.FAILURE, error=str(exc))
            await self.publish_result(
                result, topic=msg.result_topic, correlation_id=message.correlation_id
            )

    async def subscribe(self, callback: tp.Callable[[AMMessage], tp.Any]) -> None:
        """Subscribe to messages from the queue.

        Args:
            callback: Function to call when messages arrive. Can be sync or async.
        """
        if self.subscription is not None:
            raise ValueError("Cannot subscribe twice")

        func = functools.partial(self._receive, callback)
        self.subscription = await self.connection.subscribe(
            self.topic, func, shared=self.shared_queue
        )

    async def unsubscribe(self) -> None:
        """Unsubscribe from the queue."""
        if self.subscription is not None:
            await self.connection.unsubscribe(self.subscription)
            self.subscription = None

    async def publish_result(
        self,
        result: "pb.results.Result",
        topic: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Publish a message to the results topic.

        Args:
            result: a amlogic_messages.results.Result message
            topic: Optional override for result topic
            correlation_id: Optional correlation ID
        """
        result_topic = topic or self.result_topic
        log.info("Publishing result to: %s", result_topic)
        await self._send_message(
            result_topic, bytes(result), correlation_id=correlation_id, persistent=False
        )

    async def _receive_result(
        self,
        callback: tp.Callable[["pb.results.Result"], tp.Any],
        message: aio_pika.IncomingMessage,
    ) -> None:
        """Handle a result message from the queue.

        Args:
            callback: Function to call with deserialized result
            message: Incoming message from RabbitMQ
        """
        try:
            result = deserialize_result_message(message.body)
            result_val = callback(result)
            # Handle async callbacks
            if tp.iscoroutine(result_val):
                await result_val
        except Exception:
            log.exception("Could not process result: %s", str(message.body))

    async def subscribe_results(self, callback: tp.Callable[["pb.results.Result"], tp.Any]) -> None:
        """Subscribe to results from the queue.

        Args:
            callback: Function to call when results arrive. Can be sync or async.
        """
        if self.result_subscription is not None:
            raise ValueError("Cannot subscribe to results twice")

        func = functools.partial(self._receive_result, callback)
        self.result_subscription = await self.connection.subscribe(
            self.result_topic, func, shared=False
        )

    async def unsubscribe_results(self) -> None:
        """Unsubscribe from results."""
        if self.result_subscription is not None:
            await self.connection.unsubscribe(self.result_subscription)
            self.result_subscription = None

    async def purge(self) -> None:
        """Delete all messages from the queue."""
        if not self.shared_queue:
            raise RuntimeError("Can only purge shared queues")
        await self.connection.purge(self.topic)

    async def get_message_count(self) -> int:
        """Get current message count."""
        if not self.shared_queue:
            raise RuntimeError("Can only get count of shared queues")
        log.debug("Getting queue message count")
        return await self.connection.get_message_count(self.topic)

    async def _send_message(
        self,
        topic: str,
        body: bytes,
        correlation_id: str | None = None,
        persistent: bool = True,
    ) -> None:
        """Low-level message sending implementation.

        Args:
            topic: Topic name or routing key
            body: Serialized message
            correlation_id: Optional correlation ID
            persistent: Whether message should be persistent
        """
        message = aio_pika.Message(
            body,
            correlation_id=correlation_id,
            delivery_mode=DeliveryMode.PERSISTENT if persistent else DeliveryMode.NOT_PERSISTENT,
        )
        await self.connection.publish(topic, message)

    async def cleanup(self) -> None:
        """Clean up subscriptions."""
        await self.unsubscribe()
        await self.unsubscribe_results()


class SyncQueue:
    """Synchronous message queue backed by RabbitMQ.

    Example:
        queue = SyncQueue(topic, connection)
        queue.publish(message)
        queue.subscribe(callback)
    """

    def __init__(self, topic: "Topic", connection: SyncConnection):
        """Initialize sync queue.

        Args:
            topic: a Topic value object
            connection: SyncConnection instance
        """
        self.topic = topic.name
        self.shared_queue = topic.is_task_queue
        self.connection = connection
        self.subscription: str | None = None
        self.result_subscription: str | None = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self.topic == other.topic and self.shared_queue == other.shared_queue

    @property
    def result_topic(self) -> str:
        """Get the result topic for this queue."""
        return f"{self.topic}.result"

    def publish(self, message: AMMessage, timeout: float = 10.0) -> None:
        """Publish a message to the queue.

        Args:
            message: a protobuf message
            timeout: Maximum time to wait
        """
        self._send_message(self.topic, bytes(message), timeout=timeout)

    def _receive(
        self, callback: tp.Callable[[AMMessage], tp.Any], message: aio_pika.IncomingMessage
    ) -> None:
        """Handle a message from the queue.

        Args:
            callback: Function to process the message
            message: Incoming message from RabbitMQ
        """
        if not message.routing_key:
            raise ValueError("Routing key was not set. Invalid topic")

        # Skip result messages
        if message.routing_key == self.result_topic or message.routing_key.endswith(".result"):
            return

        msg: AMMessage = deserialize_message(message.routing_key, message.body)
        try:
            _ = callback(msg)
        except RequeueMessage:
            raise
        except Exception as exc:
            log.exception("Could not process message: %s", str(message.body))
            result = msg.make_result(return_code=pb.results.ReturnCode.FAILURE, error=str(exc))
            self.publish_result(
                result, topic=msg.result_topic, correlation_id=message.correlation_id
            )

    def subscribe(self, callback: tp.Callable[[AMMessage], tp.Any], timeout: float = 10.0) -> None:
        """Subscribe to messages from the queue.

        Args:
            callback: Function to call when messages arrive (must be synchronous)
            timeout: Maximum time to wait for subscription
        """
        if self.subscription is not None:
            raise ValueError("Cannot subscribe twice")

        func = functools.partial(self._receive, callback)
        self.subscription = self.connection.subscribe(
            self.topic, func, shared=self.shared_queue, timeout=timeout
        )

    def unsubscribe(self, timeout: float = 10.0) -> None:
        """Unsubscribe from the queue.

        Args:
            timeout: Maximum time to wait
        """
        if self.subscription is not None:
            self.connection.unsubscribe(self.subscription, timeout=timeout)
            self.subscription = None

    def publish_result(
        self,
        result: "pb.results.Result",
        topic: str | None = None,
        correlation_id: str | None = None,
        timeout: float = 10.0,
    ) -> None:
        """Publish a message to the results topic.

        Args:
            result: a amlogic_messages.results.Result message
            topic: Optional override for result topic
            correlation_id: Optional correlation ID
            timeout: Maximum time to wait
        """
        result_topic = topic or self.result_topic
        log.info("Publishing result to: %s", result_topic)
        self._send_message(
            result_topic,
            bytes(result),
            correlation_id=correlation_id,
            persistent=False,
            timeout=timeout,
        )

    def _receive_result(
        self,
        callback: tp.Callable[["pb.results.Result"], tp.Any],
        message: aio_pika.IncomingMessage,
    ) -> None:
        """Handle a result message from the queue.

        Args:
            callback: Function to call with deserialized result
            message: Incoming message from RabbitMQ
        """
        try:
            result = deserialize_result_message(message.body)
            callback(result)
        except Exception:
            log.exception("Could not process result: %s", str(message.body))

    def subscribe_results(
        self, callback: tp.Callable[["pb.results.Result"], tp.Any], timeout: float = 10.0
    ) -> None:
        """Subscribe to results from the queue.

        Args:
            callback: Function to call when results arrive (must be synchronous)
            timeout: Maximum time to wait
        """
        if self.result_subscription is not None:
            raise ValueError("Cannot subscribe to results twice")

        func = functools.partial(self._receive_result, callback)
        self.result_subscription = self.connection.subscribe(
            self.result_topic, func, shared=False, timeout=timeout
        )

    def unsubscribe_results(self, timeout: float = 10.0) -> None:
        """Unsubscribe from results.

        Args:
            timeout: Maximum time to wait
        """
        if self.result_subscription is not None:
            self.connection.unsubscribe(self.result_subscription, timeout=timeout)
            self.result_subscription = None

    def purge(self, timeout: float = 10.0) -> None:
        """Delete all messages from the queue.

        Args:
            timeout: Maximum time to wait
        """
        if not self.shared_queue:
            raise RuntimeError("Can only purge shared queues")
        self.connection.purge(self.topic, timeout=timeout)

    def get_message_count(self, timeout: float = 10.0) -> int:
        """Get current message count.

        Args:
            timeout: Maximum time to wait
        """
        if not self.shared_queue:
            raise RuntimeError("Can only get count of shared queues")
        log.debug("Getting queue message count")
        return self.connection.get_message_count(self.topic, timeout=timeout)

    def _send_message(
        self,
        topic: str,
        body: bytes,
        correlation_id: str | None = None,
        persistent: bool = True,
        timeout: float = 10.0,
    ) -> None:
        """Low-level message sending implementation.

        Args:
            topic: Topic name or routing key
            body: Serialized message
            correlation_id: Optional correlation ID
            persistent: Whether message should be persistent
            timeout: Maximum time to wait
        """
        message = aio_pika.Message(
            body,
            correlation_id=correlation_id,
            delivery_mode=DeliveryMode.PERSISTENT if persistent else DeliveryMode.NOT_PERSISTENT,
        )
        self.connection.publish(topic, message)

    def cleanup(self, timeout: float = 10.0) -> None:
        """Clean up subscriptions.

        Args:
            timeout: Maximum time to wait
        """
        self.unsubscribe(timeout=timeout)
        self.unsubscribe_results(timeout=timeout)

    def __del__(self):
        """Clean up subscriptions on deletion."""
        log.debug("Destructor called for %s %s", self.__class__, id(self))
        try:
            self.cleanup(timeout=5.0)
        except Exception:
            log.exception("Error during cleanup in destructor")


# ============================================================================
# Top-level API functions
# ============================================================================


# Async API
async def async_get_queue(
    pkg: Message | type[Message] | ModuleType, connection: AsyncConnection
) -> AsyncQueue:
    """Get an async queue for a message type.

    Args:
        pkg: Message instance, class, or module
        connection: AsyncConnection instance

    Returns:
        AsyncQueue instance
    """
    topic = get_topic(pkg)
    return AsyncQueue(topic, connection)


async def async_publish(message: AMMessage, connection: AsyncConnection) -> None:
    """Publish a message on its own queue (async).

    Args:
        message: Message to publish
        connection: AsyncConnection instance
    """
    queue = await async_get_queue(message, connection)
    await queue.publish(message)


# Sync API
def sync_get_queue(
    pkg: Message | type[Message] | ModuleType, connection: SyncConnection
) -> SyncQueue:
    """Get a sync queue for a message type.

    Args:
        pkg: Message instance, class, or module
        connection: SyncConnection instance

    Returns:
        SyncQueue instance
    """
    topic = get_topic(pkg)
    return SyncQueue(topic, connection)


def sync_publish(message: AMMessage, connection: SyncConnection, timeout: float = 10.0) -> None:
    """Publish a message on its own queue (sync).

    Args:
        message: Message to publish
        connection: SyncConnection instance
        timeout: Maximum time to wait
    """
    queue = sync_get_queue(message, connection)
    queue.publish(message, timeout=timeout)


# Shared utility functions (no changes needed)
def deserialize_message(topic: str | None, body: bytes) -> Message | None:
    """Deserialize the body of a serialized pika message.

    Args:
        topic: The topic. Used to determine the message type.
        body: The serialized message

    Returns:
        A deserialized message
    """
    if not topic:
        raise ValueError("Routing key was not set. Invalid topic")
    message_type: tp.Type[Message] = get_message_class_from_topic(topic)
    return message_type().parse(body) if message_type else None


def deserialize_result_message(body: bytes) -> "pb.results.Result":
    """Deserialize the result message.

    Args:
        body: The serialized amlogic_messages.results.Result

    Returns:
        Instance of amlogic_messages.results.Result
    """
    return pb.results.Result().parse(body)


def to_json_content(data: dict[str, tp.Any]) -> "pb.commons.JsonContent":
    """Serialize an object and build a JsonContent message.

    Args:
        data: A json-serializable object

    Returns:
        A pb.commons.JsonContent instance
    """
    import json

    # Encode a json string to bytes
    encoded = json.dumps(data, cls=ProtobunnyJsonEncoder).encode()
    # build the JsonContent field
    content = pb.commons.JsonContent(content=encoded)
    return content


def deserialize_content(msg: "pb.commons.JsonContent") -> dict[str, tp.Any]:
    """Deserialize a JsonContent message back into a dictionary.

    Args:
        msg: The JsonContent object

    Returns:
        The decoded dictionary
    """
    import json

    # Decode bytes back to JSON string and parse
    return json.loads(msg.content.decode())


# ============================================================================
# Context manager helpers for easier usage
# ============================================================================


class QueueContext:
    """Base class for queue context managers."""

    def __init__(self, topic: "Topic"):
        self.topic = topic
        self._queue = None


class AsyncQueueContext(QueueContext):
    """Async context manager for queue operations.

    Example:
        async with AsyncQueueContext(topic, connection) as queue:
            await queue.publish(message)
    """

    def __init__(self, topic: "Topic", connection: AsyncConnection):
        super().__init__(topic)
        self.connection = connection

    async def __aenter__(self) -> AsyncQueue:
        self._queue = AsyncQueue(self.topic, self.connection)
        return self._queue

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._queue:
            await self._queue.cleanup()
        return False


class SyncQueueContext(QueueContext):
    """Sync context manager for queue operations.

    Example:
        with SyncQueueContext(topic, connection) as queue:
            queue.publish(message)
    """

    def __init__(self, topic: "Topic", connection: SyncConnection):
        super().__init__(topic)
        self.connection = connection

    def __enter__(self) -> SyncQueue:
        self._queue = SyncQueue(self.topic, self.connection)
        return self._queue

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._queue:
            try:
                self._queue.cleanup()
            except Exception:
                log.exception("Error cleaning up queue")
        return False
