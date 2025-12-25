"""Test Union type flattening functionality."""

from __future__ import annotations

import typing
from typing import Union

import pytest
from pydantic import BaseModel, Field
import funcnodes as fn

from funcnodes_pydantic.union_flattener import (
    collect_union_fields,
    flatten_union_output,
    resolve_union_models,
)


class SuccessResponse(BaseModel):
    status: typing.Literal["success"] = "success"
    data: str = Field(..., description="Success data")
    timestamp: float = Field(..., description="Success timestamp")


class ErrorResponse(BaseModel):
    status: typing.Literal["error"] = "error"
    error_code: int = Field(..., description="Error code")
    message: str = Field(..., description="Error message")


class WarningResponse(BaseModel):
    status: typing.Literal["warning"] = "warning"
    warning_level: int = Field(..., description="Warning severity level")
    details: list[str] = Field(default_factory=list, description="Warning details")


ApiResponse = Union[SuccessResponse, ErrorResponse, WarningResponse]


def test_resolve_union_models():
    """Test extracting BaseModel types from Union."""
    models = resolve_union_models(ApiResponse)
    assert models is not None
    assert len(models) == 3
    assert SuccessResponse in models
    assert ErrorResponse in models
    assert WarningResponse in models


def test_collect_union_fields():
    """Test collecting all fields from Union members."""
    models = resolve_union_models(ApiResponse)
    fields = collect_union_fields(models)

    # Should have all unique fields from all models
    expected_fields = {
        "status",
        "data",
        "timestamp",
        "error_code",
        "message",
        "warning_level",
        "details",
    }
    assert set(fields.keys()) == expected_fields
    assert len(fields["status"].owners) == 3
    assert [owner.__name__ for owner in fields["data"].owners] == ["SuccessResponse"]


def test_flatten_union_output_success():
    """Test flattening a success response."""
    response = SuccessResponse(data="test", timestamp=123.45)
    models = resolve_union_models(ApiResponse)
    fields = collect_union_fields(models)

    flattened = flatten_union_output(response, fields, base_name="ApiResponse")

    # Check present fields
    assert flattened["ApiResponse_status"] == "success"
    assert flattened["SuccessResponse_data"] == "test"
    assert flattened["SuccessResponse_timestamp"] == 123.45

    # Check sentinel values for fields from other models
    assert flattened["ErrorResponse_error_code"] is fn.NoValue
    assert flattened["ErrorResponse_message"] is fn.NoValue
    assert flattened["WarningResponse_warning_level"] is fn.NoValue
    assert flattened["WarningResponse_details"] is fn.NoValue


def test_flatten_union_output_error():
    """Test flattening an error response."""
    response = ErrorResponse(error_code=404, message="Not found")
    models = resolve_union_models(ApiResponse)
    fields = collect_union_fields(models)

    flattened = flatten_union_output(response, fields, base_name="ApiResponse")

    # Check present fields
    assert flattened["ApiResponse_status"] == "error"
    assert flattened["ErrorResponse_error_code"] == 404
    assert flattened["ErrorResponse_message"] == "Not found"

    # Check sentinel values
    assert flattened["SuccessResponse_data"] is fn.NoValue
    assert flattened["SuccessResponse_timestamp"] is fn.NoValue
    assert flattened["WarningResponse_warning_level"] is fn.NoValue
    assert flattened["WarningResponse_details"] is fn.NoValue


def test_optional_union():
    """Test handling Optional[Union[...]]."""
    OptionalApi = typing.Optional[ApiResponse]

    models = resolve_union_models(OptionalApi)
    assert models is not None
    assert len(models) == 3  # None is filtered out


def test_union_with_non_model_members():
    """Mixed unions that include non-model types shouldn't be flattened."""

    MixedUnion = Union[SuccessResponse, dict]

    models = resolve_union_models(MixedUnion)
    assert models is None


def test_flatten_union_output_forces_custom_name():
    """Ensure we can force a shared prefix when requested."""
    response = SuccessResponse(data="test", timestamp=1.23)
    models = resolve_union_models(ApiResponse)
    fields = collect_union_fields(models)

    flattened = flatten_union_output(
        response,
        fields,
        base_name="response",
        force_base_name=True,
    )

    assert flattened["response_status"] == "success"
    assert flattened["response_data"] == "test"
    assert flattened["response_timestamp"] == 1.23
