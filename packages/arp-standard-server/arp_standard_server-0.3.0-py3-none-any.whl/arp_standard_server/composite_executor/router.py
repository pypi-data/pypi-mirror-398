from __future__ import annotations

from inspect import isawaitable
from typing import TYPE_CHECKING

from fastapi import APIRouter, Body

from arp_standard_model import (
    CompositeBeginRequestBody,
    CompositeBeginResponse,
    CompositeExecutorBeginCompositeNodeRunRequest,
    CompositeExecutorHealthRequest,
    CompositeExecutorVersionRequest,
    Health,
    VersionInfo,
)


if TYPE_CHECKING:
    from .server import BaseCompositeExecutorServer

def create_router(server: BaseCompositeExecutorServer) -> APIRouter:
    router = APIRouter()

    @router.post("/v1/composite-node-runs:begin", response_model=CompositeBeginResponse, status_code=200)
    async def begin_composite_node_run(
        body: CompositeBeginRequestBody = Body(...),
    ) -> CompositeBeginResponse:
        request = CompositeExecutorBeginCompositeNodeRunRequest(body=body)
        result = server.begin_composite_node_run(request)
        if isawaitable(result):
            result = await result
        return result

    @router.get("/v1/health", response_model=Health, status_code=200)
    async def health(
    ) -> Health:
        request = CompositeExecutorHealthRequest()
        result = server.health(request)
        if isawaitable(result):
            result = await result
        return result

    @router.get("/v1/version", response_model=VersionInfo, status_code=200)
    async def version(
    ) -> VersionInfo:
        request = CompositeExecutorVersionRequest()
        result = server.version(request)
        if isawaitable(result):
            result = await result
        return result

    return router
