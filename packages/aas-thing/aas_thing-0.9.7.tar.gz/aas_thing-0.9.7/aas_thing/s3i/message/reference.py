from basyx.aas.model import Key, KeyTypes, ExternalReference
from enum import Enum, IntEnum


class I40MessageKeys(str, Enum):
    """
    Enumeration of possible keys in an I40Message.

    Provides a type-safe way to access the various parts of an I40Message.

    :cvar frame:               Key for the message 'frame'.
    :cvar interaction_elements: Key for 'interactionElements'.
    :cvar semantic_protocol:   Key for 'semanticProtocol'.
    :cvar type:                Key for 'type' (message type).
    :cvar message_id:          Key for 'messageId'.
    :cvar sender:              Key for 'sender'.
    :cvar receiver:            Key for 'receiver'.
    :cvar in_reply_to:         Key for 'inReplyTo'.
    :cvar reply_by:            Key for 'replyBy'.
    :cvar conversation_id:     Key for 'conversationId'.
    :cvar identification:      Key for 'identification'.
    :cvar role:                Key for 'role'.
    :cvar name:                Key for 'name'.
    :cvar value:               Key for 'value'.
    :cvar keys:                Key for nested 'keys'.
    :cvar id_short:            Key for 'idShort'.
    :cvar semantic_id:         Key for 'semanticId'.
    :cvar model_type:          Key for 'modelType'.
    :cvar value_type:          Key for 'valueType'.
    """

    frame = "frame"
    interaction_elements = "interactionElements"
    semantic_protocol = "semanticProtocol"
    type = "type"
    message_id = "messageId"
    sender = "sender"
    receiver = "receiver"
    in_reply_to = "inReplyTo"
    reply_by = "replyBy"
    conversation_id = "conversationId"
    identification = "identification"
    role = "role"
    name = "name"
    value = "value"
    keys = "keys"
    id_short = "idShort"
    semantic_id = "semanticId"
    model_type = "modelType"
    value_type = "valueType"

class I40MessageGlobalReferenceValues:
    """
    This class contains global reference values used in the I4.0 messaging protocol.
    It provides key strings for the I4.0 messaging protocol, which are used to identify
    the semantic meaning of the data in the message.
    """
    
    invoke_operation_sync = "https://admin-shell.io/aas/API/InvokeOperationSync/3/0"
    invoke_operation_async = "https://admin-shell.io/aas/API/InvokeOperationAsync/3/0"
    invoke_operation_sync_submodel_id = "https://admin-shell.io/aas/API/InvokeOperationSync/submodelId/3/0"
    invoke_operation_async_submodel_id = "https://admin-shell.io/aas/API/InvokeOperationAsync/submodelId/3/0"
    invoke_operation_sync_path = "https://admin-shell.io/aas/API/InvokeOperationSync/path/3/0"
    invoke_operation_async_path = "https://admin-shell.io/aas/API/InvokeOperationAsync/path/3/0"
    invoke_operation_sync_input_arguments = "https://admin-shell.io/aas/API/InvokeOperationSync/inputArguments/3/0"
    invoke_operation_async_input_arguments = "https://admin-shell.io/aas/API/InvokeOperationAsync/inputArguments/3/0"
    invoke_operation_sync_status_code = "https://admin-shell.io/aas/API/InvokeOperationSync/statusCode/3/0"
    invoke_operation_async_status_code = "https://admin-shell.io/aas/API/InvokeOperationAsync/statusCode/3/0"
    invoke_operation_sync_payload = "https://admin-shell.io/aas/API/InvokeOperationSync/payload/3/0"
    invoke_operation_async_payload = "https://admin-shell.io/aas/API/InvokeOperationAsync/payload/3/0"
    invoke_operation_sync_output_arguments = "https://admin-shell.io/aas/API/InvokeOperationSync/outputArguments/3/0"
    invoke_operation_async_output_arguments = "https://admin-shell.io/aas/API/InvokeOperationAsync/outputArguments/3/0"
    invoke_operation_sync_execution_state = "https://admin-shell.io/aas/API/InvokeOperationSync/executionState/3/0"
    invoke_operation_async_execution_state = "https://admin-shell.io/aas/API/InvokeOperationAsync/executionState/3/0"
    invoke_operation_sync_success = "https://admin-shell.io/aas/API/InvokeOperationSync/success/3/0"
    invoke_operation_async_success = "https://admin-shell.io/aas/API/InvokeOperationAsync/success/3/0"
    result = "https://admin-shell.io/aas/API/DataTypes/Result/3/0"
    message = "https://admin-shell.io/aas/API/DataTypes/Message/3/0"
    message_type = "https://admin-shell.io/aas/API/DataTypes/Message/messageType/3/0"
    text = "https://admin-shell.io/aas/API/DataTypes/Message/text/3/0"
    get_submodel = "https://admin-shell.io/aas/API/GetSubmodel/3/0"
    get_submodel_element_by_path = "https://admin-shell.io/aas/API/GetSubmodelElementByPath/3/0"
    get_submodel_element_by_path_submodel_id = "https://admin-shell.io/aas/API/GetSubmodelElementByPath/submodelId/3/0"
    get_submodel_element_by_path_path = "https://admin-shell.io/aas/API/GetSubmodelElementByPath/path/3/0"
    get_submodel_element_by_path_status_code = "https://admin-shell.io/aas/API/GetSubmodelElementByPath/statusCode/3/0"
    get_submodel_element_by_path_payload = "https://admin-shell.io/aas/API/GetSubmodelElementByPath/payload/3/0"
    event_message = "https://admin-shell.io/aas/3/0/EventPayload"
    event_message_source = "https://admin-shell.io/aas/3/0/EventPayload/source"
    event_message_source_semantic_id = "https://admin-shell.io/aas/3/0/EventPayload/sourceSemanticId"
    event_message_observable_reference = "https://admin-shell.io/aas/3/0/EventPayload/observableReference"
    event_message_observable_semantic_id = "https://admin-shell.io/aas/3/0/EventPayload/observableSemanticId"
    event_message_topic = "https://admin-shell.io/aas/3/0/EventPayload/topic"
    event_message_timestamp = "https://admin-shell.io/aas/3/0/EventPayload/timestamp"
    event_message_payload = "https://admin-shell.io/aas/3/0/EventPayload/payload"

