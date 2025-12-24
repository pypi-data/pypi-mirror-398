import abc

from fastapi import APIRouter, FastAPI

from apppy.logger import WithLogger


class HealthCheck(abc.ABC):
    @abc.abstractmethod
    def health_check(self) -> bool:
        pass

    def ping(self) -> str:
        return "ok"


class DefaultHealthCheck(HealthCheck):
    def health_check(self) -> bool:
        return True


class HealthApi(WithLogger):
    def __init__(self, fastapi: FastAPI, health_check: HealthCheck):
        self._health_check: HealthCheck = health_check
        fastapi.include_router(self.__create_router())

    def __create_router(self) -> APIRouter:
        router = APIRouter()

        @router.get("/health/check")
        async def health_check():
            return {"healthy": self._health_check.health_check()}

        @router.get("/health/ping")
        async def health_ping():
            return {"ping": self._health_check.ping()}

        return router
