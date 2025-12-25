from __future__ import annotations

import types
from typing import Any

import pytest
from pydantic import BaseModel, ConfigDict

from funcnodes_pydantic import model_get_field, model_set_field
from funcnodes_pydantic.models import (
    _assign_path,
    _ensure_list_index,
    _ensure_model_class,
    _navigate_mutable,
    _parse_field_path,
    _parse_import_path,
    _walk_value,
)


class Inner(BaseModel):
    code: int


class Container(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    tags: list[str]
    data: dict[str, int]
    child: Inner
    obj: Any


def test_parse_import_path_with_explicit_attribute():
    module, attr = _parse_import_path("some.module", "MyModel")
    assert module == "some.module"
    assert attr == "MyModel"


def test_parse_import_path_supports_colon_separators():
    module, attr = _parse_import_path("some.module:MyModel", None)
    assert module == "some.module"
    assert attr == "MyModel"


def test_parse_import_path_supports_dot_separators():
    module, attr = _parse_import_path("some.module.MyModel", None)
    assert module == "some.module"
    assert attr == "MyModel"


def test_parse_import_path_requires_module_and_attribute():
    with pytest.raises(ValueError, match="import_path must include both module and attribute"):
        _parse_import_path("MyModel", None)


def test_ensure_model_class_accepts_instances():
    instance = Inner(code=1)
    assert _ensure_model_class(instance) is Inner


def test_ensure_model_class_rejects_non_models():
    with pytest.raises(TypeError, match="Value is not a BaseModel instance or subclass"):
        _ensure_model_class(object())


def test_parse_field_path_supports_list_indices():
    assert _parse_field_path("tags[0].upper") == ["tags", 0, "upper"]


def test_parse_field_path_rejects_empty():
    with pytest.raises(ValueError, match="field path cannot be empty"):
        _parse_field_path("")


def test_walk_value_supports_mappings_and_attributes():
    payload = Container(
        tags=["a", "b"],
        data={"key": 5},
        child=Inner(code=10),
        obj=types.SimpleNamespace(foo=42),
    )
    assert _walk_value(payload, _parse_field_path("data.key")) == 5
    assert _walk_value(payload, _parse_field_path("obj.foo")) == 42
    assert _walk_value(payload, _parse_field_path("tags[1]")) == "b"


def test_walk_value_raises_key_error_for_index_on_non_sequence():
    payload = Container(
        tags=["a"],
        data={"key": 5},
        child=Inner(code=10),
        obj=types.SimpleNamespace(foo=42),
    )
    with pytest.raises(KeyError, match="Index 0 not available"):
        _walk_value(payload, _parse_field_path("child[0]"))


def test_ensure_list_index_out_of_bounds_raises():
    with pytest.raises(IndexError, match="out of bounds"):
        _ensure_list_index([1], 1)


def test_navigate_mutable_creates_missing_dict_segments_when_enabled():
    payload: dict[str, Any] = {}
    nested = _navigate_mutable(payload, "nested", create_missing=True)
    assert payload == {"nested": {}}
    assert nested == {}


def test_navigate_mutable_rejects_missing_keys_without_create():
    with pytest.raises(KeyError, match="not found while traversing path"):
        _navigate_mutable({}, "missing", create_missing=False)


def test_navigate_mutable_rejects_integer_segments_on_non_lists():
    with pytest.raises(TypeError, match="Cannot index .* with integer segments"):
        _navigate_mutable({}, 0, create_missing=True)


def test_navigate_mutable_rejects_unsupported_container_types():
    with pytest.raises(TypeError, match="Unsupported container"):
        _navigate_mutable([], "segment", create_missing=True)


def test_navigate_mutable_can_index_existing_lists():
    assert _navigate_mutable([1, 2], 1, create_missing=False) == 2


def test_assign_path_rejects_empty_paths():
    with pytest.raises(ValueError, match="field path cannot be empty"):
        _assign_path({}, [], 1, create_missing=False)


def test_assign_path_can_update_list_indices():
    payload: dict[str, Any] = {"tags": ["a", "b"]}
    _assign_path(payload, _parse_field_path("tags[0]"), "z", create_missing=False)
    assert payload["tags"] == ["z", "b"]


def test_assign_path_rejects_attribute_assignment_on_list():
    payload: dict[str, Any] = {"tags": ["a", "b"]}
    with pytest.raises(TypeError, match="Cannot set attribute"):
        _assign_path(payload, _parse_field_path("tags.foo"), 1, create_missing=False)


def test_assign_path_rejects_integer_assignment_on_non_lists():
    payload: dict[str, Any] = {"a": {}}
    with pytest.raises(TypeError, match="Only list values support integer assignment"):
        _assign_path(payload, _parse_field_path("a[0]"), 1, create_missing=False)


def test_assign_path_rejects_traversal_into_non_dict_container():
    payload: dict[str, Any] = {"tags": ["a", "b"]}
    with pytest.raises(TypeError, match="Unsupported container"):
        _assign_path(payload, _parse_field_path("tags.foo.bar"), 1, create_missing=False)

def test_model_get_field_errors_by_default(user_model, user_payload):
    user = user_model(**user_payload)
    with pytest.raises(ValueError, match="Failed to resolve path"):
        model_get_field.o_func(user, "address[0]")

def test_model_get_field_returns_none_when_missing_and_error_disabled(
    user_model, user_payload
):
    user = user_model(**user_payload)
    assert (
        model_get_field.o_func(user, "missing", error_if_missing=False) is None
    )

def test_model_get_field_returns_default_when_missing_and_error_disabled(
    user_model, user_payload
):
    user = user_model(**user_payload)
    assert (
        model_get_field.o_func(user, "missing", default="fallback", error_if_missing=False)
        == "fallback"
    )

def test_model_set_field_requires_value(user_model, user_payload):
    user = user_model(**user_payload)
    with pytest.raises(ValueError, match="value input is required"):
        model_set_field.o_func(user, "name")

def test_model_set_field_can_skip_validation(user_model, user_payload):
    user = user_model(**user_payload)
    updated = model_set_field.o_func(
        user, "id", value="not-an-int", validate=False
    )
    assert updated.id == "not-an-int"