class I40MessageGlobalReferenceKeys:
    """
    Contains all global reference keys used in i40 messages.

    This class contains all global reference keys used in i40 messages.
    The keys are used to identify the semantic meaning of a submodel element in an i40 message.
    """
    invoke_operation_sync = Key(type_=KeyTypes.GLOBAL_REFERENCE,
                                value=I40MessageGlobalReferenceValues.invoke_operation_sync)

    invoke_operation_async = Key(type_=KeyTypes.GLOBAL_REFERENCE,
                                 value=I40MessageGlobalReferenceValues.invoke_operation_async)

    invoke_operation_sync_submodel_id = Key(type_=KeyTypes.GLOBAL_REFERENCE,
                                            value=I40MessageGlobalReferenceValues.invoke_operation_sync_submodel_id)

    invoke_operation_async_submodel_id = Key(type_=KeyTypes.GLOBAL_REFERENCE,
                                             value=I40MessageGlobalReferenceValues.invoke_operation_async_submodel_id)

    invoke_operation_sync_path = Key(type_=KeyTypes.GLOBAL_REFERENCE,
                                     value=I40MessageGlobalReferenceValues.invoke_operation_sync_path)

    invoke_operation_async_path = Key(type_=KeyTypes.GLOBAL_REFERENCE,
                                      value=I40MessageGlobalReferenceValues.invoke_operation_async_path)

    invoke_operation_sync_input_arguments = Key(type_=KeyTypes.GLOBAL_REFERENCE,
                                               value=I40MessageGlobalReferenceValues.invoke_operation_sync_input_arguments)

    invoke_operation_async_input_arguments = Key(type_=KeyTypes.GLOBAL_REFERENCE,
                                                value=I40MessageGlobalReferenceValues.invoke_operation_async_input_arguments)

    invoke_operation_sync_status_code = Key(type_=KeyTypes.GLOBAL_REFERENCE,
                                            value=I40MessageGlobalReferenceValues.invoke_operation_sync_status_code)

    invoke_operation_async_status_code = Key(type_=KeyTypes.GLOBAL_REFERENCE,
                                             value=I40MessageGlobalReferenceValues.invoke_operation_async_status_code)

    invoke_operation_sync_payload = Key(type_=KeyTypes.GLOBAL_REFERENCE,
                                        value=I40MessageGlobalReferenceValues.invoke_operation_sync_payload)

    invoke_operation_async_payload = Key(type_=KeyTypes.GLOBAL_REFERENCE,
                                         value=I40MessageGlobalReferenceValues.invoke_operation_async_payload)

    invoke_operation_sync_output_arguments = Key(type_=KeyTypes.GLOBAL_REFERENCE,
                                                value=I40MessageGlobalReferenceValues.invoke_operation_sync_output_arguments)

    invoke_operation_async_output_arguments = Key(type_=KeyTypes.GLOBAL_REFERENCE,
                                                 value=I40MessageGlobalReferenceValues.invoke_operation_async_output_arguments)

    invoke_operation_sync_execution_state = Key(type_=KeyTypes.GLOBAL_REFERENCE,
                                                value=I40MessageGlobalReferenceValues.invoke_operation_sync_execution_state)

    invoke_operation_async_execution_state = Key(type_=KeyTypes.GLOBAL_REFERENCE,
                                                 value=I40MessageGlobalReferenceValues.invoke_operation_async_execution_state)

    invoke_operation_sync_success = Key(type_=KeyTypes.GLOBAL_REFERENCE,
                                        value=I40MessageGlobalReferenceValues.invoke_operation_sync_success)

    invoke_operation_async_success = Key(type_=KeyTypes.GLOBAL_REFERENCE,
                                         value=I40MessageGlobalReferenceValues.invoke_operation_async_success)

    result = Key(type_=KeyTypes.GLOBAL_REFERENCE, value=I40MessageGlobalReferenceValues.result)

    message = Key(type_=KeyTypes.GLOBAL_REFERENCE, value=I40MessageGlobalReferenceValues.message)

    message_type = Key(type_=KeyTypes.GLOBAL_REFERENCE, value=I40MessageGlobalReferenceValues.message_type)

    text = Key(type_=KeyTypes.GLOBAL_REFERENCE, value=I40MessageGlobalReferenceValues.text)

    get_submodel_element_by_path = Key(type_=KeyTypes.GLOBAL_REFERENCE,
                                       value=I40MessageGlobalReferenceValues.get_submodel_element_by_path)

    get_submodel_element_by_path_submodel_id = Key(type_=KeyTypes.GLOBAL_REFERENCE,
                                                   value=I40MessageGlobalReferenceValues.get_submodel_element_by_path_submodel_id)

    get_submodel_element_by_path_path = Key(type_=KeyTypes.GLOBAL_REFERENCE,
                                            value=I40MessageGlobalReferenceValues.get_submodel_element_by_path_path)

    get_submodel_element_by_path_status_code = Key(type_=KeyTypes.GLOBAL_REFERENCE,
                                                   value=I40MessageGlobalReferenceValues.get_submodel_element_by_path_status_code)

    get_submodel_element_by_path_payload = Key(type_=KeyTypes.GLOBAL_REFERENCE,
                                               value=I40MessageGlobalReferenceValues.get_submodel_element_by_path_payload)
    
    event_message = Key(type_=KeyTypes.GLOBAL_REFERENCE, value=I40MessageGlobalReferenceValues.event_message)
    event_message_source = Key(type_=KeyTypes.GLOBAL_REFERENCE, value=I40MessageGlobalReferenceValues.event_message_source)
    event_message_source_semantic_id = Key(type_=KeyTypes.GLOBAL_REFERENCE, value=I40MessageGlobalReferenceValues.event_message_source_semantic_id)
    event_message_observable_reference = Key(type_=KeyTypes.GLOBAL_REFERENCE, value=I40MessageGlobalReferenceValues.event_message_observable_reference)
    event_message_observable_semantic_id = Key(type_=KeyTypes.GLOBAL_REFERENCE, value=I40MessageGlobalReferenceValues.event_message_observable_semantic_id)
    event_message_topic = Key(type_=KeyTypes.GLOBAL_REFERENCE, value=I40MessageGlobalReferenceValues.event_message_topic)
    event_message_timestamp = Key(type_=KeyTypes.GLOBAL_REFERENCE, value=I40MessageGlobalReferenceValues.event_message_timestamp)
    event_message_payload = Key(type_=KeyTypes.GLOBAL_REFERENCE, value=I40MessageGlobalReferenceValues.event_message_payload)

