from __future__ import annotations

import inspect
from abc import ABC, abstractmethod

from fastapi import FastAPI

from arp_standard_model import (
    Health,
    Run,
    RunGatewayCancelRunRequest,
    RunGatewayGetRunRequest,
    RunGatewayHealthRequest,
    RunGatewayStartRunRequest,
    RunGatewayStreamRunEventsRequest,
    RunGatewayVersionRequest,
    VersionInfo,
)

from arp_standard_server.app import build_app
from arp_standard_server.auth import AuthSettings
from .router import create_router


class BaseRunGatewayServer(ABC):
    @abstractmethod
    async def cancel_run(self, request: RunGatewayCancelRunRequest) -> Run:
        raise NotImplementedError

    @abstractmethod
    async def get_run(self, request: RunGatewayGetRunRequest) -> Run:
        raise NotImplementedError

    @abstractmethod
    async def health(self, request: RunGatewayHealthRequest) -> Health:
        raise NotImplementedError

    @abstractmethod
    async def start_run(self, request: RunGatewayStartRunRequest) -> Run:
        raise NotImplementedError

    @abstractmethod
    async def stream_run_events(self, request: RunGatewayStreamRunEventsRequest) -> str:
        raise NotImplementedError

    @abstractmethod
    async def version(self, request: RunGatewayVersionRequest) -> VersionInfo:
        raise NotImplementedError

    def create_app(
        self,
        *,
        title: str | None = None,
        auth_settings: AuthSettings | None = None,
    ) -> FastAPI:
        if inspect.isabstract(self.__class__):
            raise TypeError(
                "BaseRunGatewayServer has unimplemented abstract methods. "
                "Implement all required endpoints before creating the app."
            )
        return build_app(
            router=create_router(self),
            title=title or "ARP Run Gateway Server",
            auth_settings=auth_settings,
        )
