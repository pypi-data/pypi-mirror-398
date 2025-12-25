from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from funcnodes_core.lib import Shelf
from funcnodes_core.utils.serialization import JSONEncoder,Encdata

from .models import (
    model_fields,
    model_get_field,
    model_set_field,
    model_to_dict,
    model_to_json,
    validate_json,
    validate_python,
)
from .unpackers import PydanticUnpacker


def _encode_base_model(value: Any, preview: bool = False):
    if isinstance(value, BaseModel):
        model_schema = value.model_json_schema()
        model_data = value.model_dump(mode="json" if preview else "python")
        obj = {
            "data": model_data,
            "schema": model_schema,
        }
        return Encdata(data=obj, handeled=True, done=False)
    return Encdata(data=value, handeled=False)


JSONEncoder.add_encoder(_encode_base_model, [BaseModel])

FUNCNODES_RENDER_OPTIONS = {
    "typemap": {
        f"{BaseModel.__module__}.{BaseModel.__name__}": "json_schema",
    },
}

VALIDATION_SHELF = Shelf(
    name="Validation",
    description="Import model classes and validate data",
    nodes=[validate_python, validate_json],
)

SERIALIZATION_SHELF = Shelf(
    name="Serialization",
    description="Convert models to primitive dict/JSON payloads",
    nodes=[model_to_dict, model_to_json],
)

FIELD_SHELF = Shelf(
    name="Fields",
    description="Inspect, get, and set model fields",
    nodes=[model_fields, model_get_field, model_set_field],
)

# from ._demo import NODE_SHELF as DEMO_SHELF

NODE_SHELF = Shelf(
    name="Funcnodes Pydantic",
    description="Nodes for validating and manipulating Pydantic models",
    subshelves=[
        VALIDATION_SHELF,
        SERIALIZATION_SHELF,
        FIELD_SHELF,
#       DEMO_SHELF,
    ],
)
__all__ = [
    "FIELD_SHELF",
    "FUNCNODES_RENDER_OPTIONS",
    "NODE_SHELF",
    "PydanticUnpacker",
    "SERIALIZATION_SHELF",
    "VALIDATION_SHELF",
    "model_fields",
    "model_get_field",
    "model_set_field",
    "model_to_dict",
    "model_to_json",
    "validate_json",
    "validate_python",
]
