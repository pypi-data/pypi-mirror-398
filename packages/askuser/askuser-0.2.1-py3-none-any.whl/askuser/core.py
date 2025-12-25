from typing import Any, Dict, Union, Hashable, Literal

from colorfulPyPrint.py_color import print_blue, input_custom
from string_list import str_enumerate
from tabulate import tabulate

from .logic import (
    is_valid_alpha,
    is_valid_alphanum,
    is_valid_char,
    is_valid_custom,
    is_valid_date,
    is_valid_decimal,
    is_valid_email,
    is_valid_float,
    is_valid_date_future,
    is_valid_int,
    is_valid_language,
    none_if_blank,
    is_not_in,
    is_valid_phone,
    is_valid_regex,
    is_not_blank,
    is_valid_slug,
    is_valid_time,
    is_url,
    is_yes_no,
)

BuiltinValidationType = Literal[
    'custom', 'required', 'not_in', 'none_if_blank', 'yes_no',
    'int', 'float', 'decimal', 'alpha', 'alphanum', 'custom_chars', 'regex',
    'date', 'future_date', 'time',
    'url', 'slug', 'email', 'phone', 'language']

VALIDATOR_FUNC = {
    'alpha': is_valid_alpha,
    'alphanum': is_valid_alphanum,
    'custom_chars': is_valid_char,
    'custom': is_valid_custom,
    'date': is_valid_date,
    'decimal': is_valid_decimal,
    'email': is_valid_email,
    'float': is_valid_float,
    'future_date': is_valid_date_future,
    'int': is_valid_int,
    'language': is_valid_language,
    'none_if_blank': none_if_blank,
    'not_in': is_not_in,
    'phone': is_valid_phone,
    'regex': is_valid_regex,
    'required': is_not_blank,
    'slug': is_valid_slug,
    'time': is_valid_time,
    'url': is_url,
    'yes_no': is_yes_no,
}


