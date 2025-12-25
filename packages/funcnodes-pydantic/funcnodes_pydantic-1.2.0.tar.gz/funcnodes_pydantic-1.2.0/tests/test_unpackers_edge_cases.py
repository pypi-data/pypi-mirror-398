from __future__ import annotations

import inspect
import typing
import types
from enum import Enum
from typing import Annotated, Any, Union

import pytest
from pydantic import BaseModel, ConfigDict, Field

from funcnodes_core.io import NoValue, OutputMeta
from funcnodes_pydantic.unpackers import (
    PydanticUnpacker,
    _annotate_scalar_output,
    _annotation_for_output,
    _derive_union_base_name,
    _extract_output_name,
    _extract_value,
)


def _extract_meta(annotation):
    origin = typing.get_origin(annotation)
    assert origin is Annotated
    base, meta = typing.get_args(annotation)
    return base, meta


class SingleFieldA(BaseModel):
    value: int


class SingleFieldB(BaseModel):
    value: int


def test_union_single_field_outputs_extract_value():
    @PydanticUnpacker(output_levels=1)
    def run() -> Union[SingleFieldA, SingleFieldB]:
        return SingleFieldA(value=1)

    assert run() == 1


def test_union_single_field_outputs_validate_dict():
    @PydanticUnpacker(output_levels=1)
    def run() -> Union[SingleFieldA, SingleFieldB]:
        return {"value": 2}  # type: ignore[return-value]

    assert run() == 2


def test_union_single_field_outputs_reject_unvalidatable_payload():
    @PydanticUnpacker(output_levels=1)
    def run() -> Union[SingleFieldA, SingleFieldB]:
        return {"wrong": 2}  # type: ignore[return-value]

    with pytest.raises(ValueError, match="Could not validate value as any of the union members"):
        run()


def test_union_single_field_outputs_reject_none():
    @PydanticUnpacker(output_levels=1)
    def run() -> Union[SingleFieldA, SingleFieldB]:
        return None  # type: ignore[return-value]

    with pytest.raises(ValueError, match="Expected Union\\[BaseModel\\] return value, got None"):
        run()


class DisjointA(BaseModel):
    a: int


class DisjointB(BaseModel):
    b: int


def test_union_multiple_fields_outputs_fill_missing_with_novalue():
    @PydanticUnpacker(output_levels=1)
    def run() -> Union[DisjointA, DisjointB]:
        return DisjointA(a=5)

    assert run() == (5, NoValue)


def test_union_multiple_fields_outputs_validate_dict_and_fill_missing_with_novalue():
    @PydanticUnpacker(output_levels=1)
    def run() -> Union[DisjointA, DisjointB]:
        return {"b": 7}  # type: ignore[return-value]

    assert run() == (NoValue, 7)


def test_union_multiple_fields_outputs_reject_unvalidatable_payload():
    @PydanticUnpacker(output_levels=1)
    def run() -> Union[DisjointA, DisjointB]:
        return {"wrong": 7}  # type: ignore[return-value]

    with pytest.raises(ValueError, match="Could not validate value as any of the union members"):
        run()


def test_union_multiple_fields_outputs_reject_none():
    @PydanticUnpacker(output_levels=1)
    def run() -> Union[DisjointA, DisjointB]:
        return None  # type: ignore[return-value]

    with pytest.raises(ValueError, match="Expected Union\\[BaseModel\\] return value, got None"):
        run()


class OutputSingle(BaseModel):
    code: int = Field(..., ge=0, le=10)


def test_single_model_output_flattener_validates_dict_and_exposes_value_options():
    @PydanticUnpacker(output_levels=1)
    def run() -> OutputSingle:
        return {"code": 3}  # type: ignore[return-value]

    assert run() == 3

    hints = typing.get_type_hints(run, include_extras=True)
    base, meta = _extract_meta(hints["return"])
    assert base is int
    assert meta["value_options"]["min"] == 0
    assert meta["value_options"]["max"] == 10


def test_single_model_output_flattener_rejects_none():
    @PydanticUnpacker(output_levels=1)
    def run() -> OutputSingle:
        return None  # type: ignore[return-value]

    with pytest.raises(ValueError, match="Expected BaseModel return value, got None"):
        run()


