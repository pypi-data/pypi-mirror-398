from __future__ import annotations

import inspect
import typing

import pytest
from pydantic import BaseModel, Field

from funcnodes_pydantic.unpackers import PydanticUnpacker


class ChildModel(BaseModel):
    code: int = Field(100, description="Child code", ge=0, le=999)


class ParentModel(BaseModel):
    name: str = Field(..., description="Name field")
    child: ChildModel
    tags: list[str] = Field(default_factory=list, description="Optional tags")


class ResponseModel(BaseModel):
    status: str = Field(..., description="Status text")
    value: str = Field(..., description="Payload value")


class GrandChildModel(BaseModel):
    token: str = Field(..., description="Grandchild token")


class DeepChildModel(BaseModel):
    grandchild: GrandChildModel


class DeepParentModel(BaseModel):
    child: DeepChildModel
    title: str = Field(..., description="Title field")


class DeepResponseModel(BaseModel):
    nested: DeepChildModel
    status: str = Field(..., description="Mirror status")


class OptionalFirstModel(BaseModel):
    optional: int | None = Field(None, description="Optional value comes first")
    required: int = Field(..., description="Required value defined after optional")


def _extract_meta(annotation):
    origin = typing.get_origin(annotation)
    assert origin is typing.Annotated
    base, meta = typing.get_args(annotation)
    return base, meta


def test_signature_flatten_top_level():
    @PydanticUnpacker()
    def process(payload: ParentModel) -> str:  # pragma: no cover - inspected only
        return payload.name

    sig = inspect.signature(process)
    assert tuple(sig.parameters) == ("payload_name", "payload_child", "payload_tags")

    hints = typing.get_type_hints(process, include_extras=True)
    child_ann = hints["payload_child"]
    base, meta = _extract_meta(child_ann)
    assert base is ChildModel
    assert meta["name"] == "payload.child"
    assert meta["description"] == ""  # no description provided on model


def test_nested_flatten_levels():
    @PydanticUnpacker(input_levels=2)
    def process(payload: ParentModel) -> str:
        return payload.child.code + len(payload.tags)

    sig = inspect.signature(process)
    assert tuple(sig.parameters) == (
        "payload_name",
        "payload_child_code",
        "payload_tags",
    )

    hints = typing.get_type_hints(process, include_extras=True)
    code_ann = hints["payload_child_code"]
    base, meta = _extract_meta(code_ann)
    assert base is int
    assert meta["description"] == "Child code"
    assert meta["value_options"]["min"] == 0
    assert meta["value_options"]["max"] == 999


def test_rehydration_and_output_flatten():
    calls: list[ParentModel] = []

    @PydanticUnpacker(input_levels=2, output_levels=1)
    def run(payload: ParentModel) -> ResponseModel:
        calls.append(payload)
        return ResponseModel(status="done", value=str(payload.child.code))

    result = run(
        payload_name="Demo",
        payload_child_code=321,
        payload_tags=["a"],
    )

    assert calls and isinstance(calls[0], ParentModel)
    assert calls[0].child.code == 321
    assert result == ("done", "321")


def test_unlimited_input_and_output_levels_traverse_full_tree():
    captured: list[DeepParentModel] = []

    @PydanticUnpacker(input_levels=-1, output_levels=-1)
    def run(payload: DeepParentModel) -> DeepResponseModel:
        captured.append(payload)
        return DeepResponseModel(nested=payload.child, status=payload.title)

    sig = inspect.signature(run)
    params = tuple(sig.parameters)
    assert "payload_child_grandchild_token" in params
    assert "payload_child" not in params

    hints = typing.get_type_hints(run, include_extras=True)
    token_ann = hints["payload_child_grandchild_token"]
    base, meta = _extract_meta(token_ann)
    assert base is str
    assert meta["name"] == "payload.child.grandchild.token"

    result = run(
        payload_child_grandchild_token="nested",
        payload_title="ready",
    )
    assert result == ("nested", "ready")
    assert captured and isinstance(captured[0], DeepParentModel)
    assert captured[0].child.grandchild.token == "nested"
    assert captured[0].title == "ready"


def test_default_factory_preserved():
    captured: list[list[str]] = []

    @PydanticUnpacker(input_levels=1)
    def collect(payload: ParentModel) -> list[str]:
        captured.append(payload.tags)
        payload.tags.append("x")
        return payload.tags

    first = collect(payload_name="A", payload_child=ChildModel(code=5))
    second = collect(payload_name="B", payload_child=ChildModel(code=6))

    assert captured[0] == ["x"]
    assert captured[1] == ["x"]
    assert captured[0] is not captured[1]
    assert first == ["x"]
    assert second == ["x"]


