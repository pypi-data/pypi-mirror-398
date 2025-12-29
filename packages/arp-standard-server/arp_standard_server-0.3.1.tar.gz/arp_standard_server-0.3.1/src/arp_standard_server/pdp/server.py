from __future__ import annotations

import inspect
from abc import ABC, abstractmethod

from fastapi import FastAPI

from arp_standard_model import (
    Health,
    PdpDecidePolicyRequest,
    PdpHealthRequest,
    PdpVersionRequest,
    PolicyDecision,
    VersionInfo,
)

from arp_standard_server.app import build_app
from arp_standard_server.auth import AuthSettings
from .router import create_router


class BasePdpServer(ABC):
    @abstractmethod
    async def decide_policy(self, request: PdpDecidePolicyRequest) -> PolicyDecision:
        raise NotImplementedError

    @abstractmethod
    async def health(self, request: PdpHealthRequest) -> Health:
        raise NotImplementedError

    @abstractmethod
    async def version(self, request: PdpVersionRequest) -> VersionInfo:
        raise NotImplementedError

    def create_app(
        self,
        *,
        title: str | None = None,
        auth_settings: AuthSettings | None = None,
    ) -> FastAPI:
        if inspect.isabstract(self.__class__):
            raise TypeError(
                "BasePdpServer has unimplemented abstract methods. "
                "Implement all required endpoints before creating the app."
            )
        return build_app(
            router=create_router(self),
            title=title or "ARP Pdp Server",
            auth_settings=auth_settings,
        )
