from hmac import compare_digest

from asgiref.sync import sync_to_async
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from rest_framework.authentication import SessionAuthentication as BaseSessionAuthentication
from rest_framework.authentication import get_authorization_header
from rest_framework.request import Request

from ..conf import DRF_BEARER_TOKEN
from ..gettext_lazy import _


class BearerTokenAuthentication(BaseAuthentication):
    """
    Simple token based authentication.

    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string "Token ".  For example:

        Authorization: Bearer 401f7ac837da42b97f613d789819ff93537bee6a
    """

    keyword = "Bearer"
    keyword_test = keyword.lower().encode()
    expected_token_value: str | list[str] = DRF_BEARER_TOKEN

    async def aauthenticate(self, request: Request):
        return self.authenticate(request)

    def authenticate(self, request: Request):
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != self.keyword_test:
            return None

        if len(auth) == 1:
            raise exceptions.AuthenticationFailed(_("Invalid Authorization header: no credentials provided."))
        elif len(auth) > 2:
            raise exceptions.AuthenticationFailed(_("Invalid Authorization header: token contains spaces."))

        try:
            token = auth[1].decode()
        except UnicodeError:
            raise exceptions.AuthenticationFailed(_("Invalid Authorization header: token contains invalid characters.")) from None

        expected = self.expected_token_value
        if isinstance(expected, list):
            result = list(filter(None, (compare_digest(token, value) for value in expected)))
        else:
            result = compare_digest(token, expected)

        if result:
            return None, token
        else:
            return None

    def authenticate_header(self, request):
        return self.keyword


class SessionAuthentication(BaseSessionAuthentication):
    async def aauthenticate(self, request: Request):
        return await sync_to_async(self.authenticate, thread_sensitive=False)(request)

    def authenticate(self, request: Request):
        return super().authenticate(request)
