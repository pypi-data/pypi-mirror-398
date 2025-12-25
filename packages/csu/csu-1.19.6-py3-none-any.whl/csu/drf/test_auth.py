from types import SimpleNamespace
from unittest.mock import call

from . import auth


class StrTokenAuthentication(auth.BearerTokenAuthentication):
    expected_token_value = "123"  # noqa: S105


def test_one_token_auth(mocker):
    spy = mocker.spy(auth, "compare_digest")
    assert StrTokenAuthentication().authenticate(SimpleNamespace(META={"HTTP_AUTHORIZATION": b"Bearer 123"})) == (None, "123")
    assert spy.call_args_list == [call("123", "123")]
    assert spy.spy_return_list == [True]


def test_one_token_auth_longer(mocker):
    spy = mocker.spy(auth, "compare_digest")
    assert StrTokenAuthentication().authenticate(SimpleNamespace(META={"HTTP_AUTHORIZATION": b"Bearer 1234"})) is None
    assert spy.call_args_list == [call("1234", "123")]
    assert spy.spy_return_list == [False]


def test_one_token_auth_shorter(mocker):
    spy = mocker.spy(auth, "compare_digest")
    assert StrTokenAuthentication().authenticate(SimpleNamespace(META={"HTTP_AUTHORIZATION": b"Bearer 12"})) is None
    assert spy.call_args_list == [call("12", "123")]
    assert spy.spy_return_list == [False]


class ListTokenAuthentication(auth.BearerTokenAuthentication):
    expected_token_value = ["123", "1234", "ABC"]


def test_multiple_token_auth_1(mocker):
    spy = mocker.spy(auth, "compare_digest")
    assert ListTokenAuthentication().authenticate(SimpleNamespace(META={"HTTP_AUTHORIZATION": b"Bearer 123"})) == (None, "123")
    assert spy.call_args_list == [
        call("123", "123"),
        call("123", "1234"),
        call("123", "ABC"),
    ]
    assert spy.spy_return_list == [True, False, False]


def test_multiple_token_auth_2(mocker):
    spy = mocker.spy(auth, "compare_digest")
    assert ListTokenAuthentication().authenticate(SimpleNamespace(META={"HTTP_AUTHORIZATION": b"Bearer 1234"})) == (None, "1234")
    assert spy.call_args_list == [
        call("1234", "123"),
        call("1234", "1234"),
        call("1234", "ABC"),
    ]
    assert spy.spy_return_list == [False, True, False]


def test_multiple_token_auth_3(mocker):
    spy = mocker.spy(auth, "compare_digest")
    assert ListTokenAuthentication().authenticate(SimpleNamespace(META={"HTTP_AUTHORIZATION": b"Bearer ABC"})) == (None, "ABC")
    assert spy.call_args_list == [
        call("ABC", "123"),
        call("ABC", "1234"),
        call("ABC", "ABC"),
    ]
    assert spy.spy_return_list == [False, False, True]


def test_multiple_token_auth_shorter(mocker):
    spy = mocker.spy(auth, "compare_digest")
    assert ListTokenAuthentication().authenticate(SimpleNamespace(META={"HTTP_AUTHORIZATION": b"Bearer 12"})) is None
    assert spy.call_args_list == [
        call("12", "123"),
        call("12", "1234"),
        call("12", "ABC"),
    ]
    assert spy.spy_return_list == [False, False, False]


def test_multiple_token_auth_case(mocker):
    spy = mocker.spy(auth, "compare_digest")
    assert ListTokenAuthentication().authenticate(SimpleNamespace(META={"HTTP_AUTHORIZATION": b"Bearer abc"})) is None
    assert spy.call_args_list == [
        call("abc", "123"),
        call("abc", "1234"),
        call("abc", "ABC"),
    ]
    assert spy.spy_return_list == [False, False, False]
