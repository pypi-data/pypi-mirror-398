from __future__ import annotations

import pytest
from pydantic import BaseModel


class Address(BaseModel):
    street: str
    city: str
    zip_code: int


class User(BaseModel):
    id: int
    name: str = "anonymous"
    address: Address
    tags: list[str] = []


@pytest.fixture()
def user_model() -> type[User]:
    return User


@pytest.fixture()
def address_model() -> type[Address]:
    return Address


@pytest.fixture()
def user_payload() -> dict:
    return {
        "id": 1,
        "name": "Jane Doe",
        "address": {"street": "Main St", "city": "Berlin", "zip_code": 10115},
        "tags": ["alpha", "beta"],
    }
