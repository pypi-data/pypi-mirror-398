import logging
import subprocess
import sys
import typing
from typing import Any

import uvicorn
from dependency_injector import containers, providers
from fastapi import FastAPI
from fastapi_lifespan_manager import LifespanManager
from pydantic import Field

from apppy.app.context import (
    create_context_authenticated,
    create_context_unauthenticated,
)
from apppy.app.health import DefaultHealthCheck, HealthApi, HealthCheck
from apppy.app.middleware import (
    CORSMiddleware,
    CORSMiddlewareSettings,
    ErrorHandlerMiddleware,
    JwtAuthMiddleware,
    JwtAuthMiddlewareSettings,
    RequestIdMiddleware,
    RequestIdMiddlewareSettings,
    SessionMiddleware,
    SessionMiddlewareSettings,
)
from apppy.app.version import VersionApi, VersionMutation, VersionQuery, VersionSettings
from apppy.auth.jwks import JwksAuthStorage, JwksAuthStorageSettings
from apppy.auth.jwt import JwtAuthSettings
from apppy.auth.oauth import OAuthRegistry, OAuthRegistrySettings
from apppy.db.migrations import DefaultMigrations, Migrations
from apppy.db.postgres import PostgresClient, PostgresClientSettings
from apppy.env import Env, EnvSettings
from apppy.fastql import FastQL
from apppy.fastql.typed_id import TypedIdEncoder, TypedIdEncoderSettings
from apppy.fs import FileSystem, FileSystemSettings
from apppy.fs.local import LocalFileSystem, LocalFileSystemSettings
from apppy.logger import bootstrap_global_logging

_logger = logging.getLogger("apppy.app.App")


def _noop_provider(*args: Any, **kwargs: Any) -> None:
    return None


class MinimalApp(containers.DeclarativeContainer):
    """
    A conceptual representation of a minimal application. This includes:

    - A reference to the configuration environment
    """

    env: providers.Dependency[Env] = providers.Dependency(instance_of=Env)
    setup_global_services = providers.Callable(_noop_provider)

    @classmethod
    def create(
        cls,
        env_prefix: str = "APP",
        **kwargs,
    ) -> typing.Self:
        bootstrap_global_logging(kwargs.get("log_level", logging.INFO), stdout=True)

        # We can pass an environment in one of two ways
        # Either a pre-created environment object, or
        # a name of an environment to load.
        if "env" in kwargs:
            env: Env = kwargs["env"]
            logging.debug(
                "Received environment directly",
                extra={"env_prefix": env.prefix, "env_name": env.name},
            )
        else:
            env = Env.load(prefix=env_prefix, name=kwargs.get("env_name"))

        _logger.info("Creating application", extra=kwargs)
        app: typing.Self = cls()
        app.env.override(providers.Object(env))

        app.setup_global_services(app)
        return app


class GraphqlSettings(EnvSettings):
    # GRAPHQL_GRAPHIQL
    graphiql: bool = Field(default=False)

    def __init__(self, env: Env) -> None:
        super().__init__(env=env, domain_prefix="GRAPHQL")


