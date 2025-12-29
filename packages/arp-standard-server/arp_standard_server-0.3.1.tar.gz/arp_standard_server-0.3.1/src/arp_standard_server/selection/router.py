from __future__ import annotations

from inspect import isawaitable
from typing import TYPE_CHECKING

from fastapi import APIRouter, Body

from arp_standard_model import (
    CandidateSet,
    CandidateSetRequestBody,
    Health,
    SelectionGenerateCandidateSetRequest,
    SelectionHealthRequest,
    SelectionVersionRequest,
    VersionInfo,
)


if TYPE_CHECKING:
    from .server import BaseSelectionServer

def create_router(server: BaseSelectionServer) -> APIRouter:
    router = APIRouter()

    @router.post("/v1/candidate-sets", response_model=CandidateSet, status_code=200)
    async def generate_candidate_set(
        body: CandidateSetRequestBody = Body(...),
    ) -> CandidateSet:
        request = SelectionGenerateCandidateSetRequest(body=body)
        result = server.generate_candidate_set(request)
        if isawaitable(result):
            result = await result
        return result

    @router.get("/v1/health", response_model=Health, status_code=200)
    async def health(
    ) -> Health:
        request = SelectionHealthRequest()
        result = server.health(request)
        if isawaitable(result):
            result = await result
        return result

    @router.get("/v1/version", response_model=VersionInfo, status_code=200)
    async def version(
    ) -> VersionInfo:
        request = SelectionVersionRequest()
        result = server.version(request)
        if isawaitable(result):
            result = await result
        return result

    return router
