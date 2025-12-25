frame_schema = {
    "$schema": "https://json-schema.org/draft/2019-09/schema",
    "title": "Frame",
    "type": "object",
    "additionalProperties": True,
    "properties": {
        "semanticProtocol": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "type": {"type": "string"},
                "keys": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "type": {"type": "string"},
                            "value": {"type": "string"}
                        },
                        "required": ["type", "value"]
                    }
                }
            },
            "required": ["type", "keys"]
        },
        "type": {"type": "string"},
        "messageId": {"type": "string"},
        "conversationId": {"type": "string"},
        "replyBy": {"type": "number"},
        "inReplyTo": {"type": "string"},
        "sender": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "identification": {"type": "string"},
                "role": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "name": {"type": "string"}
                    },
                    "required": ["name"]
                }
            },
            "required": ["identification"]
        },
        "receiver": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "identification": {"type": "string"},
                "role": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "name": {"type": "string"}
                    },
                    "required": ["name"]
                }
            },
            "required": ["identification"]
        }
    },
    "required": ["semanticProtocol", "type", "messageId"]
}

invoke_operation_request_json_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "interactionElements": {
            "type": "array",
            "minItems": 3,
            "maxItems": 3,
            "uniqueItems": True,
            "items": {
                "allOf": [
                    {
                        "contains": {
                            "type": "object",
                            "properties": {
                                "idShort": {"const": "submodelId"},
                                "semanticId": {
                                    "type": "object",
                                    "properties": {
                                        "type": {"const": "ExternalReference"},
                                        "keys": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "type": {
                                                        "const": "GlobalReference"
                                                    },
                                                    "value": {
                                                        "type": "string",
                                                        "enum": [
                                                            "https://admin-shell.io/aas/API/InvokeOperationSync/submodelId/3/0",
                                                            "https://admin-shell.io/aas/API/InvokeOperationAsync/submodelId/3/0",
                                                        ],
                                                    },
                                                },
                                                "required": ["type", "value"],
                                            },
                                        },
                                    },
                                    "required": ["type", "keys"],
                                },
                                "modelType": {"const": "Property"},
                                "valueType": {"const": "xs:string"},
                                "value": {"type": "string"},
                            },
                            "required": [
                                "idShort",
                                "semanticId",
                                "modelType",
                                "valueType",
                                "value",
                            ],
                        }
                    },
                    {
                        "contains": {
                            "type": "object",
                            "properties": {
                                "idShort": {"const": "path"},
                                "semanticId": {
                                    "type": "object",
                                    "properties": {
                                        "type": {"const": "ExternalReference"},
                                        "keys": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "type": {
                                                        "const": "GlobalReference"
                                                    },
                                                    "value": {
                                                        "type": "string",
                                                        "enum": [
                                                            "https://admin-shell.io/aas/API/InvokeOperationSync/path/3/0",
                                                            "https://admin-shell.io/aas/API/InvokeOperationAsync/path/3/0",
                                                        ],
                                                    },
                                                },
                                                "required": ["type", "value"],
                                            },
                                        },
                                    },
                                    "required": ["type", "keys"],
                                },
                                "modelType": {"const": "Property"},
                                "valueType": {"const": "xs:string"},
                                "value": {"type": "string"},
                            },
                            "required": [
                                "idShort",
                                "semanticId",
                                "modelType",
                                "valueType",
                                "value",
                            ],
                        }
                    },
                    {
                        "contains": {
                            "type": "object",
                            "properties": {
                                "idShort": {"const": "inputArguments"},
                                "semanticId": {
                                    "type": "object",
                                    "properties": {
                                        "type": {"const": "ExternalReference"},
                                        "keys": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "type": {
                                                        "const": "GlobalReference"
                                                    },
                                                    "value": {
                                                        "type": "string",
                                                        "enum": [
                                                            "https://admin-shell.io/aas/API/InvokeOperationSync/inputArguments/3/0",
                                                            "https://admin-shell.io/aas/API/InvokeOperationAsync/inputArguments/3/0",
                                                        ],
                                                    },
                                                },
                                                "required": ["type", "value"],
                                            },
                                        },
                                    },
                                    "required": ["type", "keys"],
                                },
                                "modelType": {"const": "SubmodelElementCollection"},
                                "value": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "idShort": {"type": "string"},
                                            "modelType": {"type": "string"},
                                            "semanticId": {
                                                "type": "object",
                                                "properties": {
                                                    "type": {"type": "string"},
                                                    "keys": {
                                                        "type": "array",
                                                        "items": {
                                                            "type": "object",
                                                            "properties": {
                                                                "type": {
                                                                    "type": "string"
                                                                },
                                                                "value": {
                                                                    "type": "string"
                                                                },
                                                            },
                                                            "required": [
                                                                "type",
                                                                "value",
                                                            ],
                                                        },
                                                    },
                                                },
                                                "required": ["type", "keys"],
                                            },
                                            "value": {
                                                "oneOf": [
                                                    {"type": "string"},
                                                    {
                                                        "type": "array",
                                                        "items": {"type": "object"},
                                                    },
                                                ]
                                            },
                                            "valueType": {"type": "string"},
                                        },
                                        "required": [
                                            "idShort",
                                            "modelType",
                                            "value",
                                            "valueType",
                                        ],
                                    },
                                },
                            },
                            "required": ["idShort", "semanticId", "modelType", "value"],
                        }
                    },
                ]
            },
        },
    },
    "required": ["interactionElements"],
}