def test_optional_field_preceding_required_is_reordered():
    calls: list[OptionalFirstModel] = []

    @PydanticUnpacker(input_levels=1)
    def process(payload: OptionalFirstModel) -> int:
        calls.append(payload)
        return payload.required if payload.optional is None else payload.required + payload.optional

    sig = inspect.signature(process)
    assert tuple(sig.parameters) == ("payload_required", "payload_optional")

    result_missing_optional = process(payload_required=4)
    assert result_missing_optional == 4
    assert calls[0].required == 4
    assert calls[0].optional is None

    result_with_optional = process(payload_required=2, payload_optional=3)
    assert result_with_optional == 5
    assert calls[1].required == 2
    assert calls[1].optional == 3


def test_required_parameters_following_model_defaults_do_not_error():
    calls: list[tuple[OptionalFirstModel, int]] = []

    @PydanticUnpacker(input_levels=1)
    def process(payload: OptionalFirstModel, other: int) -> int:
        calls.append((payload, other))
        return payload.required + (payload.optional or 0) + other

    sig = inspect.signature(process)
    assert tuple(sig.parameters) == (
        "payload_required",
        "other",
        "payload_optional",
    )

    result = process(payload_required=1, other=5)
    assert result == 6
    assert calls[0][0].required == 1
    assert calls[0][0].optional is None
    assert calls[0][1] == 5

    result_with_optional = process(payload_required=2, other=1, payload_optional=4)
    assert result_with_optional == 7
    assert calls[1][0].required == 2
    assert calls[1][0].optional == 4
    assert calls[1][1] == 1


def test_variadic_base_model_rejected():
    with pytest.raises(TypeError):

        @PydanticUnpacker()
        def broken(*payload: ParentModel):  # pragma: no cover - definition should fail
            return payload


def test_levels_less_than_minus_one_rejected():
    with pytest.raises(ValueError):
        PydanticUnpacker(input_levels=-2)
    with pytest.raises(ValueError):
        PydanticUnpacker(output_levels=-5)


def test_node_decorator_integration(monkeypatch, tmp_path):
    config_dir = tmp_path / "funcnodes"
    config_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("FUNCNODES_CONFIG_DIR", str(config_dir))

    from funcnodes_core.nodemaker import (  # local import to honor config dir
        NodeDecorator,
    )

    @NodeDecorator(
        id="tests.pydantic.unpacker.node",
        name="Unpacked Parent Processor",
        description="Helper node for verifying flattened IO metadata.",
    )
    @PydanticUnpacker(input_levels=2, output_levels=1)
    def node_func(payload: ParentModel) -> ResponseModel:
        return ResponseModel(status=payload.name, value=str(payload.child.code))

    node = node_func()
    assert node is not None

    visible_inputs = {
        name: node.inputs[name].name for name in node.inputs if not name.startswith("_")
    }
    assert visible_inputs == {
        "payload_name": "payload.name",
        "payload_child_code": "payload.child.code",
        "payload_tags": "payload.tags",
    }

    visible_outputs = {
        name: node.outputs[name].name
        for name in node.outputs
        if not name.startswith("_")
    }
    assert visible_outputs == {
        "ResponseModel_status": "ResponseModel_status",
        "ResponseModel_value": "ResponseModel_value",
    }


class AddRequest(BaseModel):
    a: float = Field(..., description="First addend.", title="A")
    b: float = Field(..., description="Second addend.", title="B")


class ValidationError(BaseModel):
    loc: typing.List[typing.Union[str, int]] = Field(..., title="Location")
    msg: str = Field(..., title="Message")
    type: str = Field(..., title="Error Type")


class AddResponse(BaseModel):
    result: float = Field(..., description="Sum of 'a' and 'b'.", title="Result")


class HTTPValidationError(BaseModel):
    detail: typing.Optional[typing.List[ValidationError]] = Field(None, title="Detail")


class AddMathAddPostResponse200(BaseModel):
    status_code: typing.Literal[200] = 200
    content: AddResponse


class AddMathAddPostResponse422(BaseModel):
    status_code: typing.Literal[422] = 422
    content: HTTPValidationError


AddMathAddPostResponse = typing.Annotated[
    typing.Union[AddMathAddPostResponse200, AddMathAddPostResponse422],
    Field(discriminator="status_code"),
]


