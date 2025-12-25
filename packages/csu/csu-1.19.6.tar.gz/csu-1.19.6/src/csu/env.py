import builtins
import os
import pathlib
import re
from datetime import timedelta

UNSET = object()


def get(key) -> builtins.str | None:
    return os.environ.get(key)


def str(key, default=UNSET) -> builtins.str | None:
    if default is UNSET:
        if bool("__strict_env__", True):
            return os.environ[key]
        else:
            return os.environ.get(key)
    else:
        return os.environ.get(key, default)


def list(key, default=UNSET, separator=",") -> builtins.list:
    value = str(key, default)
    if value is None:
        return []
    elif isinstance(value, builtins.str):
        return value.split(separator)
    else:
        return value


def int(key, default=UNSET) -> builtins.int | None:
    value = str(key, default)
    if value is None:
        return
    else:
        return builtins.int(value)


def float(key, default=UNSET) -> builtins.float | None:
    value = str(key, default)
    if value is None:
        return
    else:
        return builtins.float(value)


def bool(key, default=UNSET) -> builtins.bool | None:
    value = str(key, default)
    if isinstance(value, builtins.str):
        return value.lower() in ("yes", "true", "y", "1")
    else:
        return value


def path(key, default=UNSET) -> pathlib.Path | None:
    value = str(key, default)
    if value is None:
        return
    else:
        value = pathlib.Path(value)
        assert value.exists(), f"{value!r} does not exist"
        return value


DURATION_RE = re.compile(
    r"""
        ^P
        (?:(?P<days>\d+\.\d+|\d+)D)?
        T?
        (?:(?P<hours>\d+\.\d+|\d+)H)?
        (?:(?P<minutes>\d+\.\d+|\d+)M)?
        (?:(?P<seconds>\d+\.\d+|\d+)S)?
        $
    """,
    re.VERBOSE,
)


def duration(
    key,
    default=UNSET,
) -> timedelta | None:
    """
    Parses a ISO8601-ish duration.
    """
    value = str(key, default)
    if value is None:
        return
    else:
        match = DURATION_RE.match(value)
        if not match:
            raise ValueError(f"Invalid ISO 8601 duration: {value!r} did not match.")
        print(match.groupdict())
        parts = {k: builtins.float(v) for k, v in match.groupdict("0").items()}
        try:
            return timedelta(**parts)
        except Exception as exc:
            raise ValueError(f"Invalid ISO 8601 duration: {value!r} raised: {exc!r}") from exc
