from __future__ import annotations

import typing
from typing import Union

from pydantic import BaseModel

from funcnodes_pydantic.union_flattener import resolve_union_models


class ModelA(BaseModel):
    value: int


class ModelB(BaseModel):
    value: int


def test_resolve_union_models_supports_annotated_union_members():
    AnnotatedA = typing.Annotated[ModelA, "meta"]
    models = resolve_union_models(Union[AnnotatedA, ModelB])
    assert models == [ModelA, ModelB]

