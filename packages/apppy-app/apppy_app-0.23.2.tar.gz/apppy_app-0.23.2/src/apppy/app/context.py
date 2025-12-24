from dataclasses import dataclass

from fastapi import Request
from strawberry.fastapi.context import BaseContext

from apppy.auth.jwt import JwtAuthContext


@dataclass
class UnauthenticatedAppContext(BaseContext):
    request: Request


def create_context_unauthenticated(request: Request) -> UnauthenticatedAppContext:
    return UnauthenticatedAppContext(request=request)


@dataclass
class AuthenticatedAppContext(BaseContext):
    auth: JwtAuthContext
    request: Request


def create_context_authenticated(request: Request) -> AuthenticatedAppContext:
    # NOTE: The current JwtAuthContext is set in JwtAuthMiddleware
    auth_ctx: JwtAuthContext = JwtAuthContext.current_auth_context()
    return AuthenticatedAppContext(auth=auth_ctx, request=request)
