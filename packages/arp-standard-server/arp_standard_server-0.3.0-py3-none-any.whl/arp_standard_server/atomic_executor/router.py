from __future__ import annotations

from inspect import isawaitable
from typing import TYPE_CHECKING

from fastapi import APIRouter, Body

from arp_standard_model import (
    AtomicExecuteRequestBody,
    AtomicExecuteResult,
    AtomicExecutorExecuteAtomicNodeRunRequest,
    AtomicExecutorHealthRequest,
    AtomicExecutorVersionRequest,
    Health,
    VersionInfo,
)


if TYPE_CHECKING:
    from .server import BaseAtomicExecutorServer

def create_router(server: BaseAtomicExecutorServer) -> APIRouter:
    router = APIRouter()

    @router.post("/v1/atomic-node-runs:execute", response_model=AtomicExecuteResult, status_code=200)
    async def execute_atomic_node_run(
        body: AtomicExecuteRequestBody = Body(...),
    ) -> AtomicExecuteResult:
        request = AtomicExecutorExecuteAtomicNodeRunRequest(body=body)
        result = server.execute_atomic_node_run(request)
        if isawaitable(result):
            result = await result
        return result

    @router.get("/v1/health", response_model=Health, status_code=200)
    async def health(
    ) -> Health:
        request = AtomicExecutorHealthRequest()
        result = server.health(request)
        if isawaitable(result):
            result = await result
        return result

    @router.get("/v1/version", response_model=VersionInfo, status_code=200)
    async def version(
    ) -> VersionInfo:
        request = AtomicExecutorVersionRequest()
        result = server.version(request)
        if isawaitable(result):
            result = await result
        return result

    return router
