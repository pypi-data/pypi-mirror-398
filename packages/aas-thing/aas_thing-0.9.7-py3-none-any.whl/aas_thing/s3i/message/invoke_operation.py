from code import interact
from email import message
from email.headerregistry import MessageIDHeader
from optparse import Option
from re import M
import stat
from typing import Dict, Optional, Any
from unittest import result
from basyx.aas.model import SubmodelElement
from aas_thing.s3i.message import frame
from aas_thing.s3i.message.message import I40Message
from aas_thing.s3i.message.frame import Frame, I40MessageType, ConversationPartner, Role , Requester, Replier
from aas_thing.s3i.message.model import StatusCode, Text
from aas_thing.s3i.message.model import MessageType, Text, Success, ExecutionState, SubmodelId, Path, InputArguments, Payload, OutputArguments, Message, Result
from aas_thing.s3i.message.reference import  I40MessageConversationRole, I40MessageSemanticProtocols, I40MessageExecutionState, I40MessageSuccess, I40MessageStatusCode, I40ResultMessageType
from abc import ABC
import uuid 
import json 

class I40InvokeOperationRequest(I40Message, ABC):

    def __init__(self,
                 submodelId: str,
                 operationIdShort: str,
                 sender: str,
                 receiver: str,
                 inputMap: Dict[str, SubmodelElement],
                 sync: bool,
                 messageId: Optional[str] = None,
                 conversationId: Optional[str] = None 
                 ):
        frame = Frame(
            semanticProtocol = I40MessageSemanticProtocols.invoke_operation_sync if sync else I40MessageSemanticProtocols.invoke_operation_async,
            type=I40MessageType.request,
            sender=Requester(identification=sender),
            receiver=Replier(identification=receiver),
            messageId=messageId if messageId is not None else str(uuid.uuid4()),
            conversationId=conversationId
        )
        submodel_id = SubmodelId(
            semantic_id=I40MessageSemanticProtocols.invoke_operation_sync_request_submodel_id if sync else I40MessageSemanticProtocols.invoke_operation_async_request_submodel_id,
            value=submodelId
        ) 
        path = Path(
            semantic_id=I40MessageSemanticProtocols.invoke_operation_sync_request_path if sync else I40MessageSemanticProtocols.invoke_operation_async_request_path,
            value=operationIdShort
        )
        input_argument = InputArguments(
            semantic_id=I40MessageSemanticProtocols.invoke_operation_sync_request_input_arguments if sync else I40MessageSemanticProtocols.invoke_operation_async_request_input_arguments,
            value=inputMap.values()
        )
        super().__init__(
            frame=frame,
            interactionElements=[submodel_id, path, input_argument]
        )

    def to_json(self) -> Dict[str, Any]:
        return super().to_json()

class I40InvokeOperationSyncRequest(I40InvokeOperationRequest):
    def __init__(
        self,
        sender: str,
        receiver: str,
        submodelId: str,
        operationIdShort: str,
        inputMap: Dict[str, SubmodelElement],
        messageId: Optional[str] = None,
        conversationId: Optional[str] = None 
    ):
        super().__init__(
            submodelId=submodelId,
            operationIdShort=operationIdShort,
            sender=sender,
            messageId=messageId,
            receiver=receiver,
            inputMap=inputMap,
            sync=True,
            conversationId=conversationId
        )
    
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "I40InvokeOperationSyncRequest":
        
        raw = json.loads(data) if isinstance(data, str) else data

        base: I40Message = I40Message.from_json(raw)

        submodel_id   = base._submodel_id
        operation_id  = base._path
        input_map     = base._input_map
        frame         = base.frame
        sender        = frame.sender.identification
        receiver      = frame.receiver.identification
        msg_id        = frame.messageId
        conv_id       = frame.conversationId

        return cls(
            submodelId    = submodel_id,
            operationIdShort = operation_id,
            sender        = sender,
            receiver      = receiver,
            inputMap      = input_map,
            messageId     = msg_id,
            conversationId= conv_id
        )

class I40InvokeOperationAsyncRequest(I40InvokeOperationRequest):
    def __init__(
        self,
        submodelId: str,
        operationIdShort: str,
        sender: str,
        receiver: str,
        inputMap: Dict[str, SubmodelElement],
        messageId: Optional[str] = None,
        conversationId: Optional[str] = None 

    ):
        super().__init__(
            submodelId=submodelId,
            operationIdShort=operationIdShort,
            sender=sender,
            messageId=messageId,
            receiver=receiver,
            inputMap=inputMap,
            sync=False,
            conversationId=conversationId 
        )

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "I40InvokeOperationAsyncRequest":
        
        raw = json.loads(data) if isinstance(data, str) else data

        base: I40Message = I40Message.from_json(raw)

        submodel_id   = base._submodel_id
        operation_id  = base._path
        input_map     = base._input_map
        frame         = base.frame
        sender        = frame.sender.identification
        receiver      = frame.receiver.identification
        msg_id        = frame.messageId
        conv_id       = frame.conversationId

        return cls(
            submodelId    = submodel_id,
            operationIdShort = operation_id,
            sender        = sender,
            receiver      = receiver,
            inputMap      = input_map,
            messageId     = msg_id,
            conversationId= conv_id
        )
    