class ApiApp(containers.DeclarativeContainer):
    """
    A conceptual representation of an API application. This includes:

    - A reference to the configuration environment
    - A reference to fastapi
    - Common services associated with an api server
    """

    ##### Basic Application #####
    env: providers.Dependency[Env] = providers.Dependency(instance_of=Env)
    fastapi: providers.Dependency[FastAPI] = providers.Dependency(instance_of=FastAPI)
    fastql: providers.Provider[FastQL] = providers.Singleton(FastQL)
    graphql_settings: providers.Provider[GraphqlSettings] = providers.Singleton(
        GraphqlSettings, env=env
    )
    lifespan: providers.Provider[LifespanManager] = providers.Singleton(LifespanManager)

    # Typed Ids
    typed_id_encoder_settings: providers.Provider[TypedIdEncoderSettings] = providers.Singleton(
        TypedIdEncoderSettings, env=env
    )
    typed_id_encoder: providers.Provider[TypedIdEncoder] = providers.Singleton(
        TypedIdEncoder, settings=typed_id_encoder_settings
    )

    ##### Core Application Systems #####
    # FileSystem
    fs_settings: providers.Provider[FileSystemSettings] = providers.Singleton(
        FileSystemSettings, env=env
    )
    fs: providers.Provider[FileSystem] = providers.Singleton(FileSystem, settings=fs_settings)
    fs_local_settings: providers.Provider[LocalFileSystemSettings] = providers.Singleton(
        LocalFileSystemSettings, env=env
    )
    fs_local: providers.Provider[LocalFileSystem] = providers.Singleton(
        LocalFileSystem, settings=fs_local_settings, fs=fs
    )

    ##### Microservice: Auth #####
    jwt_auth_settings: providers.Provider[JwtAuthSettings] = providers.Singleton(
        JwtAuthSettings, env=env
    )
    jwks_auth_storage_settings: providers.Provider[JwksAuthStorageSettings] = providers.Singleton(
        JwksAuthStorageSettings, env=env
    )
    jwks_auth_storage: providers.Provider[JwksAuthStorage] = providers.Singleton(
        JwksAuthStorage, settings=jwks_auth_storage_settings, lifespan=lifespan, fs=fs
    )

    oauth_registry_settings: providers.Provider[OAuthRegistrySettings] = providers.Singleton(
        OAuthRegistrySettings, env=env
    )
    oauth_registry: providers.Provider[OAuthRegistry] = providers.Singleton(
        OAuthRegistry, settings=oauth_registry_settings
    )

    session_middleware_settings: providers.Provider[SessionMiddlewareSettings] = (
        providers.Singleton(SessionMiddlewareSettings, env=env)
    )

    jwt_auth_middleware_settings: providers.Provider[JwtAuthMiddlewareSettings] = (
        providers.Singleton(JwtAuthMiddlewareSettings, env=env)
    )

    ##### Microservice: Database #####
    migrations: providers.Dependency[Migrations] = providers.Dependency()
    migrations.override(providers.Singleton(DefaultMigrations))

    postgres_settings: providers.Provider[PostgresClientSettings] = providers.Singleton(
        PostgresClientSettings, env=env
    )
    postgres: providers.Provider[PostgresClient] = providers.Singleton(
        PostgresClient, settings=postgres_settings, lifespan=lifespan
    )

    ##### Microservice: Health #####
    health_check: providers.Provider[HealthCheck] = providers.Singleton[HealthCheck](
        DefaultHealthCheck
    )

    health_api: providers.Provider[HealthApi] = providers.Singleton(
        HealthApi, fastapi=fastapi, health_check=health_check
    )

    ##### Microservice: Version #####
    version_settings: providers.Provider[VersionSettings] = providers.Singleton(
        VersionSettings, env=env
    )
    version_api: providers.Provider[VersionApi] = providers.Singleton(
        VersionApi,
        settings=version_settings,
        fastapi=fastapi,
        migrations=migrations,
    )
    version_mutation: providers.Provider[VersionMutation] = providers.Singleton(
        VersionMutation,
        settings=version_settings,
        fastql=fastql,
        migrations=migrations,
    )
    version_query: providers.Provider[VersionQuery] = providers.Singleton(
        VersionQuery,
        settings=version_settings,
        fastql=fastql,
        migrations=migrations,
    )

    ##### Microservice: CORS #####
    cors_middleware_settings: providers.Provider[CORSMiddlewareSettings] = providers.Singleton(
        CORSMiddlewareSettings, env=env
    )

    ##### Microservice: Request Id #####
    request_id_middleware_settings: providers.Provider[RequestIdMiddlewareSettings] = (
        providers.Singleton(RequestIdMiddlewareSettings, env=env)
    )

    # Setup services which are attached to an API, which
    # means that they will not have a chance to be otherwise
    # instantiated.
    setup_global_services = providers.Callable(_noop_provider)
    # This registers all necessary middleware.
    register_middleware = providers.Callable(_noop_provider)
    # This registers all externally facing GraphQL operations.
    register_graphql_operations = providers.Callable(_noop_provider)
    # This registers all externally facing REST API routes.
    register_rest_routes = providers.Callable(_noop_provider)

    @classmethod
    def create(
        cls,
        env_prefix: str = "APP",
        fastapi_fn: typing.Callable[[LifespanManager], FastAPI] | None = None,
        inject_auth: bool = True,
        **kwargs,
    ) -> typing.Self:
        bootstrap_global_logging(kwargs.get("log_level", logging.INFO))

        # We can pass an environment in one of two ways
        # Either a pre-created environment object, or
        # a name of an environment to load.
        if "env" in kwargs:
            env: Env = kwargs["env"]
            logging.debug(
                "Received environment directly",
                extra={"env_prefix": env.prefix, "env_name": env.name},
            )
        else:
            env = Env.load(prefix=env_prefix, name=kwargs.get("env_name"))

        _logger.info("Creating application", extra=kwargs)
        app: typing.Self = cls()
        app.env.override(providers.Object(env))

        if fastapi_fn is not None:
            fastapi: FastAPI = fastapi_fn(app.lifespan())
        else:
            fastapi = FastAPI(lifespan=app.lifespan())
        app.fastapi.override(providers.Object(fastapi))

        _logger.info("Assembling application")
        app.health_api()  # Register a health API with each application
        app.version_api()  # Register a version API with each application
        app.version_mutation()  # Register a version mutation with each application
        app.version_query()  # Register a version query with each application

        # Run hook for individual applications to
        # set up their custom global services
        app.setup_global_services(app)
        if inject_auth is True:
            # We'll instantiate the local file system here
            # to allow for the jwks auth storage to work.
            # However, in production application should use
            # a more robust filesystem (e.g. S3 or Supabase)
            app.fs_local()
            # Pre-build the jwks auth service. Note that we load
            # this singleton for service GraphQL requests but we
            # would like the constructor to be run beforehand here
            # NOTE: This needs to come after the FileSystem
            app.jwks_auth_storage()

            app.fastapi().add_middleware(
                SessionMiddleware,  # type: ignore[invalid-argument-type]
                settings=app.session_middleware_settings(),
            )
            app.fastapi().add_middleware(
                JwtAuthMiddleware,  # type: ignore[invalid-argument-type]
                settings=app.jwt_auth_middleware_settings(),
                jwt_auth_settings=app.jwt_auth_settings(),
                jwks_auth_storage=app.jwks_auth_storage(),
            )

        # Register error handling middleware with each application
        fastapi.add_middleware(ErrorHandlerMiddleware)  # type: ignore[invalid-argument-type]
        # Register CORS middleware with each application
        app.fastapi().add_middleware(
            CORSMiddleware,  # type: ignore[invalid-argument-type]
            settings=app.cors_middleware_settings(),
        )
        # Register a request id middleware with each application
        fastapi.add_middleware(
            RequestIdMiddleware,  # type: ignore[invalid-argument-type]
            settings=app.request_id_middleware_settings(),
        )

        # Run hook for individual applications to
        # set up their custom middleware and APIs
        app.register_middleware(app)
        app.register_graphql_operations(app)
        app.register_rest_routes(app)

        _logger.info("Preloading graphql schema with FastQL")
        fastql = app.fastql()
        _ = fastql.schema
        if len(fastql.types_id_raw) > 0:
            _logger.info("Found FastQL id types. Registering TypedIdEncoder.")
            TypedIdEncoder.set_global(app.typed_id_encoder())

        _logger.info("Including graphql router in FastAPI")
        include_graphiql = (not app.env().is_production) or app.graphql_settings().graphiql
        _logger.info(
            "Checking for Graphiql user interface inclusion",
            extra={"include_graphiql": include_graphiql},
        )
        fastapi.include_router(
            router=app.fastql().create_router(
                context_getter=(
                    create_context_authenticated if inject_auth else create_context_unauthenticated
                ),
                graphiql=include_graphiql,
            ),
        )

        return app

    @classmethod
    def create_debug_fastapi(cls) -> "FastAPI":
        # NOTE: A uvicorn factory must be completely self-contained with
        # no runtime configuration. Therefore, we just have to assume
        # that we're running in debug mode and that we're in a local environment.
        app = cls.create(
            **{"env_name": "local", "log_level": logging.DEBUG},  # type: ignore[arg-type]
        )
        return app.fastapi()

    @classmethod
    def run(cls, app_name: str, debug: bool = False, **kwargs) -> None:
        if debug:
            # When in debug using hot reloads, we have to launch a subprocess
            cmd = [
                sys.executable,  # python interpreter
                "-m",
                "uvicorn",
                f"{cls.__module__}:{cls.__name__}.create_debug_fastapi",
                "--factory",
                "--host",
                "0.0.0.0",
                "--log-level",
                kwargs.get("log_level", "debug"),
                "--port",
                str(kwargs.get("port", 8000)),
                "--reload",
                "--reload-dir",
                f"applications/{app_name}",
            ]
            subprocess.run(cmd, check=True)
        else:
            app = cls.create(**kwargs)
            uvicorn_config = uvicorn.Config(
                app=app.fastapi(),
                host="0.0.0.0",
                log_level=kwargs.get("log_level", "info"),
                port=kwargs.get("port", 8000),
                reload=False,
            )
            uvicorn_server = uvicorn.Server(uvicorn_config)
            uvicorn_server.run()
