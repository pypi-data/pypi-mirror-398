# AskUser

**AskUser** is a smart CLI utility for collecting and validating user input in Python. It wraps common prompt patterns—validation, menus, defaults, multi-selects, and autocompletion—into a simple, consistent API.

---

## 📑 Table of Contents

- [Installation](#-installation)
- [API Overview](#-api-overview)
- [`validate_input`](#-validate_input)
- [Menus & Options](#-menus--options)
- [Database-Style Selection](#-database-style-selection)
- [Yes/No Shortcut](#-yesno-shortcut)
- [Autocomplete](#-autocomplete)
- [Validation Types](#-validation-types)
- [Custom Validators (Extension API)](#-custom-validators-extension-api)
- [Testing](#-testing)
- [License](#-license)

---

## 📦 Installation

```bash
pip install askuser
```

---

## 📖 API Overview

| Function / Class                                  | What It Does |
|--------------------------------------------------|--------------|
| `validate_input(...)`                            | Prompt for free-form input, validate type/pattern, retry until valid |
| `pretty_menu(*args, **kwargs)`                   | Print a formatted menu |
| `validate_user_option(...)`                      | Show a menu and return the selected **key** |
| `validate_user_option_value(...)`                | Return the selected **value** |
| `validate_user_option_enumerated(...)`           | Enumerate a dict and return `(key, value)` |
| `validate_user_option_multi(...)`                | Multi-select menu (returns keys) |
| `validate_user_option_value_multi(...)`          | Multi-select menu (returns values) |
| `choose_from_db(...)`                            | Select an existing DB id from tabulated rows |
| `choose_dict_from_list_of_dicts(...)`            | Select and return a dict |
| `yes(...)`                                       | Yes/No shortcut |
| `user_prompt(...)`                               | Prompt with autocomplete |
| `SubstringCompleter`                             | Substring-based completer (advanced use) |

---

## 🔍 `validate_input`

```python
validate_input(
    input_msg: str,
    validation_type: str | Literal[
      'custom','required','not_in','none_if_blank','yes_no',
      'int','float','decimal','alpha','alphanum','custom_chars','regex',
      'date','future_date','time','url','slug','email','phone','language'
    ],
    expected_inputs: list = None,
    not_in:        list = None,
    maximum:       int | float = None,
    minimum:       int | float = None,
    allowed_chars: str = None,
    allowed_regex: str = None,
    default:       Any = None
) -> Union[str,int,float,None]
```

### Behavior

- **Defaults**  
  - If `default` is set, pressing Enter returns the default.
- **Automatic hints**  
  - `yes_no` → `(y/n)`
  - `none_if_blank` → `(optional)`
  - `time` → `(hh:mm:ss)`
  - `maximum` / `minimum` → `(max: …)` / `(min: …)`
  - `default` → `(default: …)`
- **Validation types**
  - **Built-in:** `int`, `float`, `decimal`, `alpha`, `alphanum`, `date`, `future_date`, `time`, `url`, `email`, `phone`, `slug`, `language`.
  - **List/pattern helpers:**
    - `custom` with `expected_inputs=[...]`
    - `not_in` with `not_in=[...]`
    - `custom_chars` with `allowed_chars="abc123"`
    - `regex` with `allowed_regex="^[A-Z]+$"`
- **Errors**  
  - Invalid input raises internally and the user is re-prompted.

### Example

```python
count = validate_input(
    "How many items?",
    "int",
    minimum=1,
    maximum=100,
    default=10
)
```

---

## 🧭 Menus & Options

### `pretty_menu(*args, **kwargs)`

Prints a menu without prompting:

```python
pretty_menu("List", "Add", d="Delete", q="Quit")
```

Output:
```
0: List    1: Add    d: Delete    q: Quit
```

> **Keys are case-sensitive.** What you see is what you type.

---

### `validate_user_option(...)`

```python
validate_user_option(
    input_msg: str = "Option:",
    *args,
    **kwargs  # pass q=False to suppress quit
) -> Any
```

- **Auto-adds** `q: quit` unless `q=False`
- Returns the selected **key**
- For `**kwargs`
- For `*args`, keys are enumerated strings (`"0"`, `"1"`, …)

```python
opt = validate_user_option("Pick:", "Red", "Blue", g="Green")
# keys: '0','1','g','q'

opt = validate_user_option("Pick:", "One", "Two", q=False)
# keys: '0','1'
```

---

### `validate_user_option_value(...)`

- Builds same menu, returns the **value**.
- **No `q` by default** (legacy behavior).

```python
genre = validate_user_option_value(a="Action", c="Comedy", d="Drama")
# 'c' → "Comedy"
```

---

### `validate_user_option_multi(...)`

- **Multi-select** version of `validate_user_option`.
- Exit with **`d: done`** by default. If `d` is already used in your options, exit appears as **`xd`**, or **`xd2`**, **`xd3`**, ...
- Pass **`d=False`** to disable exit and force “pick until exhausted.”
- Returns a list of **keys** in the order picked.

```python
STATUS = {0: "new", 1: "active", 7: "rejected"}
picked = validate_user_option_multi("Select statuses:", **STATUS)
# → [1, 7]
```

- Exit with `d: done` (or `xd`, `xd2`, … if `d` is taken)
- Pass `d=False` to force selection until exhausted

---

### `validate_user_option_value_multi(...)`

- **Multi-select** version of `validate_user_option_value`.

```python
vals = validate_user_option_value_multi(
    "Pick genres",
    a="Action",
    c="Comedy",
    d="Drama"
)
# user picks: c, a → ['Comedy', 'Action']
```

---

### `validate_user_option_enumerated(dict, msg="Option:", start=1)`

```python
validate_user_option_enumerated(
    a_dict: dict,
    msg: str = "Option:",
    start: int = 1
) -> tuple
```

- Enumerates `.items()` starting at `start`.
- Adds `q: quit`.
- Returns `(key, value)` or `('q', None)`.

```python
movies = {101: "Inception", 202: "Memento"}
mid, title = validate_user_option_enumerated(movies, start=1)
```

- Enumerates dict items
- Adds `q: quit`
- Returns `(key, value)` or `('q', None)`

---

## 🗄 Database-Style Selection

### `choose_from_db(db_result, input_msg=None, table_desc=None, xq=False)`

```python
choose_from_db(
    db_result: list[dict],
    input_msg: str = None,
    table_desc: str = None,
    xq: bool = False
) -> tuple
```

- Pretty-prints rows with `tabulate`.
- Only **existing** `id` values in `db_result` are valid.
- If `xq=True`, also accepts `xq` → returns `('xq', 'quit')`.
- Invalid entries re-prompt.

---

### `choose_dict_from_list_of_dicts(list_of_dicts, key_to_choose)`

```python
choose_dict_from_list_of_dicts(
    list_of_dicts: list[dict],
    key_to_choose: str
) -> dict
```

- Menu of `dict[key_to_choose]`.
- Returns selected dict.

```python
fruits = [
    {"name": "Apple", "color": "red"},
    {"name": "Banana", "color": "yellow"},
]
choice = choose_dict_from_list_of_dicts(fruits, "name")
```

---

## ✅ Yes/No Shortcut

```python
yes("Continue?", default="y")  # True if 'y', False if 'n'; blank → default
```

---

## 💬 Autocomplete

```python
from askuser.autocomplete import user_prompt

country = user_prompt("Country: ", ["USA", "UK", "IN"])
# typing ≥2 chars will start showing suggestions from list
```

With dicts:
- return_value=True returns the value (defaults to False, returning the key)
```python
opts = {"usa": "United States", "uk": "United Kingdom"}
val = user_prompt("Code: ", opts, return_value=True)
print(val)
# Code: usa
# United States

```

---

## 🔎 Validation Types

This table reflects **actual runtime behavior**, including case handling.

| Type            | Description |
|-----------------|-------------|
| `required`      | Must not be blank |
| `none_if_blank` | Blank input returns `None` |
| `yes_no`        | Accepts `y` / `n` (case-insensitive, normalized to lowercase) |
| `int`           | Integer with optional `minimum` / `maximum` |
| `float`         | Float with optional `minimum` / `maximum` |
| `decimal`       | `Decimal` with optional bounds |
| `alpha`         | Alphabetic characters only |
| `alphanum`      | Alphanumeric characters only |
| `date`          | `YYYY-MM-DD` or `YYYY-MM-DD HH:MM:SS` |
| `future_date`   | Date must be today or in the future |
| `time`          | `HH:MM:SS` |
| `email`         | RFC-compliant email |
| `phone`         | Digits with optional `+` (spaces/dashes stripped) |
| `url`           | Hostname with optional path/query |
| `slug`          | Lowercased `[a-z0-9-]`, deduplicated delimiter |
| `language`      | ISO-639 via `pycountry` |
| `custom`        | Exact match against `expected_inputs` (**case-sensitive**) |
| `not_in`        | Reject values in `not_in` (**case-insensitive comparison**) |
| `custom_chars`  | Only characters in `allowed_chars` |
| `regex`         | Must match provided regex |

> **Design note:** Case-sensitivity is intentional.  
> If you want case-insensitive behavior for `custom`, normalize input yourself or register a custom validator.

---

## 🧩 Custom Validators (Extension API)

AskUser supports registering additional validators at runtime without mutating internal globals directly.

```python
from askuser import register_validator, validate_input

def is_even(user_input: str) -> int:
    n = int(user_input)
    if n % 2:
        raise ValueError("Must be even")
    return n

register_validator("even", is_even)

x = validate_input("Enter even number:", "even")
```

Helpers available:

- `get_validators()`
- `register_validator(name, func, overwrite=False)`
- `register_validators({name: func, ...}, overwrite=False)`
- `unregister_validator(name)`

---

## 🧪 Testing

Under `tests/`, examples:

```python
import pytest
from askuser import validate_input, yes, validate_user_option

def test_default(monkeypatch):
    monkeypatch.setattr('builtins.input', lambda _: '')
    assert validate_input("Prompt?", "int", default=7) == 7

def test_no_quit(monkeypatch):
    monkeypatch.setattr('builtins.input', lambda _: '0')
    assert validate_user_option("Pick:", "A", "B", q=False) == '0'
```

Run:
```bash
pytest tests/
```

---

## 📜 License

MIT — free to use, modify, and distribute.