class I40InvokeOperationReply(I40Message, ABC):

    def __init__(self,
                 sender: str,
                 receiver: str,
                 sync: bool,
                 statusCode: I40MessageStatusCode,
                 inReplyTo: Optional[str] = None,
                 outputMap: Optional[Dict[str, SubmodelElement]] = None,
                 messageType: Optional[I40ResultMessageType] = None,
                 text: Optional[str] = None,
                 success: Optional[I40MessageSuccess] = None,
                 executionState: Optional[I40MessageExecutionState] = None,
                 messageId: Optional[str] = None,
                 conversationId: Optional[str] = None):
        
        frame = Frame(
            semanticProtocol = I40MessageSemanticProtocols.invoke_operation_sync if sync else I40MessageSemanticProtocols.invoke_operation_async,
            type=I40MessageType.reply,
            sender=Replier(identification=sender),
            receiver=Requester(identification=receiver),
            messageId=messageId if messageId is not None else str(uuid.uuid4()),
            conversationId=conversationId,
            inReplyTo=inReplyTo 
        )
        status_code = StatusCode(
            semantic_id=I40MessageSemanticProtocols.invoke_operation_sync_status_code if sync else I40MessageSemanticProtocols.invoke_operation_async_status_code,
            value=statusCode
        )
        if isinstance(executionState, I40MessageExecutionState) and isinstance(success, I40MessageSuccess) and isinstance(outputMap, dict):
            output_argument = OutputArguments(
                semantic_id=I40MessageSemanticProtocols.invoke_operation_async_output_arguments,
                value=tuple(outputMap.values())
            )
            execution_state = ExecutionState(
                semantic_id=I40MessageSemanticProtocols.invoke_operation_async_execution_state,
                value=executionState
            )
            success_element = Success(
                semantic_id=I40MessageSemanticProtocols.invoke_operation_async_success,
                value=success
            )

            payload = Payload(
                semantic_id=I40MessageSemanticProtocols.invoke_operation_async_payload,
                value=(execution_state, success_element, output_argument)
            )
        else:
            text_element = Text(
                semantic_id=I40MessageSemanticProtocols.invoke_operation_sync_text if sync else I40MessageSemanticProtocols.invoke_operation_async_text,
                value=text
            )
            message_type_element = MessageType(
                semantic_id=I40MessageSemanticProtocols.invoke_operation_sync_message_type if sync else I40MessageSemanticProtocols.invoke_operation_async_message_type,
                value=messageType
            )

            message_element = Message(
                semantic_id=I40MessageSemanticProtocols.invoke_operation_sync_message if sync else I40MessageSemanticProtocols.invoke_operation_async_message,
                value=(message_type_element, text_element)
                )
            result_element = Result(
                semantic_id=I40MessageSemanticProtocols.invoke_operation_sync_result if sync else I40MessageSemanticProtocols.invoke_operation_async_result,
                value=(message_element, )
            )
            payload = Payload(
                semantic_id=I40MessageSemanticProtocols.invoke_operation_sync_payload if sync else I40MessageSemanticProtocols.invoke_operation_async_payload,  
                value=(result_element, )
                )
        super().__init__(
            frame=frame,
            interactionElements=[status_code, payload]
        )

    @classmethod 
    def create_error(
        cls,
        sender: str,
        receiver: str,
        inReplyTo: str,
        statusCode: I40MessageStatusCode,
        messageType: I40ResultMessageType,
        text: str,
        messageId: Optional[str] = None,
        conversationId: Optional[str] = None
    ): 
        return cls(
            sender=sender,
            receiver=receiver,  
            inReplyTo=inReplyTo,
            statusCode=statusCode,
            messageType=messageType,
            text=text,
            messageId=messageId,
            conversationId=conversationId
        )

    @classmethod 
    def create_success(
        cls, 
        sender: str,
        receiver: str,
        inReplyTo: str,
        outputMap: Dict[str, SubmodelElement],
        statusCode: I40MessageStatusCode,
        executionState: I40MessageExecutionState,
        messageId: Optional[str] = None,
        conversationId: Optional[str] = None
    ): 
        return cls(
            sender=sender,
            receiver=receiver,
            inReplyTo=inReplyTo,
            outputMap=outputMap,
            statusCode=statusCode,
            success=I40MessageSuccess.true,
            executionState=executionState,
            messageId=messageId,
            conversationId=conversationId
        ) 
    
    def to_json(self) -> Dict[str, Any]:
        return super().to_json()
    