class I40MessageSemanticProtocols:
    """
    This class contains the I4.0 message semantic protocols used in the i40 messages.
    
    The semantic protocols are used to define the meaning of the data in the message.
    
    """
    invoke_operation_sync = ExternalReference(key=(I40MessageGlobalReferenceKeys.invoke_operation_sync,))
    invoke_operation_async = ExternalReference(key=(I40MessageGlobalReferenceKeys.invoke_operation_async,))

    invoke_operation_sync_request_submodel_id = ExternalReference(key=(I40MessageGlobalReferenceKeys.invoke_operation_sync_submodel_id,))
    invoke_operation_async_request_submodel_id = ExternalReference(key=(I40MessageGlobalReferenceKeys.invoke_operation_async_submodel_id,))

    invoke_operation_sync_request_path = ExternalReference(key=(I40MessageGlobalReferenceKeys.invoke_operation_sync_path,))
    invoke_operation_async_request_path = ExternalReference(key=(I40MessageGlobalReferenceKeys.invoke_operation_async_path,))

    invoke_operation_sync_request_input_arguments = ExternalReference(key=(I40MessageGlobalReferenceKeys.invoke_operation_sync_input_arguments,))
    invoke_operation_async_request_input_arguments = ExternalReference(key=(I40MessageGlobalReferenceKeys.invoke_operation_async_input_arguments,))

    invoke_operation_sync_status_code = ExternalReference(key=(I40MessageGlobalReferenceKeys.invoke_operation_sync_status_code,))
    invoke_operation_async_status_code = ExternalReference(key=(I40MessageGlobalReferenceKeys.invoke_operation_async_status_code,))

    invoke_operation_sync_execution_state = ExternalReference(key=(I40MessageGlobalReferenceKeys.invoke_operation_sync_execution_state,))   
    invoke_operation_async_execution_state = ExternalReference(key=(I40MessageGlobalReferenceKeys.invoke_operation_async_execution_state,))

    invoke_operation_sync_payload = ExternalReference(key=(I40MessageGlobalReferenceKeys.invoke_operation_sync_payload,))
    invoke_operation_async_payload = ExternalReference(key=(I40MessageGlobalReferenceKeys.invoke_operation_async_payload,))

    invoke_operation_sync_success = ExternalReference(key=(I40MessageGlobalReferenceKeys.invoke_operation_sync_success,))
    invoke_operation_async_success = ExternalReference(key=(I40MessageGlobalReferenceKeys.invoke_operation_async_success,))

    invoke_operation_sync_output_arguments = ExternalReference(key=(I40MessageGlobalReferenceKeys.invoke_operation_sync_output_arguments,))
    invoke_operation_async_output_arguments = ExternalReference(key=(I40MessageGlobalReferenceKeys.invoke_operation_async_output_arguments,))

    invoke_operation_sync_message_type = ExternalReference(key=(I40MessageGlobalReferenceKeys.message_type,))
    invoke_operation_async_message_type = ExternalReference(key=(I40MessageGlobalReferenceKeys.message_type,))

    invoke_operation_sync_message = ExternalReference(key=(I40MessageGlobalReferenceKeys.message, ))
    invoke_operation_async_message = ExternalReference(key=(I40MessageGlobalReferenceKeys.message, ))

    invoke_operation_sync_text = ExternalReference(key=(I40MessageGlobalReferenceKeys.text, ))
    invoke_operation_async_text = ExternalReference(key=(I40MessageGlobalReferenceKeys.text, ))

    invoke_operation_sync_result = ExternalReference(key=(I40MessageGlobalReferenceKeys.result, ))
    invoke_operation_async_result = ExternalReference(key=(I40MessageGlobalReferenceKeys.result, ))

    get_submodel_element_by_path = ExternalReference(key=(I40MessageGlobalReferenceKeys.get_submodel_element_by_path, ))
    get_submodel_element_by_path_submodel_id = ExternalReference(key=(I40MessageGlobalReferenceKeys.get_submodel_element_by_path_submodel_id, ))
    get_submodel_element_by_path_path = ExternalReference(key=(I40MessageGlobalReferenceKeys.get_submodel_element_by_path_path, ))
    get_submodel_element_by_path_status_code = ExternalReference(key=(I40MessageGlobalReferenceKeys.get_submodel_element_by_path_status_code, ))
    get_submodel_element_by_path_payload = ExternalReference(key=(I40MessageGlobalReferenceKeys.get_submodel_element_by_path_payload, ))
    get_submodel_element_by_path_result = ExternalReference(key=(I40MessageGlobalReferenceKeys.result, ))
    get_submodel_element_by_path_message_type = ExternalReference(key=(I40MessageGlobalReferenceKeys.message_type, ))
    get_submodel_element_by_path_message = ExternalReference(key=(I40MessageGlobalReferenceKeys.message, ))
    get_submodel_element_by_path_text = ExternalReference(key=(I40MessageGlobalReferenceKeys.text, ))

    event = ExternalReference(key=(I40MessageGlobalReferenceKeys.event_message, ))
    event_source = ExternalReference(key=(I40MessageGlobalReferenceKeys.event_message_source, ))
    event_source_semantic_id = ExternalReference(key=(I40MessageGlobalReferenceKeys.event_message_source_semantic_id, ))
    event_observable_reference = ExternalReference(key=(I40MessageGlobalReferenceKeys.event_message_observable_reference, ))
    event_observable_semantic_id = ExternalReference(key=(I40MessageGlobalReferenceKeys.event_message_observable_semantic_id, ))
    event_topic = ExternalReference(key=(I40MessageGlobalReferenceKeys.event_message_topic, ))
    event_timestamp = ExternalReference(key=(I40MessageGlobalReferenceKeys.event_message_timestamp, ))
    event_payload = ExternalReference(key=(I40MessageGlobalReferenceKeys.event_message_payload, ))


