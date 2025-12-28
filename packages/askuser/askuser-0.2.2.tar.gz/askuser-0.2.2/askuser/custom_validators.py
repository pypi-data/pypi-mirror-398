"""
askuser.custom_validators

This module provides the *official* way to extend AskUser with custom validators.

Why this exists:
- AskUser ships with a built-in validator registry (name -> function).
- Some projects need additional validators (e.g., DB checks) that should NOT be imported
  by default (to keep imports fast and avoid heavy dependencies).
- Instead of mutating internal globals directly, projects can register validators via
  these helpers.

Validator contract:
- A validator is a callable where the first argument is `user_input: str`.
- It must return the validated/normalized value on success.
- It must raise ValueError on invalid input (AskUser will re-prompt).
"""

from __future__ import annotations

from typing import Callable, Mapping, Any

from .core import VALIDATOR_FUNC

ValidatorFn = Callable[..., Any]


def get_validators() -> dict[str, ValidatorFn]:
    """
    Return the live validator registry.

    Notes:
    - This returns the underlying registry dict used by AskUser.
    - Mutating this dict directly will affect behavior globally in-process.
      Prefer register_validator/register_validators for intentional changes.
    """
    return VALIDATOR_FUNC


def register_validator(name: str, func: ValidatorFn, *, overwrite: bool = False) -> None:
    """
    Register a custom validator by name.

    Args:
        name: The validation_type string used by validate_input(...).
        func: The validator function. Must be callable and should raise ValueError on invalid input.
        overwrite: If False (default), raises KeyError if name is already registered.

    Raises:
        ValueError: If name is blank or func is not callable.
        KeyError: If name already exists and overwrite=False.

    Example:
        def is_valid_even_int(user_input: str) -> int:
            n = int(user_input)
            if n % 2 != 0:
                raise ValueError("Must be even")
            return n

        register_validator("even_int", is_valid_even_int)
        x = validate_input("Enter even:", "even_int")
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Validator name must be a non-empty string")
    if not callable(func):
        raise ValueError(f"Validator func for '{name}' must be callable")

    key = name.strip().lower()

    if key in VALIDATOR_FUNC and not overwrite:
        raise KeyError(
            f"Validator '{key}' already exists. "
            f"Pass overwrite=True to replace it intentionally."
        )

    VALIDATOR_FUNC[key] = func


def register_validators(validators: Mapping[str, ValidatorFn], *, overwrite: bool = False) -> None:
    """
    Register many validators at once.

    Args:
        validators: Mapping of {name: func}.
        overwrite: If False (default), raises on the first duplicate name.

    Example:
        register_validators({
            "movie_ids": is_valid_movie_ids,
            "bundle_ids": is_valid_bundle_ids,
        })
    """
    for name, func in validators.items():
        register_validator(name, func, overwrite=overwrite)


def unregister_validator(name: str) -> bool:
    """
    Remove a validator from the registry.

    Returns:
        True if removed, False if it didn't exist.

    Why include this:
    - Useful for tests, temporary overrides, and interactive CLI tooling.

    Note:
    - We intentionally keep this small and explicit; no magic reset logic here.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Validator name must be a non-empty string")
    key = name.strip().lower()
    return VALIDATOR_FUNC.pop(key, None) is not None


__all__ = [
    "get_validators",
    "register_validator",
    "register_validators",
    "unregister_validator",
]
