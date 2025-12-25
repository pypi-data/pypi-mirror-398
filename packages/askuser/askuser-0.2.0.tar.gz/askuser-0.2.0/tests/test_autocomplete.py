import pytest

from askuser.autocomplete import user_prompt


class DummySession:
    def __init__(self, response):
        self.response = response

    def prompt(self, msg, completer=None):
        return self.response


def test_user_prompt_list(monkeypatch):
    monkeypatch.setattr('askuser.autocomplete.PromptSession', lambda: DummySession('apple'))
    res = user_prompt('Enter', ['apple', 'banana'])
    assert res == 'apple'


def test_user_prompt_dict(monkeypatch):
    items = {'key1': 'value1', 'key2': 'value2'}
    monkeypatch.setattr('askuser.autocomplete.PromptSession', lambda: DummySession('key2'))
    res = user_prompt('Choose', items, return_value=True)
    assert res == 'value2'


def test_user_prompt_invalid_items():
    with pytest.raises(ValueError):
        user_prompt('Enter', 'not a list')