def validate_input(input_msg: str,
                   validation_type: Union[str, BuiltinValidationType],
                   expected_inputs: list = None,
                   not_in: list = None,
                   maximum=None, minimum=None,
                   allowed_chars: str = None, allowed_regex: str = None,
                   default=None):
    """
    The validate_input function is used to validate user input.
    
    The validation_type can be as follows:
     - custom: Allow only values passed as list in expected_inputs parameter
     - required: Make sure that the user enters something
     - not_in: Validate that the user input is not in a list of values passed in the not_in parameter
     - none_if_blank: Allow the user to enter nothing (by hitting enter), which will return None
     - yes_no: Validate yes/no input
     - int: Validate the user input is an integer
     - float: Validate a float value
     - alpha: Validate that the user input is alphabetic
     - alphanum: Validate user input to ensure it is alphanumeric
     - custom_chars: Validate the user input against a set of characters passed in custom_chars parameter
     - regex: Validate the user input against a regular expression
     - date: Validate the user input as a date
     - future_date: Validate a date that is in the future
     - time: Validate user_input is in time format
     - url: Validate that user_input is a valid url
     - email: Validate the user input is an email address
     - language: Validate the user_input is a valid language
    
    :param input_msg: str: Display a message to the user
    :param validation_type: Type of validation to be performed on user input
       
    :param expected_inputs: list: Define the allowed values for 'custom' validation
    :param not_in: list: Define the the values that should not be in user_input for 'not_in' validation
    :param maximum: int: Define the maximum value for 'int' and 'float' validation
    :param minimum: int: Define the minimum value for 'int' and 'float' validation
    :param allowed_chars: str: Define the allowed characters for 'custom_chars' validation
    :param allowed_regex: str: Define the allowed regex for 'regex' validation
    :param default: Set a default value for the user_input (if user doesn't enter anything)
    :return: The user input if it is valid, or throw an appropriate error message and ask for user_input again
    """
    hints = []
    vt = validation_type.strip().lower()
    if vt not in VALIDATOR_FUNC:
        raise ValueError(f"Unknown validation_type: '{vt}'. Did you forget to register it?")

    # Validators that require extra parameters
    if vt == "custom" and expected_inputs is None:
        raise ValueError("validation_type='custom' requires expected_inputs")
    if vt == "not_in" and not_in is None:
        raise ValueError("validation_type='not_in' requires not_in")
    if vt == "custom_chars" and allowed_chars is None:
        raise ValueError("validation_type='custom_chars' requires allowed_chars")
    if vt == "regex" and allowed_regex is None:
        raise ValueError("validation_type='regex' requires allowed_regex")

    if vt == 'yes_no' and '(y/n)' not in input_msg.lower():
        hints.append('(y/n):')
    elif vt == 'none_if_blank' and '(optional)' not in input_msg.lower():
        hints.append('(optional):')
    elif vt == 'time' and '(hh:mm:ss)' not in input_msg.lower():
        hints.append('(hh:mm:ss):')

    if maximum is not None and 'max' not in input_msg.lower():
        hints.append(f'(max: {maximum})')
    if minimum is not None and 'min' not in input_msg.lower():
        hints.append(f'(min: {minimum})')
    if default is not None and 'default' not in input_msg.lower():
        hints.append(f'(default: {default})')

    suffix = ''
    if hints:
        # Only add a space if input_msg is non-empty and doesn't already end with one
        needs_space = bool(input_msg) and not input_msg.endswith(' ')
        suffix = (' ' if needs_space else '') + ' '.join(hints) + ' '

    user_input = input_custom(f"{input_msg}{suffix}")

    # If default is set and user_input is blank
    if len(user_input) == 0 and default is not None:
        return default

    # Otherwise try to validate
    try:
        if vt in ['custom'] and expected_inputs is not None:
            return VALIDATOR_FUNC[vt](user_input, expected_inputs)
        elif vt in ['int', 'float', 'decimal'] and (expected_inputs or maximum or minimum):
            return VALIDATOR_FUNC[vt](user_input, expected_inputs, maximum, minimum)
        elif vt in ['not_in'] and not_in is not None:
            return VALIDATOR_FUNC['not_in'](user_input, not_in)
        elif vt in ['custom_chars'] and allowed_chars is not None:
            return VALIDATOR_FUNC[vt](user_input, allowed_chars)
        elif vt in ['regex'] and allowed_regex is not None:
            return VALIDATOR_FUNC[vt](user_input, allowed_regex)
        else:
            user_input = user_input.strip()
            return VALIDATOR_FUNC[vt](user_input)
    except (ValueError, TypeError):
        print()
        return validate_input(
            input_msg=input_msg,
            validation_type=validation_type,
            expected_inputs=expected_inputs,
            not_in=not_in,
            maximum=maximum,
            minimum=minimum,
            allowed_chars=allowed_chars,
            allowed_regex=allowed_regex,
            default=default,
        )


def pretty_menu(*args, **kwargs):
    """
    Displays in a nice menu format, based on args and kwargs
    For example:
        1: Create bundle    2: Add sections     3: Add movies
        o: Order movies     dm: Order movies    db: Delete bundle

    :param args: a list of values (will be displayed as <num>: value)
    :param kwargs: a dict of key-value pairs (will be displayed key: value)
    """
    ops_dict = {}

    for i, op in enumerate(args):
        ops_dict[str(i)] = op
    for i, op in kwargs.items():
        ops_dict[str(i)] = op

    if not ops_dict:
        print()
        return

    longest_option = max(len(str(k)) for k in ops_dict)
    longest_desc = max(len(str(v)) for v in ops_dict.values())
    count = 0
    print()
    for i, op in ops_dict.items():
        if len(ops_dict) > 5:
            print_blue(i.rjust(longest_option), end="")
            print(f": {op}".ljust(longest_desc + 5), end="")
            count += 1
            if count % 3 == 0:
                print()
        else:
            print_blue(i, end="")
            print(f": {op}")
    if count % 3 != 0:  # Add a line for the input_msg (else it will print in same line)
        print()


