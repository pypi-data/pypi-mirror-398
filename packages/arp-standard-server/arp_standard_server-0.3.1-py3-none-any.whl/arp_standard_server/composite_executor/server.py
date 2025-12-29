from __future__ import annotations

import inspect
from abc import ABC, abstractmethod

from fastapi import FastAPI

from arp_standard_model import (
    CompositeBeginResponse,
    CompositeExecutorBeginCompositeNodeRunRequest,
    CompositeExecutorCancelCompositeNodeRunRequest,
    CompositeExecutorHealthRequest,
    CompositeExecutorVersionRequest,
    Health,
    VersionInfo,
)

from arp_standard_server.app import build_app
from arp_standard_server.auth import AuthSettings
from .router import create_router


class BaseCompositeExecutorServer(ABC):
    @abstractmethod
    async def begin_composite_node_run(self, request: CompositeExecutorBeginCompositeNodeRunRequest) -> CompositeBeginResponse:
        raise NotImplementedError

    @abstractmethod
    async def cancel_composite_node_run(self, request: CompositeExecutorCancelCompositeNodeRunRequest) -> None:
        raise NotImplementedError

    @abstractmethod
    async def health(self, request: CompositeExecutorHealthRequest) -> Health:
        raise NotImplementedError

    @abstractmethod
    async def version(self, request: CompositeExecutorVersionRequest) -> VersionInfo:
        raise NotImplementedError

    def create_app(
        self,
        *,
        title: str | None = None,
        auth_settings: AuthSettings | None = None,
    ) -> FastAPI:
        if inspect.isabstract(self.__class__):
            raise TypeError(
                "BaseCompositeExecutorServer has unimplemented abstract methods. "
                "Implement all required endpoints before creating the app."
            )
        return build_app(
            router=create_router(self),
            title=title or "ARP Composite Executor Server",
            auth_settings=auth_settings,
        )