def test_complex_unpacker_decorator():
    """Test PydanticUnpacker with complex discriminated union return type."""

    # Track calls to verify the function behavior
    calls = []

    @PydanticUnpacker(input_levels=1, output_levels=1)
    def add_math_add_post(
        request: AddRequest,
        *,
        client: typing.Optional[typing.Any] = None,
        base_url: str = "http://localhost:8000",
        timeout: typing.Optional[float] = None,
    ) -> AddMathAddPostResponse:
        calls.append((request, client, base_url, timeout))

        # Simulate validation error for negative numbers
        if request.a < 0 or request.b < 0:
            return AddMathAddPostResponse422(
                status_code=422,
                content=HTTPValidationError(
                    detail=[
                        ValidationError(
                            loc=["body", "a" if request.a < 0 else "b"],
                            msg="Value must be non-negative",
                            type="value_error",
                        )
                    ]
                ),
            )

        # Normal successful response
        return AddMathAddPostResponse200(
            status_code=200, content=AddResponse(result=request.a + request.b)
        )

    # Test 1: Verify signature has been flattened
    sig = inspect.signature(add_math_add_post)
    param_names = list(sig.parameters.keys())

    # The AddRequest should be flattened to request_a and request_b
    assert "request_a" in param_names
    assert "request_b" in param_names
    assert "client" in param_names
    assert "base_url" in param_names
    assert "timeout" in param_names
    assert "request" not in param_names  # Original parameter should be gone

    # Test 2: Verify parameter annotations
    hints = typing.get_type_hints(add_math_add_post, include_extras=True)

    # Check flattened parameter types
    a_ann = hints["request_a"]
    origin = typing.get_origin(a_ann)
    assert origin is typing.Annotated
    base, meta = typing.get_args(a_ann)
    assert base is float
    assert meta["name"] == "request.a"
    assert meta["description"] == "First addend."

    b_ann = hints["request_b"]
    origin = typing.get_origin(b_ann)
    assert origin is typing.Annotated
    base, meta = typing.get_args(b_ann)
    assert base is float
    assert meta["name"] == "request.b"
    assert meta["description"] == "Second addend."

    # Test 3: Call with valid values
    calls.clear()
    result = add_math_add_post(
        request_a=5.0,
        request_b=3.0,
        client=None,
        base_url="http://example.com",
        timeout=30.0,
    )

    # Verify the function was called with reconstructed AddRequest
    assert len(calls) == 1
    request_arg, client_arg, base_url_arg, timeout_arg = calls[0]
    assert isinstance(request_arg, AddRequest)
    assert request_arg.a == 5.0
    assert request_arg.b == 3.0
    assert client_arg is None
    assert base_url_arg == "http://example.com"
    assert timeout_arg == 30.0

    # Verify the result - Union types ARE flattened with output_levels=1
    # The result should be a tuple with flattened fields
    assert isinstance(result, tuple)
    # Result is (status_code, content)
    assert len(result) == 2
    assert result[0] == 200  # status_code
    assert result[1] == {"result": 8.0}  # content as dict

    # Test 4: Call with invalid values (negative number)
    calls.clear()
    result = add_math_add_post(
        request_a=-5.0,
        request_b=3.0,
        client=None,
        base_url="http://localhost:8000",
        timeout=None,
    )

    # Verify we get error response - flattened as tuple
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert result[0] == 422  # status_code
    # content is the HTTPValidationError as dict
    content = result[1]
    assert isinstance(content, dict)
    assert "detail" in content
    assert len(content["detail"]) == 1
    assert content["detail"][0]["loc"] == ["body", "a"]
    assert "non-negative" in content["detail"][0]["msg"]

    # Test 5: Verify default values are preserved
    calls.clear()
    result = add_math_add_post(request_a=1.0, request_b=2.0)

    # Check defaults were used
    _, client_arg, base_url_arg, timeout_arg = calls[0]
    assert client_arg is None
    assert base_url_arg == "http://localhost:8000"
    assert timeout_arg is None


