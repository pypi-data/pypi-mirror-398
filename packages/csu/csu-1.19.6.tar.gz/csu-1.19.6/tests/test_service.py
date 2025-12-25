from os import getpid

import pytest

from csu import service
from csu.exceptions import DecodeError
from csu.exceptions import ExhaustedRetriesError
from csu.exceptions import InternalServiceError
from csu.exceptions import OpenServiceError
from csu.exceptions import RetryableStatusError
from csu.exceptions import UnexpectedStatusError
from csu.service import HTTPService
from csu.service import HTTPServiceContext
from csu.views import exception_handler


class OkError(OpenServiceError):
    message = "It's ok."
    error_code = "ok"
    status_code = 200


class BingoService(HTTPService):
    def __init__(self, url):
        super().__init__(config={"BASE_URL": url})

    def run(self):
        with self.context() as ctx:
            resp = ctx.request(
                "GET",
                "redirect-to",
                params={
                    "status_code": 307,
                    "url": "https://httpbingo.org/json",
                },
                follow_redirects=True,
            )
            return resp.json

    def error(self):
        with self.context() as ctx:
            try:
                return ctx.request("GET", "status/599", expect_json=False)
            except UnexpectedStatusError as exc:
                if exc.status_code == 599:
                    raise OkError(details=[exc], event_id=ctx.event_id) from exc
                else:
                    raise

    def error_long(self):
        def error_long_wrap_1():
            def error_long_wrap_2():
                def error_long_wrap_3():
                    def error_long_wrap_4():
                        def error_long_wrap_5():
                            def error_long_wrap_6():
                                raise OkError(details=[1], event_id=ctx.event_id)

                            return error_long_wrap_6()

                        return error_long_wrap_5()

                    return error_long_wrap_4()

                return error_long_wrap_3()

            return error_long_wrap_2()

        with self.context() as ctx:
            error_long_wrap_1()

    def json(self):
        with self.context() as ctx:
            return ctx.request("GET", "status/418", accept_statuses=[418]).json


@pytest.mark.vcr
def test_redirects(fake_accident_id, httpbin):
    service = BingoService(httpbin.url)
    data = service.run()
    assert data == {
        "slideshow": {
            "author": "Yours Truly",
            "date": "date of publication",
            "slides": [
                {"title": "Wake up to WonderWidgets!", "type": "all"},
                {"items": ["Why <em>WonderWidgets</em> are great", "Who <em>buys</em> WonderWidgets"], "title": "Overview", "type": "all"},
            ],
            "title": "Sample Slide Show",
        }
    }


@pytest.mark.vcr
def test_error_long(fake_accident_id, caplogs, httpbin):
    bingo = BingoService(httpbin.url)
    with pytest.raises(OkError) as exc:
        bingo.error_long()
    exception_handler(exc.value, {})
    assert exc.value.message == "It's ok."
    api_exc = exc.value.as_api_service_error()
    assert api_exc.status_code == 200
    assert api_exc.detail == {"accident_id": "20241212:01:79200.00", "code": "ok", "detail": "It's ok."}

    assert fake_accident_id.calls == [
        "service.py:62",
    ]
    assert caplogs.get() == (
        f"""INFO    | [pid:{getpid()}] Setting up BingoService with BASE_URL='{httpbin.url}' TIMEOUT=60 RETRIES=3 VERIFY=True
WARNING | [01:79200.00] __exit__ !> OkError("It's ok.", 1, event_id=20241212:01:79200.00)
WARNING |  (renderer: NoneType)
----------------------------------------------------------------- context ------------------------------------------------------------------
  {{}}
---------------------------------------------------------------- traceback -----------------------------------------------------------------
Traceback (most recent call last):
  File "{__file__}", line 65, in error_long_wrap_2
    return error_long_wrap_3()
  File "{__file__}", line 63, in error_long_wrap_3
    return error_long_wrap_4()
  File "{__file__}", line 61, in error_long_wrap_4
    return error_long_wrap_5()
  File "{__file__}", line 59, in error_long_wrap_5
    return error_long_wrap_6()
  File "{__file__}", line 57, in error_long_wrap_6
    raise OkError(details=[1], event_id=ctx.event_id)
test_service.OkError: OkError("It's ok.")
(1,)

The above exception was the direct cause of the following exception:

csu.exceptions.APIServiceError: {{'accident_id': '20241212:01:79200.00', 'detail': "It's ok.", 'code': 'ok'}}
------------------------------------------------------------ response exception ------------------------------------------------------------
  {{'accident_id': '20241212:01:79200.00', 'detail': "It's ok.", 'code': 'ok'}}
============================================================================================================================================"""
    )


@pytest.mark.vcr
def test_error(fake_accident_id, caplogs, httpbin):
    bingo = BingoService(httpbin.url)
    with pytest.raises(OkError) as exc:
        bingo.error()
    assert exc.value.message == "It's ok."
    api_exc = exc.value.as_api_service_error()
    status_exc: UnexpectedStatusError = exc.value.details[0]
    assert api_exc.status_code == 200
    assert api_exc.detail == {"accident_id": "20241212:01:79200.00", "code": "ok", "detail": "It's ok."}

    assert fake_accident_id.calls == [
        "service.py:62",
    ]
    assert caplogs.get() == (
        f"""INFO    | [pid:{getpid()}] Setting up BingoService with BASE_URL='{httpbin.url}' TIMEOUT=60 RETRIES=3 VERIFY=True
INFO    | [01:79200.00] GET {httpbin.url}/status/599 +[]
INFO    | [01:79200.00] GET {httpbin.url}/status/599 => 599 in {status_exc.response.elapsed.total_seconds():.4f}s
--------------------------------------------------- response body utf-8: utf-8 - 0 bytes ---------------------------------------------------
  b''
============================================================================================================================================
WARNING | [01:79200.00] GET {httpbin.url}/status/599 !> failed: UnexpectedStatusError('599 not in [200]', 599, b'', event_id=20241212:01:79200.00)
WARNING | [01:79200.00] __exit__ !> OkError("It's ok.", UnexpectedStatusError('599 not in [200]', 599, b'', event_id=20241212:01:79200.00), event_id=20241212:01:79200.00)"""
    )


