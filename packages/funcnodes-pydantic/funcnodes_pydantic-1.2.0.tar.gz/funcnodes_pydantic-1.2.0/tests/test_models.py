from __future__ import annotations

import json

import pytest
from pytest_funcnodes import nodetest

from funcnodes_pydantic import (
    model_fields,
    model_get_field,
    model_set_field,
    model_to_dict,
    model_to_json,
    validate_json,
    validate_python,
)


@nodetest([validate_python])
async def test_import_and_validate(user_model, user_payload):
    validator = validate_python()
    validator.inputs["model_class"] < user_model
    validator.inputs["data"] < user_payload
    await validator
    instance = validator.outputs["model"].value
    assert instance.address.city == "Berlin"


@nodetest([model_get_field, model_set_field])
async def test_get_and_set_field(user_model, user_payload):
    user = user_model(**user_payload)

    getter = model_get_field()
    getter.inputs["model"] < user
    getter.inputs["field_path"] < "address.city"
    await getter
    assert getter.outputs["value"].value == "Berlin"
    assert "address" in getter.inputs["field_path"].value_options.get("options", [])

    setter = model_set_field()
    setter.inputs["model"] < user
    setter.inputs["field_path"] < "address.city"
    setter.inputs["value"] < "Hamburg"
    await setter
    updated = setter.outputs["updated model"].value
    assert updated.address.city == "Hamburg"
    assert user.address.city == "Berlin"


@nodetest([model_to_dict, model_to_json])
async def test_model_to_dict_and_json(user_model, user_payload):
    user = user_model(**user_payload)

    dump_node = model_to_dict()
    dump_node.inputs["model"] < user
    dump_node.inputs["exclude_defaults"] < True
    await dump_node
    payload = dump_node.outputs["data"].value
    assert payload["address"]["zip_code"] == 10115
    assert "name" in payload

    json_node = model_to_json()
    json_node.inputs["model"] < user
    json_node.inputs["indent"] < 2
    await json_node
    json_payload = json.loads(json_node.outputs["json"].value)
    assert json_payload["address"]["city"] == "Berlin"


@nodetest([model_fields])
async def test_model_fields_metadata(user_model):
    inspector = model_fields()
    inspector.inputs["model_or_class"] < user_model
    await inspector
    metadata = inspector.outputs["fields"].value
    names = {field["name"] for field in metadata}
    assert {"id", "name", "address", "tags"}.issubset(names)
    address_field = next(field for field in metadata if field["name"] == "address")
    assert address_field["required"] is True


@nodetest([validate_json])
async def test_validate_json(user_model, user_payload):
    validator = validate_json()
    validator.inputs["model_class"] < user_model
    validator.inputs["json_data"] < json.dumps(user_payload)
    await validator

    instance = validator.outputs["model"].value
    assert instance.address.street == "Main St"
    assert instance.tags == ["alpha", "beta"]
