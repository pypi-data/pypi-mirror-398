from dataclasses import dataclass

import strawberry
from fastapi import APIRouter, FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import Field

from apppy.db.migrations import Migrations
from apppy.env import Env, EnvSettings
from apppy.fastql import FastQL
from apppy.fastql.annotation import fastql_query, fastql_query_field, fastql_type_output
from apppy.fastql.annotation.mutation import fastql_mutation, fastql_mutation_field
from apppy.logger import WithLogger


class VersionSettings(EnvSettings):
    # VERSION_COMMIT
    commit: str = Field(default="local")
    # VERSION_ENVIRONMENT
    environment: str = Field(default="local")
    # VERSION_RELEASE
    release: str = Field(default="local")

    def __init__(self, env: Env) -> None:
        super().__init__(env=env, domain_prefix="VERSION")


@dataclass
@fastql_type_output
class VersionApiOutput:
    commit: str
    environment: str
    migration: str | None
    release: str


class VersionApi(WithLogger):
    def __init__(self, settings: VersionSettings, fastapi: FastAPI, migrations: Migrations):
        self._settings = settings
        self._migrations = migrations
        fastapi.include_router(self.__create_router())

    def __create_router(self) -> APIRouter:
        router = APIRouter()

        @router.get("/version")
        async def version():
            version_output = VersionApiOutput(
                commit=self._settings.commit,
                environment=self._settings.environment,
                migration=(await self._migrations.head()),
                release=self._settings.release,
            )

            resp_json = jsonable_encoder(version_output)
            return JSONResponse(content=resp_json, status_code=200)

        return router


@fastql_mutation()
class VersionMutation(WithLogger):
    def __init__(self, settings: VersionSettings, fastql: FastQL, migrations: Migrations) -> None:
        self._settings = settings
        self._migrations = migrations
        fastql.include_in_schema(self)

    @fastql_mutation_field(
        skip_permission_checks=True,
    )
    async def version(self, info: strawberry.Info) -> VersionApiOutput:
        version_output = VersionApiOutput(
            commit=self._settings.commit,
            environment=self._settings.environment,
            migration=(await self._migrations.head()),
            release=self._settings.release,
        )

        return version_output


@fastql_query()
class VersionQuery(WithLogger):
    def __init__(self, settings: VersionSettings, fastql: FastQL, migrations: Migrations) -> None:
        self._settings = settings
        self._migrations = migrations
        fastql.include_in_schema(self)

    @fastql_query_field(
        skip_permission_checks=True,
    )
    async def version(self, info: strawberry.Info) -> VersionApiOutput:
        version_output = VersionApiOutput(
            commit=self._settings.commit,
            environment=self._settings.environment,
            migration=(await self._migrations.head()),
            release=self._settings.release,
        )

        return version_output