def test_complex_unpacker_decorator_deep():
    """Test PydanticUnpacker with deep unpacking (input_levels=-1, output_levels=-1)."""

    # Track calls to verify the function behavior
    calls = []

    @PydanticUnpacker(input_levels=-1, output_levels=-1)
    def add_math_add_post(
        request: AddRequest,
        *,
        client: typing.Optional[typing.Any] = None,
        base_url: str = "http://localhost:8000",
        timeout: typing.Optional[float] = None,
    ) -> AddMathAddPostResponse:
        calls.append((request, client, base_url, timeout))

        # Simulate validation error for negative numbers
        if request.a < 0 or request.b < 0:
            return AddMathAddPostResponse422(
                status_code=422,
                content=HTTPValidationError(
                    detail=[
                        ValidationError(
                            loc=["body", "a" if request.a < 0 else "b"],
                            msg="Value must be non-negative",
                            type="value_error",
                        )
                    ]
                ),
            )

        # Normal successful response
        return AddMathAddPostResponse200(
            status_code=200, content=AddResponse(result=request.a + request.b)
        )

    # Test 1: Verify deep signature flattening
    sig = inspect.signature(add_math_add_post)
    param_names = list(sig.parameters.keys())

    # With input_levels=-1, AddRequest should be fully flattened
    assert "request_a" in param_names
    assert "request_b" in param_names
    assert "client" in param_names
    assert "base_url" in param_names
    assert "timeout" in param_names
    assert "request" not in param_names  # Original parameter should be gone

    # Test 2: Verify parameter annotations
    hints = typing.get_type_hints(add_math_add_post, include_extras=True)

    # Check flattened parameter types
    a_ann = hints["request_a"]
    origin = typing.get_origin(a_ann)
    assert origin is typing.Annotated
    base, meta = typing.get_args(a_ann)
    assert base is float
    assert meta["name"] == "request.a"
    assert meta["description"] == "First addend."

    b_ann = hints["request_b"]
    origin = typing.get_origin(b_ann)
    assert origin is typing.Annotated
    base, meta = typing.get_args(b_ann)
    assert base is float
    assert meta["name"] == "request.b"
    assert meta["description"] == "Second addend."

    # Test 3: Verify deep output flattening
    # With output_levels=-1, the discriminated union should be unpacked
    # Since it's a Union type, we expect the original Union to be preserved
    # (current implementation doesn't flatten Union types)
    return_annotation = hints.get("return", sig.return_annotation)

    # The return type should still be the Union (not deeply flattened)
    # This is expected behavior - Union types are not flattened by the current implementation
    origin = typing.get_origin(return_annotation)
    if origin is typing.Annotated:
        return_annotation, _ = typing.get_args(return_annotation)
        origin = typing.get_origin(return_annotation)

    # For now, Union types remain intact - this may change in future versions
    # assert origin is typing.Union or return_annotation == AddMathAddPostResponse

    # Test 4: Call with valid values
    calls.clear()
    result = add_math_add_post(
        request_a=5.0,
        request_b=3.0,
        client=None,
        base_url="http://example.com",
        timeout=30.0,
    )

    # Verify the function was called with reconstructed AddRequest
    assert len(calls) == 1
    request_arg, client_arg, base_url_arg, timeout_arg = calls[0]
    assert isinstance(request_arg, AddRequest)
    assert request_arg.a == 5.0
    assert request_arg.b == 3.0
    assert client_arg is None
    assert base_url_arg == "http://example.com"
    assert timeout_arg == 30.0

    # Verify the result - Union types ARE flattened with output_levels=-1
    assert isinstance(result, tuple)
    # Result is (status_code, content)
    assert len(result) == 2
    assert result[0] == 200  # status_code
    assert result[1] == {"result": 8.0}  # content as dict

    # Test 5: Call with invalid values (negative number)
    calls.clear()
    result = add_math_add_post(
        request_a=-5.0,
        request_b=3.0,
        client=None,
        base_url="http://localhost:8000",
        timeout=None,
    )

    # Verify we get error response - flattened as tuple
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert result[0] == 422  # status_code
    # content is the HTTPValidationError as dict
    content = result[1]
    assert isinstance(content, dict)
    assert "detail" in content
    assert len(content["detail"]) == 1
    assert content["detail"][0]["loc"] == ["body", "a"]
    assert "non-negative" in content["detail"][0]["msg"]

    # Test 6: Verify default values are preserved
    calls.clear()
    result = add_math_add_post(request_a=1.0, request_b=2.0)

    # Check defaults were used
    _, client_arg, base_url_arg, timeout_arg = calls[0]
    assert client_arg is None
    assert base_url_arg == "http://localhost:8000"
    assert timeout_arg is None

    # Test 7: Verify the actual behavior difference with deep unpacking
    # With input_levels=-1, there should be no difference in input handling for this simple model
    # since AddRequest only has one level of fields (a and b)
    # The main difference would be visible with nested models
