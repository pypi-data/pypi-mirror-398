from __future__ import annotations

from inspect import isawaitable
from typing import TYPE_CHECKING

from fastapi import APIRouter, Body, Path

from arp_standard_model import (
    Health,
    NodeRun,
    NodeRunCompleteRequestBody,
    NodeRunEvaluationReportRequestBody,
    NodeRunsCreateRequestBody,
    NodeRunsCreateResponse,
    Run,
    RunCoordinatorCancelRunParams,
    RunCoordinatorCancelRunRequest,
    RunCoordinatorCompleteNodeRunParams,
    RunCoordinatorCompleteNodeRunRequest,
    RunCoordinatorCreateNodeRunsRequest,
    RunCoordinatorGetNodeRunParams,
    RunCoordinatorGetNodeRunRequest,
    RunCoordinatorGetRunParams,
    RunCoordinatorGetRunRequest,
    RunCoordinatorHealthRequest,
    RunCoordinatorReportNodeRunEvaluationParams,
    RunCoordinatorReportNodeRunEvaluationRequest,
    RunCoordinatorStartRunRequest,
    RunCoordinatorStreamNodeRunEventsParams,
    RunCoordinatorStreamNodeRunEventsRequest,
    RunCoordinatorStreamRunEventsParams,
    RunCoordinatorStreamRunEventsRequest,
    RunCoordinatorVersionRequest,
    RunStartRequestBody,
    VersionInfo,
)


if TYPE_CHECKING:
    from .server import BaseRunCoordinatorServer

def create_router(server: BaseRunCoordinatorServer) -> APIRouter:
    router = APIRouter()

    @router.post("/v1/runs/{run_id}:cancel", response_model=Run, status_code=200)
    async def cancel_run(
        run_id: str = Path(..., alias="run_id"),
    ) -> Run:
        params = RunCoordinatorCancelRunParams(
            run_id=run_id,
        )
        request = RunCoordinatorCancelRunRequest(params=params)
        result = server.cancel_run(request)
        if isawaitable(result):
            result = await result
        return result

    @router.post("/v1/node-runs/{node_run_id}:complete", status_code=204)
    async def complete_node_run(
        node_run_id: str = Path(..., alias="node_run_id"),
        body: NodeRunCompleteRequestBody = Body(...),
    ) -> None:
        params = RunCoordinatorCompleteNodeRunParams(
            node_run_id=node_run_id,
        )
        request = RunCoordinatorCompleteNodeRunRequest(params=params, body=body)
        result = server.complete_node_run(request)
        if isawaitable(result):
            result = await result
        return None

    @router.post("/v1/node-runs", response_model=NodeRunsCreateResponse, status_code=200)
    async def create_node_runs(
        body: NodeRunsCreateRequestBody = Body(...),
    ) -> NodeRunsCreateResponse:
        request = RunCoordinatorCreateNodeRunsRequest(body=body)
        result = server.create_node_runs(request)
        if isawaitable(result):
            result = await result
        return result

    @router.get("/v1/node-runs/{node_run_id}", response_model=NodeRun, status_code=200)
    async def get_node_run(
        node_run_id: str = Path(..., alias="node_run_id"),
    ) -> NodeRun:
        params = RunCoordinatorGetNodeRunParams(
            node_run_id=node_run_id,
        )
        request = RunCoordinatorGetNodeRunRequest(params=params)
        result = server.get_node_run(request)
        if isawaitable(result):
            result = await result
        return result

    @router.get("/v1/runs/{run_id}", response_model=Run, status_code=200)
    async def get_run(
        run_id: str = Path(..., alias="run_id"),
    ) -> Run:
        params = RunCoordinatorGetRunParams(
            run_id=run_id,
        )
        request = RunCoordinatorGetRunRequest(params=params)
        result = server.get_run(request)
        if isawaitable(result):
            result = await result
        return result

    @router.get("/v1/health", response_model=Health, status_code=200)
    async def health(
    ) -> Health:
        request = RunCoordinatorHealthRequest()
        result = server.health(request)
        if isawaitable(result):
            result = await result
        return result

    @router.post("/v1/node-runs/{node_run_id}:evaluation", status_code=204)
    async def report_node_run_evaluation(
        node_run_id: str = Path(..., alias="node_run_id"),
        body: NodeRunEvaluationReportRequestBody = Body(...),
    ) -> None:
        params = RunCoordinatorReportNodeRunEvaluationParams(
            node_run_id=node_run_id,
        )
        request = RunCoordinatorReportNodeRunEvaluationRequest(params=params, body=body)
        result = server.report_node_run_evaluation(request)
        if isawaitable(result):
            result = await result
        return None

    @router.post("/v1/runs", response_model=Run, status_code=200)
    async def start_run(
        body: RunStartRequestBody = Body(...),
    ) -> Run:
        request = RunCoordinatorStartRunRequest(body=body)
        result = server.start_run(request)
        if isawaitable(result):
            result = await result
        return result

    @router.get("/v1/node-runs/{node_run_id}/events", response_model=str, status_code=200)
    async def stream_node_run_events(
        node_run_id: str = Path(..., alias="node_run_id"),
    ) -> str:
        params = RunCoordinatorStreamNodeRunEventsParams(
            node_run_id=node_run_id,
        )
        request = RunCoordinatorStreamNodeRunEventsRequest(params=params)
        result = server.stream_node_run_events(request)
        if isawaitable(result):
            result = await result
        return result

    @router.get("/v1/runs/{run_id}/events", response_model=str, status_code=200)
    async def stream_run_events(
        run_id: str = Path(..., alias="run_id"),
    ) -> str:
        params = RunCoordinatorStreamRunEventsParams(
            run_id=run_id,
        )
        request = RunCoordinatorStreamRunEventsRequest(params=params)
        result = server.stream_run_events(request)
        if isawaitable(result):
            result = await result
        return result

    @router.get("/v1/version", response_model=VersionInfo, status_code=200)
    async def version(
    ) -> VersionInfo:
        request = RunCoordinatorVersionRequest()
        result = server.version(request)
        if isawaitable(result):
            result = await result
        return result

    return router
