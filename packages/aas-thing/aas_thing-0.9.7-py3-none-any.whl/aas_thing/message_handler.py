import logging
from typing import Callable, Dict, Iterable, Union

from aas_python_http_client import SubmodelElementCollection
from basyx.aas import model
from basyx.aas.model import SubmodelElement, Property

from aas_thing.aas_connection import AASAPI, SubmodelAPI
from aas_thing.s3i.message import (
    I40Message,
    I40EventMessage,
    I40GetSubmodelElementByPathRequest,
    I40InvokeOperationSyncRequest,
    I40InvokeOperationAsyncRequest,
    I40GetSubmodelElementByPathReply,
    I40InvokeOperationSyncReply,
    I40InvokeOperationAsyncReply,
)
from aas_thing.s3i.message.frame import Requester, Replier, Emitter 
from aas_thing.s3i.message.frame import Frame, ConversationPartner, Role

from aas_thing.s3i.message.reference import (
    I40MessageType,
    I40MessageStatusCode,
    I40ResultMessageType,
    I40MessageExecutionState,
    I40MessageSuccess,
    I40MessageSemanticProtocols, I40MessageConversationRole,
)

from aas_thing.s3i.message.model import (
    StatusCode, Payload, Text, Message, MessageType, Result, Success, OutputArguments, ExecutionState)


