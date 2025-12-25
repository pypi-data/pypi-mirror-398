"""Dynamic decorator that flattens Pydantic models into FuncNodes IO metadata.

This module implements :func:`PydanticUnpacker`, a decorator described in
`pydanticunpacker_plan.md`, which rewrites a callable so that any
``BaseModel`` inputs/outputs turn into primitive ``Annotated`` IOs enriched
with ``funcnodes_core.io.InputMeta``/``OutputMeta``. The wrapper restores
actual ``BaseModel`` instances before invoking the original function so that
downstream code can stay type-safe while FuncNodes receives fully described IO
ports.
"""

from __future__ import annotations

import asyncio
import inspect
import os
import typing
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache, wraps
from typing import (
    Annotated,
    Any,
    Callable,
    Sequence,
    Tuple,
    Union,
    get_args,
    get_origin,
)

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from funcnodes_core.io import InputMeta, OutputMeta, NoValue

# Import Union flattening utilities
from .union_flattener import (
    resolve_union_models,
    collect_union_fields,
    derive_field_base_name,
)


_SENTINEL = object()
"""Unique value used to signal 'no user value' for default factories."""


@dataclass
class _FieldSummary:
    """Describe a single field encountered during recursive traversal.

    Attributes:
        path: Tuple of canonical attribute names from the root model.
        alias_path: Tuple of alias-aware names mirroring ``path``.
        annotation: Raw annotation for the field (may include ``Annotated``).
        field_info: ``FieldInfo`` instance with defaults / descriptions.
        is_model: Flag indicating whether the field itself is a ``BaseModel``.
    """

    path: Tuple[str, ...]
    alias_path: Tuple[str, ...]
    annotation: Any
    field_info: FieldInfo
    is_model: bool


@dataclass
class _InputFieldSpec:
    """Record how one flattened field maps back to a function parameter."""

    parameter: str
    name: str
    path: Tuple[str, ...]
    uses_sentinel: bool


@dataclass
class _ModelParamSpec:
    """Group the flattened fields for a single BaseModel parameter."""

    model_cls: type[BaseModel]
    fields: tuple[_InputFieldSpec, ...]


@dataclass
class _OutputFieldSpec:
    """Describe the metadata needed to flatten BaseModel return values."""

    path: Tuple[str, ...]
    meta: OutputMeta


