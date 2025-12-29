from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from ._generated import (
    AtomicExecuteRequest,
    CandidateSetRequest,
    CompositeBeginRequest,
    NodeKind,
    NodeRunCompleteRequest,
    NodeRunEvaluationReportRequest,
    NodeRunsCreateRequest,
    NodeTypePublishRequest,
    PolicyDecisionRequest,
    RunStartRequest,
)

AtomicExecuteRequestBody = AtomicExecuteRequest
CandidateSetRequestBody = CandidateSetRequest
CompositeBeginRequestBody = CompositeBeginRequest
NodeRunCompleteRequestBody = NodeRunCompleteRequest
NodeRunEvaluationReportRequestBody = NodeRunEvaluationReportRequest
NodeRunsCreateRequestBody = NodeRunsCreateRequest
NodeTypePublishRequestBody = NodeTypePublishRequest
PolicyDecisionRequestBody = PolicyDecisionRequest
RunStartRequestBody = RunStartRequest

class RunGatewayGetRunParams(BaseModel):
    run_id: str

class RunGatewayCancelRunParams(BaseModel):
    run_id: str

class RunGatewayStreamRunEventsParams(BaseModel):
    run_id: str

class RunCoordinatorGetRunParams(BaseModel):
    run_id: str

class RunCoordinatorCancelRunParams(BaseModel):
    run_id: str

class RunCoordinatorStreamRunEventsParams(BaseModel):
    run_id: str

class RunCoordinatorGetNodeRunParams(BaseModel):
    node_run_id: str

class RunCoordinatorStreamNodeRunEventsParams(BaseModel):
    node_run_id: str

class RunCoordinatorReportNodeRunEvaluationParams(BaseModel):
    node_run_id: str

class RunCoordinatorCompleteNodeRunParams(BaseModel):
    node_run_id: str

class AtomicExecutorCancelAtomicNodeRunParams(BaseModel):
    node_run_id: str

class CompositeExecutorCancelCompositeNodeRunParams(BaseModel):
    node_run_id: str

class NodeRegistryListNodeTypesParams(BaseModel):
    q: str | None = None
    kind: NodeKind | None = None

class NodeRegistryGetNodeTypeParams(BaseModel):
    node_type_id: str
    version: str | None = None

class RunGatewayHealthRequest(BaseModel):
    pass

class RunGatewayVersionRequest(BaseModel):
    pass

class RunGatewayStartRunRequest(BaseModel):
    body: RunStartRequestBody

class RunGatewayGetRunRequest(BaseModel):
    params: RunGatewayGetRunParams

class RunGatewayCancelRunRequest(BaseModel):
    params: RunGatewayCancelRunParams

class RunGatewayStreamRunEventsRequest(BaseModel):
    params: RunGatewayStreamRunEventsParams

class RunCoordinatorHealthRequest(BaseModel):
    pass

class RunCoordinatorVersionRequest(BaseModel):
    pass

class RunCoordinatorStartRunRequest(BaseModel):
    body: RunStartRequestBody

class RunCoordinatorGetRunRequest(BaseModel):
    params: RunCoordinatorGetRunParams

class RunCoordinatorCancelRunRequest(BaseModel):
    params: RunCoordinatorCancelRunParams

class RunCoordinatorStreamRunEventsRequest(BaseModel):
    params: RunCoordinatorStreamRunEventsParams

class RunCoordinatorCreateNodeRunsRequest(BaseModel):
    body: NodeRunsCreateRequestBody

class RunCoordinatorGetNodeRunRequest(BaseModel):
    params: RunCoordinatorGetNodeRunParams

class RunCoordinatorStreamNodeRunEventsRequest(BaseModel):
    params: RunCoordinatorStreamNodeRunEventsParams

class RunCoordinatorReportNodeRunEvaluationRequest(BaseModel):
    params: RunCoordinatorReportNodeRunEvaluationParams
    body: NodeRunEvaluationReportRequestBody

class RunCoordinatorCompleteNodeRunRequest(BaseModel):
    params: RunCoordinatorCompleteNodeRunParams
    body: NodeRunCompleteRequestBody

class AtomicExecutorHealthRequest(BaseModel):
    pass

class AtomicExecutorVersionRequest(BaseModel):
    pass

class AtomicExecutorExecuteAtomicNodeRunRequest(BaseModel):
    body: AtomicExecuteRequestBody

