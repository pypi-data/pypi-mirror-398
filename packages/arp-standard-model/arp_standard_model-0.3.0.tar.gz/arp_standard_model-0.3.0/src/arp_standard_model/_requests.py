from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from ._generated import (
    AtomicExecuteRequest,
    CandidateSetRequest,
    CompositeBeginRequest,
    GraphPatchSubmitRequest,
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
GraphPatchSubmitRequestBody = GraphPatchSubmitRequest
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

class RunCoordinatorGetNodeRunParams(BaseModel):
    node_run_id: str

class RunCoordinatorReportNodeRunEvaluationParams(BaseModel):
    node_run_id: str

class RunCoordinatorCompleteNodeRunParams(BaseModel):
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

class RunCoordinatorCreateNodeRunsRequest(BaseModel):
    body: NodeRunsCreateRequestBody

class RunCoordinatorGetNodeRunRequest(BaseModel):
    params: RunCoordinatorGetNodeRunParams

class RunCoordinatorSubmitGraphPatchRequest(BaseModel):
    body: GraphPatchSubmitRequestBody

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

class CompositeExecutorHealthRequest(BaseModel):
    pass

class CompositeExecutorVersionRequest(BaseModel):
    pass

class CompositeExecutorBeginCompositeNodeRunRequest(BaseModel):
    body: CompositeBeginRequestBody

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
    'GraphPatchSubmitRequestBody',
    'NodeRunCompleteRequestBody',
    'NodeRunEvaluationReportRequestBody',
    'NodeRunsCreateRequestBody',
    'NodeTypePublishRequestBody',
    'PolicyDecisionRequestBody',
    'RunStartRequestBody',
    'RunGatewayGetRunParams',
    'RunGatewayCancelRunParams',
    'RunGatewayStreamRunEventsParams',
    'RunCoordinatorGetNodeRunParams',
    'RunCoordinatorReportNodeRunEvaluationParams',
    'RunCoordinatorCompleteNodeRunParams',
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
    'RunCoordinatorCreateNodeRunsRequest',
    'RunCoordinatorGetNodeRunRequest',
    'RunCoordinatorSubmitGraphPatchRequest',
    'RunCoordinatorReportNodeRunEvaluationRequest',
    'RunCoordinatorCompleteNodeRunRequest',
    'AtomicExecutorHealthRequest',
    'AtomicExecutorVersionRequest',
    'AtomicExecutorExecuteAtomicNodeRunRequest',
    'CompositeExecutorHealthRequest',
    'CompositeExecutorVersionRequest',
    'CompositeExecutorBeginCompositeNodeRunRequest',
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
