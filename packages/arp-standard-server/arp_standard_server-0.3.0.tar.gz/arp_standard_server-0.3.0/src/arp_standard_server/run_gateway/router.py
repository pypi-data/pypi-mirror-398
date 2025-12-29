from __future__ import annotations

from inspect import isawaitable
from typing import TYPE_CHECKING

from fastapi import APIRouter, Body, Path

from arp_standard_model import (
    Health,
    Run,
    RunGatewayCancelRunParams,
    RunGatewayCancelRunRequest,
    RunGatewayGetRunParams,
    RunGatewayGetRunRequest,
    RunGatewayHealthRequest,
    RunGatewayStartRunRequest,
    RunGatewayStreamRunEventsParams,
    RunGatewayStreamRunEventsRequest,
    RunGatewayVersionRequest,
    RunStartRequestBody,
    VersionInfo,
)


if TYPE_CHECKING:
    from .server import BaseRunGatewayServer

def create_router(server: BaseRunGatewayServer) -> APIRouter:
    router = APIRouter()

    @router.post("/v1/runs/{run_id}:cancel", response_model=Run, status_code=200)
    async def cancel_run(
        run_id: str = Path(..., alias="run_id"),
    ) -> Run:
        params = RunGatewayCancelRunParams(
            run_id=run_id,
        )
        request = RunGatewayCancelRunRequest(params=params)
        result = server.cancel_run(request)
        if isawaitable(result):
            result = await result
        return result

    @router.get("/v1/runs/{run_id}", response_model=Run, status_code=200)
    async def get_run(
        run_id: str = Path(..., alias="run_id"),
    ) -> Run:
        params = RunGatewayGetRunParams(
            run_id=run_id,
        )
        request = RunGatewayGetRunRequest(params=params)
        result = server.get_run(request)
        if isawaitable(result):
            result = await result
        return result

    @router.get("/v1/health", response_model=Health, status_code=200)
    async def health(
    ) -> Health:
        request = RunGatewayHealthRequest()
        result = server.health(request)
        if isawaitable(result):
            result = await result
        return result

    @router.post("/v1/runs", response_model=Run, status_code=200)
    async def start_run(
        body: RunStartRequestBody = Body(...),
    ) -> Run:
        request = RunGatewayStartRunRequest(body=body)
        result = server.start_run(request)
        if isawaitable(result):
            result = await result
        return result

    @router.get("/v1/runs/{run_id}/events", response_model=str, status_code=200)
    async def stream_run_events(
        run_id: str = Path(..., alias="run_id"),
    ) -> str:
        params = RunGatewayStreamRunEventsParams(
            run_id=run_id,
        )
        request = RunGatewayStreamRunEventsRequest(params=params)
        result = server.stream_run_events(request)
        if isawaitable(result):
            result = await result
        return result

    @router.get("/v1/version", response_model=VersionInfo, status_code=200)
    async def version(
    ) -> VersionInfo:
        request = RunGatewayVersionRequest()
        result = server.version(request)
        if isawaitable(result):
            result = await result
        return result

    return router