class I40SemanticProtocolHandler:
    """
    Base class for message handling
    with lifecycle callbacks.
    Basic usage:
    
    .. code-block:: python

        handler = I40SemanticProtocolHandler(aas, submodels, logger)
        handler.register_operation(submodel_id, path, callback)
        handler.register_reply_handler(correlation_id, callback)
    """
    def __init__(
        self,
        aas: model.AssetAdministrationShell,
        submodels: Iterable[model.Submodel],
        logger: logging.Logger
    )-> None:
        """
        Initialize the handler for semantic protocols.

        :param aas: The Asset Administration Shell.
        :param submodels: The Submodels.
        :param logger: The logger.
        :raises KeyError: If a Submodel or an Operation could not be found.
        """
        self._aas_api = AASAPI(aas)
        self._submodel_apis: Dict[str, SubmodelAPI] = {
            sm.id: SubmodelAPI(sm) for sm in submodels
        }
        self._operation_handlers: Dict[str, Dict[str, Callable]] = {}
        self._reply_handlers: Dict[str, Callable] = {}
        self._event_handlers: Dict[str, Callable] = {}
        self.__logger = logger

    def register_operation_handler(
        self,
        submodel_id: str,
        operation_id: str,
        handler: Callable,
    ) -> None:
        """Register a handler for a synchronous/asynchronous operation.

        :param submodel_id: The ID of the Submodel.
        :param operation_id: The ID of the Operation.
        :param handler: The handler function. It should take a single argument of type I40Message which is the request message.
        :raises KeyError: If the Submodel or the Operation could not be found.
        """
        _sm_api = self._submodel_apis.get(submodel_id, None)
        if _sm_api is None:
            raise KeyError(f"Submodel '{submodel_id}' not found")

        _operation = _sm_api.get_submodel_element_by_path(path=operation_id)
        if operation_id is None:
            raise KeyError(f"Operation '{operation_id}' in Submodel '{submodel_id}' not found")
        # Store the handler in the dictionary
        self._operation_handlers.setdefault(submodel_id, {})[operation_id] = handler

    def register_reply_handler(
        self,
        correlation_id: str,
        handler: Callable,
    ) -> None:
        """
        Register a handler for an asynchronous reply.

        This handler must be implemented with the reply message as input, e.g., def handler(reply: I40Message).
        
        :param correlation_id: The correlation ID (i.e., messageId) for the reply message.
        :param handler: The handler function that processes the reply message.
        """
        # Store the handler in the dictionary with the correlation ID as the key
        self._reply_handlers[correlation_id] = handler

    def register_event_handler(
        self,
        topic: str,
        handler: Callable,
    ) -> None:
        """
        Register a handler for an event.

        This handler must be implemented with the event message as input (def handler(reply: I40EventMessage)).
        
        :param topic: The topic of the respective source BasicEventElement of the I40EventMessage.
        :param handler: The handler function that processes the event message.
        """
        # Store the handler in the dictionary with the topic as the key
        self._event_handlers[topic] = handler

    async def handle_request(
        self,
        request: Union[
            I40GetSubmodelElementByPathRequest,
            I40InvokeOperationSyncRequest,
            I40InvokeOperationAsyncRequest,
        ]
    ) -> I40Message:
        """
        Dispatch incoming I4.0 requests.
        Currently, only invoke operation async and sync, and get submodel element by path are supported.

        :param request: The request message.
        :return: The response message.
        """
        self.__logger.info(
            f"Handling request {type(request).__name__} from {request.frame.sender.identification}"
        )

        # Handle GetSubmodelElementByPath requests
        if request.frame.semanticProtocol == I40MessageSemanticProtocols.get_submodel_element_by_path:
            return self._handle_get_submodel_element_by_path(request)

        # Handle synchronous operation invocations
        elif request.frame.semanticProtocol == I40MessageSemanticProtocols.invoke_operation_sync:
            return self._handle_invoke_sync(request)

        # Handle asynchronous operation invocations
        elif request.frame.semanticProtocol == I40MessageSemanticProtocols.invoke_operation_async:
            return await self._handle_invoke_async(request)

    async def handle_reply(
        self,
        reply: Union[
            I40GetSubmodelElementByPathReply,
            I40InvokeOperationSyncReply,
            I40InvokeOperationAsyncReply,
        ]) -> None:
        """
        Dispatch incoming I4.0 replies.

        This function calls the registered handler for the reply message. If
        no handler is found, a warning is logged.
        """
        corr_id = reply.frame.inReplyTo
        self.__logger.info(f"Received a reply {corr_id}")

        # Search for the status code in the interaction elements
        status_code = None
        for el in reply.interactionElements:
            if el.id_short == "statusCode":
                status_code = el.value
        if status_code is None:
            raise ValueError("Missing 'statusCode'")
        else:
            self.__logger.info(f"Reply {corr_id} has a status code {status_code}")

        # Call the registered handler for the reply
        handler = self._reply_handlers.get(corr_id)
        if not handler:
            self.__logger.warning(f"No handler registered for reply {corr_id}")
            return
        handler(reply)

    async def handle_event(
        self,
        event: I40EventMessage) -> None:
        """
        Dispatch incoming I4.0 events.

        This function calls the registered handler for the event message. If
        no handler is found, a warning is logged.
        """
        topic = event._topic
        self.__logger.info(f"Received a event {topic}")

        # Call the registered handler for the event
        handler = self._event_handlers.get(topic)
        if not handler:
            self.__logger.warning(f"No handler registered for event {topic}")
            return
        handler(event)

    def _handle_get_submodel_element_by_path(
        self, request: I40GetSubmodelElementByPathRequest
    ) -> I40Message:
        """Handle GetSubmodelElementByPath requests.

        This function handles incoming GetSubmodelElementByPath requests. It
        checks if the request is valid and if the Submodel and the path can be
        found in the Submodel API. If the request is invalid or the Submodel and
        path cannot be found, an error interaction element is created. If the
        request is valid, the Submodel element is obtained from the Submodel API
        and an interaction element with the status code and the payload is
        created. The function then returns an I40Message with the created
        interaction elements.

        :param request: The incoming request message.
        :return: The response message.
        """
        if not request._submodel_id or not request._path:
            return I40GetSubmodelElementByPathReply.create_error(
                sender=request.frame.receiver.identification,
                receiver=request.frame.sender.identification,
                inReplyTo=request.frame.messageId,
                statusCode=I40MessageStatusCode.client_error_bad_request,
                messageType=I40ResultMessageType.error,
                text="submodel id or path not found",
            )

        else:
            try:
                api = self._submodel_apis.get(request._submodel_id)
                element = api.get_submodel_element_by_path(request._path)
                element.parent = None
                return I40GetSubmodelElementByPathReply.create_success(
                    sender=request.frame.receiver.identification,
                    receiver=request.frame.sender.identification,
                    inReplyTo=request.frame.messageId,
                    submodelElement=element,
                    statusCode=I40MessageStatusCode.success
                )
            except Exception as e:
                return I40GetSubmodelElementByPathReply.create_error(
                sender=request.frame.receiver.identification,
                receiver=request.frame.sender.identification,
                inReplyTo=request.frame.messageId,
                statusCode=I40MessageStatusCode.client_error_resource_not_found,
                messageType=I40ResultMessageType.error,
                text="SubmodelElement not found",
            )

    def _handle_invoke_sync(
        self, request: I40InvokeOperationSyncRequest
    ) -> I40Message:
        """Handle synchronous InvokeOperation requests.

        This function handles incoming synchronous InvokeOperation requests. It
        checks if the request is valid and if the Submodel and the path can be
        found in the Submodel and operation handler APIs. If the request is
        invalid or the Submodel and path cannot be found, an error interaction
        element is created. If the request is valid, the operation is invoked
        with the input arguments from the request and the result is used to
        create a success interaction element. The function then returns an
        I40Message with the created interaction elements.
        """
        if not request._submodel_id or not request._path:
            return I40InvokeOperationSyncReply.create_error(
                sender=request.frame.receiver.identification,
                receiver=request.frame.sender.identification,
                inReplyTo=request.frame.messageId,
                statusCode=I40MessageStatusCode.client_error_bad_request,
                messageType=I40ResultMessageType.error,
                text="submodel id or path not found"
            )

        else:
            # Get the operation handler for the submodel and path
            handler = self._operation_handlers[request._submodel_id][request._path]

            # If the operation handler is not found, create an error interaction element
            if handler is None:
                return I40InvokeOperationSyncReply.create_error(
                    sender=request.frame.receiver.identification,
                    receiver=request.frame.sender.identification,
                    inReplyTo=request.frame.messageId,
                    statusCode=I40MessageStatusCode.client_error_resource_not_found,
                    messageType=I40ResultMessageType.error,
                    text="Operation not registered",
                )
            else:
                # Invoke the operation with the input arguments from the request
                result = handler(**request._input_map)

                return I40InvokeOperationSyncReply.create_success(
                    sender=request.frame.receiver.identification,
                    receiver=request.frame.sender.identification,
                    inReplyTo=request.frame.messageId,
                    outputMap=result,
                    statusCode=I40MessageStatusCode.success,
                    executionState=I40MessageExecutionState.completed
                )

    async def _handle_invoke_async(
            self, request: I40InvokeOperationAsyncRequest
    ) -> I40Message:
        """
        Handle asynchronous InvokeOperation requests.

        This function processes incoming asynchronous InvokeOperation requests.
        It checks the validity of the request, finds the appropriate operation
        handler, and invokes it with the input arguments. The result is used to
        create interaction elements for the reply message.

        :param request: The incoming request message.
        :return: The response message with interaction elements.
        """
        # Check if the request contains necessary identifiers
        if not request._submodel_id or not request._path:
            return I40InvokeOperationAsyncReply.create_error(
                sender=request.frame.receiver.identification,
                receiver=request.frame.sender.identification,
                inReplyTo=request.frame.messageId,
                statusCode=I40MessageStatusCode.client_error_bad_request,
                messageType=I40ResultMessageType.error,
                text="submodel id or path not found",
            )
        else:
            # Retrieve the operation handler for the given submodel and path
            handler = self._operation_handlers[request._submodel_id][request._path]
            if handler is None:
                return I40InvokeOperationAsyncReply.create_error(
                    sender=request.frame.receiver.identification,
                    receiver=request.frame.sender.identification,
                    inReplyTo=request.frame.messageId,
                    statusCode=I40MessageStatusCode.client_error_resource_not_found,
                    messageType=I40ResultMessageType.error,
                    text="Operation not registered",
                )
            else:
                # Invoke the operation handler asynchronously with input arguments
                result = await handler(**request._input_map)  # result must be output map format
                
                return I40InvokeOperationAsyncReply.create_success(
                    sender=request.frame.receiver.identification,
                    receiver=request.frame.sender.identification,
                    inReplyTo=request.frame.messageId,
                    outputMap=result,
                    statusCode=I40MessageStatusCode.success,
                    executionState=I40MessageExecutionState.completed
                )

    def _build_frame_from_request(self,
                                  request: I40Message
                                  ) -> Frame:
        """
        Build a Frame for a reply message from an incoming request.

        :param request: The incoming request message.
        :return: A Frame for the reply message.
        """
        return Frame(
            semanticProtocol=request.frame.semanticProtocol,
            type=I40MessageType.reply,
            sender=ConversationPartner(identification=request.frame.receiver.identification, role=Role(name=I40MessageConversationRole.replier)),
            receiver=ConversationPartner(identification=request.frame.sender.identification, role=Role(name=I40MessageConversationRole.requester)),
            inReplyTo=request.frame.messageId
        )

    def _build_error_interaction_element(
            self,
            request: I40Message,
            status_code_value: I40MessageStatusCode,
            error_text: str
    ) -> Iterable[Union[Property, SubmodelElementCollection]]:
        """
        Build a generic error reply with a status code, message type, and text.

        :param request: The incoming request message.
        :param status_code_value: The status code value.
        :param error_text: The error message text.
        :return: A list of interaction elements for the error reply message.
        """
        status_code = StatusCode(
            semantic_id=I40MessageSemanticProtocols.invoke_operation_async_status_code,
            value=status_code_value
        )

        # Build the message interaction element
        message_type = MessageType(
            semantic_id=I40MessageSemanticProtocols.invoke_operation_async_message_type,
            value=I40ResultMessageType.error
        )
        text = Text(
            semantic_id=I40MessageSemanticProtocols.invoke_operation_async_text,
            value=error_text
        )
        message = Message(
            semantic_id=I40MessageSemanticProtocols.invoke_operation_async_message,
            value=(message_type, text)
        )

        # Build the result interaction element
        result = Result(
            semantic_id=I40MessageSemanticProtocols.invoke_operation_async_result,
            value=(message,)
        )

        # Build the payload interaction element
        payload = Payload(
            semantic_id=I40MessageSemanticProtocols.invoke_operation_async_payload,
            value=(result,)
        )

        return [status_code, payload]

    def _build_success_operation_interaction_element_for_reply(self, output_map: dict[str, SubmodelElement])\
            -> Iterable[Union[Property, SubmodelElementCollection]]:

        """
        Build interaction elements for a successful operation reply message.

        This function constructs a list of interaction elements to be included in a
        reply message indicating a successful operation execution. It creates a status
        code, success flag, execution state, and output arguments based on the provided
        output map.

        :param output_map: A dictionary mapping output argument names to SubmodelElement
                        instances representing the results of the operation.
        :return: A list of interaction elements including the status code and payload
                for the success response message.
        """

        status_code = StatusCode(
            semantic_id=I40MessageSemanticProtocols.invoke_operation_async_status_code,
            value=I40MessageStatusCode.success
        )
        success = Success(
            semantic_id=I40MessageSemanticProtocols.invoke_operation_async_success,
            value=I40MessageSuccess.true
        )
        execution_state = ExecutionState(
            semantic_id=I40MessageSemanticProtocols.invoke_operation_async_execution_state,
            value=I40MessageExecutionState.completed
        )

        output_argument = OutputArguments(
            semantic_id=I40MessageSemanticProtocols.invoke_operation_async_output_arguments,
            value=tuple(output_map.values())
        )
        payload = Payload(
            semantic_id=I40MessageSemanticProtocols.invoke_operation_async_payload,
            value=(success, execution_state, output_argument)
        )

        return [status_code, payload]