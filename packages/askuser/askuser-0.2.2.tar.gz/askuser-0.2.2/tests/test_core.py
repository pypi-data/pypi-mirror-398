from askuser.core import (
    validate_input, validate_user_option,
    validate_user_option_value, validate_user_option_enumerated,
    choose_from_db, choose_dict_from_list_of_dicts, yes,
    validate_user_option_multi, validate_user_option_value_multi,
)


# ---------- Helpers ----------

def setup_input(monkeypatch, inputs):
    """Patch console IO so tests are non-interactive."""
    gen = (i for i in inputs)
    # Patch both, to be safe across versions
    try:
        monkeypatch.setattr('askuser.core.input_custom', lambda prompt: next(gen))
    except AttributeError:
        pass

    try:
        monkeypatch.setattr('askuser.core.input_white', lambda prompt: next(gen))
    except AttributeError:
        pass

    # Silence colored menu printing
    monkeypatch.setattr('askuser.core.print_blue', lambda *args, **kwargs: None, raising=False)


def test_validate_input_int(monkeypatch):
    setup_input(monkeypatch, ['42'])
    assert validate_input('Enter number', 'int') == 42


def test_validate_input_default(monkeypatch):
    setup_input(monkeypatch, [''])
    assert validate_input('Enter number', 'int', default=7) == 7


def test_validate_input_custom(monkeypatch):
    setup_input(monkeypatch, ['usd'])
    assert validate_input('Currency?', 'custom', expected_inputs=['usd', 'eur']) == 'usd'


def test_validate_input_not_in(monkeypatch):
    setup_input(monkeypatch, ['new'])
    assert validate_input('Value?', 'not_in', not_in=['old', 'existing']) == 'new'


def test_yes_function(monkeypatch):
    setup_input(monkeypatch, ['y'])
    assert yes('Continue?') is True
    setup_input(monkeypatch, ['n'])
    assert yes('Continue?') is False


def test_yes_uppercase(monkeypatch):
    setup_input(monkeypatch, ['Y'])
    assert yes("Continue?") is True


def test_validate_user_option(monkeypatch):
    setup_input(monkeypatch, ['0'])
    # q is auto-added
    key = validate_user_option('Pick', 'A', 'B')
    assert key == '0'


def test_validate_user_option_no_quit(monkeypatch):
    setup_input(monkeypatch, ['1'])
    # suppress quit
    key = validate_user_option('Pick', 'X', 'Y', q=False)
    assert key == '1'


def test_validate_user_option_value(monkeypatch):
    setup_input(monkeypatch, ['b'])
    val = validate_user_option_value(a='Alpha', b='Beta', c='Gamma')
    assert val == 'Beta'


def test_validate_user_option_enumerated(monkeypatch):
    # start=1 → indices are 1,2,...; pick "1" to get the first pair (10, 'Ten')
    setup_input(monkeypatch, ['1'])
    key, val = validate_user_option_enumerated({10: 'Ten', 20: 'Twenty'}, start=1)
    assert (key, val) == (10, 'Ten')


def test_choose_from_db(monkeypatch):
    data = [{'id': 1, 'name': 'One'}, {'id': 2, 'name': 'Two'}]
    setup_input(monkeypatch, ['2'])
    idx, row = choose_from_db(data)
    assert idx == 2 and row['name'] == 'Two'


def test_choose_from_db_xq(monkeypatch):
    data = [{'id': 1, 'name': 'One'}]
    setup_input(monkeypatch, ['xq'])
    idx, val = choose_from_db(data, xq=True)
    assert idx == 'xq' and val == 'quit'


def test_choose_dict_from_list_of_dicts(monkeypatch):
    # Monkeypatch validate_user_option to return key directly
    monkeypatch.setattr('askuser.core.validate_user_option', lambda msg, **kwargs: 'Banana')
    fruits = [{'name': 'Apple', 'color': 'red'}, {'name': 'Banana', 'color': 'yellow'}]
    chosen = choose_dict_from_list_of_dicts(fruits, 'name')
    assert chosen['color'] == 'yellow'


# ---------- multi-select tests ----------

def test_validate_user_option_multi_with_args(monkeypatch):
    # Select two items then done
    setup_input(monkeypatch, ['0', '2', 'd'])
    keys = validate_user_option_multi("Pick", "Alpha", "Beta", "Gamma")
    assert keys == ['0', '2']  # menu keys from *args enumeration


def test_validate_user_option_multi_with_kwargs(monkeypatch):
    # Select two items by key then done
    setup_input(monkeypatch, ['a', 'c', 'd'])
    keys = validate_user_option_multi("Pick", a='Alpha', b='Beta', c='Gamma')
    assert keys == ['a', 'c']


def test_validate_user_option_multi_mixed_inputs(monkeypatch):
    # *args become 0,1; kwargs add named options; select 1 (args) then 'x' (kwargs) then done
    setup_input(monkeypatch, ['1', 'x', 'd'])
    keys = validate_user_option_multi("Pick", "Alpha", "Beta", x="X-ray", y="Yankee")
    assert keys == ['1', 'x']


def test_validate_user_option_multi_no_exit(monkeypatch):
    # Exit disabled (d=False) → user must pick everything; order may vary
    setup_input(monkeypatch, ['a', 'b', 'c'])
    keys = validate_user_option_multi("Pick (no exit)", d=False, a='Alpha', b='Beta', c='Gamma')
    assert set(keys) == {'a', 'b', 'c'}


def test_validate_user_option_value_multi_with_kwargs(monkeypatch):
    # Select order b, a then done → return values in selection order
    setup_input(monkeypatch, ['b', 'a', 'd'])
    vals = validate_user_option_value_multi("Pick values", a='Alpha', b='Beta', c='Gamma')
    assert vals == ['Beta', 'Alpha']


def test_validate_user_option_value_multi_with_args(monkeypatch):
    # *args path → returns selected values (by enumerated positions)
    setup_input(monkeypatch, ['0', '2', 'd'])
    vals = validate_user_option_value_multi("Pick values", "Red", "Green", "Blue")
    assert vals == ['Red', 'Blue']


def test_validate_user_option_value_multi_done_first(monkeypatch):
    # Immediate done → empty list
    setup_input(monkeypatch, ['d'])
    vals = validate_user_option_value_multi("Pick values", a='Alpha', b='Beta')
    assert vals == []


# ---------- Exit-key collision tests for multi ----------

def test_multi_exit_collision_with_d(monkeypatch):
    # Caller already uses 'd' → exit should become 'xd'
    setup_input(monkeypatch, ['a', 'xd'])
    keys = validate_user_option_multi("Pick", d="DELETE", a="Alpha")
    assert keys == ['a']


def test_multi_exit_collision_with_d_and_xd(monkeypatch):
    # Caller uses both 'd' and 'xd' → exit should become 'xd2'
    setup_input(monkeypatch, ['a', 'xd2'])
    keys = validate_user_option_multi("Pick", d="DELETE", xd="EXTRA", a="Alpha")
    assert keys == ['a']


def test_validate_user_option_preserves_string_key(monkeypatch):
    setup_input(monkeypatch, ['2'])
    key = validate_user_option("Pick:", **{"2": "Two", "10": "Ten"})
    assert key == "2"


def test_substring_completer_basic():
    # You made this public; sanity-check it does what it says.
    from askuser.autocomplete import SubstringCompleter

    class DummyDoc:
        def __init__(self, text):
            self.text_before_cursor = text

    c = SubstringCompleter(["Alpha", "Beta", "Gamma"], min_chars=2)
    out = list(c.get_completions(DummyDoc("al"), None))
    assert any(x.text == "Alpha" for x in out)
