from typing import TYPE_CHECKING
from typing import NotRequired
from typing import Protocol
from typing import TypedDict
from typing import Unpack

from rest_framework.permissions import BasePermission

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.views import APIView


class PermissionTest(Protocol):
    def __call__(self, request: Request, view: APIView) -> bool: ...


class MethodTests(TypedDict):
    get: NotRequired[PermissionTest]
    options: NotRequired[PermissionTest]
    head: NotRequired[PermissionTest]
    post: NotRequired[PermissionTest]
    put: NotRequired[PermissionTest]
    patch: NotRequired[PermissionTest]
    delete: NotRequired[PermissionTest]


class GenericPermission(BasePermission):
    def __init__(self, default_test: PermissionTest, **method_tests: Unpack[MethodTests]):
        self.default_test = default_test
        self.method_tests = method_tests

    def __call__(self):
        return self

    def has_permission(self, request, view):
        method = request.method.lower()
        if method in self.method_tests:
            return self.method_tests[method](request, view)
        else:
            return self.default_test(request, view)


class AnyAuthentication(BasePermission):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self, request, view):
        return bool((request.user and request.user.is_authenticated) or request.auth)