class AtomicExecutorCancelAtomicNodeRunRequest(BaseModel):
    params: AtomicExecutorCancelAtomicNodeRunParams

class CompositeExecutorHealthRequest(BaseModel):
    pass

class CompositeExecutorVersionRequest(BaseModel):
    pass

class CompositeExecutorBeginCompositeNodeRunRequest(BaseModel):
    body: CompositeBeginRequestBody

class CompositeExecutorCancelCompositeNodeRunRequest(BaseModel):
    params: CompositeExecutorCancelCompositeNodeRunParams

class NodeRegistryHealthRequest(BaseModel):
    pass

class NodeRegistryVersionRequest(BaseModel):
    pass

class NodeRegistryListNodeTypesRequest(BaseModel):
    params: NodeRegistryListNodeTypesParams

class NodeRegistryPublishNodeTypeRequest(BaseModel):
    body: NodeTypePublishRequestBody

class NodeRegistryGetNodeTypeRequest(BaseModel):
    params: NodeRegistryGetNodeTypeParams

class SelectionHealthRequest(BaseModel):
    pass

class SelectionVersionRequest(BaseModel):
    pass

class SelectionGenerateCandidateSetRequest(BaseModel):
    body: CandidateSetRequestBody

class PdpHealthRequest(BaseModel):
    pass

class PdpVersionRequest(BaseModel):
    pass

class PdpDecidePolicyRequest(BaseModel):
    body: PolicyDecisionRequestBody

__all__ = [
    'AtomicExecuteRequestBody',
    'CandidateSetRequestBody',
    'CompositeBeginRequestBody',
    'NodeRunCompleteRequestBody',
    'NodeRunEvaluationReportRequestBody',
    'NodeRunsCreateRequestBody',
    'NodeTypePublishRequestBody',
    'PolicyDecisionRequestBody',
    'RunStartRequestBody',
    'RunGatewayGetRunParams',
    'RunGatewayCancelRunParams',
    'RunGatewayStreamRunEventsParams',
    'RunCoordinatorGetRunParams',
    'RunCoordinatorCancelRunParams',
    'RunCoordinatorStreamRunEventsParams',
    'RunCoordinatorGetNodeRunParams',
    'RunCoordinatorStreamNodeRunEventsParams',
    'RunCoordinatorReportNodeRunEvaluationParams',
    'RunCoordinatorCompleteNodeRunParams',
    'AtomicExecutorCancelAtomicNodeRunParams',
    'CompositeExecutorCancelCompositeNodeRunParams',
    'NodeRegistryListNodeTypesParams',
    'NodeRegistryGetNodeTypeParams',
    'RunGatewayHealthRequest',
    'RunGatewayVersionRequest',
    'RunGatewayStartRunRequest',
    'RunGatewayGetRunRequest',
    'RunGatewayCancelRunRequest',
    'RunGatewayStreamRunEventsRequest',
    'RunCoordinatorHealthRequest',
    'RunCoordinatorVersionRequest',
    'RunCoordinatorStartRunRequest',
    'RunCoordinatorGetRunRequest',
    'RunCoordinatorCancelRunRequest',
    'RunCoordinatorStreamRunEventsRequest',
    'RunCoordinatorCreateNodeRunsRequest',
    'RunCoordinatorGetNodeRunRequest',
    'RunCoordinatorStreamNodeRunEventsRequest',
    'RunCoordinatorReportNodeRunEvaluationRequest',
    'RunCoordinatorCompleteNodeRunRequest',
    'AtomicExecutorHealthRequest',
    'AtomicExecutorVersionRequest',
    'AtomicExecutorExecuteAtomicNodeRunRequest',
    'AtomicExecutorCancelAtomicNodeRunRequest',
    'CompositeExecutorHealthRequest',
    'CompositeExecutorVersionRequest',
    'CompositeExecutorBeginCompositeNodeRunRequest',
    'CompositeExecutorCancelCompositeNodeRunRequest',
    'NodeRegistryHealthRequest',
    'NodeRegistryVersionRequest',
    'NodeRegistryListNodeTypesRequest',
    'NodeRegistryPublishNodeTypeRequest',
    'NodeRegistryGetNodeTypeRequest',
    'SelectionHealthRequest',
    'SelectionVersionRequest',
    'SelectionGenerateCandidateSetRequest',
    'PdpHealthRequest',
    'PdpVersionRequest',
    'PdpDecidePolicyRequest',
]