@pytest.mark.vcr
def test_decoding(fake_accident_id, caplogs, httpbin):
    bingo = BingoService(httpbin.url)
    with pytest.raises(DecodeError) as exc:
        bingo.json()
    exception_handler(exc.value, {})
    assert fake_accident_id.calls == [
        "service.py:62",
    ]
    assert caplogs.get() == (
        f"""INFO    | [pid:{getpid()}] Setting up BingoService with BASE_URL='{httpbin.url}' TIMEOUT=60 RETRIES=3 VERIFY=True
INFO    | [01:79200.00] GET {httpbin.url}/status/418 +[]
INFO    | [01:79200.00] GET {httpbin.url}/status/418 => 418 in {exc.value.response.elapsed.total_seconds():.4f}s
----------------------------------------------- response body utf-8: no charset - 135 bytes ------------------------------------------------
  b'\\n    -=[ teapot ]=-\\n\\n       _...._\\n     .\\'  _ _ `.\\n    | ."` ^ `". _,\\n    \\\\_;`"---"`|//\\n      |       ;/\\n      \\\\_     _/\\n        `\"""`\\n'
============================================================================================================================================
WARNING | [01:79200.00] GET {httpbin.url}/status/418 !> failed: DecodeError(JSONDecodeError('Expecting value: line 2 column 5 (char 5)'), 418, b'\\n    -=[ teapot ]=-\\n\\n       _...._\\n     .\\'  _ _ `.\\n    | ."` ^ `". _,\\n    \\\\_;`"---"`|//\\n      |       ;/\\n      \\\\_     _/\\n        `""\"`\\n', event_id=20241212:01:79200.00)
WARNING | [01:79200.00] __exit__ !> DecodeError(JSONDecodeError('Expecting value: line 2 column 5 (char 5)'), 418, b'\\n    -=[ teapot ]=-\\n\\n       _...._\\n     .\\'  _ _ `.\\n    | ."` ^ `". _,\\n    \\\\_;`"---"`|//\\n      |       ;/\\n      \\\\_     _/\\n        `""\"`\\n', event_id=20241212:01:79200.00)
ERROR   |  (renderer: NoneType)
----------------------------------------------------------------- context ------------------------------------------------------------------
  {{}}
---------------------------------------------------------------- traceback -----------------------------------------------------------------
Traceback (most recent call last):
  File "{__file__}", line 168, in test_decoding
    bingo.json()
    ~~~~~~~~~~^^
  File "{__file__}", line 74, in json
    return ctx.request("GET", "status/418", accept_statuses=[418]).json
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "{service.__file__}", line 223, in request
    return self.handle_process_response(response, retry_statuses=retry_statuses, accept_statuses=accept_statuses, expect_json=expect_json)
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "{service.__file__}", line 156, in handle_process_response
    raise DecodeError(response, exc, event_id=self.event_id) from None
csu.exceptions.DecodeError: DecodeError(JSONDecodeError('Expecting value: line 2 column 5 (char 5)'), response=<Response [418 I'M A TEAPOT]>)
(418, b'\\n    -=[ teapot ]=-\\n\\n       _...._\\n     .\\'  _ _ `.\\n    | ."` ^ `". _,\\n    \\\\_;`"---"`|//\\n      |       ;/\\n      \\\\_     _/\\n        `\"""`\\n')
------------------------------------------------------------ response exception ------------------------------------------------------------
  {{'accident_id': '20241212:01:79200.00', 'detail': 'Internal server error.', 'code': 'server'}}
============================================================================================================================================"""
    )


@pytest.mark.vcr
def test_logging(fake_accident_id, caplogs, httpbin):
    bingo = BingoService(httpbin.url)
    with pytest.raises(OkError) as exc:
        bingo.error()
    status_exc: UnexpectedStatusError = exc.value.details[0]
    exception_handler(exc.value, {})
    assert fake_accident_id.calls == [
        "service.py:62",
    ]
    assert caplogs.get() == (
        f"""INFO    | [pid:{getpid()}] Setting up BingoService with BASE_URL='{httpbin.url}' TIMEOUT=60 RETRIES=3 VERIFY=True
INFO    | [01:79200.00] GET {httpbin.url}/status/599 +[]
INFO    | [01:79200.00] GET {httpbin.url}/status/599 => 599 in {status_exc.response.elapsed.total_seconds():.4f}s
--------------------------------------------------- response body utf-8: utf-8 - 0 bytes ---------------------------------------------------
  b''
============================================================================================================================================
WARNING | [01:79200.00] GET {httpbin.url}/status/599 !> failed: UnexpectedStatusError('599 not in [200]', 599, b'', event_id=20241212:01:79200.00)
WARNING | [01:79200.00] __exit__ !> OkError("It's ok.", UnexpectedStatusError('599 not in [200]', 599, b'', event_id=20241212:01:79200.00), event_id=20241212:01:79200.00)
WARNING |  (renderer: NoneType)
----------------------------------------------------------------- context ------------------------------------------------------------------
  {{}}
---------------------------------------------------------------- traceback -----------------------------------------------------------------
Traceback (most recent call last):
  File "{__file__}", line 43, in error
    return ctx.request("GET", "status/599", expect_json=False)
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "{service.__file__}", line 223, in request
    return self.handle_process_response(response, retry_statuses=retry_statuses, accept_statuses=accept_statuses, expect_json=expect_json)
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "{service.__file__}", line 150, in handle_process_response
    raise UnexpectedStatusError(response, accept_statuses, event_id=self.event_id)
csu.exceptions.UnexpectedStatusError: UnexpectedStatusError(<Response [599 UNKNOWN]>, accept_statuses=[200])
(599, b'')

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "{__file__}", line 210, in test_logging
    bingo.error()
    ~~~~~~~~~~~^^
  File "{__file__}", line 46, in error
    raise OkError(details=[exc], event_id=ctx.event_id) from exc
test_service.OkError: OkError("It's ok.")
(UnexpectedStatusError('599 not in [200]', 599, b'', event_id=20241212:01:79200.00),)

The above exception was the direct cause of the following exception:

csu.exceptions.APIServiceError: {{'accident_id': '20241212:01:79200.00', 'detail': "It's ok.", 'code': 'ok'}}
------------------------------------------------------------ response exception ------------------------------------------------------------
  {{'accident_id': '20241212:01:79200.00', 'detail': "It's ok.", 'code': 'ok'}}
============================================================================================================================================"""
    )