def PydanticUnpacker(input_levels: int = 1, output_levels: int = 1):
    """Flatten BaseModel inputs/outputs into Annotated IO definitions.

    Args:
        input_levels: Maximum recursion depth when expanding input models.
            ``1`` flattens only the top-level fields; higher numbers continue
            into nested ``BaseModel`` attributes. ``0`` disables input
            flattening entirely, while ``-1`` traverses without a depth limit.
        output_levels: Same as ``input_levels`` but applied to the return
            annotation. ``0`` keeps the original return type untouched and
            ``-1`` traverses without a depth limit.

    Returns:
        Callable[..., Any]: Decorator that rewrites the target function’s
        signature and return type but preserves its runtime behavior.

    Raises:
        ValueError: If the provided levels are less than ``-1``.
    """

    if input_levels < -1:
        raise ValueError("input_levels must be >= -1")
    if output_levels < -1:
        raise ValueError("output_levels must be >= -1")

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        signature = inspect.signature(func)
        type_hints = _get_type_hints(func)

        # Book-keeping structures used while rewriting the signature.
        param_name_counts: Counter[str] = Counter()
        model_param_specs: dict[str, _ModelParamSpec] = {}
        new_parameters: list[inspect.Parameter] = []
        new_annotations: dict[str, Any] = dict(getattr(func, "__annotations__", {}))

        for parameter in signature.parameters.values():
            annotation = type_hints.get(parameter.name, parameter.annotation)
            model_cls = _resolve_model_cls(annotation)

            if model_cls is None or input_levels == 0:
                resolved = (
                    annotation
                    if annotation is not inspect._empty
                    else parameter.annotation
                )
                new_parameters.append(parameter.replace(annotation=resolved))
                continue

            if parameter.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                raise TypeError(
                    f"Cannot unpack BaseModel parameter '{parameter.name}' defined as variadic"
                )

            traversal_levels = None if input_levels == -1 else max(1, input_levels)
            summaries = _collect_field_summaries(model_cls, traversal_levels)
            field_specs: list[_InputFieldSpec] = []
            for summary in summaries:
                generated = _build_parameter_name(
                    parameter.name, summary.path, param_name_counts
                )
                default_value, uses_sentinel = _resolve_field_default(
                    summary.field_info
                )
                input_meta = _build_input_meta(parameter.name, summary)
                if default_value is not PydanticUndefined:
                    input_meta["default"] = default_value
                value_options = _derive_value_options(
                    summary.field_info, summary.annotation
                )
                if value_options:
                    input_meta["value_options"] = value_options
                annotation_with_meta = Annotated[summary.annotation, input_meta]
                default = (
                    _SENTINEL
                    if uses_sentinel
                    else (
                        default_value
                        if default_value is not PydanticUndefined
                        else inspect._empty
                    )
                )
                new_param = inspect.Parameter(
                    generated,
                    kind=parameter.kind,
                    default=default,
                    annotation=annotation_with_meta,
                )
                new_parameters.append(new_param)
                new_annotations[generated] = annotation_with_meta
                field_specs.append(
                    _InputFieldSpec(
                        parameter=parameter.name,
                        name=generated,
                        path=summary.path,
                        uses_sentinel=uses_sentinel,
                    )
                )
            model_param_specs[parameter.name] = _ModelParamSpec(
                model_cls=model_cls,
                fields=tuple(field_specs),
            )

        output_processor: Callable[[Any], Any] | None = None
        output_annotation = type_hints.get("return", signature.return_annotation)
        processed_return_annotation = output_annotation

        # First check for Union types
        union_models = None
        custom_union_name: str | None = None
        if resolve_union_models is not None:
            union_models = resolve_union_models(output_annotation)

        if union_models is not None and output_levels != 0:
            # Handle Union[BaseModel, ...] flattening
            all_union_fields = collect_union_fields(union_models)
            output_specs = []
            custom_union_name = _extract_output_name(output_annotation)
            union_base_name = custom_union_name or _derive_union_base_name(union_models)
            force_union_name = custom_union_name is not None

            # Create specs for all possible fields across all union members
            for field_name, field in all_union_fields.items():
                field_base = derive_field_base_name(
                    field,
                    union_base_name,
                    force_base_name=force_union_name,
                )
                meta: OutputMeta = OutputMeta(
                    name=_format_output_name(field_base, (field_name,)),
                    description=field.field_info.description or "",
                )
                value_options = _derive_value_options(
                    field.field_info, field.annotation
                )
                if value_options:
                    meta["value_options"] = value_options
                output_specs.append(_OutputFieldSpec(path=(field_name,), meta=meta))

            if output_specs:
                if len(output_specs) == 1:
                    field_name = output_specs[0].path[0]
                    field_annotation = all_union_fields[field_name].annotation
                    processed_return_annotation = Annotated[
                        field_annotation, output_specs[0].meta
                    ]

                    def _process_union_output(value: Any) -> Any:
                        if value is None:
                            raise ValueError(
                                "Expected Union[BaseModel] return value, got None"
                            )
                        if not isinstance(value, BaseModel):
                            for model_cls in union_models:
                                try:
                                    value = model_cls.model_validate(value)
                                    break
                                except (
                                    Exception
                                ):  # pragma: no cover - validation fallback
                                    continue
                            else:
                                raise ValueError(
                                    "Could not validate value as any of the union members "
                                    f"{union_models}"
                                )
                        value_dict = value.model_dump()
                        return (
                            value_dict[field_name]
                            if field_name in value_dict
                            else NoValue
                        )

                else:
                    output_annotations = []
                    for spec in output_specs:
                        field_name = spec.path[0]
                        field_annotation = all_union_fields[field_name].annotation
                        output_annotations.append(
                            Annotated[field_annotation, spec.meta]
                        )

                    processed_return_annotation = tuple[tuple(output_annotations)]  # type: ignore[assignment]

                    def _process_union_output(value: Any) -> tuple[Any, ...]:
                        if value is None:
                            raise ValueError(
                                "Expected Union[BaseModel] return value, got None"
                            )
                        # Validate that it's one of the expected types
                        if not isinstance(value, BaseModel):
                            # Try to construct from one of the union members
                            for model_cls in union_models:
                                try:
                                    value = model_cls.model_validate(value)
                                    break
                                except (
                                    Exception
                                ):  # pragma: no cover - validation fallback
                                    continue
                            else:
                                raise ValueError(
                                    "Could not validate value as any of the union members: "
                                    f"{union_models}"
                                )

                        # Get the actual model's fields
                        value_dict = value.model_dump()
                        result = []

                        for spec in output_specs:
                            field_name = spec.path[0]
                            if field_name in value_dict:
                                result.append(value_dict[field_name])
                            else:
                                # Use sentinel for fields not in this model
                                result.append(NoValue)

                        return tuple(result)

                output_processor = _process_union_output

        # Fallback to single model handling
        else:
            output_model_cls = _resolve_model_cls(output_annotation)
            if output_model_cls is not None and output_levels != 0:
                traversal_levels = (
                    None if output_levels == -1 else max(1, output_levels)
                )
                base_name = (
                    _extract_output_name(output_annotation) or output_model_cls.__name__
                )
                output_specs = _build_output_specs(
                    output_model_cls, traversal_levels, base_name
                )
                if output_specs:
                    if len(output_specs) == 1:
                        spec = output_specs[0]
                        processed_return_annotation = Annotated[
                            _annotation_for_output(output_model_cls, spec.path),
                            spec.meta,
                        ]

                        def _process_output(value: Any) -> Any:
                            if value is None:
                                raise ValueError(
                                    "Expected BaseModel return value, got None"
                                )
                            if not isinstance(value, output_model_cls):
                                value = output_model_cls.model_validate(value)
                            return _extract_value(value, spec.path)

                    else:
                        output_annotations = []

                        for spec in output_specs:
                            field_annotation = _annotation_for_output(
                                output_model_cls, spec.path
                            )
                            output_annotations.append(
                                Annotated[field_annotation, spec.meta]
                            )

                        processed_return_annotation = tuple[tuple(output_annotations)]  # type: ignore[assignment]

                        def _process_output(value: Any) -> tuple[Any, ...]:
                            if value is None:
                                raise ValueError(
                                    "Expected BaseModel return value, got None"
                                )
                            if not isinstance(value, output_model_cls):
                                value = output_model_cls.model_validate(value)
                            return tuple(
                                _extract_value(value, spec.path)
                                for spec in output_specs
                            )

                    output_processor = _process_output
            elif output_model_cls is not None and output_levels == 0:
                processed_return_annotation = _annotate_scalar_output(
                    output_annotation,
                    _format_output_name(
                        _extract_output_name(output_annotation)
                        or output_model_cls.__name__
                    ),
                )

        if processed_return_annotation is not inspect._empty:
            new_annotations["return"] = processed_return_annotation
        else:
            new_annotations.pop("return", None)

        def _reorder_parameters(params: list[inspect.Parameter]) -> list[inspect.Parameter]:
            """Ensure required positional parameters precede defaults.

            Python forbids a positional-only/positional-or-keyword parameter without
            a default from following one that has a default. BaseModel flattening can
            produce that invalid ordering when the original model declares optional
            fields before required ones. We reorder only within each compatible
            ``Parameter.kind`` bucket to preserve the overall call semantics.
            """

            kind_order = [
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.KEYWORD_ONLY,
                inspect.Parameter.VAR_KEYWORD,
            ]

            reordered: list[inspect.Parameter] = []
            for kind in kind_order:
                bucket = [p for p in params if p.kind == kind]
                if kind in (
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                ):
                    required = [p for p in bucket if p.default is inspect._empty]
                    optional = [p for p in bucket if p.default is not inspect._empty]
                    reordered.extend(required + optional)
                else:
                    reordered.extend(bucket)
            return reordered

        new_parameters = _reorder_parameters(new_parameters)

        new_signature = signature.replace(
            parameters=new_parameters,
            return_annotation=processed_return_annotation,
        )

        is_async = inspect.iscoroutinefunction(func)

        def _build_call_arguments(
            bound: inspect.BoundArguments,
        ) -> tuple[list[Any], dict[str, Any]]:
            """Restore original args/kwargs layout expected by ``func``."""

            model_instances: dict[str, BaseModel] = {}
            for param, spec in model_param_specs.items():
                payload: dict[str, Any] = {}
                for field in spec.fields:
                    value = bound.arguments.get(field.name, inspect._empty)
                    if value is inspect._empty or (
                        field.uses_sentinel and value is _SENTINEL
                    ):
                        continue
                    _assign_path(payload, field.path, value)
                model_instances[param] = spec.model_cls.model_validate(payload)

            call_args: list[Any] = []
            call_kwargs: dict[str, Any] = {}
            for parameter in signature.parameters.values():
                if parameter.kind == inspect.Parameter.VAR_POSITIONAL:
                    call_args.extend(bound.arguments.get(parameter.name, ()))
                    continue
                if parameter.kind == inspect.Parameter.VAR_KEYWORD:
                    call_kwargs.update(bound.arguments.get(parameter.name, {}))
                    continue

                if parameter.name in model_instances:
                    value = model_instances[parameter.name]
                else:
                    value = bound.arguments[parameter.name]

                if parameter.kind in (
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                ):
                    call_args.append(value)
                else:
                    call_kwargs[parameter.name] = value

            return call_args, call_kwargs

        @wraps(func)
        async def _async_wrapper(*args: Any, **kwargs: Any) -> Any:
            bound = new_signature.bind_partial(*args, **kwargs)
            bound.apply_defaults()

            call_args, call_kwargs = _build_call_arguments(bound)
            result = func(*call_args, **call_kwargs)
            if asyncio.iscoroutine(result):
                result = await result
            if output_processor:
                return output_processor(result)
            return result

        @wraps(func)
        def _sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            bound = new_signature.bind_partial(*args, **kwargs)
            bound.apply_defaults()

            call_args, call_kwargs = _build_call_arguments(bound)
            result = func(*call_args, **call_kwargs)
            if asyncio.iscoroutine(result):
                try:
                    result = asyncio.run(result)
                except RuntimeError as exc:  # pragma: no cover - loop already running
                    raise RuntimeError(
                        "Coroutine return value requires awaiting within a running event loop"
                    ) from exc
            if output_processor:
                return output_processor(result)
            return result

        wrapper = _async_wrapper if is_async else _sync_wrapper
        wrapper.__signature__ = new_signature
        wrapper.__annotations__ = new_annotations
        return wrapper

    return decorator


