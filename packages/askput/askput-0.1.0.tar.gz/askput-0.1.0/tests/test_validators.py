import pytest
from askput.validators import (
    validate_int,
    validate_float,
    validate_str,
    validate_email,
    validate_confirm,
    validate_choice,
    validate_pattern,
    validate_password_strength,
)

def test_validate_int():
    assert validate_int("5", min_value=1, max_value=10) == 5
    with pytest.raises(ValueError):
        validate_int("0", min_value=1)

def test_validate_float():
    assert validate_float("3.5", min_value=1) == 3.5
    with pytest.raises(ValueError):
        validate_float("abc")

def test_validate_str():
    assert validate_str("hello", min_len=2) == "hello"
    with pytest.raises(ValueError):
        validate_str("", min_len=1)

def test_validate_email():
    assert validate_email("a@b.com") == "a@b.com"
    with pytest.raises(ValueError):
        validate_email("invalid")

def test_validate_confirm():
    assert validate_confirm("y") is True
    assert validate_confirm("no") is False
    with pytest.raises(ValueError):
        validate_confirm("maybe")

def test_validate_choice():
    assert validate_choice("a", ["a", "b"]) == "a"
    with pytest.raises(ValueError):
        validate_choice("c", ["a", "b"])

def test_validate_pattern():
    assert validate_pattern("ABC123", r"^[A-Z]+\d+$") == "ABC123"
    with pytest.raises(ValueError):
        validate_pattern("abc", r"^[A-Z]+$")

def test_validate_password_strength():
    assert validate_password_strength("Strong123") == "Strong123"
    with pytest.raises(ValueError):
        validate_password_strength("weak")
