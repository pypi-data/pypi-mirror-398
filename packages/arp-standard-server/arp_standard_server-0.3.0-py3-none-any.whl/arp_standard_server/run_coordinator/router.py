from __future__ import annotations

from inspect import isawaitable
from typing import TYPE_CHECKING

from fastapi import APIRouter, Body, Path

from arp_standard_model import (
    GraphPatchSubmitRequestBody,
    GraphPatchSubmitResponse,
    Health,
    NodeRun,
    NodeRunCompleteRequestBody,
    NodeRunEvaluationReportRequestBody,
    NodeRunsCreateRequestBody,
    NodeRunsCreateResponse,
    RunCoordinatorCompleteNodeRunParams,
    RunCoordinatorCompleteNodeRunRequest,
    RunCoordinatorCreateNodeRunsRequest,
    RunCoordinatorGetNodeRunParams,
    RunCoordinatorGetNodeRunRequest,
    RunCoordinatorHealthRequest,
    RunCoordinatorReportNodeRunEvaluationParams,
    RunCoordinatorReportNodeRunEvaluationRequest,
    RunCoordinatorSubmitGraphPatchRequest,
    RunCoordinatorVersionRequest,
    VersionInfo,
)


if TYPE_CHECKING:
    from .server import BaseRunCoordinatorServer

def create_router(server: BaseRunCoordinatorServer) -> APIRouter:
    router = APIRouter()

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

    @router.post("/v1/graph-patches", response_model=GraphPatchSubmitResponse, status_code=200)
    async def submit_graph_patch(
        body: GraphPatchSubmitRequestBody = Body(...),
    ) -> GraphPatchSubmitResponse:
        request = RunCoordinatorSubmitGraphPatchRequest(body=body)
        result = server.submit_graph_patch(request)
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