def _get_type_hints(func: Callable[..., Any]) -> dict[str, Any]:
    """Resolve annotations with ``include_extras=True`` when available.

    ``typing.get_type_hints`` normally evaluates postponed annotations using the
    function's module globals. That breaks when decorators are defined inside
    another function (common in tests) because any locally defined models are
    only accessible through closure cells. We surface those closure locals to the
    type-hint resolver so nested BaseModel declarations remain valid.
    """

    globalns = getattr(func, "__globals__", {})

    # Gather closure locals (``co_freevars``) so nested classes remain visible
    # when ``from __future__ import annotations`` stores string annotations.
    localns: dict[str, Any] = {}
    closure = getattr(func, "__closure__", None)
    if closure:
        for name, cell in zip(func.__code__.co_freevars, closure):
            try:
                localns[name] = cell.cell_contents
            except ValueError:  # pragma: no cover - empty cell
                continue

    try:  # Python 3.10+
        return typing.get_type_hints(
            func,
            globalns=globalns,
            localns=localns or None,
            include_extras=True,
        )  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover - fallback for minimal environments
        return typing.get_type_hints(func, globalns=globalns, localns=localns or None)


def _resolve_model_cls(annotation: Any) -> type[BaseModel] | None:
    """Return the concrete ``BaseModel`` subclass hidden inside an annotation."""

    if annotation is inspect._empty:
        return None
    base = _base_annotation(annotation)
    if isinstance(base, type) and issubclass(base, BaseModel):
        return base
    return None


