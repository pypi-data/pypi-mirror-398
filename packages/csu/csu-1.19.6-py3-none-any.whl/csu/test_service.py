from typing import reveal_type

import httpx
import time_machine

from csu.service import AsyncHTTPService
from csu.service import AsyncHTTPServiceContext
from csu.service import HTTPService
from csu.service import HTTPServiceContext

from . import exceptions
from .exceptions import get_event_id


def test_get_accident_id(monkeypatch):
    monkeypatch.setattr(exceptions, "urandom", lambda len: bytes(range(len)))
    with time_machine.travel(1674777700.5816755):
        assert get_event_id() == "20230127:00010203:00100.58"


class CustomResponse:
    def bar(self, x: float) -> float: ...


class CustomServiceContext(HTTPServiceContext[CustomResponse]):
    def request(self, custom: int):
        reveal_type(self)
        resp = super().request("GET", "custom")
        reveal_type(resp)
        return resp

    def handle_process_response(self, response: httpx.Response, **kwargs):
        reveal_type(self)
        return CustomResponse()


reveal_type(HTTPServiceContext.request)
reveal_type(CustomServiceContext.request)
reveal_type(CustomServiceContext.handle_process_response)


class CustomService(HTTPService[CustomServiceContext]):
    context_class = CustomServiceContext

    def auth(self, request: httpx.Request, context):
        reveal_type(context)
        reveal_type(context.request)
        yield request

    def foo(self):
        with self.context() as ctx:
            reveal_type(ctx)
            reveal_type(ctx.request)
            r = ctx.request(123)
            reveal_type(r)
            reveal_type(r.bar)
            return r


reveal_type(HTTPService.context)
reveal_type(CustomService.context)
reveal_type(CustomService.foo)

###################
###### async ######
###################


class AsyncCustomServiceContext(AsyncHTTPServiceContext):
    async def request(self, custom: int) -> CustomResponse:
        return await super().request("GET", "custom")

    def handle_process_response(self, response: httpx.Response, **kwargs) -> CustomResponse:
        return CustomResponse()


reveal_type(AsyncHTTPServiceContext.request)
reveal_type(AsyncHTTPServiceContext.request)
reveal_type(AsyncCustomServiceContext.request)
reveal_type(AsyncCustomServiceContext.handle_process_response)


class AsyncCustomService(AsyncHTTPService[AsyncCustomServiceContext]):
    context_class = AsyncCustomServiceContext

    def auth(self, request: httpx.Request, context):
        reveal_type(context)
        reveal_type(context.request)
        yield request

    async def foo(self):
        with self.context() as ctx:
            reveal_type(ctx)
            reveal_type(ctx.request)
            r = await ctx.request(123)
            reveal_type(r)
            reveal_type(r.bar)
            return r


reveal_type(AsyncHTTPService.context)
reveal_type(AsyncCustomService.context)
reveal_type(AsyncCustomService.foo)
