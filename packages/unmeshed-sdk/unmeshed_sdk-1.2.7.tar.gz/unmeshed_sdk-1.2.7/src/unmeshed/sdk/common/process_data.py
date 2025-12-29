from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

from ..common.tag_value import TagValue
from ..common.json_decorator import JSONSerializable
from ..common.step_data import StepId, StepData
from ..common.unmeshed_constants import ProcessType, ProcessStatus, ProcessTriggerType

@dataclass
class ProcessData(JSONSerializable):
    processId: int = 0

    processType: Optional[ProcessType] = field(default=None)
    triggerType: Optional[ProcessTriggerType] = field(default=None)

    namespace: Optional[str] = field(default=None)
    name: Optional[str] = field(default=None)
    version: Optional[int] = field(default=None)

    historyId: Optional[int] = field(default=None)

    requestId: Optional[str] = field(default=None)
    correlationId: Optional[str] = field(default=None)

    status: Optional[ProcessStatus] = field(default=None)

    input: Optional[Dict[str, Any]] = field(default=None)
    output: Optional[Dict[str, Any]] = field(default=None)

    state: Optional[Dict[str, Any]] = field(default=None)
    secretState: Optional[Dict[str, Any]] = field(default=None)

    authClaims: Optional[Dict[str, Any]] = field(default=None)

    stepIdCount: Optional[int] = field(default=None)

    shardName: Optional[str] = field(default=None)
    shardInstanceId: Optional[int] = field(default=None)

    steps: Optional[List[StepId]] = field(default=None)
    stepRecords: Optional[List[StepData]] = field(default=None)

    created: Optional[int] = field(default=None)
    updated: Optional[int] = field(default=None)
    createdBy: Optional[str] = field(default=None)
    tags: Optional[List[TagValue]] = field(default=None)