def _build_parameter_name(param: str, path: Sequence[str], counts: Counter[str]) -> str:
    """Create globally unique parameter names based on the field path."""

    tokens = [param, *path]
    base = "_".join(tokens)
    counts[base] += 1
    if counts[base] == 1:
        return base
    return f"{base}__{counts[base]}"


def _resolve_field_default(field: FieldInfo) -> tuple[Any, bool]:
    """Return either the default value or a sentinel when a factory is present."""

    if field.is_required():
        return PydanticUndefined, False
    if field.default_factory is not None:
        return PydanticUndefined, True
    return field.default, False


def _build_input_meta(param_name: str, summary: _FieldSummary) -> InputMeta:
    """Project ``FieldInfo`` details into an ``InputMeta`` record."""

    alias = ".".join(summary.alias_path)
    qualified_name = f"{param_name}.{alias}" if alias else param_name
    meta: InputMeta = InputMeta(
        name=qualified_name,
        description=summary.field_info.description or "",
        required=summary.field_info.is_required(),
    )
    return meta


def _derive_value_options(field: FieldInfo, annotation: Any) -> dict[str, Any]:
    """Translate annotated field constraints into FuncNodes ``value_options``."""

    options: dict[str, Any] = {}
    for meta in field.metadata:
        if hasattr(meta, "ge") and meta.ge is not None:
            options["min"] = meta.ge
        if hasattr(meta, "gt") and meta.gt is not None:
            options["min"] = meta.gt
            options["exclusive_min"] = True
        if hasattr(meta, "le") and meta.le is not None:
            options["max"] = meta.le
        if hasattr(meta, "lt") and meta.lt is not None:
            options["max"] = meta.lt
            options["exclusive_max"] = True
        if hasattr(meta, "multiple_of") and meta.multiple_of is not None:
            options["step"] = meta.multiple_of
        if hasattr(meta, "min_length") and meta.min_length is not None:
            options["min_length"] = meta.min_length
        if hasattr(meta, "max_length") and meta.max_length is not None:
            options["max_length"] = meta.max_length
        if hasattr(meta, "pattern") and meta.pattern:
            options["regex"] = meta.pattern
        if hasattr(meta, "min_items") and meta.min_items is not None:
            options["min_items"] = meta.min_items
        if hasattr(meta, "max_items") and meta.max_items is not None:
            options["max_items"] = meta.max_items

    enum_options = _enum_options(annotation)
    if enum_options:
        options.setdefault("options", enum_options)
    return options


