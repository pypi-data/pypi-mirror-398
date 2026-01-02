import builtins
import pytest
from askput.core import ask

def test_ask_int(monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda _: "10")
    assert ask.int("Age", min=1, max=20) == 10

def test_ask_float(monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda _: "2.5")
    assert ask.float("Price", min=1) == 2.5

def test_ask_string(monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda _: "hello")
    assert ask.string("Name", min_len=2) == "hello"

def test_ask_email(monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda _: "a@b.com")
    assert ask.email("Email") == "a@b.com"

def test_ask_confirm_yes(monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda _: "y")
    assert ask.confirm("Continue") is True

def test_ask_confirm_no(monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda _: "n")
    assert ask.confirm("Continue") is False

def test_ask_choice(monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda _: "2")
    result = ask.choice("Select role", ["Admin", "User", "Guest"])
    assert result == "User"

def test_ask_multi(monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda _: "a, b, c")
    assert ask.multi("Tags") == ["a", "b", "c"]

def test_ask_pattern(monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda _: "ABC123")
    assert ask.pattern("Code", r"^[A-Z]+\d+$") == "ABC123"

def test_confirm_phrase(monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda _: "DELETE")
    assert ask.confirm_phrase("Confirm", "DELETE") is True

def test_password_strong(monkeypatch):
    monkeypatch.setattr("getpass.getpass", lambda _: "Strong123")
    assert ask.password_strong("Password") == "Strong123"
