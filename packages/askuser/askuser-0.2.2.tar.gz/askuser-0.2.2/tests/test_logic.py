from decimal import Decimal

import pytest

from askuser.logic import (
    is_valid_int, is_valid_float, is_valid_alpha, is_valid_alphanum,
    is_valid_regex, is_valid_char, is_valid_custom, is_not_in,
    is_yes_no, none_if_blank, is_not_blank,
    is_valid_slug,
    is_valid_decimal,
)


def test_is_valid_int():
    assert is_valid_int('5') == 5
    with pytest.raises(ValueError):
        is_valid_int('a')


def test_is_valid_float():
    assert is_valid_float('3.14') == 3.14
    with pytest.raises(ValueError):
        is_valid_float('pi')


def test_is_valid_decimal_basic():
    # Happy path and invalid decimal
    assert is_valid_decimal('3.14') == Decimal('3.14')
    with pytest.raises(ValueError):
        is_valid_decimal('pi')


def test_is_valid_decimal_expected_inputs():
    allowed = [Decimal('1.0'), Decimal('2.5')]
    assert is_valid_decimal('1.0', expected_inputs=allowed) == Decimal('1.0')
    with pytest.raises(ValueError):
        is_valid_decimal('3.0', expected_inputs=allowed)


def test_is_valid_decimal_minimum_maximum():
    # in range
    assert is_valid_decimal('5.0', minimum=Decimal('1'), maximum=Decimal('10')) == Decimal('5.0')

    # below minimum
    with pytest.raises(ValueError):
        is_valid_decimal('0.5', minimum=Decimal('1'))

    # above maximum
    with pytest.raises(ValueError):
        is_valid_decimal('10.5', maximum=Decimal('10'))


def test_is_valid_alpha():
    assert is_valid_alpha('abc') == 'abc'
    with pytest.raises(ValueError):
        is_valid_alpha('abc123')


def test_is_valid_alphanum():
    assert is_valid_alphanum('abc123') == 'abc123'
    with pytest.raises(ValueError):
        is_valid_alphanum('abc!')


def test_is_valid_regex():
    assert is_valid_regex('ABC', r'^[A-Z]+$') == 'ABC'
    with pytest.raises(ValueError):
        is_valid_regex('Abc', r'^[A-Z]+$')


def test_is_valid_char():
    assert is_valid_char('123', '123') == '123'
    with pytest.raises(ValueError):
        is_valid_char('1234', '123')


def test_is_valid_custom():
    assert is_valid_custom('yes', ['yes', 'no']) == 'yes'
    with pytest.raises(ValueError):
        is_valid_custom('maybe', ['yes', 'no'])


def test_is_not_in():
    assert is_not_in('new', ['old']) == 'new'
    with pytest.raises(ValueError):
        is_not_in('old', ['old'])


def test_is_yes_no():
    assert is_yes_no('y') == 'y'
    with pytest.raises(ValueError):
        is_yes_no('maybe')


def test_none_if_blank():
    assert none_if_blank('') is None
    assert none_if_blank('text') == 'text'


def test_is_not_blank():
    assert is_not_blank('data') == 'data'
    with pytest.raises(ValueError):
        is_not_blank('')


def test_is_valid_slug():
    assert is_valid_slug('Hello-World!!') == 'hello-world'
    assert is_valid_slug('--Test__Slug--') == 'testslug'