def _sanitize_segment(segment: str) -> str:
    return segment.replace(".", "_").replace(" ", "_")


def _format_output_name(base_name: str, path: Sequence[str] | None = None) -> str:
    tokens: list[str] = []
    if base_name:
        tokens.append(_sanitize_segment(base_name))
    if path:
        tokens.extend(_sanitize_segment(part) for part in path if part)
    return "_".join(tokens) if tokens else "out"


def _derive_union_base_name(models: Sequence[type[BaseModel]]) -> str:
    names = [model.__name__ for model in models if getattr(model, "__name__", None)]
    if not names:
        return "Union"
    prefix = os.path.commonprefix(names).rstrip("_")
    if prefix and len(prefix) >= 3:
        return prefix
    return names[0]


def _annotate_scalar_output(annotation: Any, name: str) -> Any:
    """Attach an ``OutputMeta`` name to scalar return annotations."""

    base = annotation
    metadata: list[Any] = []
    if get_origin(annotation) is Annotated:
        args = list(get_args(annotation))
        base = args[0]
        metadata = args[1:]
    return Annotated[base, *metadata, OutputMeta(name=name)]


def _extract_output_name(annotation: Any) -> str | None:
    """Return a custom output name defined via ``Annotated`` metadata if present."""

    if get_origin(annotation) is not Annotated:
        return None

    args = get_args(annotation)
    base = args[0]
    metas = args[1:]

    for meta in metas:
        name = _name_from_meta(meta)
        if name:
            return _sanitize_segment(name)

    # Support nested Annotated layers
    return _extract_output_name(base)


def _name_from_meta(meta: Any) -> str | None:
    if isinstance(meta, Mapping):
        name = meta.get("name")
        if isinstance(name, str) and name:
            return name
    if isinstance(meta, FieldInfo):
        extra = meta.json_schema_extra or {}
        name = extra.get("funcnodes_output_name") or extra.get("name")
        if isinstance(name, str) and name:
            return name
    name = getattr(meta, "name", None)
    if isinstance(name, str) and name:
        return name
    return None


def _enum_options(annotation: Any) -> list[Any] | None:
    """Return enum/literal choices if the annotation encodes them."""

    base = _base_annotation(annotation)
    origin = get_origin(base)
    if origin is Union:
        args = [arg for arg in get_args(base) if arg is not type(None)]
        if len(args) == 1:
            base = args[0]
            origin = get_origin(base)
    if isinstance(base, type) and issubclass(base, Enum):
        return [member.value for member in base]
    if origin is typing.Literal:  # type: ignore[attr-defined]
        return list(get_args(base))
    return None


