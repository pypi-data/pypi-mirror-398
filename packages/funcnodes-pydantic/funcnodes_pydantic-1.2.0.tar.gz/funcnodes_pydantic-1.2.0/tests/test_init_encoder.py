from __future__ import annotations

from pydantic import BaseModel

import funcnodes_pydantic as fnp


class ExampleModel(BaseModel):
    value: int


def test_encode_base_model_returns_encdata():
    encoded = fnp._encode_base_model(ExampleModel(value=1))
    assert encoded.handeled is True
    assert encoded.done is False
    assert isinstance(encoded.data, dict)
    assert set(encoded.data.keys()) == {"data", "schema"}
    assert encoded.data["data"]["value"] == 1
    assert "properties" in encoded.data["schema"]


def test_encode_base_model_passes_through_non_models():
    encoded = fnp._encode_base_model(123)
    assert encoded.handeled is False
    assert encoded.data == 123

