import uuid
from collections.abc import Iterable
from contextlib import suppress

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_another_jwt_auth import AuthJWT as JWT
from pydantic import Field
from starlette.middleware.sessions import SessionMiddleware as StarletteSessionMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from apppy.auth.errors.service import (
    ServiceKeyAlgorithmMissingError,
)
from apppy.auth.jwks import JwkInfo, JwkPemFile, JwksAuthStorage
from apppy.auth.jwt import JwtAuthContext, JwtAuthSettings
from apppy.env import Env, EnvSettings
from apppy.fastql.errors import GraphQLClientError, GraphQLServerError
from apppy.generic.errors import ApiClientError, ApiError, ApiServerError
from apppy.logger import WithLogger
from apppy.logger.storage import LoggingStorage


class CORSMiddlewareSettings(EnvSettings):
    # CORS_ALLOW_CREDENTIALS
    allow_credentials: bool = Field(default=False)
    # CORS_ALLOW_HEADERS
    allow_headers: list[str] = Field(default=["*"])
    # CORS_ALLOW_METHODS
    allow_methods: list[str] = Field(default=["*"])
    # CORS_ALLOW_ORIGIN_REGEX
    allow_origin_regex: str | None = Field(default=None)
    # CORS_ALLOW_ORIGINS
    allow_origins: list[str] = Field(default=[])
    # CORS_MAX_AGE
    max_age: int = Field(default=600)

    def __init__(self, env: Env) -> None:
        super().__init__(env=env, domain_prefix="CORS")


class CORSMiddleware(FastAPICORSMiddleware, WithLogger):
    """
    Simple wrapper around FastAPI's CORSMiddleware to allow for
    injected settings via EnvSettings
    """

    def __init__(self, app: ASGIApp, settings: CORSMiddlewareSettings):
        super().__init__(
            app=app,
            allow_credentials=settings.allow_credentials,
            allow_headers=settings.allow_headers,
            allow_methods=settings.allow_methods,
            allow_origin_regex=settings.allow_origin_regex,
            allow_origins=settings.allow_origins,
            max_age=settings.max_age,
        )
        self._logger.info(
            "Added CORS middleware",
            extra={
                "allow_credentials": settings.allow_credentials,
                "allow_headers": settings.allow_headers,
                "allow_methods": settings.allow_methods,
                "allow_origin_regex": settings.allow_origin_regex,
                "allow_origins": settings.allow_origins,
                "max_age": settings.max_age,
            },
        )


class ErrorHandlerMiddleware(WithLogger):
    def __init__(
        self,
        app: ASGIApp,
        graphql_paths: Iterable[str] = ("/graphql",),
    ):
        self._app = app
        self._graphql_paths = graphql_paths

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        request_path = scope.get("path") or scope.get("raw_path", b"").decode("latin1")
        is_graphql_api = any(request_path.startswith(p) for p in self._graphql_paths)
        response_started = {"value": False}

        async def send_wrapper(message: Message) -> None:
            # Note if the response has already been started
            if message["type"] == "http.response.start":
                response_started["value"] = True
            await send(message)

        if is_graphql_api is True:
            try:
                await self._app(scope, receive, send_wrapper)
            except GraphQLClientError as e:
                e_json = jsonable_encoder(e)
                self._logger.warning(
                    "Client error during graphql request",
                    extra={"code": e.code, "status": e.status, "details": e_json},
                )
                raise
            except GraphQLServerError as e:
                e_json = jsonable_encoder(e)
                self._logger.exception(
                    "Server error during graphql request",
                    extra={"code": e.code, "status": e.status, "details": e_json},
                )
                raise
            except Exception:
                self._logger.exception(
                    "Unhandled error during graphql request "
                    + "(it is possible that the error type does not inherit "
                    + "from GraphQLClientError / GraphQLServerError)",
                    extra={"code": "unknown_graphql_server_error", "status": 500},
                )
                raise

            return

        try:
            await self._app(scope, receive, send_wrapper)
        except ApiClientError as e:
            e_json = jsonable_encoder(e)
            self._logger.warning(
                "Client error during api request",
                extra={"code": e.code, "status": e.status, "details": e_json},
            )

            if response_started["value"] is True:
                # Too late to change the response; just log.
                return

            resp = JSONResponse(content=e_json, status_code=e.status)
            await resp(scope, receive, send)
        except ApiServerError as e:
            e_json = jsonable_encoder(e)
            self._logger.exception(
                "Server error during api request",
                extra={"code": e.code, "status": e.status, "details": e_json},
            )

            if response_started["value"] is True:
                # Too late to change the response; just log.
                return

            resp = JSONResponse(content={"code": e.code, "status": e.status}, status_code=e.status)
            await resp(scope, receive, send)
        except Exception:
            self._logger.exception(
                "Unhandled error during api request",
                extra={"code": "unknown_server_error", "status": 500},
            )
            if response_started["value"] is True:
                # Too late to change the response; just log.
                return

            resp = JSONResponse(
                content={"code": "unknown_server_error", "status": 500},
                status_code=500,
            )
            await resp(scope, receive, send)


