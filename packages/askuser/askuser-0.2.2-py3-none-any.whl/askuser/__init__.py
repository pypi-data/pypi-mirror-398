"""
AskUser - Smart input prompt and validation helpers for Python CLI apps.
"""

# core.py (main public API)
from .core import (
    validate_input,
    pretty_menu,
    validate_user_option,
    validate_user_option_value,
    validate_user_option_enumerated,
    validate_user_option_multi,
    validate_user_option_value_multi,
    choose_from_db,
    choose_dict_from_list_of_dicts,
    yes,
)

# logic.py (backwards compatibility exports)
from .logic import (
    is_valid_custom,
    is_not_in,
    is_yes_no,
    none_if_blank,
    is_not_blank,
    is_valid_int,
    is_valid_float,
    is_valid_decimal,
    is_valid_alpha,
    is_valid_alphanum,
    is_valid_regex,
    is_valid_char,
    get_language_ISO_639_1,
    is_valid_language,
    is_valid_date,
    is_valid_date_future,
    is_valid_time,
    is_url,
    is_valid_email,
    is_valid_phone,
    is_valid_slug,
)

# autocomplete.py
from .autocomplete import user_prompt, SubstringCompleter

# Optional extension API
from .custom_validators import (
    get_validators,
    register_validator,
    register_validators,
    unregister_validator,
)

__all__ = [
    # core
    "validate_input",
    "pretty_menu",
    "validate_user_option",
    "validate_user_option_value",
    "validate_user_option_enumerated",
    "validate_user_option_multi",
    "validate_user_option_value_multi",
    "choose_from_db",
    "choose_dict_from_list_of_dicts",
    "yes",
    # logic (legacy / public validators)
    "is_valid_custom",
    "is_not_in",
    "is_yes_no",
    "none_if_blank",
    "is_not_blank",
    "is_valid_int",
    "is_valid_float",
    "is_valid_decimal",
    "is_valid_alpha",
    "is_valid_alphanum",
    "is_valid_regex",
    "is_valid_char",
    "get_language_ISO_639_1",
    "is_valid_language",
    "is_valid_date",
    "is_valid_date_future",
    "is_valid_time",
    "is_url",
    "is_valid_email",
    "is_valid_phone",
    "is_valid_slug",
    # autocomplete
    "user_prompt",
    "SubstringCompleter",
    # extension hooks
    "get_validators",
    "register_validator",
    "register_validators",
    "unregister_validator",
]
