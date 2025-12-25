import uuid
import json
from jsonschema import validate as js_validate, ValidationError as JSONSchemaError
from enum import Enum
from typing import Optional, Union
from pydantic import BaseModel, Field
from basyx.aas.model import ExternalReference
from basyx.aas.adapter.json import AASFromJsonDecoder, AASToJsonEncoder
from aas_thing.s3i.message.reference import (
    I40MessageType,
    I40MessageConversationRole,
)
from aas_thing.s3i.message.schema import frame_schema

class VdiBaseModel(BaseModel):
    # Allow arbitrary external types (e.g., basyx ExternalReference)
    model_config = {"arbitrary_types_allowed": True, "extra": "forbid"}


class Role(VdiBaseModel):
    name: I40MessageConversationRole


class ConversationPartner(VdiBaseModel):
    """Identifies a party in a message exchange."""
    identification: str
    role: Role

class Requester(ConversationPartner):
    identification: str
    role: Role = Role(name=I40MessageConversationRole.requester)

class Replier(ConversationPartner):
    identification: str
    role: Role = Role(name=I40MessageConversationRole.replier)

class Emitter(ConversationPartner):
    identification: str
    role: Role = Role(name=I40MessageConversationRole.emitter)

class Frame(VdiBaseModel):
    semanticProtocol: ExternalReference
    type: I40MessageType
    sender: ConversationPartner
    receiver: Optional[ConversationPartner] = None
    messageId: str = Field(default_factory=lambda: str(uuid.uuid4()))

    inReplyTo: Optional[str] = None
    replyBy: Optional[int] = None
    conversationId: Optional[str] = None

    def to_json(self) -> str:
        """
        Serialize the Frame to a JSON string, handling ExternalReference and Enums via FrameJSONEncoder.
        """
        # Build a custom encoder for ExternalReference and Enum types

        class FrameJSONEncoder(AASToJsonEncoder):
            def default(self, obj):
                # Handle Enum types (e.g., I40MessageType)
                if isinstance(obj, Enum):
                    return obj.value if hasattr(obj, 'value') else obj.name
                # Fallback to AASJSONEncoder for ExternalReference
                return super().default(obj)

                # Dump the BaseModel to primitive types, excluding None values
        data = self.model_dump(exclude_none=True)
        # Serialize to JSON
        return json.loads(json.dumps(data, cls=FrameJSONEncoder))

    @classmethod
    def from_json(cls, data: Union[str, dict]) -> "Frame":
        """
        Deserialize a JSON string or dict into a Frame instance.
        Use AASFromJsonDecoder to parse only the ExternalReference field.
        """
        # Prepare raw dict
        raw = json.loads(data) if isinstance(data, str) else data.copy()
        # Validate using json schema 
        try:
            js_validate(instance=raw, schema=frame_schema)
        except JSONSchemaError as e:
            raise ValueError(f"Json validation failed: {e.message}")
        
        # Decode semanticProtocol field if present
        sp = raw.get('semanticProtocol')
        if sp is not None and not isinstance(sp, ExternalReference):
            # Dump to JSON and decode just that part
            decoded_sp = AASFromJsonDecoder._construct_reference(dct=sp)
            raw['semanticProtocol'] = decoded_sp
        # Validate and construct Frame
        return cls.model_validate(raw)


