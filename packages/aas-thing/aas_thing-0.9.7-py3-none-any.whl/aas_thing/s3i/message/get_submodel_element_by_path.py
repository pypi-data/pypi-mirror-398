from typing import Any, Optional, Dict
from basyx.aas.model import SubmodelElement
from aas_thing.s3i.message.message import I40Message
from aas_thing.s3i.message.model import Text
from aas_thing.s3i.message.model import StatusCode, MessageType, SubmodelId, Path, Payload, Result, Message 
from aas_thing.s3i.message.frame import Frame, I40MessageType, ConversationPartner, Replier, Requester, Role
from aas_thing.s3i.message.reference import I40MessageSemanticProtocols, I40MessageConversationRole, I40MessageStatusCode, I40ResultMessageType
import uuid
import json


class I40GetSubmodelElementByPathRequest(I40Message):
    def __init__(self,
                 submodelId: str,
                 submodelElementIdShort: str,
                 sender: str,
                 receiver: str,
                 messageId: Optional[str] = None,
                 conversationId: Optional[str] = None):
        
        frame = Frame(
            semanticProtocol=I40MessageSemanticProtocols.get_submodel_element_by_path,
            type=I40MessageType.request,
            sender=Requester(identification=sender),
            receiver=Replier(identification=receiver),
            messageId=messageId if messageId is not None else str(uuid.uuid4()),
            conversationId=conversationId
        )
        submodel_id = SubmodelId(
            semantic_id=I40MessageSemanticProtocols.get_submodel_element_by_path_submodel_id,
            value=submodelId
        )
        path = Path(
            semantic_id=I40MessageSemanticProtocols.get_submodel_element_by_path_path,
            value=submodelElementIdShort
        )
        super().__init__(
            frame=frame,
            interactionElements=[submodel_id, path]
        )

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "I40GetSubmodelElementByPathRequest":
        raw = json.loads(data) if isinstance(data, str) else data
        base: I40Message = I40Message.from_json(raw)
        submodel_id = base._submodel_id
        path = base._path
        frame = base.frame
        sender = frame.sender.identification
        receiver = frame.receiver.identification
        msg_id = frame.messageId
        conv_id = frame.conversationId
        return cls(
            submodelId=submodel_id,
            submodelElementIdShort=path,
            sender=sender,
            receiver=receiver,
            messageId=msg_id,
            conversationId=conv_id
        )


class I40GetSubmodelElementByPathReply(I40Message):
    def __init__(self,
                 sender: str,
                 receiver: str,
                 inReplyTo: str,
                 statusCode: I40MessageStatusCode,
                 submodelElement: Optional[SubmodelElement] = None,
                 messageType: Optional[I40ResultMessageType] = None,
                 text: Optional[str] = None,
                 messageId: Optional[str] = None,
                 conversationId: Optional[str] = None):
        frame = Frame(
            semanticProtocol=I40MessageSemanticProtocols.get_submodel_element_by_path,
            type=I40MessageType.reply,
            sender=Replier(identification=sender),
            receiver=Requester(identification=receiver),
            messageId=messageId if messageId is not None else str(uuid.uuid4()),
            conversationId=conversationId,
            inReplyTo=inReplyTo
        )
        status_code = StatusCode(
            semantic_id=I40MessageSemanticProtocols.get_submodel_element_by_path_status_code,
            value=statusCode
        )
        if submodelElement:
            submodelElement.parent = None 
            payload = Payload(
                semantic_id=I40MessageSemanticProtocols.get_submodel_element_by_path_payload,  
                value=(submodelElement, )
            )
        else:
            text_element = Text(
                semantic_id=I40MessageSemanticProtocols.get_submodel_element_by_path_text,
                value=text
            )
            message_type = MessageType(
                semantic_id=I40MessageSemanticProtocols.get_submodel_element_by_path_message_type,
                value=messageType
            )

            message = Message(
                semantic_id=I40MessageSemanticProtocols.get_submodel_element_by_path_message,
                value=(message_type, text_element)
                )
            result = Result(
                semantic_id=I40MessageSemanticProtocols.get_submodel_element_by_path_result,
                value=(message, )
            )
            payload = Payload(
                semantic_id=I40MessageSemanticProtocols.get_submodel_element_by_path_payload,  
                value=(result, )
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
        submodelElement: SubmodelElement, 
        statusCode: I40MessageStatusCode,
        messageId: Optional[str] = None,
        conversationId: Optional[str] = None
    ): 
        return cls(
            sender=sender,
            receiver=receiver,
            inReplyTo=inReplyTo,
            statusCode=statusCode,
            submodelElement=submodelElement,
            messageId=messageId,
            conversationId=conversationId
        ) 
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "I40GetSubmodelElementByPathReply":
        raw = json.loads(data) if isinstance(data, str) else data
        base: I40Message = I40Message.from_json(raw)
        status_code = base._status_code
        payload = base._payload 
        frame = base.frame
        sender = frame.sender.identification
        receiver = frame.receiver.identification
        msg_id = frame.messageId
        conv_id = frame.conversationId
        in_reply_to = frame.inReplyTo
        text = ""
        messageType = ""
        if status_code == I40MessageStatusCode.success.value:
            submodel_element = next(iter(payload.value))
            submodel_element.parent = None
        else:
            for element in payload.value: #
                if element.id_short == "result":
                    for result_element in element.value:
                        if result_element.id_short == "message":
                            for message_element in result_element.value:
                                if message_element.id_short == "text":
                                    text = message_element.value
                                if message_element.id_short == "messageType":
        
                                    messageType = message_element.value
        return cls(
            sender=sender,
            receiver=receiver,
            inReplyTo=in_reply_to,
            messageId=msg_id,
            conversationId=conv_id,
            submodelElement=submodel_element if submodel_element else None,
            statusCode=I40MessageStatusCode(status_code),
            messageType=I40ResultMessageType(messageType) if messageType else None,
            text=text if text else None
        )
    
