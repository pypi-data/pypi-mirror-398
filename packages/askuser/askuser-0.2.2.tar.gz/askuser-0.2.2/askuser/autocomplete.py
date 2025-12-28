from typing import Union

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion


class SubstringCompleter(Completer):
    def __init__(self, items_list, min_chars):
        self.items_list = items_list
        self.min_chars = min_chars

    def get_completions(self, document, complete_event):
        text_before_cursor = document.text_before_cursor
        words = text_before_cursor.split()
        if not words:
            return
        if len(words[-1]) >= self.min_chars:
            last_word = words[-1].lower()
            for item in self.items_list:
                if last_word in item.lower():
                    yield Completion(item, start_position=-len(last_word))


def user_prompt(input_msg, items: Union[list, dict, tuple], return_value=False):
    """
    It takes in an input message, and a list of items to be used as autocomplete options.
    For items that is a list it will always use key to autocomplete.

    Returns the user's input if return_value=False (default), or
    the value associated with that key if return_value=True (only when type(items)==dict)

    :param input_msg: Prompt the user for input
    :param items: Specify that the items parameter can be a list, tuple or dict
    :param return_value: (only if type(items)==dict). Return the value associated with the key selected by user
    :return: A string
    """
    if type(items) is dict:
        items_list = items.keys()
    elif type(items) in [list, tuple]:
        items_list = items
        return_value = False
    else:
        raise ValueError(f"Items can only be list/tuple/dict not {type(items)}")

    completer = SubstringCompleter(items_list, min_chars=2)
    session = PromptSession()

    user_input = session.prompt(input_msg, completer=completer)
    return items[user_input] if return_value else user_input