class I40InvokeOperationSyncReply(I40InvokeOperationReply):
    def __init__(self,
                 sender: str,
                 receiver: str,
                 inReplyTo: str,
                 outputMap: Optional[Dict[str, SubmodelElement]] = None,
                 statusCode: Optional[I40MessageStatusCode] = None,
                 messageType: Optional[I40ResultMessageType] = None,
                 text: Optional[str] = None,
                 success: Optional[I40MessageSuccess] = None,
                 executionState: Optional[I40MessageExecutionState] = None,
                 messageId: Optional[str] = None,
                 conversationId: Optional[str] = None):
        
        super().__init__(sender=sender,
                         receiver=receiver,
                         sync=True, 
                         inReplyTo=inReplyTo,   
                         outputMap=outputMap,
                         statusCode=statusCode,
                         messageType=messageType,
                         text=text,
                         success=success,
                         executionState=executionState,
                         messageId=messageId,
                         conversationId=conversationId)
        


    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "I40InvokeOperationSyncReply":
        
        raw = json.loads(data) if isinstance(data, str) else data

        base: I40Message = I40Message.from_json(raw)

        status_code   = base._status_code
        payload       = base._payload
        output_map    = base._output_map
        frame         = base.frame
        sender        = frame.sender.identification
        receiver      = frame.receiver.identification
        msg_id        = frame.messageId
        conv_id       = frame.conversationId
        in_reply_to   = frame.inReplyTo

        success       = None
        execution_state = None
        text          = None 
        message_type  = None    
        for element in payload.value: 
            if element.id_short == "success":
                success = element.value
            elif element.id_short == "executionState":
                execution_state = element.value
            elif element.id_short == "text":
                text = element.value
            elif element.id_short == "messageType":
                message_type = element.value

        return cls(
            sender        = sender,
            receiver      = receiver,
            messageId     = msg_id,
            conversationId= conv_id,
            inReplyTo     = in_reply_to,
            statusCode    = I40MessageStatusCode(status_code),
            outputMap     = output_map,
            success       = I40MessageSuccess(success) if success else None,
            executionState= I40MessageExecutionState(execution_state) if execution_state else None,   
            text          = text,
            messageType   = I40ResultMessageType(message_type) if message_type else None
        )

class I40InvokeOperationAsyncReply(I40InvokeOperationReply):
    def __init__(
            self,
            sender: str,
            receiver: str,  
            inReplyTo: str,   
            outputMap: Optional[Dict[str, SubmodelElement]] = None,     
            statusCode: Optional[I40MessageStatusCode] = None,    
            messageType: Optional[I40ResultMessageType] = None,    
            text: Optional[str] = None,    
            success: Optional[I40MessageSuccess] = None,    
            executionState: Optional[I40MessageExecutionState] = None,    
            messageId: Optional[str] = None,    
            conversationId: Optional[str] = None
    ):
        
        super().__init__(sender=sender,
                         receiver=receiver,
                         sync=False, 
                         inReplyTo=inReplyTo,   
                         outputMap=outputMap,
                         statusCode=statusCode,
                         messageType=messageType,
                         text=text,
                         success=success,
                         executionState=executionState,
                         messageId=messageId,
                         conversationId=conversationId)
    
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "I40InvokeOperationAsyncReply":
        
        raw = json.loads(data) if isinstance(data, str) else data
        base: I40Message = I40Message.from_json(raw)

        status_code   = base._status_code
        payload       = base._payload
        output_map    = base._output_map
        frame         = base.frame
        interaction_elements = base.interactionElements
        sender        = frame.sender.identification
        receiver      = frame.receiver.identification
        msg_id        = frame.messageId
        conv_id       = frame.conversationId
        in_reply_to   = frame.inReplyTo

        success       = None
        execution_state = None
        text          = None 
        message_type  = None    
        
        for element in interaction_elements:
            if element.id_short == "payload":
                for payload_element in element.value:
                    if payload_element.id_short == "result":
                        for result_element in payload_element.value:
                            if result_element.id_short == "message":
                                for message_element in result_element.value:
                                    if message_element.id_short == "text":
                                        text = message_element.value
                                    elif message_element.id_short == "messageType":
                                        message_type = message_element.value
                    elif payload_element.id_short == "success":  
                        success = payload_element.value  
                    elif payload_element.id_short == "executionState":   
                        execution_state = payload_element.value
        return cls(
            sender        = sender,
            receiver      = receiver,
            messageId     = msg_id,
            conversationId= conv_id,
            inReplyTo     = in_reply_to,
            statusCode    = I40MessageStatusCode(status_code),
            outputMap     = output_map,
            success       = I40MessageSuccess(success) if success else None,
            executionState= I40MessageExecutionState(execution_state) if execution_state else None,   
            text          = text,
            messageType   = I40ResultMessageType(message_type) if message_type else None
        )