def validate_user_option(input_msg: str = 'Option:', *args: Any, **kwargs: Any) -> Union[str, int, Hashable]:
    """
    Displays menu for user, and returns validated user's option (the key).
    - For **kwargs menus**: returns the ORIGINAL key type (e.g., int keys stay ints).
    - For *args menus*: keys are enumerated strings ("0","1",...), same as before.
    - Auto-adds q: quit unless q=False is passed.

    For example:
        1: Create bundle    2: Add sections     3: Add movies
        o: Order movies     dm: Order movies    db: Delete bundle
        q: quit
        Option: 2
        > 2

        :param input_msg: Instructions for user
        :param args: [operation_descriptions]
        :param kwargs: {key: operation_description}
        :return: user selection (key for **kwargs, number for *args)
    """
    ops_dict: Dict[str, str] = {}
    # Reverse map to preserve original key types when kwargs are used
    orig_key_by_menu_key: Dict[str, Hashable] = {}

    # Positional args → "0","1",...  (unchanged)
    for i, op in enumerate(args):
        menu_key = str(i)
        ops_dict[menu_key] = str(op)

    # Keyword args → preserve original key type via reverse map
    for k, v in kwargs.items():
        # Keep menu key as string for display / validation, but remember the original key
        menu_key = str(k)
        ops_dict[menu_key] = str(v) if v is not False else False
        orig_key_by_menu_key[menu_key] = k

    # Handle q option like before
    if 'q' not in ops_dict:
        ops_dict['q'] = 'quit'
    elif ops_dict['q'] is False:  # q=False suppresses quit
        ops_dict.pop('q')

    # Pretty print (same layout logic as your existing function)
    items_per_col = 3
    longest_option = (max(len(str(k)) for k in ops_dict)) if ops_dict else 1
    longest_desc = (max(len(str(v)) for v in ops_dict.values())) if ops_dict else 1
    count = 0
    print()
    for i, op in ops_dict.items():
        if len(ops_dict) > 5:
            # Calculate items per column (max row length = 120 characters)
            max_item_len = longest_desc + len(': ') + longest_option + 5
            items_per_col = max(1, int(120 / max_item_len))
            print_blue(i.rjust(longest_option), end="")
            print(f": {op}".ljust(longest_desc + 5 - len(i) + 1), end="")
            count += 1
            if count % items_per_col == 0:
                print()
        else:
            print_blue(i, end="")
            print(f": {op}")
    if count % items_per_col != 0:
        print()

    # Validate input against the displayed menu keys
    choice: str = validate_input(input_msg, "custom", expected_inputs=list(ops_dict.keys()))

    # Map back to original key type when possible (kwargs)
    if choice in orig_key_by_menu_key:
        return orig_key_by_menu_key[choice]
    return choice  # covers *args case (string indices) and 'q'


def validate_user_option_value(input_msg: str = 'Option:', *args: Any, **kwargs: Any) -> Any:
    """
    Like validate_user_option but returns the VALUE for the chosen key.
    - For *args: we enumerate into "0","1",... and return the matching value.
    - For **kwargs: we map the preserved original key to its value.

    For example:
    a_dict = {'a': 'ABC', 'd': 'DEF', 'g': 'GHI', 'j': 'JKL', 'n': 'NOP', 'q': 'QRS'}
    start = 1
    will result in
        a: ABC    d: DEF    g: GHI
        j: JKL    n: NOP    q: QRS
        q: quit
        Option: n
        > 'NOP'

    :param input_msg: Instructions for user
    :param kwargs: {key: operation_description}
    :return: value based on key selected by user
    """
    # If list has been passed as arguments add them to kwargs
    if args:
        arg_dict = str_enumerate(list(args))  # keys are strings "0","1",...
        if kwargs:
            arg_dict.update(kwargs)
        kwargs = arg_dict

    # Add q=False if it is not in kwargs,
    # if q=(something other than False), make xq=(something other than False) and q=False
    if 'q' not in kwargs:
        kwargs['q'] = False
    else:
        if kwargs['q']:
            kwargs['xq'], kwargs['q'] = kwargs['q'], False

    key = validate_user_option(input_msg, **kwargs)
    return kwargs[key]