class CustomContext(HTTPServiceContext):
    def __init__(self, service: CustomService):
        super().__init__(service)
        self.config = service.config

    # noinspection PyMethodOverriding
    def handle_prepare_request(
        self,
        method,
        url,
        *,
        accept_statuses,
        expect_json,
        follow_redirects,
        retries_left,
        retry_count,
        retry_statuses,
        payload,
        params,
        **kwargs,
    ):
        assert "json" not in kwargs
        assert "data" not in kwargs
        params.update(
            accept_statuses=accept_statuses,
            expect_json=expect_json,
            follow_redirects=follow_redirects,
            retries_left=retries_left,
            retry_count=retry_count,
            retry_statuses=retry_statuses,
        )
        content = payload.format(
            config=self.config,
            **kwargs,
        )
        return self.client.build_request(method, url, content=content, params=params, **kwargs)


class CustomService(HTTPService):
    context_class = CustomContext

    def __init__(self, url, **config):
        super().__init__(config={"BASE_URL": url, **config})
        self.config = {"custom": "config"}

    def run(self):
        with self.context() as ctx:
            resp = ctx.request(
                "POST",
                "anything",
                params={
                    "foo": "bar",
                },
                payload="config={config}",
                retry_statuses=[200],
                accept_statuses=[999],
            )
            return resp.content


