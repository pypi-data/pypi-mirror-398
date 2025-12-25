import traceback

from . import exceptions
from .exceptions import APIServiceError
from .exceptions import ExhaustedRetriesError
from .exceptions import OpenServiceError


class OpenFooError(OpenServiceError):
    pass


class ProperOpenFooError(OpenServiceError):
    message = "proper foo"


def test_open_service_error(monkeypatch):
    exc = OpenServiceError(event_id=None)
    assert exc.message == "Unknown error"
    monkeypatch.setattr(exceptions, "get_event_id", lambda: 234)
    api_exc = exc.as_api_service_error()
    assert isinstance(api_exc, APIServiceError)
    assert api_exc.detail == {
        "accident_id": 234,
        "code": "unknown",
        "detail": "Unknown error",
    }


def test_open_service_error_subclass(monkeypatch):
    exc = ProperOpenFooError(event_id=None)
    assert exc.message == "proper foo"
    monkeypatch.setattr(exceptions, "get_event_id", lambda: 123)
    api_exc = exc.as_api_service_error()
    assert isinstance(api_exc, APIServiceError)
    assert api_exc.detail == {
        "accident_id": 123,
        "code": "unknown",
        "detail": "proper foo",
    }


def test_add_note():
    exc = OpenServiceError("My message!", details=[1, 2, Exception(123)], event_id=None)
    assert exc.__notes__ == [
        "(1, 2, Exception(123))",
    ]

    exc = OpenServiceError("My message!", details=[], event_id=None)
    assert getattr(exc, "__notes__", []) == []


def test_exhausted_retries_error():
    errors = [
        Exception(1),
        Exception(2),
        Exception(3),
    ]
    exc = ExhaustedRetriesError("failfailfail", errors, event_id="event:id")
    assert (
        "".join(traceback.format_exception(exc))
        == """  | csu.exceptions.ExhaustedRetriesError: ExhaustedRetriesError('failfailfail')
  | ([Exception(1), Exception(2), Exception(3)],)
  +-+---------------- 1 ----------------
    | Exception: 1
    +---------------- 2 ----------------
    | Exception: 2
    +---------------- 3 ----------------
    | Exception: 3
    +------------------------------------
"""
    )
    assert exc.details == (errors,)
    assert exc.exceptions == tuple(errors)
    assert exc.__notes__ == ["([Exception(1), Exception(2), Exception(3)],)"]
    assert exc.event_id == "event:id"