class I40MessageType(str, Enum):
    """
    This enumeration contains the possible message types of an i40 message.

    The message type is used to define the type of the message.
    The possible message types are:

    :cvar request: The message is a request.
    :cvar reply: The message is a reply to a request.
    :cvar event: The message is an event.

    """
    request = "request"
    reply   = "reply"
    event   = "event"

class I40MessageConversationRole(str, Enum):
    """
    This enumeration contains the possible conversation roles of an i40 message.

    The conversation role is used to define the role of the conversation partner in the conversation.
    The possible conversation roles are:

    :cvar requester: The conversation partner is the requester of the request.
    :cvar replier:   The conversation partner is the replier of the request.
    :cvar emitter:   The conversation partner is the emitter of the event.

    """
    requester  = "requester"
    replier = "replier"
    emitter = "emitter"

class I40MessageStatusCode(str, Enum):
    """
    This enumeration contains the possible status codes of an i40 message.

    The status code is used to indicate the status of the message processing.
    The possible status codes are:

    :cvar success: The message was processed successfully.
    :cvar success_created: The message was processed successfully and a new resource was created.
    :cvar success_accepted: The message was processed successfully and the processing is ongoing.
    :cvar success_no_content: The message was processed successfully but there is no content to return.
    :cvar client_error_bad_request: The message was processed but the request was bad.
    :cvar client_not_authorized: The message was processed but the requester is not authorized.
    :cvar client_forbidden: The message was processed but the requester is not allowed to access the resource.
    :cvar client_method_not_allowed: The message was processed but the method is not allowed.
    :cvar client_error_resource_not_found: The message was processed but the requested resource was not found.
    :cvar client_resource_conflict: The message was processed but the resource already exists.

    """
    success = "Success"
    success_created = "SuccessCreated"
    success_accepted = "SuccessAccepted"
    success_no_content = "SuccessNoContent"
    client_error_bad_request = "ClientErrorBadRequest"
    client_not_authorized = "ClientNotAuthorized"
    client_forbidden = "ClientForbidden"
    client_method_not_allowed = "ClientMethodNotAllowed"
    client_error_resource_not_found = "ClientErrorResourceNotFound"
    client_resource_conflict = "ClientResourceConflict"
    server_internal_error = "ServerInternalError"
    server_error_bad_gateway = "ServerErrorBadGateway"