def validate_user_option_enumerated(a_dict: dict, msg: str = 'Option:', start: int = 0):
    """
    Takes a dictionary, and asks user options by simplifying the key and
    returns the original key, value from dict based on user selection

    For example:
    a_dict = {194: 'ABC', 289: 'DEF', 923: 'GHI', 901: 'JKL', 920: 'NOP', 390: 'QRS'}
    start = 1
    will result in
        1: ABC    2: DEF    3: GHI
        4: JKL    5: NOP    6: QRS
        q: quit
        Option: 5
        > (920, 'NOP')

    :param a_dict: Any dictionary {id1: value1, id2: value2, ...}
    :param msg: Message you want to display to the user (default - Option:)
    :param start: starting value of count
    :return: {id: value} based on user selection or None if user enters 'q'
    """
    d_enumerated = dict(enumerate(a_dict.items(), start=start))
    d_index_dict = {str(index): boncon_title for index, (boncon_id, boncon_title) in d_enumerated.items()}
    index = validate_user_option(msg, **d_index_dict, q="quit")
    if index == 'q':
        return 'q', None
    else:
        d_id, d_value = d_enumerated[int(index)]
        return d_id, d_value


def validate_user_option_multi(input_msg='Option:', *args, **kwargs) -> list[Any]:
    """
    Multi-select version of validate_user_option.

    - Shows an explicit exit key: 'd: done' by default (no 'q').
    - If caller already uses key 'd', exit becomes 'xd: done'; if 'xd' is taken, 'xd2', 'xd3', ...
    - Returns list of keys in selection order.
      * For **kwargs menus: returns ORIGINAL key types (e.g., int keys stay ints)
      * For *args menus: returns enumerated string keys "0","1",...
    - To disable exit entirely (force select-until-exhausted), pass d=False.
    """
    # Build menu display dict and reverse map for kwargs to preserve original key types
    menu = {}
    kw_reverse = {}  # menu_key(str) -> original key (could be int, str, etc.)

    # Positional options → "0","1",...
    for i, op in enumerate(args):
        mk = str(i)
        menu[mk] = str(op)

    # Keyword options → remember original key types
    # If d=False was passed, treat as "suppress exit" signal (remove it from options).
    suppress_done = ('d' in kwargs and kwargs['d'] is False)
    kw_items = {k: v for k, v in kwargs.items() if not (k == 'd' and kwargs['d'] is False)}

    for k, v in kw_items.items():
        mk = str(k)
        menu[mk] = str(v)
        kw_reverse[mk] = k  # preserve original type

    # Decide exit key (d / xd / xd2 / ...)
    exit_key = None
    if not suppress_done:
        candidate = 'd'
        i = 0
        existing_keys = set(menu.keys())
        while candidate in existing_keys:
            i += 1
            candidate = 'xd' if i == 1 else f'xd{i}'
        exit_key = candidate
        menu[exit_key] = 'done'

    selected = []
    while menu:
        # Suppress 'q' in the underlying single-select to avoid showing/accepting it
        choice = validate_user_option(input_msg, q=False, **menu)

        # Exit when user picks the done key
        if exit_key is not None and choice == exit_key:
            break

        # Map back to original key type if this came from kwargs; otherwise keep the string key (args path)
        selected.append(kw_reverse.get(choice, choice))

        # Remove the picked option so it won't show again
        menu.pop(choice, None)

        # If the only remaining entry is the exit key, and user must continue, loop will allow picking done next
        if exit_key is not None and len(menu) == 1 and exit_key in menu:
            # continue to allow user to hit 'done' explicitly
            pass

        # If exit was suppressed, loop will end when all options are consumed
        if not menu:
            break

    return selected


