from __future__ import annotations

import importlib
import re
from collections.abc import Mapping, Sequence
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel
from pydantic_core import PydanticUndefined

from funcnodes_core.decorator import update_other_io_value_options, fn
from funcnodes_core.io import InputMeta, OutputMeta
from funcnodes_core.nodemaker import NodeDecorator


PathToken = Union[str, int]
DumpMode = Literal["python", "json"]
_PATH_TOKEN_RE = re.compile(r"(?:[^.\[\]]+|\[-?\d+\])")


def _parse_import_path(import_path: str, attribute: str | None) -> tuple[str, str]:
    if attribute:
        return import_path, attribute
    if ":" in import_path:
        module_path, _, attr = import_path.partition(":")
    else:
        module_path, _, attr = import_path.rpartition(".")
    if not module_path or not attr:
        raise ValueError(
            "import_path must include both module and attribute (module:Class or module.Class)"
        )
    return module_path, attr


def _ensure_model_class(
    model_or_cls: type[BaseModel] | BaseModel,
) -> type[BaseModel]:
    if isinstance(model_or_cls, type) and issubclass(model_or_cls, BaseModel):
        return model_or_cls
    if isinstance(model_or_cls, BaseModel):
        return model_or_cls.__class__
    raise TypeError("Value is not a BaseModel instance or subclass")


def _parse_field_path(path: str) -> list[PathToken]:
    tokens: list[PathToken] = []
    for chunk in _PATH_TOKEN_RE.findall(path or ""):
        if chunk.startswith("["):
            tokens.append(int(chunk[1:-1]))
        else:
            tokens.append(chunk)
    if not tokens:
        raise ValueError("field path cannot be empty")
    return tokens


def _walk_value(value: Any, tokens: Sequence[PathToken]) -> Any:
    current = value
    for token in tokens:
        if isinstance(token, int):
            if isinstance(current, (list, tuple)):
                current = current[token]
            else:
                raise KeyError(f"Index {token} not available on {type(current)}")
        else:
            if isinstance(current, BaseModel):
                current = getattr(current, token)
            elif isinstance(current, Mapping):
                current = current[token]
            else:
                current = getattr(current, token)
    return current


def _ensure_list_index(seq: list[Any], index: int):
    if index >= len(seq) or index < -len(seq):
        raise IndexError(f"Index {index} out of bounds for list of length {len(seq)}")


def _navigate_mutable(container: Any, token: PathToken, *, create_missing: bool) -> Any:
    if isinstance(token, int):
        if not isinstance(container, list):
            raise TypeError(f"Cannot index {type(container)} with integer segments")
        _ensure_list_index(container, token)
        return container[token]

    if isinstance(container, dict):
        if token not in container:
            if not create_missing:
                raise KeyError(f"{token} not found while traversing path")
            container[token] = {}
        return container[token]

    raise TypeError(f"Unsupported container {type(container)} for segment {token}")


def _assign_path(
    payload: dict[str, Any],
    tokens: Sequence[PathToken],
    value: Any,
    *,
    create_missing: bool,
):
    if not tokens:
        raise ValueError("field path cannot be empty")
    current: Any = payload
    for idx, token in enumerate(tokens):
        last = idx == len(tokens) - 1
        if last:
            if isinstance(token, int):
                if not isinstance(current, list):
                    raise TypeError("Only list values support integer assignment")
                _ensure_list_index(current, token)
                current[token] = value
            else:
                if isinstance(current, dict):
                    current[token] = value
                else:
                    raise TypeError(f"Cannot set attribute {token} on {type(current)}")
            return
        current = _navigate_mutable(current, token, create_missing=create_missing)


def _field_value_options(model: BaseModel) -> dict[str, list[str]]:
    field_names = list(getattr(model.__class__, "model_fields", {}).keys())
    return {"options": sorted(field_names)}


@NodeDecorator(
    id="pydantic.validate_python",
    name="Validate Data",
    description="Validate a mapping into a Pydantic model instance.",
)
def validate_python(
    model_class: Annotated[
        type[BaseModel],
        InputMeta(name="model_class", required=True, description="BaseModel subclass"),
    ],
    data: Annotated[
        Mapping[str, Any],
        InputMeta(name="data", description="Mapping with field values", required=True),
    ],
    strict: Annotated[
        bool, InputMeta(name="strict", description="Disallow coercion")
    ] = False,
    from_attributes: Annotated[
        bool,
        InputMeta(
            name="from_attributes",
            description="Read attributes instead of dict keys when True",
        ),
    ] = False,
    context: Annotated[
        Mapping[str, Any] | None,
        InputMeta(name="context", description="Validation context", required=False),
    ] = None,
) -> Annotated[
    BaseModel,
    OutputMeta(name="model", description="Validated BaseModel instance"),
]:
    return model_class.model_validate(
        data,
        strict=strict or None,
        from_attributes=from_attributes or None,
        context=dict(context) if context else None,
    )


