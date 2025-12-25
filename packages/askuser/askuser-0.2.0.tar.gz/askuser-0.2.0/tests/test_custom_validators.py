import pytest

from askuser import validate_input
from askuser.custom_validators import (
    get_validators,
    register_validator,
    register_validators,
    unregister_validator,
)

def test_register_validator_and_validate_input(monkeypatch):
    # Patch input_custom inside askuser.core (same style as your other tests)
    monkeypatch.setattr("askuser.core.input_custom", lambda prompt: "12")

    def is_even(user_input: str) -> int:
        n = int(user_input)
        if n % 2 != 0:
            raise ValueError("Must be even")
        return n

    register_validator("even_int", is_even, overwrite=True)
    assert validate_input("Enter:", "even_int") == 12

    # cleanup (avoid leaking into other tests)
    assert unregister_validator("even_int") is True

def test_register_validator_duplicate_raises():
    def v(user_input: str) -> str:
        return user_input

    register_validator("dup_test", v, overwrite=True)

    with pytest.raises(KeyError):
        register_validator("dup_test", v, overwrite=False)

    assert unregister_validator("dup_test") is True

def test_register_validators_bulk_and_get_validators():
    def v1(x: str) -> str: return x
    def v2(x: str) -> str: return x

    register_validators({"bulk1": v1, "bulk2": v2}, overwrite=True)

    reg = get_validators()
    assert "bulk1" in reg and "bulk2" in reg

    assert unregister_validator("bulk1") is True
    assert unregister_validator("bulk2") is True

def test_unregister_missing_is_false():
    assert unregister_validator("does_not_exist") is False