@pytest.mark.vcr
def test_custom_context(httpbin, fake_accident_id, caplogs):
    custom = CustomService(httpbin.url)
    with pytest.raises(ExhaustedRetriesError) as exc:
        custom.run()
    assert repr(exc.value).startswith("ExhaustedRetriesError(3, [RetryableStatusError(")
    assert str(exc.value) == "ExhaustedRetriesError(3)"
    assert exc.value.message == "4xRetryableStatusError"
    assert len(exc.value.details) == 1
    assert len(exc.value.details[0]) == 4
    assert len(exc.value.exceptions) == 4
    fail = exc.value.exceptions[0]
    assert isinstance(fail, RetryableStatusError)
    assert fail.status_code == 200
    fail_data = fail.response.json()
    assert fail_data["args"] == {
        "foo": "bar",
        "accept_statuses": "{999}",
        "expect_json": "true",
        "follow_redirects": "false",
        "retries_left": "3",
        "retry_count": "0",
        "retry_statuses": "{200}",
    }
    assert fail_data["data"] == "config={'custom': 'config'}"

    fail = exc.value.exceptions[1]
    assert isinstance(fail, RetryableStatusError)
    assert fail.status_code == 200
    fail_data = fail.response.json()
    assert fail_data["args"] == {
        "foo": "bar",
        "accept_statuses": "{999}",
        "expect_json": "true",
        "follow_redirects": "false",
        "retries_left": "2",
        "retry_count": "1",
        "retry_statuses": "{200}",
    }
    assert fail_data["data"] == "config={'custom': 'config'}"

    fail = exc.value.exceptions[2]
    assert isinstance(fail, RetryableStatusError)
    assert fail.status_code == 200
    fail_data = fail.response.json()
    assert fail_data["args"] == {
        "foo": "bar",
        "accept_statuses": "{999}",
        "expect_json": "true",
        "follow_redirects": "false",
        "retries_left": "1",
        "retry_count": "2",
        "retry_statuses": "{200}",
    }
    assert fail_data["data"] == "config={'custom': 'config'}"

    fail = exc.value.exceptions[3]
    assert isinstance(fail, RetryableStatusError)
    assert fail.status_code == 200
    fail_data = fail.response.json()
    assert fail_data["args"] == {
        "foo": "bar",
        "accept_statuses": "{999}",
        "expect_json": "true",
        "follow_redirects": "false",
        "retries_left": "0",
        "retry_count": "3",
        "retry_statuses": "{200}",
    }
    assert fail_data["data"] == "config={'custom': 'config'}"

    exception_handler(exc.value, {})
    assert fake_accident_id.calls == [
        "service.py:62",
    ]
    assert caplogs.get() == (
        f"""INFO    | [pid:{getpid()}] Setting up CustomService with BASE_URL='{httpbin.url}' TIMEOUT=60 RETRIES=3 VERIFY=True
INFO    | [01:79200.00] POST {httpbin.url}/anything?foo=bar&accept_statuses=%7B999%7D&expect_json=true&follow_redirects=false&retries_left=3&retry_count=0&retry_statuses=%7B200%7D +[]
------------------------------------------------------------- request content --------------------------------------------------------------
   b"config={{'custom': 'config'}}"
============================================================================================================================================
INFO    | [01:79200.00] POST {httpbin.url}/anything?foo=bar&accept_statuses=%7B999%7D&expect_json=true&follow_redirects=false&retries_left=3&retry_count=0&retry_statuses=%7B200%7D => 200 in 0.0000s
----------------------------------------------- response body utf-8: no charset - 598 bytes ------------------------------------------------
  b'{{"args":{{"accept_statuses":"{{999}}","expect_json":"true","follow_redirects":"false","foo":"bar","retries_left":"3","retry_count":"0","retry_statuses":"{{200}}"}},"data":"config={{\\'custom\\': \\'config\\'}}","files":{{}},"form":{{}},"headers":{{"Accept":"*/*","Accept-Encoding":"gzip, deflate, br","Connection":"keep-alive","Content-Length":"27","Host":"127.0.0.1:12345","User-Agent":"python-httpx/0.X.X"}},"json":null,"method":"POST","origin":"127.0.0.1","url":"http://127.0.0.1:12345/anything?foo=bar&accept_statuses={{999}}&expect_json=true&follow_redirects=false&retries_left=3&retry_count=0&retry_statuses={{200}}"}}\\n'
============================================================================================================================================
ERROR   | [01:79200.00] POST {httpbin.url}/anything?foo=bar&accept_statuses=%7B999%7D&expect_json=true&follow_redirects=false&retries_left=3&retry_count=0&retry_statuses=%7B200%7D !> RetryableStatusError('200 not in [999] but in [200]', 200, b'{{"args":{{"accept_statuses":"{{999}}","expect_json":"true","follow_redirects":"false","foo":"bar","retries_left":"3","retry_count":"0","retry_statuses":"{{200}}"}},"data":"config={{\\'custom\\': \\'config\\'}}","files":{{}},"form":{{}},"headers":{{"Accept":"*/*","Accept-Encoding":"gzip, deflate, br","Connection":"keep-alive","Content-Length":"27","Host":"127.0.0.1:12345","User-Agent":"python-httpx/0.X.X"}},"json":null,"method":"POST","origin":"127.0.0.1","url":"http://127.0.0.1:12345/anything?foo=bar&accept_statuses={{999}}&expect_json=true&follow_redirects=false&retries_left=3&retry_count=0&retry_statuses={{200}}"}}\\n', event_id=20241212:01:79200.00) (will retry 3 more times)
Traceback (most recent call last):
  File "{service.__file__}", line 223, in request
    return self.handle_process_response(response, retry_statuses=retry_statuses, accept_statuses=accept_statuses, expect_json=expect_json)
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "{service.__file__}", line 148, in handle_process_response
    raise RetryableStatusError(response, accept_statuses, retry_statuses, event_id=self.event_id)
csu.exceptions.RetryableStatusError: RetryableStatusError(<Response [200 OK]>, accept_statuses=[999], retry_statuses=[200])
(200, b'{{"args":{{"accept_statuses":"{{999}}","expect_json":"true","follow_redirects":"false","foo":"bar","retries_left":"3","retry_count":"0","retry_statuses":"{{200}}"}},"data":"config={{\\'custom\\': \\'config\\'}}","files":{{}},"form":{{}},"headers":{{"Accept":"*/*","Accept-Encoding":"gzip, deflate, br","Connection":"keep-alive","Content-Length":"27","Host":"127.0.0.1:12345","User-Agent":"python-httpx/0.X.X"}},"json":null,"method":"POST","origin":"127.0.0.1","url":"http://127.0.0.1:12345/anything?foo=bar&accept_statuses={{999}}&expect_json=true&follow_redirects=false&retries_left=3&retry_count=0&retry_statuses={{200}}"}}\\n')

INFO    | [01:79200.00] POST {httpbin.url}/anything?foo=bar&accept_statuses=%7B999%7D&expect_json=true&follow_redirects=false&retries_left=2&retry_count=1&retry_statuses=%7B200%7D +[]
------------------------------------------------------------- request content --------------------------------------------------------------
   b"config={{'custom': 'config'}}"
============================================================================================================================================
INFO    | [01:79200.00] POST {httpbin.url}/anything?foo=bar&accept_statuses=%7B999%7D&expect_json=true&follow_redirects=false&retries_left=2&retry_count=1&retry_statuses=%7B200%7D => 200 in 0.0000s
----------------------------------------------- response body utf-8: no charset - 598 bytes ------------------------------------------------
  b'{{"args":{{"accept_statuses":"{{999}}","expect_json":"true","follow_redirects":"false","foo":"bar","retries_left":"2","retry_count":"1","retry_statuses":"{{200}}"}},"data":"config={{\\'custom\\': \\'config\\'}}","files":{{}},"form":{{}},"headers":{{"Accept":"*/*","Accept-Encoding":"gzip, deflate, br","Connection":"keep-alive","Content-Length":"27","Host":"127.0.0.1:12345","User-Agent":"python-httpx/0.X.X"}},"json":null,"method":"POST","origin":"127.0.0.1","url":"http://127.0.0.1:12345/anything?foo=bar&accept_statuses={{999}}&expect_json=true&follow_redirects=false&retries_left=2&retry_count=1&retry_statuses={{200}}"}}\\n'
============================================================================================================================================
ERROR   | [01:79200.00] POST {httpbin.url}/anything?foo=bar&accept_statuses=%7B999%7D&expect_json=true&follow_redirects=false&retries_left=2&retry_count=1&retry_statuses=%7B200%7D !> RetryableStatusError('200 not in [999] but in [200]', 200, b'{{"args":{{"accept_statuses":"{{999}}","expect_json":"true","follow_redirects":"false","foo":"bar","retries_left":"2","retry_count":"1","retry_statuses":"{{200}}"}},"data":"config={{\\'custom\\': \\'config\\'}}","files":{{}},"form":{{}},"headers":{{"Accept":"*/*","Accept-Encoding":"gzip, deflate, br","Connection":"keep-alive","Content-Length":"27","Host":"127.0.0.1:12345","User-Agent":"python-httpx/0.X.X"}},"json":null,"method":"POST","origin":"127.0.0.1","url":"http://127.0.0.1:12345/anything?foo=bar&accept_statuses={{999}}&expect_json=true&follow_redirects=false&retries_left=2&retry_count=1&retry_statuses={{200}}"}}\\n', event_id=20241212:01:79200.00) (will retry 2 more times)
Traceback (most recent call last):
  File "{service.__file__}", line 223, in request
    return self.handle_process_response(response, retry_statuses=retry_statuses, accept_statuses=accept_statuses, expect_json=expect_json)
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "{service.__file__}", line 148, in handle_process_response
    raise RetryableStatusError(response, accept_statuses, retry_statuses, event_id=self.event_id)
csu.exceptions.RetryableStatusError: RetryableStatusError(<Response [200 OK]>, accept_statuses=[999], retry_statuses=[200])
(200, b'{{"args":{{"accept_statuses":"{{999}}","expect_json":"true","follow_redirects":"false","foo":"bar","retries_left":"2","retry_count":"1","retry_statuses":"{{200}}"}},"data":"config={{\\'custom\\': \\'config\\'}}","files":{{}},"form":{{}},"headers":{{"Accept":"*/*","Accept-Encoding":"gzip, deflate, br","Connection":"keep-alive","Content-Length":"27","Host":"127.0.0.1:12345","User-Agent":"python-httpx/0.X.X"}},"json":null,"method":"POST","origin":"127.0.0.1","url":"http://127.0.0.1:12345/anything?foo=bar&accept_statuses={{999}}&expect_json=true&follow_redirects=false&retries_left=2&retry_count=1&retry_statuses={{200}}"}}\\n')

INFO    | [01:79200.00] POST {httpbin.url}/anything?foo=bar&accept_statuses=%7B999%7D&expect_json=true&follow_redirects=false&retries_left=1&retry_count=2&retry_statuses=%7B200%7D +[]
------------------------------------------------------------- request content --------------------------------------------------------------
   b"config={{'custom': 'config'}}"
============================================================================================================================================
INFO    | [01:79200.00] POST {httpbin.url}/anything?foo=bar&accept_statuses=%7B999%7D&expect_json=true&follow_redirects=false&retries_left=1&retry_count=2&retry_statuses=%7B200%7D => 200 in 0.0000s
----------------------------------------------- response body utf-8: no charset - 598 bytes ------------------------------------------------
  b'{{"args":{{"accept_statuses":"{{999}}","expect_json":"true","follow_redirects":"false","foo":"bar","retries_left":"1","retry_count":"2","retry_statuses":"{{200}}"}},"data":"config={{\\'custom\\': \\'config\\'}}","files":{{}},"form":{{}},"headers":{{"Accept":"*/*","Accept-Encoding":"gzip, deflate, br","Connection":"keep-alive","Content-Length":"27","Host":"127.0.0.1:12345","User-Agent":"python-httpx/0.X.X"}},"json":null,"method":"POST","origin":"127.0.0.1","url":"http://127.0.0.1:12345/anything?foo=bar&accept_statuses={{999}}&expect_json=true&follow_redirects=false&retries_left=1&retry_count=2&retry_statuses={{200}}"}}\\n'
============================================================================================================================================
ERROR   | [01:79200.00] POST {httpbin.url}/anything?foo=bar&accept_statuses=%7B999%7D&expect_json=true&follow_redirects=false&retries_left=1&retry_count=2&retry_statuses=%7B200%7D !> RetryableStatusError('200 not in [999] but in [200]', 200, b'{{"args":{{"accept_statuses":"{{999}}","expect_json":"true","follow_redirects":"false","foo":"bar","retries_left":"1","retry_count":"2","retry_statuses":"{{200}}"}},"data":"config={{\\'custom\\': \\'config\\'}}","files":{{}},"form":{{}},"headers":{{"Accept":"*/*","Accept-Encoding":"gzip, deflate, br","Connection":"keep-alive","Content-Length":"27","Host":"127.0.0.1:12345","User-Agent":"python-httpx/0.X.X"}},"json":null,"method":"POST","origin":"127.0.0.1","url":"http://127.0.0.1:12345/anything?foo=bar&accept_statuses={{999}}&expect_json=true&follow_redirects=false&retries_left=1&retry_count=2&retry_statuses={{200}}"}}\\n', event_id=20241212:01:79200.00) (will retry 1 more times)
Traceback (most recent call last):
  File "{service.__file__}", line 223, in request
    return self.handle_process_response(response, retry_statuses=retry_statuses, accept_statuses=accept_statuses, expect_json=expect_json)
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "{service.__file__}", line 148, in handle_process_response
    raise RetryableStatusError(response, accept_statuses, retry_statuses, event_id=self.event_id)
csu.exceptions.RetryableStatusError: RetryableStatusError(<Response [200 OK]>, accept_statuses=[999], retry_statuses=[200])
(200, b'{{"args":{{"accept_statuses":"{{999}}","expect_json":"true","follow_redirects":"false","foo":"bar","retries_left":"1","retry_count":"2","retry_statuses":"{{200}}"}},"data":"config={{\\'custom\\': \\'config\\'}}","files":{{}},"form":{{}},"headers":{{"Accept":"*/*","Accept-Encoding":"gzip, deflate, br","Connection":"keep-alive","Content-Length":"27","Host":"127.0.0.1:12345","User-Agent":"python-httpx/0.X.X"}},"json":null,"method":"POST","origin":"127.0.0.1","url":"http://127.0.0.1:12345/anything?foo=bar&accept_statuses={{999}}&expect_json=true&follow_redirects=false&retries_left=1&retry_count=2&retry_statuses={{200}}"}}\\n')

INFO    | [01:79200.00] POST {httpbin.url}/anything?foo=bar&accept_statuses=%7B999%7D&expect_json=true&follow_redirects=false&retries_left=0&retry_count=3&retry_statuses=%7B200%7D +[]
------------------------------------------------------------- request content --------------------------------------------------------------
   b"config={{'custom': 'config'}}"
============================================================================================================================================
INFO    | [01:79200.00] POST {httpbin.url}/anything?foo=bar&accept_statuses=%7B999%7D&expect_json=true&follow_redirects=false&retries_left=0&retry_count=3&retry_statuses=%7B200%7D => 200 in 0.0000s
----------------------------------------------- response body utf-8: no charset - 598 bytes ------------------------------------------------
  b'{{"args":{{"accept_statuses":"{{999}}","expect_json":"true","follow_redirects":"false","foo":"bar","retries_left":"0","retry_count":"3","retry_statuses":"{{200}}"}},"data":"config={{\\'custom\\': \\'config\\'}}","files":{{}},"form":{{}},"headers":{{"Accept":"*/*","Accept-Encoding":"gzip, deflate, br","Connection":"keep-alive","Content-Length":"27","Host":"127.0.0.1:12345","User-Agent":"python-httpx/0.X.X"}},"json":null,"method":"POST","origin":"127.0.0.1","url":"http://127.0.0.1:12345/anything?foo=bar&accept_statuses={{999}}&expect_json=true&follow_redirects=false&retries_left=0&retry_count=3&retry_statuses={{200}}"}}\\n'
============================================================================================================================================
ERROR   | [01:79200.00] POST {httpbin.url}/anything?foo=bar&accept_statuses=%7B999%7D&expect_json=true&follow_redirects=false&retries_left=0&retry_count=3&retry_statuses=%7B200%7D !> RetryableStatusError('200 not in [999] but in [200]', 200, b'{{"args":{{"accept_statuses":"{{999}}","expect_json":"true","follow_redirects":"false","foo":"bar","retries_left":"0","retry_count":"3","retry_statuses":"{{200}}"}},"data":"config={{\\'custom\\': \\'config\\'}}","files":{{}},"form":{{}},"headers":{{"Accept":"*/*","Accept-Encoding":"gzip, deflate, br","Connection":"keep-alive","Content-Length":"27","Host":"127.0.0.1:12345","User-Agent":"python-httpx/0.X.X"}},"json":null,"method":"POST","origin":"127.0.0.1","url":"http://127.0.0.1:12345/anything?foo=bar&accept_statuses={{999}}&expect_json=true&follow_redirects=false&retries_left=0&retry_count=3&retry_statuses={{200}}"}}\\n', event_id=20241212:01:79200.00) (exhausted retries)
WARNING | [01:79200.00] __exit__ !> ExhaustedRetriesError(3, [RetryableStatusError('200 not in [999] but in [200]', 200, b'{{"args":{{"accept_statuses":"{{999}}","expect_json":"true","follow_redirects":"false","foo":"bar","retries_left":"3","retry_count":"0","retry_statuses":"{{200}}"}},"data":"config={{\\'custom\\': \\'config\\'}}","files":{{}},"form":{{}},"headers":{{"Accept":"*/*","Accept-Encoding":"gzip, deflate, br","Connection":"keep-alive","Content-Length":"27","Host":"127.0.0.1:12345","User-Agent":"python-httpx/0.X.X"}},"json":null,"method":"POST","origin":"127.0.0.1","url":"http://127.0.0.1:12345/anything?foo=bar&accept_statuses={{999}}&expect_json=true&follow_redirects=false&retries_left=3&retry_count=0&retry_statuses={{200}}"}}\\n', event_id=20241212:01:79200.00), RetryableStatusError('200 not in [999] but in [200]', 200, b'{{"args":{{"accept_statuses":"{{999}}","expect_json":"true","follow_redirects":"false","foo":"bar","retries_left":"2","retry_count":"1","retry_statuses":"{{200}}"}},"data":"config={{\\'custom\\': \\'config\\'}}","files":{{}},"form":{{}},"headers":{{"Accept":"*/*","Accept-Encoding":"gzip, deflate, br","Connection":"keep-alive","Content-Length":"27","Host":"127.0.0.1:12345","User-Agent":"python-httpx/0.X.X"}},"json":null,"method":"POST","origin":"127.0.0.1","url":"http://127.0.0.1:12345/anything?foo=bar&accept_statuses={{999}}&expect_json=true&follow_redirects=false&retries_left=2&retry_count=1&retry_statuses={{200}}"}}\\n', event_id=20241212:01:79200.00), RetryableStatusError('200 not in [999] but in [200]', 200, b'{{"args":{{"accept_statuses":"{{999}}","expect_json":"true","follow_redirects":"false","foo":"bar","retries_left":"1","retry_count":"2","retry_statuses":"{{200}}"}},"data":"config={{\\'custom\\': \\'config\\'}}","files":{{}},"form":{{}},"headers":{{"Accept":"*/*","Accept-Encoding":"gzip, deflate, br","Connection":"keep-alive","Content-Length":"27","Host":"127.0.0.1:12345","User-Agent":"python-httpx/0.X.X"}},"json":null,"method":"POST","origin":"127.0.0.1","url":"http://127.0.0.1:12345/anything?foo=bar&accept_statuses={{999}}&expect_json=true&follow_redirects=false&retries_left=1&retry_count=2&retry_statuses={{200}}"}}\\n', event_id=20241212:01:79200.00), RetryableStatusError('200 not in [999] but in [200]', 200, b'{{"args":{{"accept_statuses":"{{999}}","expect_json":"true","follow_redirects":"false","foo":"bar","retries_left":"0","retry_count":"3","retry_statuses":"{{200}}"}},"data":"config={{\\'custom\\': \\'config\\'}}","files":{{}},"form":{{}},"headers":{{"Accept":"*/*","Accept-Encoding":"gzip, deflate, br","Connection":"keep-alive","Content-Length":"27","Host":"127.0.0.1:12345","User-Agent":"python-httpx/0.X.X"}},"json":null,"method":"POST","origin":"127.0.0.1","url":"http://127.0.0.1:12345/anything?foo=bar&accept_statuses={{999}}&expect_json=true&follow_redirects=false&retries_left=0&retry_count=3&retry_statuses={{200}}"}}\\n', event_id=20241212:01:79200.00)], event_id=20241212:01:79200.00)
ERROR   |  (renderer: NoneType)
----------------------------------------------------------------- context ------------------------------------------------------------------
  {{}}
---------------------------------------------------------------- traceback -----------------------------------------------------------------
+ Exception Group Traceback (most recent call last):
  |   File "{__file__}", line 325, in test_custom_context
  |     custom.run()
  |     ~~~~~~~~~~^^
  |   File "{__file__}", line 308, in run
  |     resp = ctx.request(
  |         "POST",
  |     ...<6 lines>...
  |         accept_statuses=[999],
  |     )
  |   File "{service.__file__}", line 234, in request
  |     raise ExhaustedRetriesError(retry_buget, retry_failures, event_id=self.event_id)
  | csu.exceptions.ExhaustedRetriesError: ExhaustedRetriesError(3)
  | ([RetryableStatusError('200 not in [999] but in [200]', 200, b'{{"args":{{"accept_statuses":"{{999}}","expect_json":"true","follow_redirects":"false","foo":"bar","retries_left":"3","retry_count":"0","retry_statuses":"{{200}}"}},"data":"config={{\\'custom\\': \\'config\\'}}","files":{{}},"form":{{}},"headers":{{"Accept":"*/*","Accept-Encoding":"gzip, deflate, br","Connection":"keep-alive","Content-Length":"27","Host":"127.0.0.1:12345","User-Agent":"python-httpx/0.X.X"}},"json":null,"method":"POST","origin":"127.0.0.1","url":"http://127.0.0.1:12345/anything?foo=bar&accept_statuses={{999}}&expect_json=true&follow_redirects=false&retries_left=3&retry_count=0&retry_statuses={{200}}"}}\\n', event_id=20241212:01:79200.00), RetryableStatusError('200 not in [999] but in [200]', 200, b'{{"args":{{"accept_statuses":"{{999}}","expect_json":"true","follow_redirects":"false","foo":"bar","retries_left":"2","retry_count":"1","retry_statuses":"{{200}}"}},"data":"config={{\\'custom\\': \\'config\\'}}","files":{{}},"form":{{}},"headers":{{"Accept":"*/*","Accept-Encoding":"gzip, deflate, br","Connection":"keep-alive","Content-Length":"27","Host":"127.0.0.1:12345","User-Agent":"python-httpx/0.X.X"}},"json":null,"method":"POST","origin":"127.0.0.1","url":"http://127.0.0.1:12345/anything?foo=bar&accept_statuses={{999}}&expect_json=true&follow_redirects=false&retries_left=2&retry_count=1&retry_statuses={{200}}"}}\\n', event_id=20241212:01:79200.00), RetryableStatusError('200 not in [999] but in [200]', 200, b'{{"args":{{"accept_statuses":"{{999}}","expect_json":"true","follow_redirects":"false","foo":"bar","retries_left":"1","retry_count":"2","retry_statuses":"{{200}}"}},"data":"config={{\\'custom\\': \\'config\\'}}","files":{{}},"form":{{}},"headers":{{"Accept":"*/*","Accept-Encoding":"gzip, deflate, br","Connection":"keep-alive","Content-Length":"27","Host":"127.0.0.1:12345","User-Agent":"python-httpx/0.X.X"}},"json":null,"method":"POST","origin":"127.0.0.1","url":"http://127.0.0.1:12345/anything?foo=bar&accept_statuses={{999}}&expect_json=true&follow_redirects=false&retries_left=1&retry_count=2&retry_statuses={{200}}"}}\\n', event_id=20241212:01:79200.00), RetryableStatusError('200 not in [999] but in [200]', 200, b'{{"args":{{"accept_statuses":"{{999}}","expect_json":"true","follow_redirects":"false","foo":"bar","retries_left":"0","retry_count":"3","retry_statuses":"{{200}}"}},"data":"config={{\\'custom\\': \\'config\\'}}","files":{{}},"form":{{}},"headers":{{"Accept":"*/*","Accept-Encoding":"gzip, deflate, br","Connection":"keep-alive","Content-Length":"27","Host":"127.0.0.1:12345","User-Agent":"python-httpx/0.X.X"}},"json":null,"method":"POST","origin":"127.0.0.1","url":"http://127.0.0.1:12345/anything?foo=bar&accept_statuses={{999}}&expect_json=true&follow_redirects=false&retries_left=0&retry_count=3&retry_statuses={{200}}"}}\\n', event_id=20241212:01:79200.00)],)
  +-+---------------- 1 ----------------
    | Traceback (most recent call last):
    |   File "{service.__file__}", line 223, in request
    |     return self.handle_process_response(response, retry_statuses=retry_statuses, accept_statuses=accept_statuses, expect_json=expect_json)
    |            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "{service.__file__}", line 148, in handle_process_response
    |     raise RetryableStatusError(response, accept_statuses, retry_statuses, event_id=self.event_id)
    | csu.exceptions.RetryableStatusError: RetryableStatusError(<Response [200 OK]>, accept_statuses=[999], retry_statuses=[200])
    | (200, b'{{"args":{{"accept_statuses":"{{999}}","expect_json":"true","follow_redirects":"false","foo":"bar","retries_left":"3","retry_count":"0","retry_statuses":"{{200}}"}},"data":"config={{\\'custom\\': \\'config\\'}}","files":{{}},"form":{{}},"headers":{{"Accept":"*/*","Accept-Encoding":"gzip, deflate, br","Connection":"keep-alive","Content-Length":"27","Host":"127.0.0.1:12345","User-Agent":"python-httpx/0.X.X"}},"json":null,"method":"POST","origin":"127.0.0.1","url":"http://127.0.0.1:12345/anything?foo=bar&accept_statuses={{999}}&expect_json=true&follow_redirects=false&retries_left=3&retry_count=0&retry_statuses={{200}}"}}\\n')
    +---------------- 2 ----------------
    | Traceback (most recent call last):
    |   File "{service.__file__}", line 223, in request
    |     return self.handle_process_response(response, retry_statuses=retry_statuses, accept_statuses=accept_statuses, expect_json=expect_json)
    |            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "{service.__file__}", line 148, in handle_process_response
    |     raise RetryableStatusError(response, accept_statuses, retry_statuses, event_id=self.event_id)
    | csu.exceptions.RetryableStatusError: RetryableStatusError(<Response [200 OK]>, accept_statuses=[999], retry_statuses=[200])
    | (200, b'{{"args":{{"accept_statuses":"{{999}}","expect_json":"true","follow_redirects":"false","foo":"bar","retries_left":"2","retry_count":"1","retry_statuses":"{{200}}"}},"data":"config={{\\'custom\\': \\'config\\'}}","files":{{}},"form":{{}},"headers":{{"Accept":"*/*","Accept-Encoding":"gzip, deflate, br","Connection":"keep-alive","Content-Length":"27","Host":"127.0.0.1:12345","User-Agent":"python-httpx/0.X.X"}},"json":null,"method":"POST","origin":"127.0.0.1","url":"http://127.0.0.1:12345/anything?foo=bar&accept_statuses={{999}}&expect_json=true&follow_redirects=false&retries_left=2&retry_count=1&retry_statuses={{200}}"}}\\n')
    +---------------- 3 ----------------
    | Traceback (most recent call last):
    |   File "{service.__file__}", line 223, in request
    |     return self.handle_process_response(response, retry_statuses=retry_statuses, accept_statuses=accept_statuses, expect_json=expect_json)
    |            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "{service.__file__}", line 148, in handle_process_response
    |     raise RetryableStatusError(response, accept_statuses, retry_statuses, event_id=self.event_id)
    | csu.exceptions.RetryableStatusError: RetryableStatusError(<Response [200 OK]>, accept_statuses=[999], retry_statuses=[200])
    | (200, b'{{"args":{{"accept_statuses":"{{999}}","expect_json":"true","follow_redirects":"false","foo":"bar","retries_left":"1","retry_count":"2","retry_statuses":"{{200}}"}},"data":"config={{\\'custom\\': \\'config\\'}}","files":{{}},"form":{{}},"headers":{{"Accept":"*/*","Accept-Encoding":"gzip, deflate, br","Connection":"keep-alive","Content-Length":"27","Host":"127.0.0.1:12345","User-Agent":"python-httpx/0.X.X"}},"json":null,"method":"POST","origin":"127.0.0.1","url":"http://127.0.0.1:12345/anything?foo=bar&accept_statuses={{999}}&expect_json=true&follow_redirects=false&retries_left=1&retry_count=2&retry_statuses={{200}}"}}\\n')
    +---------------- 4 ----------------
    | Traceback (most recent call last):
    |   File "{service.__file__}", line 223, in request
    |     return self.handle_process_response(response, retry_statuses=retry_statuses, accept_statuses=accept_statuses, expect_json=expect_json)
    |            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "{service.__file__}", line 148, in handle_process_response
    |     raise RetryableStatusError(response, accept_statuses, retry_statuses, event_id=self.event_id)
    | csu.exceptions.RetryableStatusError: RetryableStatusError(<Response [200 OK]>, accept_statuses=[999], retry_statuses=[200])
    | (200, b'{{"args":{{"accept_statuses":"{{999}}","expect_json":"true","follow_redirects":"false","foo":"bar","retries_left":"0","retry_count":"3","retry_statuses":"{{200}}"}},"data":"config={{\\'custom\\': \\'config\\'}}","files":{{}},"form":{{}},"headers":{{"Accept":"*/*","Accept-Encoding":"gzip, deflate, br","Connection":"keep-alive","Content-Length":"27","Host":"127.0.0.1:12345","User-Agent":"python-httpx/0.X.X"}},"json":null,"method":"POST","origin":"127.0.0.1","url":"http://127.0.0.1:12345/anything?foo=bar&accept_statuses={{999}}&expect_json=true&follow_redirects=false&retries_left=0&retry_count=3&retry_statuses={{200}}"}}\\n')
    +------------------------------------
------------------------------------------------------------ response exception ------------------------------------------------------------
  {{'accident_id': '20241212:01:79200.00', 'detail': 'Internal server error.', 'code': 'server'}}
============================================================================================================================================"""
    )