@NodeDecorator(
    id="pydantic.validate_json",
    name="Validate JSON",
    description="Validate a JSON string into a Pydantic model instance.",
)
def validate_json(
    model_class: Annotated[
        type[BaseModel],
        InputMeta(name="model_class", required=True, description="BaseModel subclass"),
    ],
    json_data: Annotated[
        str,
        InputMeta(
            name="json_data",
            description="JSON payload accepted by BaseModel.model_validate_json",
            required=True,
        ),
    ],
    strict: Annotated[
        bool, InputMeta(name="strict", description="Disallow coercion")
    ] = False,
    context: Annotated[
        Mapping[str, Any] | None,
        InputMeta(name="context", description="Validation context", required=False),
    ] = None,
) -> Annotated[
    BaseModel,
    OutputMeta(name="model", description="Validated BaseModel instance"),
]:
    return model_class.model_validate_json(
        json_data,
        strict=strict or None,
        context=dict(context) if context else None,
    )


@NodeDecorator(
    id="pydantic.model_to_dict",
    name="Model → Dict",
    description="Dump a BaseModel to a Python-friendly dictionary.",
)
def model_to_dict(
    model: Annotated[
        BaseModel,
        InputMeta(name="model", description="Model instance", required=True),
    ],
    mode: Annotated[
        DumpMode,
        InputMeta(
            name="mode",
            description="`python` keeps native types, `json` coerces to JSON types",
            value_options={"options": ["python", "json"]},
        ),
    ] = "python",
    by_alias: Annotated[
        bool, InputMeta(name="by_alias", description="Use field alias names")
    ] = False,
    exclude_none: Annotated[
        bool, InputMeta(name="exclude_none", description="Drop fields with value None")
    ] = False,
    exclude_defaults: Annotated[
        bool, InputMeta(name="exclude_defaults", description="Drop default values")
    ] = False,
    exclude_unset: Annotated[
        bool,
        InputMeta(
            name="exclude_unset", description="Drop fields that were not explicitly set"
        ),
    ] = False,
    round_trip: Annotated[
        bool,
        InputMeta(
            name="round_trip",
            description="Preserve information for JSON round-tripping",
        ),
    ] = False,
    include_fields: Annotated[
        Sequence[str] | None,
        InputMeta(
            name="include",
            description="Optional whitelist of fields to keep",
            required=False,
        ),
    ] = None,
    exclude_fields: Annotated[
        Sequence[str] | None,
        InputMeta(
            name="exclude",
            description="Optional blacklist of fields to drop",
            required=False,
        ),
    ] = None,
) -> Annotated[
    dict[str, Any], OutputMeta(name="data", description="Dictionary representation")
]:
    include = set(include_fields) if include_fields else None
    exclude = set(exclude_fields) if exclude_fields else None
    return model.model_dump(
        mode=mode,
        by_alias=by_alias,
        exclude_none=exclude_none,
        exclude_defaults=exclude_defaults,
        exclude_unset=exclude_unset,
        round_trip=round_trip,
        include=include,
        exclude=exclude,
    )


@NodeDecorator(
    id="pydantic.model_to_json",
    name="Model → JSON",
    description="Serialize a BaseModel to JSON.",
)
def model_to_json(
    model: Annotated[
        BaseModel,
        InputMeta(name="model", description="Model instance", required=True),
    ],
    by_alias: Annotated[
        bool, InputMeta(name="by_alias", description="Use field alias names")
    ] = False,
    exclude_none: Annotated[
        bool, InputMeta(name="exclude_none", description="Drop fields with value None")
    ] = False,
    exclude_defaults: Annotated[
        bool, InputMeta(name="exclude_defaults", description="Drop default values")
    ] = False,
    exclude_unset: Annotated[
        bool,
        InputMeta(
            name="exclude_unset", description="Drop fields that were not explicitly set"
        ),
    ] = False,
    indent: Annotated[
        int | None,
        InputMeta(
            name="indent",
            description="Pretty-print JSON with the provided indent",
            required=False,
            value_options={"min": 0, "step": 1},
        ),
    ] = None,
    include_fields: Annotated[
        Sequence[str] | None,
        InputMeta(
            name="include",
            description="Optional whitelist",
            required=False,
        ),
    ] = None,
    exclude_fields: Annotated[
        Sequence[str] | None,
        InputMeta(
            name="exclude",
            description="Optional blacklist",
            required=False,
        ),
    ] = None,
) -> Annotated[str, OutputMeta(name="json", description="JSON string")]:
    include = set(include_fields) if include_fields else None
    exclude = set(exclude_fields) if exclude_fields else None
    return model.model_dump_json(
        by_alias=by_alias,
        exclude_none=exclude_none,
        exclude_defaults=exclude_defaults,
        exclude_unset=exclude_unset,
        indent=indent,
        include=include,
        exclude=exclude,
    )


