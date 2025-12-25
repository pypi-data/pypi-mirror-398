import json
from typing import Any, Dict, Optional, Tuple, Union, List
from copy import deepcopy
from datetime import datetime
import datetime
from basyx.aas.model import  SubmodelElement, ModelReference, BasicEventElement, Property, SubmodelElement, SubmodelElementCollection, SubmodelElementList, Key, Reference, AnnotatedRelationshipElement
from aas_thing.s3i.message.frame import Emitter, Frame, I40MessageType
from aas_thing.s3i.message.reference import I40MessageSemanticProtocols
from aas_thing.s3i.message.message import I40Message

from aas_thing.s3i.message.model import Source, SourceSemanticId, ObservableReference, ObservableSemanticId, Timestamp, Topic

class I40EventMessage(I40Message):

    
    
    def __init__(self,
                 event_id_short_path: Tuple[Key, ...],
                 observable_id_short_path: Tuple[Key, ...],
                 topic: str,
                 payload: SubmodelElement,
                 sender: str,
                 event_semantic_id: Optional[Reference] = None,
                 observable_semantic_id: Optional[Reference] = None):

        timestamp = datetime.datetime.now()
        _payload = deepcopy(payload)

        # Frame
        frame = Frame(
            semanticProtocol=I40MessageSemanticProtocols.event,
            type=I40MessageType.event,
            sender=Emitter(identification=sender)
        )

        # add source element
        source = Source(
            semantic_id=I40MessageSemanticProtocols.event_source,
            value=ModelReference(
                type_=AnnotatedRelationshipElement,
                key=event_id_short_path,
            ),
        )

        # add source semantic id if present
        source_semantic_id = None
        if event_semantic_id: 
            source_semantic_id = SourceSemanticId(
                semantic_id=I40MessageSemanticProtocols.event_source_semantic_id,
                value=event_semantic_id
            )

        # add observable
        observable_reference = ObservableReference(
            semantic_id=I40MessageSemanticProtocols.event_observable_reference,
            value=ModelReference(type_=AnnotatedRelationshipElement, key=observable_id_short_path)
        )

        observable_semantic_id = None
        if observable_semantic_id:
            observable_semantic_id = ObservableSemanticId(
                semantic_id=I40MessageSemanticProtocols.event_observable_semantic_id,
                value=observable_semantic_id
            )

        topic = Topic(
            semantic_id=I40MessageSemanticProtocols.event_topic,
            value=topic
        )

        timestamp = Timestamp(
            semantic_id=I40MessageSemanticProtocols.event_timestamp,
            value=timestamp
        )

        payload_element = SubmodelElementCollection(
            id_short="payload",
            semantic_id=I40MessageSemanticProtocols.event_payload,
            #value=()
        )
        payload_element.value = (_payload, )

        interactionElements = [
            source,
            observable_reference,
            topic,
            timestamp,
            payload_element
        ]
        if source_semantic_id:
            interactionElements.append(source_semantic_id)
        if observable_semantic_id:
            interactionElements.append(observable_semantic_id)

        super().__init__(frame=frame, interactionElements=interactionElements)

    @classmethod
    def from_elements(
        cls,
        eventElement: BasicEventElement,
        observable: Union[Property, SubmodelElementCollection, SubmodelElementList],
        topic: str,
        payload: SubmodelElement,
        sender: str,
    ) -> "I40EventMessage":
        
        return cls(
            event_id_short_path=ModelReference.from_referable(eventElement).key,
            observable_id_short_path=ModelReference.from_referable(observable).key,
            topic=topic,
            payload=payload,
            sender=sender
        )
    
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "I40EventMessage":
        
        raw = json.loads(data) if isinstance(data, str) else data

        base: I40Message = I40Message.from_json(raw)
        
        return cls(
            event_id_short_path = base._source_id_short_path,
            observable_id_short_path = base._observed_id_short_path,
            topic = base._topic,
            payload = next(iter(base._payload)),
            sender = base.frame.sender.identification,
        )
