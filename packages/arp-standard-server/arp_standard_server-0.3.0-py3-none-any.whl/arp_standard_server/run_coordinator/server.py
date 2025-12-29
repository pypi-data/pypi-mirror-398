from __future__ import annotations

import inspect
from abc import ABC, abstractmethod

from fastapi import FastAPI

from arp_standard_model import (
    GraphPatchSubmitResponse,
    Health,
    NodeRun,
    NodeRunsCreateResponse,
    RunCoordinatorCompleteNodeRunRequest,
    RunCoordinatorCreateNodeRunsRequest,
    RunCoordinatorGetNodeRunRequest,
    RunCoordinatorHealthRequest,
    RunCoordinatorReportNodeRunEvaluationRequest,
    RunCoordinatorSubmitGraphPatchRequest,
    RunCoordinatorVersionRequest,
    VersionInfo,
)

from arp_standard_server.app import build_app
from arp_standard_server.auth import AuthSettings
from .router import create_router


class BaseRunCoordinatorServer(ABC):
    @abstractmethod
    async def complete_node_run(self, request: RunCoordinatorCompleteNodeRunRequest) -> None:
        raise NotImplementedError

    @abstractmethod
    async def create_node_runs(self, request: RunCoordinatorCreateNodeRunsRequest) -> NodeRunsCreateResponse:
        raise NotImplementedError

    @abstractmethod
    async def get_node_run(self, request: RunCoordinatorGetNodeRunRequest) -> NodeRun:
        raise NotImplementedError

    @abstractmethod
    async def health(self, request: RunCoordinatorHealthRequest) -> Health:
        raise NotImplementedError

    @abstractmethod
    async def report_node_run_evaluation(self, request: RunCoordinatorReportNodeRunEvaluationRequest) -> None:
        raise NotImplementedError

    @abstractmethod
    async def submit_graph_patch(self, request: RunCoordinatorSubmitGraphPatchRequest) -> GraphPatchSubmitResponse:
        raise NotImplementedError

    @abstractmethod
    async def version(self, request: RunCoordinatorVersionRequest) -> VersionInfo:
        raise NotImplementedError

    def create_app(
        self,
        *,
        title: str | None = None,
        auth_settings: AuthSettings | None = None,
    ) -> FastAPI:
        if inspect.isabstract(self.__class__):
            raise TypeError(
                "BaseRunCoordinatorServer has unimplemented abstract methods. "
                "Implement all required endpoints before creating the app."
            )
        return build_app(
            router=create_router(self),
            title=title or "ARP Run Coordinator Server",
            auth_settings=auth_settings,
        )