_field_choice_hook = update_other_io_value_options(
    "field_path",
    options_generator=lambda model: _field_value_options(model)
    if model
    else {"options": []},
)


@NodeDecorator(
    id="pydantic.model_get_field",
    name="Get Field",
    description="Extract a (possibly nested) field from a BaseModel.",
)
def model_get_field(
    model: Annotated[
        BaseModel,
        InputMeta(
            name="model",
            description="Model instance",
            required=True,
            on={"after_set_value": _field_choice_hook},
        ),
    ],
    field_path: Annotated[
        str,
        InputMeta(
            name="field_path",
            description="Dot/bracket path to the desired field (e.g. address.city or items[0].sku)",
            required=True,
        ),
    ],
    default: Annotated[
        Any,
        InputMeta(
            name="default",
            description="Optional fallback when the path does not exist",
            required=False,
        ),
    ] = PydanticUndefined,
    error_if_missing: Annotated[
        bool,
        InputMeta(
            name="error_if_missing",
            description="Raise a ValueError when the path is not found",
        ),
    ] = True,
) -> Annotated[Any, OutputMeta(name="value", description="Field value")]:
    try:
        value = _walk_value(model, _parse_field_path(field_path))
    except Exception as exc:
        if error_if_missing:
            raise ValueError(f"Failed to resolve path '{field_path}': {exc}") from exc
        if default is PydanticUndefined:
            return None
        return default
    return value


@NodeDecorator(
    id="pydantic.model_set_field",
    name="Set Field",
    description="Return a copy of the model with an updated field.",
)
def model_set_field(
    model: Annotated[
        BaseModel,
        InputMeta(
            name="model",
            description="Model instance to copy and update",
            required=True,
            on={"after_set_value": _field_choice_hook},
        ),
    ],
    field_path: Annotated[
        str,
        InputMeta(
            name="field_path",
            description="Dot/bracket path to update",
            required=True,
        ),
    ],
    value: Annotated[
        Any, InputMeta(name="value", description="New value")
    ] = PydanticUndefined,
    validate: Annotated[
        bool,
        InputMeta(
            name="validate",
            description="Re-run full model validation after the update",
        ),
    ] = True,
    create_missing: Annotated[
        bool,
        InputMeta(
            name="create_missing",
            description="Create missing dict segments when True",
        ),
    ] = False,
) -> Annotated[
    BaseModel,
    OutputMeta(name="updated model", description="Updated BaseModel copy"),
]:
    if value is PydanticUndefined:
        raise ValueError("value input is required")
    payload = model.model_dump(mode="python")
    _assign_path(
        payload,
        _parse_field_path(field_path),
        value,
        create_missing=create_missing,
    )
    model_cls = model.__class__
    if validate:
        return model_cls.model_validate(payload)
    return model_cls.model_construct(**payload)


@NodeDecorator(
    id="pydantic.model_fields",
    name="List Fields",
    description="Return metadata for all model fields.",
)
def model_fields(
    model_or_class: Annotated[
        type[BaseModel] | BaseModel,
        InputMeta(
            name="Model",
            description="Model instance or class to inspect",
            required=True,
        ),
    ],
) -> Annotated[
    list[dict[str, Any]], OutputMeta(name="fields", description="Field metadata list")
]:
    model_cls = _ensure_model_class(model_or_class)
    metadata: list[dict[str, Any]] = []
    for name, field in model_cls.model_fields.items():
        default = None if field.default is PydanticUndefined else field.default
        metadata.append(
            {
                "name": name,
                "annotation": repr(field.annotation)
                if field.annotation is not None
                else None,
                "alias": field.alias,
                "required": field.is_required(),
                "description": field.description,
                "default": default,
            }
        )
    return metadata
