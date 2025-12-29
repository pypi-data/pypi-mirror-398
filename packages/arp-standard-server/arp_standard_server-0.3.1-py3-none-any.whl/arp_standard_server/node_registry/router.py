from __future__ import annotations

from inspect import isawaitable
from typing import TYPE_CHECKING

from fastapi import APIRouter, Body, Query, Path

from arp_standard_model import (
    Health,
    NodeKind,
    NodeRegistryGetNodeTypeParams,
    NodeRegistryGetNodeTypeRequest,
    NodeRegistryHealthRequest,
    NodeRegistryListNodeTypesParams,
    NodeRegistryListNodeTypesRequest,
    NodeRegistryPublishNodeTypeRequest,
    NodeRegistryVersionRequest,
    NodeType,
    NodeTypePublishRequestBody,
    VersionInfo,
)


if TYPE_CHECKING:
    from .server import BaseNodeRegistryServer

def create_router(server: BaseNodeRegistryServer) -> APIRouter:
    router = APIRouter()

    @router.get("/v1/node-types/{node_type_id}", response_model=NodeType, status_code=200)
    async def get_node_type(
        node_type_id: str = Path(..., alias="node_type_id"),
        version: str | None = Query(None, alias="version"),
    ) -> NodeType:
        params = NodeRegistryGetNodeTypeParams(
            node_type_id=node_type_id,
            version=version,
        )
        request = NodeRegistryGetNodeTypeRequest(params=params)
        result = server.get_node_type(request)
        if isawaitable(result):
            result = await result
        return result

    @router.get("/v1/health", response_model=Health, status_code=200)
    async def health(
    ) -> Health:
        request = NodeRegistryHealthRequest()
        result = server.health(request)
        if isawaitable(result):
            result = await result
        return result

    @router.get("/v1/node-types", response_model=list[NodeType], status_code=200)
    async def list_node_types(
        q: str | None = Query(None, alias="q"),
        kind: NodeKind | None = Query(None, alias="kind"),
    ) -> list[NodeType]:
        params = NodeRegistryListNodeTypesParams(
            q=q,
            kind=kind,
        )
        request = NodeRegistryListNodeTypesRequest(params=params)
        result = server.list_node_types(request)
        if isawaitable(result):
            result = await result
        return result

    @router.post("/v1/node-types", response_model=NodeType, status_code=200)
    async def publish_node_type(
        body: NodeTypePublishRequestBody = Body(...),
    ) -> NodeType:
        request = NodeRegistryPublishNodeTypeRequest(body=body)
        result = server.publish_node_type(request)
        if isawaitable(result):
            result = await result
        return result

    @router.get("/v1/version", response_model=VersionInfo, status_code=200)
    async def version(
    ) -> VersionInfo:
        request = NodeRegistryVersionRequest()
        result = server.version(request)
        if isawaitable(result):
            result = await result
        return result

    return router
