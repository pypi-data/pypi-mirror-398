import asyncio
import json
import logging
import time
from typing import Any, Callable, Dict, Optional, Union
import jsonschema

from aas_thing.s3i.identity_provider import S3IIdentityProviderClient
from aas_thing.s3i.broker import S3IBrokerAMQPClient
from aas_thing.s3i.message.reference import I40MessageGlobalReferenceKeys, I40MessageKeys, I40MessageType, I40MessageSemanticProtocols
from aas_thing.s3i.message.message import I40Message
from aas_thing.s3i.message.invoke_operation import (
    I40InvokeOperationAsyncRequest,
    I40InvokeOperationAsyncReply,
    I40InvokeOperationSyncRequest,
    I40InvokeOperationSyncReply,
)
from aas_thing.s3i.message.get_submodel_element_by_path import I40GetSubmodelElementByPathRequest, I40GetSubmodelElementByPathReply
from aas_thing.s3i.message.event import I40EventMessage #TODO
from aas_thing.s3i.message.frame import Frame

from aas_thing.message_handler import I40SemanticProtocolHandler
from aas_thing.util.callback_manager import CallbackManager

RECONNECT_INTERVAL = 20  # seconds
RECONNECT_DELAY = 2  # seconds


class ConfigError(Exception):
    """Configuration validation or initialization error."""
    pass


def _validate_config(obj: Any, schema: Dict[str, Any], name: str) -> None:
    """
    Validates the given configuration object against a JSON schema.

    :param obj: The configuration object to validate
    :param schema: The JSON schema to validate against
    :param name: The name of the configuration object (for error messages)
    :raises ConfigError: If the configuration is invalid
    """
    try:
        jsonschema.validate(instance=obj, schema=schema)
    except jsonschema.ValidationError as e:
        raise ConfigError(
            f"Invalid {name} configuration: {e.message}"
        )


