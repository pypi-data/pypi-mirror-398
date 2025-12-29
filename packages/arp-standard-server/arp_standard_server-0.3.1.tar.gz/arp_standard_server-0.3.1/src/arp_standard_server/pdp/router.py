from __future__ import annotations

from inspect import isawaitable
from typing import TYPE_CHECKING

from fastapi import APIRouter, Body

from arp_standard_model import (
    Health,
    PdpDecidePolicyRequest,
    PdpHealthRequest,
    PdpVersionRequest,
    PolicyDecision,
    PolicyDecisionRequestBody,
    VersionInfo,
)


if TYPE_CHECKING:
    from .server import BasePdpServer

def create_router(server: BasePdpServer) -> APIRouter:
    router = APIRouter()

    @router.post("/v1/policy:decide", response_model=PolicyDecision, status_code=200)
    async def decide_policy(
        body: PolicyDecisionRequestBody = Body(...),
    ) -> PolicyDecision:
        request = PdpDecidePolicyRequest(body=body)
        result = server.decide_policy(request)
        if isawaitable(result):
            result = await result
        return result

    @router.get("/v1/health", response_model=Health, status_code=200)
    async def health(
    ) -> Health:
        request = PdpHealthRequest()
        result = server.health(request)
        if isawaitable(result):
            result = await result
        return result

    @router.get("/v1/version", response_model=VersionInfo, status_code=200)
    async def version(
    ) -> VersionInfo:
        request = PdpVersionRequest()
        result = server.version(request)
        if isawaitable(result):
            result = await result
        return result

    return router