invoke_operation_reply_json_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "interactionElements": {
            "type": "array",
            "minItems": 2,
            "maxItems": 2,
            "items": {
                "anyOf": [
                    {
                        "type": "object",
                        "properties": {
                            "idShort": {"const": "statusCode"},
                            "modelType": {"const": "Property"},
                            "valueType": {"const": "xs:string"},
                            "value": {"type": "string"},
                        },
                        "required": ["idShort", "modelType", "valueType", "value"],

                    },
                    {
                        "contains": {
                            "type": "object",
                            "properties": {
                                "idShort": {"const": "payload"},
                                "modelType": {"const": "SubmodelElementCollection"},
                                "value": {
                                    "type": "array",
                                    "items": {
                                        "anyOf": [
                                            {
                                                "type": "object",
                                                "properties": {
                                                    "idShort": {
                                                        "const": "outputArguments"
                                                    },
                                                    "modelType": {
                                                        "const": "SubmodelElementCollection"
                                                    },
                                                    "value": {
                                                        "type": "array",
                                                        "items": {
                                                            "type": "object",
                                                            "properties": {
                                                                "idShort": {
                                                                    "type": "string"
                                                                },
                                                                "modelType": {
                                                                    "type": "string"
                                                                },
                                                                "semanticId": {
                                                                    "type": "object",
                                                                    "properties": {
                                                                        "type": {
                                                                            "type": "string"
                                                                        },
                                                                        "keys": {
                                                                            "type": "array",
                                                                            "items": {
                                                                                "type": "object",
                                                                                "properties": {
                                                                                    "type": {
                                                                                        "type": "string"
                                                                                    },
                                                                                    "value": {
                                                                                        "type": "string"
                                                                                    },
                                                                                },
                                                                                "required": [
                                                                                    "type",
                                                                                    "value",
                                                                                ],
                                                                            },
                                                                        },
                                                                    },
                                                                    "required": [
                                                                        "type",
                                                                        "keys",
                                                                    ],
                                                                },
                                                                "value": {
                                                                    "oneOf": [
                                                                        {
                                                                            "type": "string"
                                                                        },
                                                                        {
                                                                            "type": "array",
                                                                            "items": {
                                                                                "type": "object"
                                                                            },
                                                                        },
                                                                    ]
                                                                },
                                                                "valueType": {
                                                                    "type": "string"
                                                                },
                                                            },
                                                            "required": [
                                                                "idShort",
                                                                "modelType",
                                                                "value",
                                                                "valueType",
                                                            ],
                                                        },
                                                    },
                                                },
                                                "required": [
                                                    "idShort",
                                                    "modelType",
                                                    "value",
                                                ],
                                            },
                                            {
                                                "type": "object",
                                                "properties": {
                                                    "idShort": {
                                                        "const": "executionState"
                                                    },
                                                    "modelType": {"const": "Property"},
                                                    "valueType": {"const": "xs:string"},
                                                    "value": {"type": "string"},
                                                },
                                                "required": [
                                                    "idShort",
                                                    "modelType",
                                                    "valueType",
                                                    "value",
                                                ],
                                            },
                                            {
                                                "type": "object",
                                                "properties": {
                                                    "idShort": {"const": "success"},
                                                    "modelType": {"const": "Property"},
                                                    "valueType": {
                                                        "const": "xs:boolean"
                                                    },
                                                    "value": {
                                                        "type": "string",
                                                        "enum": ["true", "false"],
                                                    },
                                                },
                                                "required": [
                                                    "idShort",
                                                    "modelType",
                                                    "valueType",
                                                    "value",
                                                ],
                                            },
                                            {
                                                "type": "object",
                                                "properties": {
                                                    "idShort": {"const": "result"},
                                                    "modelType": {
                                                        "const": "SubmodelElementCollection"
                                                    },
                                                    "value": {
                                                        "type": "array",
                                                        "items": {
                                                            "type": "object",
                                                            "properties": {
                                                                "idShort": {
                                                                    "const": "message"
                                                                },
                                                                "modelType": {
                                                                    "const": "SubmodelElementCollection"
                                                                },
                                                                "value": {
                                                                    "type": "array",
                                                                    "items": {
                                                                        "anyOf": [
                                                                            {
                                                                                "contains": {
                                                                                    "type": "object",
                                                                                    "properties": {
                                                                                        "idShort": {
                                                                                            "const": "messageType"
                                                                                        },
                                                                                        "modelType": {
                                                                                            "const": "Property"
                                                                                        },
                                                                                        "valueType": {
                                                                                            "const": "xs:string"
                                                                                        },
                                                                                        "value": {
                                                                                            "const": "Error"
                                                                                        },
                                                                                    },
                                                                                    "required": [
                                                                                        "idShort",
                                                                                        "modelType",
                                                                                        "valueType",
                                                                                        "value",
                                                                                    ],
                                                                                }
                                                                            },
                                                                            {
                                                                                "contains": {
                                                                                    "type": "object",
                                                                                    "properties": {
                                                                                        "idShort": {
                                                                                            "const": "text"
                                                                                        },
                                                                                        "modelType": {
                                                                                            "const": "Property"
                                                                                        },
                                                                                        "valueType": {
                                                                                            "const": "xs:string"
                                                                                        },
                                                                                        "value": {
                                                                                            "type": "string"
                                                                                        },
                                                                                    },
                                                                                    "required": [
                                                                                        "idShort",
                                                                                        "modelType",
                                                                                        "valueType",
                                                                                        "value",
                                                                                    ],
                                                                                }
                                                                            },
                                                                        ]
                                                                    },
                                                                },
                                                            },
                                                            "required": [
                                                                "idShort",
                                                                "modelType",
                                                                "value",
                                                            ],
                                                        },
                                                    },
                                                },
                                                "required": [
                                                    "idShort",
                                                    "modelType",
                                                    "value",
                                                ],
                                            },
                                        ]
                                    },
                                },
                            },
                            "required": ["idShort", "modelType", "value"],
                        }
                    },
                ]
            },
        }
    },
    "required": ["interactionElements"],
}
