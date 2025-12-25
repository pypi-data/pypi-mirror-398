"""Test integration of PydanticUnpacker with funcnodes NodeDecorator."""

from __future__ import annotations

import typing

import pytest
import asyncio
from pydantic import BaseModel, Field

from funcnodes_pydantic import PydanticUnpacker
from funcnodes_core import NodeDecorator
from funcnodes_core.io import OutputMeta


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
    OutputMeta(name="response"),
    Field(discriminator="status_code"),
]


@pytest.mark.asyncio
async def test_deep_unpacker_with_node_decorator():
    """Test PydanticUnpacker with deep unpacking integrated with NodeDecorator."""

    # Apply both decorators - PydanticUnpacker first, then NodeDecorator
    @NodeDecorator("add_math_node")
    @PydanticUnpacker(input_levels=-1, output_levels=-1)
    def add_math_node(
        request: AddRequest,
        *,
        client: typing.Optional[typing.Any] = None,
        base_url: str = "http://localhost:8000",
        timeout: typing.Optional[float] = None,
    ) -> AddMathAddPostResponse:
        """Add two numbers via API-style interface."""
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

    # Create a node instance
    node = add_math_node()

    # Test 1: Verify node has the flattened inputs
    input_names = list(node.inputs.keys())
    assert "request_a" in input_names
    assert "request_b" in input_names
    assert "client" in input_names
    assert "base_url" in input_names
    assert "timeout" in input_names

    # Test 2: Check input metadata preservation via the serialized view
    request_a_dict = node.inputs["request_a"].to_dict()
    assert request_a_dict["type"] == "float"
    assert "First addend" in request_a_dict["description"]

    request_b_dict = node.inputs["request_b"].to_dict()
    assert request_b_dict["type"] == "float"
    assert "Second addend" in request_b_dict["description"]

    # Test 3: Verify outputs are flattened
    output_names = list(node.outputs.keys())
    # With Union flattening, we should have individual fields prefixed with the annotated name
    status_key = "response_status_code"
    content_key = "response_content"
    assert status_key in output_names
    assert content_key in output_names

    # Test 4: Execute the node with valid values
    node.inputs["request_a"].value = 5.0
    node.inputs["request_b"].value = 3.0
    node.inputs["base_url"].value = "http://example.com"

    # Run the node
    await node()

    # Check the flattened outputs
    assert node.outputs[status_key].value == 200
    assert node.outputs[content_key].value == {"result": 8.0}

    # Test 5: Execute with invalid values (negative number)
    node.inputs["request_a"].value = -5.0
    node.inputs["request_b"].value = 3.0

    await node()

    # Check error response
    assert node.outputs[status_key].value == 422
    content = node.outputs[content_key].value
    assert isinstance(content, dict)
    assert "detail" in content

    # Test 6: Test with nested model flattening (if output_levels=-1 fully flattens)
    # This depends on whether nested models in the content are also flattened


@pytest.mark.asyncio
async def test_unpacker_preserves_node_metadata():
    """Test that node metadata like title and description are preserved."""

    @NodeDecorator(
        "math_service",
        node_name="Math Addition Service",
        description="Adds two numbers with validation",
    )
    @PydanticUnpacker(input_levels=1, output_levels=1)
    def math_service(
        request: AddRequest,
    ) -> AddResponse:
        """Internal docstring for the function."""
        return AddResponse(result=request.a + request.b)

    # Create node
    node = math_service()

    # Check node metadata is preserved
    assert node.node_name == "Math Addition Service"
    assert node.description == "Adds two numbers with validation"

    # Check inputs are flattened
    assert "request_a" in node.inputs
    assert "request_b" in node.inputs

    # Execute
    node.inputs["request_a"].value = 10.0
    node.inputs["request_b"].value = 20.0
    await node()

    # Flattened outputs are exposed as model-prefixed scalar outputs
    result_key = "AddResponse_result"
    assert result_key in node.outputs
    assert node.outputs[result_key].value == 30.0


class NestedData(BaseModel):
    value: float = Field(..., description="Nested value")
    metadata: dict = Field(default_factory=dict, description="Extra metadata")


class ComplexRequest(BaseModel):
    data: NestedData
    options: typing.List[str] = Field(default_factory=list)


class ComplexResponse(BaseModel):
    processed: NestedData
    status: str = "ok"


@pytest.mark.asyncio
async def test_complex_nested_unpacking():
    """Test deep unpacking with more complex nested structures."""

    @NodeDecorator("process_complex")
    @PydanticUnpacker(input_levels=-1, output_levels=-1)
    def process_complex(request: ComplexRequest) -> ComplexResponse:
        # Process the data
        processed_data = NestedData(
            value=request.data.value * 2,
            metadata={**request.data.metadata, "processed": True},
        )
        return ComplexResponse(processed=processed_data)

    node = process_complex()

    # With input_levels=-1, nested fields should be flattened
    assert "request_data_value" in node.inputs
    assert "request_data_metadata" in node.inputs
    assert "request_options" in node.inputs

    # Set values
    node.inputs["request_data_value"].value = 5.0
    node.inputs["request_data_metadata"].value = {"original": "data"}
    node.inputs["request_options"].value = ["opt1", "opt2"]

    await node()

    # With output_levels=-1, outputs should be deeply flattened
    processed_value_key = "ComplexResponse_processed_value"
    processed_metadata_key = "ComplexResponse_processed_metadata"
    status_key = "ComplexResponse_status"
    assert processed_value_key in node.outputs
    assert processed_metadata_key in node.outputs
    assert status_key in node.outputs

    assert node.outputs[processed_value_key].value == 10.0
    assert node.outputs[processed_metadata_key].value == {
        "original": "data",
        "processed": True,
    }
    assert node.outputs[status_key].value == "ok"
