from __future__ import annotations

import inspect
from abc import ABC, abstractmethod

from fastapi import FastAPI

from arp_standard_model import (
    Health,
    NodeRegistryGetNodeTypeRequest,
    NodeRegistryHealthRequest,
    NodeRegistryListNodeTypesRequest,
    NodeRegistryPublishNodeTypeRequest,
    NodeRegistryVersionRequest,
    NodeType,
    VersionInfo,
)

from arp_standard_server.app import build_app
from arp_standard_server.auth import AuthSettings
from .router import create_router


class BaseNodeRegistryServer(ABC):
    @abstractmethod
    async def get_node_type(self, request: NodeRegistryGetNodeTypeRequest) -> NodeType:
        raise NotImplementedError

    @abstractmethod
    async def health(self, request: NodeRegistryHealthRequest) -> Health:
        raise NotImplementedError

    @abstractmethod
    async def list_node_types(self, request: NodeRegistryListNodeTypesRequest) -> list[NodeType]:
        raise NotImplementedError

    @abstractmethod
    async def publish_node_type(self, request: NodeRegistryPublishNodeTypeRequest) -> NodeType:
        raise NotImplementedError

    @abstractmethod
    async def version(self, request: NodeRegistryVersionRequest) -> VersionInfo:
        raise NotImplementedError

    def create_app(
        self,
        *,
        title: str | None = None,
        auth_settings: AuthSettings | None = None,
    ) -> FastAPI:
        if inspect.isabstract(self.__class__):
            raise TypeError(
                "BaseNodeRegistryServer has unimplemented abstract methods. "
                "Implement all required endpoints before creating the app."
            )
        return build_app(
            router=create_router(self),
            title=title or "ARP Node Registry Server",
            auth_settings=auth_settings,
        )