@lru_cache(maxsize=256)
def _collect_field_summaries(
    model_cls: type[BaseModel], levels: int | None
) -> tuple[_FieldSummary, ...]:
    """Walk ``model_cls`` and collect all fields up to ``levels`` deep.

    When ``levels`` is ``None`` the traversal continues until it reaches
    non-``BaseModel`` leaves, with cycle detection to avoid infinite recursion.
    """

    def _walk(
        current_cls: type[BaseModel],
        remaining: int | None,
        ancestors: tuple[type[BaseModel], ...],
    ) -> typing.Iterator[_FieldSummary]:
        for name, field in current_cls.model_fields.items():
            alias = field.alias or name
            annotation = field.annotation
            field_type = _base_annotation(annotation)
            is_model = isinstance(field_type, type) and issubclass(
                field_type, BaseModel
            )

            should_descend = (
                is_model
                and (remaining is None or remaining > 1)
                and field_type not in ancestors
            )
            if should_descend:
                next_levels = None if remaining is None else remaining - 1
                next_ancestors = ancestors + (field_type,)
                for nested in _walk(field_type, next_levels, next_ancestors):
                    yield _FieldSummary(
                        path=(name, *nested.path),
                        alias_path=(alias, *nested.alias_path),
                        annotation=nested.annotation,
                        field_info=nested.field_info,
                        is_model=nested.is_model,
                    )
            else:
                yield _FieldSummary(
                    path=(name,),
                    alias_path=(alias,),
                    annotation=annotation,
                    field_info=field,
                    is_model=is_model,
                )

    return tuple(_walk(model_cls, levels, (model_cls,)))


def _base_annotation(annotation: Any) -> Any:
    """Strip ``Annotated`` and ``Optional`` wrappers to expose the core type."""

    origin = get_origin(annotation)
    if origin is Annotated:
        annotation = get_args(annotation)[0]
        origin = get_origin(annotation)
    annotation, _ = _strip_optional(annotation)
    return annotation


def _strip_optional(annotation: Any) -> tuple[Any, bool]:
    """Remove ``None`` from simple ``Union`` annotations (Optional[T])."""

    origin = get_origin(annotation)
    if origin is Union:
        args = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(args) == 1:
            return args[0], True
    return annotation, False


def _assign_path(container: dict[str, Any], path: Sequence[str], value: Any) -> None:
    """Write ``value`` into ``container`` at the provided dotted path."""

    current = container
    for index, token in enumerate(path):
        if index == len(path) - 1:
            current[token] = value
        else:
            current = current.setdefault(token, {})


def _build_output_specs(
    model_cls: type[BaseModel], levels: int | None, base_name: str
) -> tuple[_OutputFieldSpec, ...]:
    """Reuse `_collect_field_summaries` to prepare return-value metadata.

    ``levels`` accepts ``None`` for unbounded traversal, mirroring the input
    handling logic.
    """

    summaries = _collect_field_summaries(model_cls, levels)
    specs: list[_OutputFieldSpec] = []
    for summary in summaries:
        meta: OutputMeta = OutputMeta(
            name=_format_output_name(base_name, summary.alias_path),
            description=summary.field_info.description or "",
        )
        value_options = _derive_value_options(summary.field_info, summary.annotation)
        if value_options:
            meta["value_options"] = value_options
        specs.append(_OutputFieldSpec(path=summary.path, meta=meta))
    return tuple(specs)


def _annotation_for_output(model_cls: type[BaseModel], path: Sequence[str]) -> Any:
    """Fetch the original field annotation for the provided path."""

    current: type[BaseModel] | None = model_cls
    field: FieldInfo | None = None
    for segment in path:
        if current is None:
            return Any
        field = current.model_fields.get(segment)
        if field is None:
            return Any
        next_type = _base_annotation(field.annotation)
        current = (
            next_type
            if isinstance(next_type, type) and issubclass(next_type, BaseModel)
            else None
        )
    return field.annotation if field else Any


def _extract_value(model: BaseModel, path: Sequence[str]) -> Any:
    """Traverse a BaseModel/dict graph to read the field at ``path``."""

    current: Any = model
    for token in path:
        if isinstance(current, BaseModel):
            current = getattr(current, token)
        elif isinstance(current, dict):
            current = current[token]
        else:
            current = getattr(current, token)
    return current


__all__ = ["PydanticUnpacker"]
