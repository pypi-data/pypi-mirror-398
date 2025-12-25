from datetime import datetime
import json
from typing import List, Union, Optional, Dict, Any, Tuple
from jsonschema import validate as js_validate, ValidationError as JSONSchemaError

from pydantic import BaseModel, Field, field_validator, PrivateAttr, model_validator
from basyx.aas.adapter.json import AASFromJsonDecoder, AASToJsonEncoder
from basyx.aas.model import Property, SubmodelElementCollection, SubmodelElement, ReferenceElement, Key

from aas_thing.s3i.message.reference import I40MessageKeys, I40MessageSemanticProtocols, I40MessageType
from aas_thing.s3i.message.frame import Frame
from aas_thing.s3i.message.schema import invoke_operation_request_json_schema, invoke_operation_reply_json_schema


class I40Message(BaseModel):
    frame: Optional[Frame] = Field(None, alias=I40MessageKeys.frame.value)
    interactionElements: List[Union[Property, SubmodelElementCollection, ReferenceElement]] = Field(
        default_factory=list,
        alias=I40MessageKeys.interaction_elements.value,
    )
    # only for requests
    _submodel_id: str = PrivateAttr(default="")
    _path: str = PrivateAttr(default="")
    _input_map: Dict[str, SubmodelElement] = PrivateAttr(default_factory=dict)

    # only for replies
    _status_code: str = PrivateAttr(default="")
    _output_map: Dict[str, SubmodelElement] = PrivateAttr(default_factory=dict)
    _success: bool = PrivateAttr(default=False)

    # only for events
    _topic: str = PrivateAttr(default="")
    _timestamp: datetime = PrivateAttr(default="")
    _source_id_short_path: Tuple[Key] = PrivateAttr(default="")
    _observed_id_short_path: Tuple[Key] = PrivateAttr(default="")
    _observed_submodel_element: SubmodelElement = PrivateAttr(default="")

    # for replies and events
    _payload: SubmodelElementCollection = PrivateAttr(default_factory=dict)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "extra": "forbid",
        "json_encoders": {
            Frame: lambda v: v.to_json(),
            Property: lambda v: json.loads(json.dumps(v, cls=AASToJsonEncoder)),
            SubmodelElementCollection: lambda v: json.loads(json.dumps(v, cls=AASToJsonEncoder)),
        },
    }

    @field_validator("frame", mode="before")
    def _load_frame(cls, v: Union[Frame, Dict[str, Any]]) -> Frame:
        """
        Load frame from a dict into a Frame instance.

        If the frame is already a Frame instance, return it as is.
        Otherwise, attempt to load it from a dict using the Frame.from_json method.
        """
        if isinstance(v, dict):
            return Frame.from_json(v)
        return v

    @field_validator("interactionElements", mode="before")
    def _load_interaction_elements(cls, v: List[Any]) -> List[SubmodelElement]:
        """
        Load interactionElements from a list of dicts into a list of SubmodelElements.

        If the interactionElements is already a list of SubmodelElements, return it as is.
        Otherwise, attempt to load it from a list of dicts using the AASFromJsonDecoder.
        """
        out: List[SubmodelElement] = []
        for item in v:
            if isinstance(item, dict):
                # Convert the dict to a json string
                json_str = json.dumps(item)
                # Load the json string into a SubmodelElement using the AASFromJsonDecoder
                out.append(json.loads(json_str, cls=AASFromJsonDecoder))
            elif isinstance(item, SubmodelElement):
                # If the item is already a SubmodelElement, simply append it to the list
                out.append(item)
            else:
                raise TypeError(f"Unexpected interactionElement type: {type(item)}")
        return out

    @model_validator(mode="after")
    def _build_request_attributes(self):
        """
        Build request attributes from interactionElements

        This validator is called after the model is initialized and validates the interactionElements field.
        It iterates over the interactionElements and extracts the submodelId and path from the elements.
        It stores the submodelId and path in instance variables for later use.
        """
        for element in self.interactionElements:
            if element.id_short == "submodelId":
                # Extract the submodelId from the interactionElements and store it in the instance variable
                self._submodel_id = element.value
            elif element.id_short == "path":
                # Extract the path from the interactionElements and store it in the instance variable
                self._path = element.value
        return self

    @model_validator(mode='after')
    def _build_reply_attributes(self) -> "I40Message":
        """
        Build reply attributes from interactionElements

        This validator is called after the model is initialized and validates the interactionElements field.
        It iterates over the interactionElements and extracts the payload from the elements.
        It stores the payload in an instance variable for later use.

        :return: The instance itself
        """
        for element in self.interactionElements:
            if element.id_short == "payload":
                # Extract the payload from the interactionElements and store it in the instance variable
                self._payload = element
            if element.id_short == "statusCode":
                self._status_code = element.value
        for element in self._payload: 
            if element.id_short == "outputArguments":
                # Extract the outputArguments from the interactionElements and store it in the instance variable
                for value in element.value:
                    value.parent = None
                    if value.id_short:
                        self._output_map[value.id_short] = value
            if element.id_short == "success":
                self._success = element.value
        return self

    @model_validator(mode='after')
    def _build_input_map(self) -> "I40Message":
        """
        Build input map from interactionElements

        This validator is called after the model is initialized and validates the interactionElements field.
        It iterates over the interactionElements and extracts the inputArguments from the elements.
        It stores the inputArguments in the instance variable input_map for later use.

        :return: The instance itself
        """
        # now self.input_map already exists
        for element in self.interactionElements:
            if element.id_short == "inputArguments":
                for value in element.value:
                    value.parent = None
                    if value.id_short:
                        self._input_map[value.id_short] = value
        # crucially return the model instance, not a dict
        return self
    
    @model_validator(mode='after')
    def build_event_attributes(self) -> "I40Message":
        for element in self.interactionElements:
            if element.id_short == "topic":
                self._topic = element.value
            elif element.id_short == "timestamp":
                self._timestamp = element.value
            elif element.id_short == "payload":
                self._payload = element
            elif element.id_short == "source":
                self._source_id_short_path = element.value.key
            elif element.id_short == "observableReference":
                self._observed_id_short_path = element.value.key
        return self

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "I40Message":
        """
        Creates an I40Message instance from a JSON-like data structure.

        :param data: A JSON-like data structure that represents the I40Message instance.
        :return: The I40Message instance created from the data.
        """
        # The data is validated when the instance is created
        _result = cls.model_validate(data)
        raw = json.loads(data) if isinstance(data, str) else data.copy()
        if _result.frame.type == I40MessageType.request:
            if _result.frame.semanticProtocol == I40MessageSemanticProtocols.invoke_operation_async or  _result.frame.semanticProtocol == I40MessageSemanticProtocols.invoke_operation_sync:
                try:
                    js_validate(instance=raw, schema=invoke_operation_request_json_schema)
                except JSONSchemaError as e:
                    raise ValueError(f"Json validation failed: {e.message}")
        elif _result.frame.type == I40MessageType.reply:
            if _result.frame.semanticProtocol == I40MessageSemanticProtocols.invoke_operation_async or _result.frame.semanticProtocol == I40MessageSemanticProtocols.invoke_operation_sync:
                try:
                    js_validate(instance=raw, schema=invoke_operation_reply_json_schema)
                except JSONSchemaError as e:
                    raise ValueError(f"Json validation failed: {e.message}")

        return _result

    def to_json(self) -> Dict[str, Any]:
        """
        Converts the I40Message instance into a JSON-like data structure.

        :return: A JSON-like data structure that represents the I40Message instance.
        """
        # by_alias=True: Use the mapped names for the fields
        # exclude_none=True: Exclude fields that are None
        # mode="json": Return a JSON-like data structure
        return self.model_dump(by_alias=True, exclude_none=True, mode="json")

