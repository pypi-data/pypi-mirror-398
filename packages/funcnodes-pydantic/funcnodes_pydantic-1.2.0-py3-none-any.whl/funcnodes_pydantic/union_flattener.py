"""Extension to PydanticUnpacker for handling Union type flattening.

This module provides utilities to flatten Union[BaseModel, ...] types
in function outputs, creating a combined output with all possible fields
where non-applicable fields are filled with a sentinel value.
"""

from __future__ import annotations

import typing
from dataclasses import dataclass
from typing import Any, Union, get_args, get_origin

from pydantic import BaseModel
import funcnodes as fn

# Sentinel object for fields not present in the actual returned union member


@dataclass
class UnionField:
    """Metadata for a field observed across all union members."""

    annotation: Any
    field_info: Any
    owners: list[type[BaseModel]]


def resolve_union_models(annotation: Any) -> list[type[BaseModel]] | None:
    """Extract BaseModel-only unions.

    Any Union that mixes BaseModel members with other concrete types (bytes,
    dicts, primitives, etc.) cannot be flattened safely, so in that case we
    return ``None`` to signal that normal union handling should be used.
    """
    origin = get_origin(annotation)

    # Handle Annotated[Union[...], ...]
    if origin is typing.Annotated:
        base_type = get_args(annotation)[0]
        origin = get_origin(base_type)
        annotation = base_type

    if origin is not Union:
        return None

    union_args = get_args(annotation)
    models: list[type[BaseModel]] = []
    saw_non_model = False

    for arg in union_args:
        # Skip None type
        if arg is type(None):
            continue

        # Extract from Annotated if needed
        if get_origin(arg) is typing.Annotated:
            arg = get_args(arg)[0]

        # Check if it's a BaseModel subclass
        if isinstance(arg, type) and issubclass(arg, BaseModel):
            models.append(arg)
            continue

        # Anything that reaches here is not a BaseModel member. Mixing such
        # types with BaseModels makes flattening ambiguous, so the caller
        # should treat the union as unsupported.
        saw_non_model = True

    if not models or saw_non_model:
        return None
    return models


def collect_union_fields(models: list[type[BaseModel]]) -> dict[str, UnionField]:
    """Collect all unique fields from a list of BaseModel types.

    Args:
        models: List of BaseModel classes to collect fields from

    Returns:
        Dictionary mapping field names to UnionField metadata
    """
    all_fields = {}

    for model in models:
        for field_name, field_info in model.model_fields.items():
            if field_name not in all_fields:
                all_fields[field_name] = UnionField(
                    annotation=field_info.annotation,
                    field_info=field_info,
                    owners=[model],
                )
            else:
                all_fields[field_name].owners.append(model)

    return all_fields


def _sanitize_segment(segment: str) -> str:
    return segment.replace(".", "_").replace(" ", "_")


def _format_union_field_name(base: str, field: str) -> str:
    tokens = []
    if base:
        tokens.append(_sanitize_segment(base))
    tokens.append(_sanitize_segment(field))
    return "_".join(tokens)


def derive_field_base_name(
    field: UnionField, fallback: str, *, force_base_name: bool = False
) -> str:
    """Return the preferred base label for a flattened union field."""

    if force_base_name:
        return fallback

    owner_names = {
        owner.__name__ for owner in field.owners if getattr(owner, "__name__", None)
    }
    if len(owner_names) == 1:
        return owner_names.pop()
    return fallback or "Union"


def flatten_union_output(
    value: BaseModel,
    all_fields: dict[str, UnionField],
    base_name: str | None = None,
    *,
    force_base_name: bool = False,
) -> dict[str, Any]:
    """Flatten a BaseModel instance with sentinel values for missing fields.

    Args:
        value: The actual BaseModel instance returned
        all_fields: All possible fields from the union
        base_name: Optional fallback prefix for generated field names
        force_base_name: When True, always use ``base_name`` regardless of ownership

    Returns:
        Dictionary with all fields, using fn.NoValue for missing ones
    """
    result = {}
    value_dict = value.model_dump()
    fallback = base_name or value.__class__.__name__ or "Union"

    for field_name, field in all_fields.items():
        label = derive_field_base_name(
            field,
            fallback,
            force_base_name=force_base_name,
        )
        key = _format_union_field_name(label, field_name)
        if field_name in value_dict:
            result[key] = value_dict[field_name]
        else:
            result[key] = fn.NoValue

    return result