def validate_user_option_value_multi(input_msg='Option:', *args, **kwargs) -> list[Union[str, int, Hashable]]:
    """
    Multi-select version of validate_user_option_value.

    Behavior:
    - Uses 'd: done' as the exit key (handled inside validate_user_option_multi). No 'q'.
    - If caller passes d=False, exit is suppressed and the user must pick until options are exhausted.
    - For **kwargs menus: original key types are preserved (e.g., int keys stay ints).
    - For *args menus: options are enumerated as "0","1",... (strings), same as single-select.

    Returns:
        list: Values corresponding to the selections, in the order picked.
    """
    # Build menu dict like validate_user_option_value (enumerate *args into "0","1",...)
    if args:
        arg_dict = str_enumerate(list(args))
        if kwargs:
            arg_dict.update(kwargs)
        kwargs = arg_dict

    # Delegate to the key-returning multi; it will handle 'd'/'xd' exit and key-type preservation
    keys = validate_user_option_multi(input_msg, **kwargs)
    return [kwargs[k] for k in keys]


def choose_from_db(db_result, input_msg=None, primary_key='id', table_desc=None, xq=False):
    """
    Displays a list of database results in a tabular format and allows the user to select an entry by ID.

    Args:
        db_result (list of dict): The result set from the database query, where each dict represents a row.
        input_msg (str): Input message to be displayed for user (default - Choose appropriate id: )
        primary_key (str): Default: 'id'. Primary key of the table - becomes key to choose.
        table_desc (str): The description of the query
        xq (bool): Gives option of '(xq: quit)'. Defaults to False

    Returns:
        tuple:
            - chosen_id (int): The ID of the selected entry.
            - chosen_row (dict): The full row data corresponding to the selected ID.
    """
    # Map IDs to their respective rows for quick lookup
    ids = {str(r[primary_key]): r for r in db_result}

    # Display the data in a tabular format for user review
    if table_desc:
        print(' ' * 85 + table_desc.upper())
        print('-' * 188)
    print(tabulate(db_result, headers="keys"))

    # Prompt the user to select an ID
    keys = list(ids.keys())
    quit_msg = ''
    if xq:
        quit_msg = ' (xq: quit)'
        keys += ['xq']
    input_msg = f"{input_msg.replace(': ', '')}{quit_msg}: " if input_msg else f"Choose appropriate id{quit_msg}: "

    chosen_id = validate_input(input_msg, "custom", expected_inputs=keys)

    # Return the selected ID and its corresponding row
    if xq and chosen_id == 'xq':
        return 'xq', 'quit'

    return int(chosen_id), ids[chosen_id]


def choose_dict_from_list_of_dicts(list_of_dicts: list[dict], key_to_choose: str) -> dict:
    """
    The choose_dict_from_list_of_dicts function takes a list of dictionaries and a key to choose from.
    It then creates two dictionaries: one with the keys being the chosen key, and values being the dictionary;
    and another with keys as chosen key, and values as lists of strings containing all other keys in each dictionary.
    The user is prompted to select an option from these lists, which returns that selected dictionary.

    :param list_of_dicts: List[dict]: Pass a list of dictionaries to the function
    :param key_to_choose: str: Specify which key in the dictionary to use for the menu
    :return: A dictionary from the list of dictionaries that is passed to it
    """
    c_dict = {f"{k[key_to_choose]}": k for k in list_of_dicts}
    keys = list(list_of_dicts[0].keys())
    keys.sort(reverse=True)
    choice = {f"{m[key_to_choose]}": [f"{k}: {m[k]}" for k in keys if k != key_to_choose] for m in list_of_dicts}
    selected_dict = c_dict[validate_user_option("Choose movie ID: ", **choice)]
    return selected_dict


def yes(input_msg, default=None):
    return validate_input(input_msg, "yes_no", default=default) == 'y'


__all__ = [
    "BuiltinValidationType",
    "VALIDATOR_FUNC",
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
]