class I40MessageSuccess(IntEnum):
    """
    This enumeration contains the possible values of the success flag of an i40 message.
    
    The success flag is used to indicate if the message was processed successfully.
    The possible values are:

    :cvar true: The message was processed successfully.
    :cvar false: The message was processed but there were errors.
    """
    true = 1
    false = 0

class I40MessageExecutionState(str, Enum):
    """
    This enumeration contains the possible values of the execution state of an i40 message.

    The execution state is used to indicate the current state of the message processing.
    The possible values are:

    :cvar initiated: The message processing has been initiated.
    :cvar running: The message processing is running.
    :cvar completed: The message processing has been completed.
    :cvar canceled: The message processing has been canceled.
    :cvar failed: The message processing has failed.
    :cvar timeout: The message processing has timed out.
    """
    initiated = "Initiated"
    running = "Running"
    completed = "Completed"
    canceled = "Canceled"
    failed = "Failed"
    timeout = "Timeout"

class I40ResultMessageType(str, Enum):
    """
    This enumeration contains the possible types of the result of an i40 message.

    The type of the result is used to indicate the type of the result of the message processing.
    The possible types are:
    
    :cvar info: The message contains additional information.
    :cvar warning: The message contains a warning.
    :cvar error: The message contains an error.
    :cvar exception: The message contains an exception.
    """
    info = "Info"
    warning = "Warning"
    error = "Error"
    exception = "Exception"
