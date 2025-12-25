import os
from datetime import timedelta
from pathlib import Path

import pytest

from . import env


def test_path(monkeypatch):
    if "XXX" in os.environ:
        monkeypatch.delitem(os.environ, "XXX")
    assert env.path("XXX", __file__) == Path(__file__)
    pytest.raises(KeyError, env.path, "XXX")
    monkeypatch.setitem(os.environ, "XXX", __file__)
    assert env.path("XXX") == Path(__file__)


def test_existing(monkeypatch):
    monkeypatch.setitem(os.environ, "XXX", "123")
    assert env.get("XXX") == "123"
    assert env.str("XXX") == "123"
    assert env.int("XXX", 234) == 123
    assert env.bool("XXX", True) is False
    assert env.float("XXX", 2345) == 123
    assert env.list("XXX") == ["123"]


def test_missing(monkeypatch):
    if "XXX" in os.environ:
        monkeypatch.delitem(os.environ, "XXX")
    assert env.get("XXX") is None
    pytest.raises(KeyError, env.str, "XXX")
    pytest.raises(KeyError, env.int, "XXX")
    pytest.raises(KeyError, env.bool, "XXX")
    pytest.raises(KeyError, env.float, "XXX")
    pytest.raises(KeyError, env.list, "XXX")


def test_defaults(monkeypatch):
    if "XXX" in os.environ:
        monkeypatch.delitem(os.environ, "XXX")
    assert env.str("XXX", "123") == "123"
    assert env.int("XXX", 234) == 234
    assert env.bool("XXX", False) is False
    assert env.float("XXX", 2345) == 2345
    assert env.list("XXX", [123]) == [123]
    assert env.list("XXX", "1,2,3") == ["1", "2", "3"]
    assert env.list("XXX", "1,2,3", ";") == ["1,2,3"]
    assert env.list("XXX", "1;2;3", ";") == ["1", "2", "3"]
    assert env.duration("XXX", "PT1H2M3S") == timedelta(hours=1, minutes=2, seconds=3)


def test_not_strict(monkeypatch):
    monkeypatch.setitem(os.environ, "__strict_env__", "fAlSe")
    if "XXX" in os.environ:
        monkeypatch.delitem(os.environ, "XXX")
    if "YYY" in os.environ:
        monkeypatch.delitem(os.environ, "YYY")

    assert env.get("XXX") is None
    assert env.str("XXX") is None
    assert env.int("XXX") is None
    assert env.bool("XXX") is None
    assert env.float("XXX") is None
    assert env.list("XXX") == []
    assert env.path("XXX") is None
    assert env.duration("XXX") is None

    assert env.str("YYY", env.str("XXX")) is None
    assert env.int("YYY", env.int("XXX")) is None
    assert env.bool("YYY", env.bool("XXX")) is None
    assert env.float("YYY", env.float("XXX")) is None
    assert env.list("YYY", env.list("XXX")) == []
    assert env.path("YYY", env.path("XXX")) is None
    assert env.duration("YYY", env.duration("XXX")) is None


def test_duration(monkeypatch):
    monkeypatch.setitem(os.environ, "XXX", "P1DT2H3M4S")
    assert env.duration("XXX") == timedelta(days=1, hours=2, minutes=3, seconds=4)
    monkeypatch.setitem(os.environ, "XXX", "P0.5DT2.5H3.5M4.5S")
    assert env.duration("XXX") == timedelta(days=0.5, hours=2.5, minutes=3.5, seconds=4.5)
    monkeypatch.setitem(os.environ, "XXX", "P0.5D")
    assert env.duration("XXX") == timedelta(days=0.5)
    monkeypatch.setitem(os.environ, "XXX", "PT0.3H")
    assert env.duration("XXX") == timedelta(hours=0.3)
    monkeypatch.setitem(os.environ, "XXX", "PDH")
    with pytest.raises(ValueError) as err:  # noqa: PT011
        env.duration("XXX")
    assert err.value.args == ("Invalid ISO 8601 duration: 'PDH' did not match.",)

    monkeypatch.setitem(os.environ, "XXX", "PT")
    assert env.duration("XXX") == timedelta()

    monkeypatch.setitem(os.environ, "XXX", "P999999999999999999D")
    with pytest.raises(ValueError) as err:  # noqa: PT011
        env.duration("XXX")
    assert err.value.args == ("Invalid ISO 8601 duration: 'P999999999999999999D' raised: OverflowError('Python int too large to convert to C int')",)