class OutputMulti(BaseModel):
    a: int
    b: int


def test_multi_model_output_flattener_validates_dict():
    @PydanticUnpacker(output_levels=1)
    def run() -> OutputMulti:
        return {"a": 1, "b": 2}  # type: ignore[return-value]

    assert run() == (1, 2)


def test_multi_model_output_flattener_rejects_none():
    @PydanticUnpacker(output_levels=1)
    def run() -> OutputMulti:
        return None  # type: ignore[return-value]

    with pytest.raises(ValueError, match="Expected BaseModel return value, got None"):
        run()


def test_output_levels_zero_preserves_base_model_and_adds_output_meta():
    @PydanticUnpacker(output_levels=0)
    def run() -> OutputMulti:
        return OutputMulti(a=1, b=2)

    assert run() == OutputMulti(a=1, b=2)

    hints = typing.get_type_hints(run, include_extras=True)
    origin = typing.get_origin(hints["return"])
    assert origin is Annotated
    base, *metas = typing.get_args(hints["return"])
    assert base is OutputMulti
    assert any(isinstance(meta, dict) and meta.get("name") == "OutputMulti" for meta in metas)


def test_output_levels_zero_preserves_existing_annotated_metadata():
    marker = {"name": "custom.name"}

    @PydanticUnpacker(output_levels=0)
    def run() -> Annotated[OutputMulti, marker]:
        _ = marker
        return OutputMulti(a=1, b=2)

    hints = typing.get_type_hints(run, include_extras=True)
    base, *metas = typing.get_args(hints["return"])
    assert base is OutputMulti
    assert marker in metas
    assert any(isinstance(meta, dict) and meta.get("name") == "custom_name" for meta in metas)


def test_build_call_arguments_supports_varargs_and_kwargs():
    calls: list[tuple[tuple[int, ...], dict[str, int]]] = []

    @PydanticUnpacker()
    def run(a: int, *args: int, **kwargs: int) -> int:
        calls.append((args, kwargs))
        return a + sum(args) + sum(kwargs.values())

    assert run(1, 2, 3, x=4) == 10
    assert calls == [((2, 3), {"x": 4})]


@pytest.mark.asyncio
async def test_async_wrapper_executes_and_processes_outputs():
    class Result(BaseModel):
        value: int

    @PydanticUnpacker(output_levels=1)
    async def run() -> Result:
        return Result(value=5)

    assert await run() == 5


@pytest.mark.asyncio
async def test_async_wrapper_returns_raw_value_when_no_output_processor():
    @PydanticUnpacker()
    async def run(value: int) -> int:
        return value + 1

    assert await run(1) == 2


def test_sync_wrapper_runs_coroutine_return_values():
    class Result(BaseModel):
        value: int

    async def inner():
        return Result(value=7)

    @PydanticUnpacker(output_levels=1)
    def run() -> Result:
        _ = Result
        return inner()  # type: ignore[return-value]

    assert run() == 7


def test_function_without_return_annotation_keeps_runtime_behavior():
    @PydanticUnpacker()
    def run(value: int):
        return value * 2

    assert run(3) == 6
    assert inspect.signature(run).return_annotation is inspect._empty


class CollisionChild(BaseModel):
    code: int


class CollisionParent(BaseModel):
    child: CollisionChild
    child_code: int


def test_colliding_parameter_names_are_disambiguated():
    calls: list[CollisionParent] = []

    @PydanticUnpacker(input_levels=2)
    def run(payload: CollisionParent) -> int:
        calls.append(payload)
        return payload.child.code + payload.child_code

    sig = inspect.signature(run)
    assert "payload_child_code" in sig.parameters
    assert "payload_child_code__2" in sig.parameters

    result = run(payload_child_code=1, payload_child_code__2=2)
    assert result == 3
    assert calls[0].child.code == 1
    assert calls[0].child_code == 2


class Choice(Enum):
    a = "a"
    b = "b"


class ValueOptionsModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    gt_value: int = Field(..., gt=1)
    lt_value: int = Field(..., lt=10)
    step_value: float = Field(..., multiple_of=0.5)
    min_len: str = Field(..., min_length=2)
    max_len: str = Field(..., max_length=5)
    regex_value: str = Field(..., pattern=r"^[a-z]+$")

    class _MinItems:
        def __init__(self, min_items: int):
            self.min_items = min_items

    class _MaxItems:
        def __init__(self, max_items: int):
            self.max_items = max_items

    min_items: Annotated[list[int], _MinItems(1)]
    max_items: Annotated[list[int], _MaxItems(3)]
    enum_value: Choice
    literal_value: typing.Literal["x", "y"]
    annotated_value: Annotated[int, "meta"]
    obj: Any


def test_value_options_cover_all_supported_constraints():
    @PydanticUnpacker()
    def run(payload: ValueOptionsModel) -> int:
        return payload.gt_value

    hints = typing.get_type_hints(run, include_extras=True)

    _, meta = _extract_meta(hints["payload_gt_value"])
    assert meta["value_options"]["min"] == 1
    assert meta["value_options"]["exclusive_min"] is True

    _, meta = _extract_meta(hints["payload_lt_value"])
    assert meta["value_options"]["max"] == 10
    assert meta["value_options"]["exclusive_max"] is True

    _, meta = _extract_meta(hints["payload_step_value"])
    assert meta["value_options"]["step"] == 0.5

    _, meta = _extract_meta(hints["payload_min_len"])
    assert meta["value_options"]["min_length"] == 2

    _, meta = _extract_meta(hints["payload_max_len"])
    assert meta["value_options"]["max_length"] == 5

    _, meta = _extract_meta(hints["payload_regex_value"])
    assert meta["value_options"]["regex"] == r"^[a-z]+$"

    _, meta = _extract_meta(hints["payload_min_items"])
    assert meta["value_options"]["min_items"] == 1

    _, meta = _extract_meta(hints["payload_max_items"])
    assert meta["value_options"]["max_items"] == 3

    _, meta = _extract_meta(hints["payload_enum_value"])
    assert meta["value_options"]["options"] == ["a", "b"]

    _, meta = _extract_meta(hints["payload_literal_value"])
    assert meta["value_options"]["options"] == ["x", "y"]

    base, meta = _extract_meta(hints["payload_annotated_value"])
    assert base is int
    assert "value_options" not in meta


def test_derive_union_base_name_handles_empty_and_short_prefixes():
    assert _derive_union_base_name(()) == "Union"

    class AOne(BaseModel):
        value: int

    class ATwo(BaseModel):
        value: int

    assert _derive_union_base_name((AOne, ATwo)) == "AOne"


def test_extract_output_name_supports_fieldinfo_and_name_attributes():
    class Meta:
        def __init__(self, name: str):
            self.name = name

    annotation_fieldinfo = Annotated[OutputSingle, Field(json_schema_extra={"name": "My Out"})]
    assert _extract_output_name(annotation_fieldinfo) == "My_Out"

    annotation_attr = Annotated[OutputSingle, Meta("my.out")]
    assert _extract_output_name(annotation_attr) == "my_out"


def test_private_helpers_cover_unreachable_output_paths_and_getattr_extraction():
    assert _annotation_for_output(OutputMulti, ("missing",)) is Any
    assert _annotation_for_output(OutputMulti, ("a", "extra")) is Any

    class DictModel(BaseModel):
        data: dict[str, int]

    dict_model = DictModel(data={"key": 3})
    assert _extract_value(dict_model, ("data", "key")) == 3

    class ObjModel(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)

        obj: Any

    model = ObjModel(obj=types.SimpleNamespace(token="x"))
    assert _extract_value(model, ("obj", "token")) == "x"


def test_annotate_scalar_output_preserves_metadata():
    marker = {"name": "marker"}
    annotated = _annotate_scalar_output(Annotated[int, marker], "out_name")
    base, *metas = typing.get_args(annotated)
    assert base is int
    assert marker in metas
    assert any(isinstance(meta, dict) and meta.get("name") == "out_name" for meta in metas)
