from basyx.aas.model import Submodel, SubmodelElement, Property, SubmodelElementCollection, SubmodelElementList, \
    Reference, ReferenceElement, ModelReference, ExternalReference
from basyx.aas.model.datatypes import String, DateTime, Boolean
from typing import Iterable
from aas_thing.s3i.message.reference import I40MessageSuccess


class InputArguments(SubmodelElementCollection):
    def __init__(self,
                 semantic_id: Reference,
                 value: Iterable[SubmodelElement]):
        """
        Initialize an InputArgument instance.

        :param semantic_id: The semantic identifier for the input argument.
        :param value: An iterable of SubmodelElement instances that represent the value of the input argument.
        """

        super().__init__(id_short="inputArguments", semantic_id=semantic_id, value=value)


class Path(Property):
    def __init__(self,
                 semantic_id: Reference,
                 value: String):
        """
        Initialize a Path instance.

        :param semantic_id: The semantic identifier for the path.
        :param value: A string representing the value of the path.
        """

        super().__init__(id_short="path", semantic_id=semantic_id, value_type=String, value=value)


class SubmodelId(Property):
    def __init__(self,
                 semantic_id: Reference,
                 value: String):
        """
        Initialize a SubmodelId instance.

        :param semantic_id: The semantic identifier for the submodel ID.
        :param value: A string representing the value of the submodel ID.
        """
        
        super().__init__(id_short="submodelId", semantic_id=semantic_id, value_type=String, value=value)

class StatusCode(Property): 
    def __init__(self,
                 semantic_id: Reference,
                 value: String):
        """
        Initialize a StatusCode instance.

        :param semantic_id: The semantic identifier for the status code.
        :param value: A string representing the value of the status code.
        """

        super().__init__(id_short="statusCode", semantic_id=semantic_id, value_type=String, value=value)

class Payload(SubmodelElementCollection):
    def __init__(self,             
                 semantic_id: Reference,    
                 value: Iterable[SubmodelElement]):
        """
        Initialize a Payload instance.

        :param semantic_id: The semantic identifier for the payload.
        :param value: An iterable of SubmodelElement instances that represent the value of the payload.
        """
        super().__init__(id_short="payload", semantic_id=semantic_id, value=value)
        
class ExecutionState(Property):
    def __init__(self,      
                 semantic_id: Reference,
                 value: String):
        """
        Initialize an ExecutionState instance.

        :param semantic_id: The semantic identifier for the execution state.
        :param value: A string representing the value of the execution state.
        """
        super().__init__(id_short="executionState", semantic_id=semantic_id, value_type=String, value=value)

class Success(Property):
    def __init__(self,      
                 semantic_id: Reference,
                 value: I40MessageSuccess):
        """
        Initialize a Success instance.

        :param semantic_id: The semantic identifier for the success.
        :param value: An I40MessageSuccess instance representing the value of the success.
        """
        super().__init__(id_short="success", semantic_id=semantic_id, value_type=Boolean, value=value)


class OutputArguments(SubmodelElementCollection):    
    def __init__(self,
                 semantic_id: Reference,
                 value: Iterable[SubmodelElement]):
        """
        Initialize an OutputArgument instance.

        :param semantic_id: The semantic identifier for the output argument.
        :param value: An iterable of SubmodelElement instances that represent the value of the output argument.
        """
        super().__init__(id_short="outputArguments", semantic_id=semantic_id, value=value)


class Result(SubmodelElementCollection):
    def __init__(self,
                 semantic_id: Reference,
                 value: Iterable[SubmodelElement]):
        """
        Initialize a Result instance.

        :param semantic_id: The semantic identifier for the result.
        :param value: An iterable of SubmodelElement instances that represent the value of the result.
        """

        super().__init__(id_short="result", semantic_id=semantic_id, value=value)

class Message(SubmodelElementCollection):
    def __init__(self,
                 semantic_id: Reference,
                 value: Iterable[SubmodelElement]):
        """
        Initialize a Message instance.

        :param semantic_id: The semantic identifier for the message.
        :param value: An iterable of SubmodelElement instances that represent the value of the message.
        """

        super().__init__(id_short="message", semantic_id=semantic_id, value=value)

class MessageType(Property):
    def __init__(self,
                 semantic_id: Reference,
                 value: String):
        """
        Initialize a MessageType instance.

        :param semantic_id: The semantic identifier for the message type.
        :param value: A string representing the value of the message type.
        """

        super().__init__(id_short="messageType", semantic_id=semantic_id, value_type=String, value=value)

class Text(Property):
    def __init__(self,
                 semantic_id: Reference,
                 value: String):        
        """
        Initialize a Text instance.

        :param semantic_id: The semantic identifier for the text.
        :param value: A string representing the value of the text.
        """

        super().__init__(id_short="text", semantic_id=semantic_id, value_type=String, value=value)

class Source(ReferenceElement):
    def __init__(self,
                semantic_id: Reference,
                value: ModelReference):
        """
        Initialize a Source instance.

        :param semantic_id: The semantic identifier for the source.
        :param value: A ModelReference instance representing the value of the source.
        """
        super().__init__(id_short="source", semantic_id=semantic_id, value=value)

class SourceSemanticId(ReferenceElement):
    def __init__(self,
                 semantic_id: Reference,
                 value: ExternalReference):
        """
        Initialize a SourceSemanticId instance.

        :param semantic_id: The semantic identifier for the source semantic ID.
        :param value: An ExternalReference instance representing the value of the source semantic ID.
        """

        super().__init__(id_short="sourceSemanticId", semantic_id=semantic_id, value=value)

class ObservableReference(ReferenceElement):
    def __init__(self,
                 semantic_id: Reference,
                 value: ModelReference):
        """
        Initialize an ObservableReference instance.

        :param semantic_id: The semantic identifier for the observable reference.
        :param value: A ModelReference instance representing the value of the observable reference.
        """
        super().__init__(id_short="observableReference", semantic_id=semantic_id, value=value)

class ObservableSemanticId(ReferenceElement):
    def __init__(self,
                 semantic_id: Reference,
                 value: ExternalReference):
        """
        Initialize an ObservableSemanticId instance.

        :param semantic_id: The semantic identifier for the observable semantic ID.
        :param value: An ExternalReference instance representing the value of the observable semantic ID.
        """
        super().__init__(id_short="observableSemanticId", semantic_id=semantic_id, value=value)

class Topic(Property):
    def __init__(self,
                 semantic_id: Reference,
                 value: String):
        """
        Initialize a Topic instance.

        :param semantic_id: The semantic identifier for the topic.
        :param value: A String instance representing the value of the topic.
        """
        super().__init__(id_short="topic", semantic_id=semantic_id, value_type=String, value=value)

class Timestamp(Property):
    def __init__(self,
                 semantic_id: Reference,
                 value: DateTime):
        """
        Initialize a Timestamp instance.

        :param semantic_id: The semantic identifier for the timestamp.
        :param value: A DateTime instance representing the value of the timestamp.
        """
        super().__init__(id_short="timestamp", semantic_id=semantic_id, value_type=DateTime, value=value)
