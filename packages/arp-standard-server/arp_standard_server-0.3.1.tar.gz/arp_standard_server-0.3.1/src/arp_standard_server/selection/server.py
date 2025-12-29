from __future__ import annotations

import inspect
from abc import ABC, abstractmethod

from fastapi import FastAPI

from arp_standard_model import (
    CandidateSet,
    Health,
    SelectionGenerateCandidateSetRequest,
    SelectionHealthRequest,
    SelectionVersionRequest,
    VersionInfo,
)

from arp_standard_server.app import build_app
from arp_standard_server.auth import AuthSettings
from .router import create_router


class BaseSelectionServer(ABC):
    @abstractmethod
    async def generate_candidate_set(self, request: SelectionGenerateCandidateSetRequest) -> CandidateSet:
        raise NotImplementedError

    @abstractmethod
    async def health(self, request: SelectionHealthRequest) -> Health:
        raise NotImplementedError

    @abstractmethod
    async def version(self, request: SelectionVersionRequest) -> VersionInfo:
        raise NotImplementedError

    def create_app(
        self,
        *,
        title: str | None = None,
        auth_settings: AuthSettings | None = None,
    ) -> FastAPI:
        if inspect.isabstract(self.__class__):
            raise TypeError(
                "BaseSelectionServer has unimplemented abstract methods. "
                "Implement all required endpoints before creating the app."
            )
        return build_app(
            router=create_router(self),
            title=title or "ARP Selection Server",
            auth_settings=auth_settings,
        )