class S3IConnector:
    """
    Manages the connection to S³I identity provider, the broker, and dispatch.
    In the context of the broker connection, there are separate intialization of connections for exchanging normal I4.0 messages and events.
    """
    _IDP_SCHEMA = {
        "type": "object",
        "properties": {
            "url": {"type": "string"},
            "realm": {"type": "string"},
            "client_id": {"type": "string"},
            "client_secret": {"type": "string"},
            "username": {"type": "string"},
            "password": {"type": "string"},
        },
        "required": ["url", "realm", "client_id", "client_secret"],
    }
    _BROKER_SCHEMA = {
        "type": "object",
        "properties": {
            "url": {"type": "string"},
            "vhost": {"type": "string"},
            "exchange": {"type": "string"},
            "queue": {"type": "string"},
            "port": {"type": "number"},
            "is_ssl": {"type": "boolean"},
        },
        "required": ["url", "vhost", "exchange", "queue", "port", "is_ssl"],
    }
    idp_ready = "idp_ready"
    message_broker_ready = "message_broker_ready"
    event_broker_ready = "event_broker_ready"
    token_refreshed = "token_refreshed"

    def __init__(
        self,
        config: Dict[str, Any],
        handler: I40SemanticProtocolHandler,
        logger: logging.Logger,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        """
        Initialize the S³I connector with configuration, message handler, logger and event loop.

        :param config: S³I configuration dictionary with Json schemata shown below
        :param handler: Message handler
        :param logger: Logger
        :param loop: Event loop, defaults to asyncio.get_event_loop()
        
        .. code-block:: json

            _IDP_SCHEMA = {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "realm": {"type": "string"},
                    "client_id": {"type": "string"},
                    "client_secret": {"type": "string"},
                    "username": {"type": "string"},
                    "password": {"type": "string"},
                },
                "required": ["url", "realm", "client_id", "client_secret"],
            }
            _BROKER_SCHEMA = {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "vhost": {"type": "string"},
                    "exchange": {"type": "string"},
                    "queue": {"type": "string"},
                    "port": {"type": "number"},
                    "is_ssl": {"type": "boolean"},
                },
                "required": ["url", "vhost", "exchange", "queue", "port", "is_ssl"],
            }
        """
        self._logger = logger
        self._loop = loop or asyncio.get_event_loop()
        self._handler = handler
        self._callbacks = CallbackManager()
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._idp = self._init_idp_client(config.get("identity_provider"))

        self._msg_broker = self._init_broker_client(config.get("message_broker"), self._on_message)
        self._evt_broker = self._init_broker_client(config.get("event_broker"), self._on_event)
        self.__reconnecting = False

    @property
    def connected(self) -> bool:
        """
        Check if the S³I connector is connected.

        :return: True if connected, False otherwise
        """
        if self._msg_broker and self._evt_broker:
            return self._msg_broker._is_consuming and self._evt_broker._is_consuming
        elif self._msg_broker:
            return self._msg_broker._is_consuming
        elif self._evt_broker:
            return self._evt_broker._is_consuming
    
    @property
    def reconnecting(self) -> bool:
        """
        Check if the S³I connector is reconnecting.

        :return: True if connected, False otherwise
        """
        return self.__reconnecting

    def _init_idp_client(
        self, idp_conf: Optional[Dict[str, Any]]
    ) -> Optional[S3IIdentityProviderClient]:
        """
        Initialize the connection to S³I Identity Provider.

        :param idp_conf: S³I Identity Provider configuration
        :return: S³I Identity Provider connection instance
        """
        if not idp_conf:
            return None
        _validate_config(idp_conf, self._IDP_SCHEMA, "identity_provider")
        return S3IIdentityProviderClient(
            client_id=idp_conf["client_id"],
            client_secret=idp_conf["client_secret"],
            realm=idp_conf["realm"],
            idp_url=idp_conf["url"],
            logger=self._logger,
            username=idp_conf.get("username"),
            password=idp_conf.get("password"),
        )

    def _init_broker_client(
        self,
        broker_conf: Optional[Dict[str, Any]],
        callback: Callable,
    ) -> Optional[S3IBrokerAMQPClient]:
        """
        Initialize the connection to S³I broker.

        :param broker_conf: S³I broker configuration
        :param callback: Message callback
        :return: S³I broker instance
        """
        if not broker_conf:
            return None
        _validate_config(broker_conf, self._BROKER_SCHEMA, "broker")
        return S3IBrokerAMQPClient(
            amqp_url=broker_conf["url"],
            vhost=broker_conf["vhost"],
            exchange=broker_conf["exchange"],
            queue=broker_conf["queue"],
            message_callback=callback,
            loop=self._loop,
            logger=self._logger,
            port=int(broker_conf["port"]),
            is_ssl=broker_conf["is_ssl"],
        )

    def add_callback(
        self, key: str, func: Callable, one_shot: bool = False, is_async: bool = False, *args: Any
    ) -> None:
        """
        Register lifecycle callbacks.

        :param key: The key to identify the callback function
        :param func: The callback function
        :param one_shot: Whether the callback should be removed after the first invocation
        :param is_async: Whether the callback is an asynchronous function
        :param args: Additional arguments to be passed to the callback
        """
        self._callbacks.add(key, func, one_shot, is_async, *args)

    def connect(self) -> None:
        """
        Authenticate with the Identity Provider and start broker connections for exhchanging normal I4.0 messages and/or events.

        After the Identity Provider is ready, the broker connection will be started.
        When the connection for exchanging normal I4.0 messages is ready, the lifecycle callback
        `message_broker_ready` will be triggered.

        If the connection for exchanging events is configured, it will be started after the message
        broker is ready. When this connection is ready, the lifecycle callback
        `event_broker_ready` will be triggered.
        """
        # Authenticate with the Identity Provider
        if self._idp:
            self._idp.connect()
            # Get the token information
            token_info = self._idp.get_token_set()
            # Schedule a refresh of the token before it expires
            self._schedule_refresh(token_info["expires_in"])
            # Trigger the lifecycle callback
            self._callbacks.process(self.idp_ready, self._loop)

        # Get the access token
        token = getattr(self._idp, "access_token", None)

        # Connect the broker for exchanging normal I4.0 messages
        if self._msg_broker:
            self._msg_broker.connect(token=token)
            # Trigger the lifecycle callback after the message broker is ready
            self._msg_broker.add_on_channel_open_callback(
                lambda *_: self._callbacks.process(self.message_broker_ready, self._loop),
                one_shot=True,
                is_async=False,
            )

            self._msg_broker.add_on_connection_error_callback(
                self._reconnect_to_s3i,
                True,
                True,
                delay=RECONNECT_DELAY,
                error="Disconnected from S3I Message Broker, trying to reconnect ...",
            )

            self._msg_broker.add_on_channel_close_callback(
                self._reconnect_to_s3i,
                True,
                True,
                delay=RECONNECT_DELAY,
                error="Disconnected from S3I Message Broker, trying to reconnect ...",
            )

        # Connect the broker for exchanging events
        if self._evt_broker:
            self._evt_broker.connect(token=token)
            # Trigger the lifecycle callback after the event broker is ready
            self._callbacks.process(self.event_broker_ready, self._loop)

            self._evt_broker.add_on_connection_error_callback(
                self._reconnect_to_s3i,
                True,
                True,
                delay=RECONNECT_DELAY,
                error="Disconnected from S3I Event Broker, trying to reconnect ...",
            )

            self._evt_broker.add_on_connection_close_callback(
                self._reconnect_to_s3i,
                True,
                True,
                delay=RECONNECT_DELAY,
                error="Disconnected from S3I Event Broker, trying to reconnect ...",
            )

    def _schedule_refresh(self, expires: int) -> None:
        """
        Schedule a token refresh before it expires.

        Calculates a delay based on the token's expiration time and schedules
        the _refresh_token method to be called after the delay. The delay is
        set to 90% of the expiration time, with a minimum of 60 seconds.

        :param expires: The expiration time of the token in seconds
        """

        delay = max(int(expires * 0.9), 60)
        self._loop.call_later(delay, self._refresh_token)

    def _refresh_token(self) -> None:
        """
        Refresh the authentication token and update the broker.

        This method attempts to refresh the token using the identity provider,
        reconnects the message broker with the new token, and schedules the next
        token refresh. If any step fails, an error is logged.

        :raises Exception: If the token refresh or reconnection fails.
        """

        try:
            self._idp.refresh_token_set()  
            self._msg_broker.reconnect_with_new_token(self._idp.access_token)
            if self._evt_broker:
                self._evt_broker.reconnect_with_new_token(self._idp.access_token)
            self._callbacks.process(self.token_refreshed, self._loop)
            self._schedule_refresh(self._idp.token_set["expires_in"])
        except Exception as e:
            self._logger.error("Token refresh failed: %s", e)

    async def _reconnect_to_s3i(self, delay, error=None,):
        """
        Reconnect to S3I services after a disconnection.

        This method closes any open broker channels and connections, sets the
        connector status to disconnected, and initiates the reconnection process
        after a specified delay. It handles logging of the reconnection attempt
        and ensures that only one reconnection process is active at a time.

        :param delay: The time in seconds to wait before attempting to reconnect.
        :param error: An optional error message to log, indicating the reason for reconnection.
        """
        if self.connected:
            self._logger.info("Already Connected")
            return
        else:
            if self.__reconnecting:
                self._logger.info("Already in reconnecting with S3I")
            else:
                self._logger.warning("Reconnecting to S3I")
                self.__reconnecting = True

                try:
                    if self._msg_broker:
                        if self._msg_broker.channel.is_open:
                            self._logger.warning("Closing Msg Broker Channel")
                            self._msg_broker.channel.close()
                        if self._msg_broker.connection.is_open:
                            self._logger.warning("Closing Msg Broker Connection")
                            self._msg_broker.connection.close()
                    if self._evt_broker:
                        if self._evt_broker.channel.is_open:
                            self._logger.warning("Closing Event Broker Channel")
                            self._evt_broker.channel.close()
                        if self._evt_broker.connection.is_open:
                            self._logger.warning("Closing Event Broker Connection")
                            self._evt_broker.connection.close()
                except Exception as e:
                    self._logger.error(f"{e}")

                if error:
                    self._logger.error(f"Due to {error}, reconnect to s3i in {delay} seconds")
                else:
                    self._logger.error(f"Reconnect to s3i in {delay} seconds")
                await asyncio.sleep(delay=delay)
                try:
                    self._idp.get_token_set()
                    if self._msg_broker:
                        self._msg_broker.connect(token=self._idp.access_token)
                    if self._evt_broker:
                        self._evt_broker.connect(token=self._idp.access_token)
                except Exception as e:
                    self._logger.error(f"{e}")
                finally:
                    self.__reconnecting = False

        # check again and reconnect
        if self.connected == False:
            self._loop.call_later(RECONNECT_INTERVAL, self._loop.create_task, self._reconnect_to_s3i(delay=RECONNECT_DELAY))

    def _on_message(self, ch, method, props, body: bytes) -> None:
        """
        Message callback for the broker.

        Handles incoming messages from the broker, converts them to
        I40Message objects and dispatches them to the appropriate handler.

        :param ch: Channel object
        :param method: Delivery method
        :param props: Message properties
        :param body: Message body as bytes
        """
        try:
            msg = json.loads(body)
            frame = Frame.from_json(msg[I40MessageKeys.frame])
            self.__check_protocol_validity(frame)
            if frame.type == I40MessageType.request:
                if I40MessageSemanticProtocols.invoke_operation_sync == frame.semanticProtocol:
                    i40_msg = I40InvokeOperationSyncRequest.from_json(data=msg)
                elif I40MessageSemanticProtocols.invoke_operation_async == frame.semanticProtocol:
                    i40_msg = I40InvokeOperationAsyncRequest.from_json(data=msg)
                elif I40MessageSemanticProtocols.get_submodel_element_by_path == frame.semanticProtocol:
                    i40_msg = I40GetSubmodelElementByPathRequest.from_json(data=msg)
                else:
                    raise ValueError(f"Message Type not supported: {frame.semanticProtocol}")
                task = self._handle_request(i40_msg)
            elif frame.type == I40MessageType.reply:
                if I40MessageSemanticProtocols.invoke_operation_sync == frame.semanticProtocol:
                    i40_msg = I40InvokeOperationSyncReply.from_json(data=msg)
                elif I40MessageSemanticProtocols.invoke_operation_async == frame.semanticProtocol:
                    i40_msg = I40InvokeOperationAsyncReply.from_json(data=msg)
                elif I40MessageSemanticProtocols.get_submodel_element_by_path == frame.semanticProtocol:
                    i40_msg = I40GetSubmodelElementByPathReply.from_json(data=msg)
                else:
                    raise ValueError(f"Message Type not supported: {frame.semanticProtocol}")
                task = self._handle_reply(i40_msg)
            else:
                raise ValueError(f"Unsupported message type: {frame.type}")
            asyncio.create_task(task)
        except Exception as e:
            self._logger.error("Failed to process message: %s", e)

    async def _handle_request(
        self,
        i40_message_req: Union[
            I40GetSubmodelElementByPathRequest,
            I40InvokeOperationSyncRequest,
            I40InvokeOperationAsyncRequest,
        ],
    ) -> None:
        """
        Handle incoming request messages from the broker.

        Converts the incoming message to an I40Message and dispatches it to the
        handler. If the handler returns a reply, sends it back to the message
        broker.

        :param frame: Frame of the incoming message
        :param msg: Message body as a dictionary
        :return:
        """
        reply = await self._handler.handle_request(i40_message_req)
        if reply.frame.receiver:
            self._msg_broker.send(msg=reply.to_json(), binding=reply.frame.receiver.identification)

    async def _handle_reply(self, i40_message_reply: Union[
            I40GetSubmodelElementByPathReply,
            I40InvokeOperationSyncReply,
            I40InvokeOperationAsyncReply,
        ]) -> None:
        """
        Handle incoming reply messages from the broker.

        Converts the incoming message to an I40Message and dispatches it to the
        handler.

        :param frame: Frame of the incoming message
        :param msg: Message body as a dictionary
        :return:
        """

        if i40_message_reply.frame.inReplyTo in self._pending_requests:
            self._pending_requests[i40_message_reply.frame.inReplyTo].set_result(i40_message_reply)

        await self._handler.handle_reply(i40_message_reply)

    def send_request(self, request: I40Message) -> asyncio.Future:
        """
        Send request and return future for reply.

        The returned future is resolved when the reply to the request is
        received. If the reply is not received within the correlation
        id's timeout, the future is cancelled.
        """
        fut = self._loop.create_future()
        self._pending_requests[request.frame.messageId] = fut
        if request.frame.receiver:
            # Send the request to the message broker
            self._msg_broker.send(msg=request.to_json(), binding=request.frame.receiver.identification)
        else:
            self._logger.error("Request has no receiver")
        return fut

    def _on_event(self, ch, method, props, body: bytes) -> None:
        """
        Handle incoming event messages from the broker.

        Converts the incoming message to an I40Message and dispatches it to the
        handler.

        :param ch: Channel object
        :param method: Method object
        :param props: Properties object
        :param body: Message body as a bytes object
        :return: None
        """

        try:
            msg = json.loads(body)
            frame = Frame.from_json(msg[I40MessageKeys.frame])
            self.__check_protocol_validity(frame)
            if frame.type == I40MessageType.event:
                event_message = I40EventMessage.from_json(msg)
                asyncio.create_task(self._handle_event(i40_event=event_message))
        except Exception as e:
            self._logger.error("Failed to process event: %s", e)

    async def _handle_event(self, i40_event: I40EventMessage):
        await self._handler.handle_event(i40_event)

    def disconnect(self) -> None:
        """
        Stop consuming from broker.

        Stops consuming from the broker, closing the connection for exchanging normal I4.0 messages or events.
        """
        self._idp.disconnect()
        if self._msg_broker:
            # Stop consuming from the message broker
            self._msg_broker.stop_consuming()
        if self._evt_broker:
            # Stop consuming from the event broker
            self._evt_broker.stop_consuming()

    def __check_protocol_validity(self, frame):
        """
        Validate the semantic protocol of the given frame.

        Checks if the `semanticProtocol` of the provided `frame` is among
        the supported protocols. Raises a ValueError if the protocol is unsupported.

        :param frame: The frame whose protocol is to be validated.
        :raises ValueError: If the `semanticProtocol` is not supported.
        """

        supported_protocol = [
            I40MessageSemanticProtocols.invoke_operation_async,
            I40MessageSemanticProtocols.invoke_operation_sync,
            I40MessageSemanticProtocols.get_submodel_element_by_path,
            I40MessageSemanticProtocols.event
        ]
        if frame.semanticProtocol not in supported_protocol:
            raise ValueError(f"Unsupported protocol: {frame.semanticProtocol}")

    def remove_pending_request(self, future) -> None:
        """
        Remove a future from the list of pending requests.
        This prevents a future from receiving a response and executing its done callbacks.
        :param future: An asyncio future from the send_request_async method
        """
        for message_id, reply_future in self._pending_requests.items():
            if future is reply_future:
                del self._pending_requests[message_id]
                break