@pytest.mark.vcr
def test_custom_context_0_retries(httpbin, fake_accident_id, caplogs):
    custom = CustomService(httpbin.url, RETRIES=0)
    with pytest.raises(InternalServiceError) as exc:
        custom.run()

    fail = exc.value.args[0]
    assert isinstance(fail, RetryableStatusError)
    assert fail.status_code == 200
    fail_data = fail.response.json()
    assert fail_data["args"] == {
        "foo": "bar",
        "accept_statuses": "{999}",
        "expect_json": "true",
        "follow_redirects": "false",
        "retries_left": "0",
        "retry_count": "0",
        "retry_statuses": "{200}",
    }
    assert fail_data["data"] == "config={'custom': 'config'}"

    exception_handler(exc.value, {})
    assert fake_accident_id.calls == [
        "service.py:62",
    ]


def test_common_accept_retry_statuses():
    service = BingoService("http://localhost")
    with service.context() as ctx:
        with pytest.raises(AssertionError, match=r"\[500, 502, 503, 504\] is in both retry_statuses and accept_statuses!"):
            ctx.request("GET", "1234", accept_statuses=[200, 500, 502, 503, 504])
        with pytest.raises(AssertionError, match=r"\[999\] is in both retry_statuses and accept_statuses!"):
            ctx.request("GET", "1234", accept_statuses=[999, 500], retry_statuses=[999])
        with pytest.raises(AssertionError, match=r"\[200\] is in both retry_statuses and accept_statuses!"):
            ctx.request("GET", "1234", retry_statuses=[200])
