from __future__ import annotations

import inspect
from abc import ABC, abstractmethod

from fastapi import FastAPI

from arp_standard_model import (
    AtomicExecuteResult,
    AtomicExecutorExecuteAtomicNodeRunRequest,
    AtomicExecutorHealthRequest,
    AtomicExecutorVersionRequest,
    Health,
    VersionInfo,
)

from arp_standard_server.app import build_app
from arp_standard_server.auth import AuthSettings
from .router import create_router


class BaseAtomicExecutorServer(ABC):
    @abstractmethod
    async def execute_atomic_node_run(self, request: AtomicExecutorExecuteAtomicNodeRunRequest) -> AtomicExecuteResult:
        raise NotImplementedError

    @abstractmethod
    async def health(self, request: AtomicExecutorHealthRequest) -> Health:
        raise NotImplementedError

    @abstractmethod
    async def version(self, request: AtomicExecutorVersionRequest) -> VersionInfo:
        raise NotImplementedError

    def create_app(
        self,
        *,
        title: str | None = None,
        auth_settings: AuthSettings | None = None,
    ) -> FastAPI:
        if inspect.isabstract(self.__class__):
            raise TypeError(
                "BaseAtomicExecutorServer has unimplemented abstract methods. "
                "Implement all required endpoints before creating the app."
            )
        return build_app(
            router=create_router(self),
            title=title or "ARP Atomic Executor Server",
            auth_settings=auth_settings,
        )