class JwtAuthMiddlewareSettings(EnvSettings):
    # JWT_AUTH_EXCLUDE_PATHS
    exclude_paths: list[str] = Field(default=[])

    def __init__(self, env: Env) -> None:
        super().__init__(env=env, domain_prefix="JWT_AUTH")


class JwtAuthMiddleware(WithLogger):
    """
    A middleware instance which analyzes the request headers,
    creates a JwtAuthContext, and set it in thread local storage
    """

    def __init__(
        self,
        app: ASGIApp,
        settings: JwtAuthMiddlewareSettings,
        jwt_auth_settings: JwtAuthSettings,
        jwks_auth_storage: JwksAuthStorage,
        exclude_paths: list[str] | None = None,
    ):
        self._app = app
        self._settings = settings
        # /health and /version paths are never authenticated
        self._exclude_paths = (settings.exclude_paths or []) + ["/health", "/version"]

        self._jwks_auth_storage = jwks_auth_storage

        # Load the global JWT configuration JWT.
        # This is used for processing user requests below.
        @JWT.load_config
        def load_config_jwtauth_global():
            return jwt_auth_settings

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        request_path = scope.get("path") or scope.get("raw_path", b"").decode("latin1")
        if any(request_path.startswith(p) for p in self._exclude_paths):
            await self._app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        jwt_headers: dict | None = JwtAuthContext.peek(request)

        try:
            service_name: str | None = None
            if jwt_headers is not None:
                self._logger.debug("JWT headers", extra=jwt_headers)
                service_name, _ = JwkPemFile.parse_kid(jwt_headers.get("kid"))

            if jwt_headers is not None and service_name is not None:
                # CASE: A Service is making the request
                jwk_info: JwkInfo = self._jwks_auth_storage.get_jwk(jwt_headers["kid"])

                if "alg" not in jwt_headers:
                    raise ServiceKeyAlgorithmMissingError()

                public_key = jwk_info.jwk.get_op_key("verify")
                auth_ctx = JwtAuthContext.from_service_request(
                    request, jwt_headers["alg"], public_key
                )
            else:
                # CASE: A User is making the request
                # Instead of using the JWKS storage, we'll
                # use the global configuration loaded in __init__
                auth_ctx = JwtAuthContext.from_user_request(request)
        except ApiError as e:
            # If we encounter an error while preprocessing the
            # auth context, we'll capture the error and keep going. The
            # authentication and authorization permission are designed
            # to handle this and raise the appropriate error.
            auth_ctx = JwtAuthContext(preprocessing_error=e)

        JwtAuthContext.set_current_auth_context(auth_ctx)
        await self._app(scope, receive, send)


class RequestIdMiddlewareSettings(EnvSettings):
    # REQUEST_ID_HEADER_NAME
    header_name: str = Field(default="X-Request-ID")
    # REQUEST_ID_MAX_LENGTH
    max_length: int = Field(default=36)

    def __init__(self, env: Env) -> None:
        super().__init__(env=env, domain_prefix="REQUEST_ID")


class RequestIdMiddleware(WithLogger):
    def __init__(
        self,
        app: ASGIApp,
        settings: RequestIdMiddlewareSettings,
    ):
        self._app = app
        self._settings = settings
        self._header_name_bytes = settings.header_name.lower().encode("latin-1")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        request_id = self._read_incoming_request_id(scope) or str(uuid.uuid4())

        # Store in LoggingStorage (thread-local)
        with suppress(RuntimeError):
            LoggingStorage.get_global().add_request_id(request_id)

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append(
                    (self._settings.header_name.encode("latin-1"), request_id.encode("latin-1"))
                )
                message = {**message, "headers": headers}
            elif message["type"] == "http.response.body" and message.get("more_body") is False:
                # Cleanup after final chunk
                with suppress(RuntimeError):
                    LoggingStorage.get_global().reset()

            await send(message)

        try:
            await self._app(scope, receive, send_wrapper)
        finally:
            # If an exception short-circuited before body end, still cleanup
            with suppress(RuntimeError):
                LoggingStorage.get_global().reset()

    def _read_incoming_request_id(self, scope: Scope) -> str | None:
        # ASGI headers are list[tuple[bytes, bytes]]
        for k, v in scope.get("headers") or []:
            if k.lower() == self._header_name_bytes:
                value = (v or b"").decode("latin-1").strip()

                if not value:
                    return None

                # Length validation to prevent abuse
                if len(value) > self._settings.max_length:
                    return None

                return value

        return None


class SessionMiddlewareSettings(EnvSettings):
    # SESSION_MIDDLEWARE_SECRET_KEY
    secret_key: str = Field(exclude=True)

    def __init__(self, env: Env) -> None:
        super().__init__(env=env, domain_prefix="SESSION_MIDDLEWARE")


class SessionMiddleware(StarletteSessionMiddleware):
    """
    Simple wrapper around Starlette's SessionMiddleware to allow for
    injected settings via EnvSettings
    """

    def __init__(self, app: ASGIApp, settings: SessionMiddlewareSettings):
        super().__init__(app=app, secret_key=settings.secret_key)
