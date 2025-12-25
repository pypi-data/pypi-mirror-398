import logging
import ssl
import json
import asyncio
from typing import Any, Callable, Optional

import pika
from pika.adapters.asyncio_connection import AsyncioConnection
import pika.connection
from pika.exceptions import UnroutableError

from aas_thing.util.callback_manager import CallbackManager


class S3IBrokerAMQPClient:
    """
    An AMQP-based broker client to send and consume messages over RabbitMQ with asyncio support.

    """

    def __init__(
        self,
        amqp_url: str,
        vhost: str,
        exchange: str,
        queue: str,
        message_callback: Callable[[Any, Any, Any, bytes], None],
        logger: logging.Logger,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        port: int = 5671,
        is_ssl: bool = True,
        heartbeat: int = 60
    ) -> None:
        """
        Initialize the S3IBrokerAMQP instance with the given parameters.

        :param amqp_url: RabbitMQ host or URL.
        :param vhost: Virtual host name.
        :param exchange: Exchange name to publish messages.
        :param queue: Queue name to consume messages from.
        :param message_callback: Callback function to handle incoming messages.
        :param logger: Logger instance for logging.
        :param loop: Optional asyncio event loop, defaults to the current loop.
        :param port: Broker port, defaults to 5671.
        :param is_ssl: Whether to use SSL/TLS, defaults to True.
        :param heartbeat: Heartbeat interval in seconds, defaults to 60.
        """

        self._amqp_url = amqp_url
        self._vhost = vhost
        self._exchange = exchange
        self._queue = queue
        self._message_callback = message_callback
        self._logger = logger

        self._loop = loop or asyncio.get_event_loop()
        self._port = port
        self._is_ssl = is_ssl
        self._heartbeat = heartbeat

        self._credentials: Optional[pika.PlainCredentials] = None
        self._connection_params: Optional[pika.ConnectionParameters] = None
        self._connection: Optional[AsyncioConnection] = None
        self._channel: Optional[pika.channel.Channel] = None

        self._consumer_tag: Optional[str] = None
        self._is_consuming = False
        self._delivery_counter = 0
        self._callback_mgr = CallbackManager()

        self._ON_CONN_OPEN = "_on_connection_open"
        self._ON_CONN_CLOSE = "_on_connection_closed"
        self._ON_CONN_ERROR = "_on_connection_error"
        self._ON_CH_OPEN = "_on_channel_open"
        self._ON_CH_CLOSE = "_on_channel_closed"

    @property
    def channel(self) -> Optional[pika.channel.Channel]:
        """
        The AMQP channel object used for communication with RabbitMQ.

        :rtype: Optional[pika.channel.Channel]
        """
        return self._channel

    @property
    def connection(self) -> Optional[AsyncioConnection]:
        """
        Return the current AsyncioConnection instance.

        :return: The current connection to RabbitMQ, or None if not connected.
        :rtype: Optional[AsyncioConnection]
        """

        return self._connection

    def connect(self, token: str) -> None:
        """
        Establish connection with RabbitMQ using provided token.

        :param token: Authentication token for RabbitMQ.
        :return: None
        """
        self._logger.info("Initializing connection parameters...")
        # Create a PlainCredentials object using the provided token
        self._credentials = pika.PlainCredentials(
            username=" ", password=token, erase_on_connect=True
        )
        # Build ConnectionParameters using the credentials and other settings
        self._connection_params = self._build_connection_parameters()

        self._logger.info(
            "Connecting to RabbitMQ at %s:%d", self._amqp_url, self._port
        )
        # Establish the connection with RabbitMQ
        self._connection = AsyncioConnection(
            parameters=self._connection_params,
            on_open_callback=self._on_connection_open,
            on_open_error_callback=self._on_connection_error,
            on_close_callback=self._on_connection_closed,
            custom_ioloop=self._loop,
        )

    def _build_connection_parameters(self) -> pika.ConnectionParameters:
        """
        Build a ConnectionParameters instance to connect to RabbitMQ.

        This method creates a ConnectionParameters instance with the provided
        host, port, virtual host, credentials, heartbeat, and SSL options.

        The SSL options are only used if the connection is established over SSL/TLS.
        """
        # Create SSL context with server authentication
        context = None
        if self._is_ssl:
            # Create a default SSL context for server authentication
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ssl_opts = None
        if context:
            # Create an SSLOptions instance with the context and server hostname
            ssl_opts = pika.SSLOptions(context, server_hostname=self._amqp_url)

        return pika.ConnectionParameters(
            host=self._amqp_url,
            port=self._port,
            virtual_host=self._vhost,
            credentials=self._credentials,
            heartbeat=self._heartbeat,
            ssl_options=ssl_opts,
        )

    # ==================== Connection Callbacks ====================
    def _on_connection_open(self, conn: AsyncioConnection) -> None:
        """
        Called when the connection to RabbitMQ is established.

        This method is called by pika when the connection is established, and
        it triggers the callback registered with `add_on_connection_open_callback`.

        :param conn: The connection object
        :type conn: pika.adapters.asyncio_connection.AsyncioConnection
        """
        self._logger.info("Connection opened")
        conn.channel(on_open_callback=self._on_channel_open)
        self._callback_mgr.process(self._ON_CONN_OPEN, self._loop)

    def _on_connection_error(self, conn: AsyncioConnection, error: Exception) -> None:
        """
        Handles connection errors with RabbitMQ.

        This method is called when there is an error establishing or maintaining
        the connection to RabbitMQ. It logs the error and triggers the lifecycle
        callback associated with connection closure.

        :param conn: The connection object
        :type conn: pika.adapters.asyncio_connection.AsyncioConnection
        :param error: The exception representing the connection error
        :type error: Exception
        """

        self._logger.error("Connection error: %s", error)
        self._callback_mgr.process(self._ON_CONN_ERROR, self._loop)

    def _on_connection_closed(self, conn: AsyncioConnection, reason: Any) -> None:
        """
        Called when the connection to RabbitMQ is closed.

        This method logs a warning message indicating that the connection has
        been closed, sets the consuming flag to False, and triggers the
        lifecycle callback associated with connection closure.

        :param conn: The connection object
        :type conn: pika.adapters.asyncio_connection.AsyncioConnection
        :param reason: The reason for connection closure
        :type reason: Any
        """

        self._logger.warning("Connection closed: %s", reason)
        self._is_consuming = False
        self._callback_mgr.process(self._ON_CONN_CLOSE, self._loop)

    # ==================== Channel Callbacks ====================
    def _on_channel_open(self, channel: pika.channel.Channel) -> None:
        """
        Called when the channel is opened.

        This method is called by pika when the channel is open and ready to
        use. It logs a message indicating that the channel is open, sets up
        the channel's close callback, sets the QoS prefetch count to 1, starts
        consuming from the configured queue, and triggers the lifecycle
        callback associated with channel opening.

        :param channel: The channel object
        :type channel: pika.channel.Channel
        """
        self._channel = channel
        self._logger.info("Channel opened")
        channel.add_on_close_callback(self._on_channel_closed)
        channel.basic_qos(prefetch_count=1)
        self._start_consuming()
        self._callback_mgr.process(self._ON_CH_OPEN, self._loop)

    def _on_channel_closed(self, channel: pika.channel.Channel, reason: Any) -> None:
        """
        Called when the channel is closed.

        This method is called by pika when the channel is closed. It logs a
        message indicating that the channel is closed, closes the connection
        if it is still open, and triggers the lifecycle callback associated
        with channel closure.

        :param channel: The channel object
        :type channel: pika.channel.Channel
        :param reason: The reason for channel closure
        :type reason: Any
        """
        self._logger.error("Channel closed: %s", reason)
        if self._connection and not self._connection.is_closed:
            self._connection.close()
        self._callback_mgr.process(self._ON_CH_CLOSE, self._loop)

    # ==================== Consumption ====================
    def _start_consuming(self) -> None:
        """
        Start consuming from the configured queue.

        This method is called when the channel is open and a consumer tag is
        registered. It logs a message indicating that consumption has started.

        :raises Exception: If the channel is not open when this method is called.
        """
        if not self._channel or not self._channel.is_open:
            self._logger.error("Cannot start consuming: channel not open")
            return
        self._consumer_tag = self._channel.basic_consume(
            queue=self._queue,
            on_message_callback=self._message_callback,
            auto_ack=True,
            exclusive=True,
        )
        self._is_consuming = True
        self._logger.info("Started consuming on queue '%s'", self._queue)

    def stop_consuming(self) -> None:
        """
        Stop consuming messages from the queue.

        This method requests the RabbitMQ server to cancel the consumer using the
        consumer tag. Once the consumer is successfully cancelled, the channel
        will be closed. Logs a message indicating that consumption stop has been
        requested.

        :return: None
        """

        if self._channel and self._is_consuming:
            self._channel.basic_cancel(
                consumer_tag=self._consumer_tag, callback=self._on_cancel_ok
            )
            self._is_consuming = False
            self._logger.info("Requested stop consuming")

    def _on_cancel_ok(self, _unused_frame: Any) -> None:
        """
        Called when the server acknowledges the cancellation of a consumer.

        This method is called by pika when the server acknowledges that a
        consumer has been cancelled. It logs a message indicating that the
        consumer has been cancelled and closes the channel.

        :param _unused_frame: The server response frame (not used)
        :type _unused_frame: Any
        """
        if self._channel:
            self._channel.close()
            self._logger.info("Consumer cancelled, channel closed")

    # ==================== Publishing ====================
    def send(self, msg: dict, binding: str) -> None:
        """
        Publish a JSON message to the configured exchange with mandatory flag.

        If the message cannot be routed to the given binding, it will be
        returned to the message broker and will not be published. Logs an
        error message if the message is unroutable.

        :param msg: The message to be published
        :type msg: dict
        :param binding: The routing key to publish the message to
        :type binding: str
        """
        if not self._channel or not self._channel.is_open:
            self._logger.error("Cannot publish: channel not available")
            return
        try:
            # Create a persistent message (delivery mode 2)
            props = pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,
            )
            # Publish the message with the mandatory flag. If the message
            # cannot be routed to the given binding, it will be returned
            # to the message broker.
            self._channel.basic_publish(
                exchange=self._exchange,
                routing_key=binding,
                body=json.dumps(msg),
                properties=props,
                mandatory=True,
            )
            # Update the delivery counter
            self._delivery_counter += 1
            self._logger.info(
                "Published message #%d to '%s'", self._delivery_counter, binding
            )
        except UnroutableError:
            # Log an error if the message is unroutable
            self._logger.exception(
                "Message unroutable for routing key '%s'", binding
            )

    # ==================== Callback Registration ====================
    def add_on_connection_open_callback(
        self,
        callback: Callable[..., None],
        one_shot: bool = False,
        is_async: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Register a callback to be invoked when the connection opens.

        This method registers a callback to be invoked when the connection
        to the message broker is established. The callback is called with
        the given arguments and keyword arguments.

        :param callback: The callback to be invoked
        :param one_shot: Whether the callback should be removed after the
            first invocation, defaults to False
        :param args: Additional arguments to be passed to the callback
        :param kwargs: Additional keyword arguments to be passed to the
            callback
        """
        self._callback_mgr.add(
            self._ON_CONN_OPEN, callback, one_shot, is_async, *args, **kwargs
        )

    def add_on_connection_close_callback(
        self,
        callback: Callable[..., None],
        one_shot: bool = False,
        is_async: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Register a callback to be invoked when the connection closes.

        This method registers a callback to be invoked when the connection
        to the message broker is closed. The callback is called with
        the given arguments and keyword arguments.

        :param callback: The callback to be invoked
        :param one_shot: Whether the callback should be removed after the
            first invocation, defaults to False
        :param args: Additional arguments to be passed to the callback
        :param kwargs: Additional keyword arguments to be passed to the
            callback
        """
        self._callback_mgr.add(
            self._ON_CONN_CLOSE, callback, one_shot, is_async, *args, **kwargs
        )

    def add_on_connection_error_callback(
        self,
        callback: Callable[..., None],
        one_shot: bool = False,
        is_async: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Register a callback to be invoked when a connection error occurs.

        This method registers a callback to be invoked when a connection
        error occurs. The callback is called with
        the given arguments and keyword arguments.

        :param callback: The callback to be invoked
        :param one_shot: Whether the callback should be removed after the
            first invocation, defaults to False
        :param args: Additional arguments to be passed to the callback
        :param kwargs: Additional keyword arguments to be passed to the
            callback
        """
        self._callback_mgr.add(
            self._ON_CONN_ERROR, callback, one_shot, is_async, *args, **kwargs
        )

    def add_on_channel_open_callback(
        self,
        callback: Callable[..., None],
        one_shot: bool = False,
        is_async: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Register a callback to be invoked when the channel opens.

        This method registers a callback to be invoked when the channel to
        the message broker is established. The callback is called with the
        given arguments and keyword arguments.

        :param callback: The callback to be invoked
        :param one_shot: Whether the callback should be removed after the
            first invocation, defaults to False
        :param is_async: Whether the callback is an asynchronous function,
            defaults to False
        :param args: Additional arguments to be passed to the callback
        :param kwargs: Additional keyword arguments to be passed to the
            callback
        """
        self._callback_mgr.add(
            self._ON_CH_OPEN, callback, one_shot, is_async, *args, **kwargs
        )

    def add_on_channel_close_callback(
        self,
        callback: Callable[..., None],
        one_shot: bool = False,
        is_async: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Register a callback to be invoked when the channel closes.

        This method registers a callback to be invoked when the channel to
        the message broker is closed. The callback is called with the
        given arguments and keyword arguments.

        :param callback: The callback to be invoked
        :param one_shot: Whether the callback should be removed after the
            first invocation, defaults to False
        :param is_async: Whether the callback is an asynchronous function,
            defaults to False
        :param args: Additional arguments to be passed to the callback
        :param kwargs: Additional keyword arguments to be passed to the
            callback
        """
        self._callback_mgr.add(
            self._ON_CH_CLOSE, callback, one_shot, is_async, *args, **kwargs
        )

    def reconnect_with_new_token(self, token: str) -> None:
        """
        Reconnect to the message broker with a new authentication token.

        This method updates the authentication token without re-establishing
        the connection to the message broker. It is used to refresh the
        authentication token when it expires.

        :param token: The new authentication token
        """
        if self._connection:
            self._connection.update_secret(token, reason="Token refreshed")
        else:
            self._logger.warning("No active connection to refresh token")

    def subscribe_to_topic(self, topic: str) -> None:
        """
        Bind the queue to a topic (routing key) on the exchange or event exchange.

        :param topic: The routing key (topic) to bind to
        """
        if not self._channel or not self._channel.is_open:
            self._logger.error("Cannot subscribe: channel not open")
            return
        self._channel.queue_bind(
            queue=self._queue,
            exchange=self._exchange,
            routing_key=topic,
            callback=self._on_bind_ok
        )
        self._logger.info("Subscribed queue '%s' to topic '%s' on exchange '%s'", self._queue, topic, self._exchange)

    def unsubscribe_from_topic(self, topic: str) -> None:
        """
        Unbind the queue from a topic (routing key) on the exchange or event exchange.

        :param topic: The routing key (topic) to unbind from
        """
        if not self._channel or not self._channel.is_open:
            self._logger.error("Cannot subscribe: channel not open")
            return
        self._channel.queue_unbind(
            queue=self._queue,
            exchange=self._exchange,
            routing_key=topic,
            callback=self._on_unbind_ok
        )
        self._logger.info("Unsubscribed queue '%s' from topic '%s' on exchange '%s'", self._queue, topic, self._exchange)

    def _on_bind_ok(self, _unused_frame):
        self._logger.info("Queue bound successfully")

    def _on_unbind_ok(self, _unused_frame):
        self._logger.info("Queue unbound successfully")
