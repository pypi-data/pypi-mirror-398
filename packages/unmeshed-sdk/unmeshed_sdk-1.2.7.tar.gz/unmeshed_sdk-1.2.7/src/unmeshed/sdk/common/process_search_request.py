import time
from dataclasses import dataclass, field
from typing import Optional, List

from ..common.json_decorator import JSONSerializable
from ..common.unmeshed_constants import ProcessType, ProcessTriggerType, ProcessStatus
from ..common.tag_value import TagValue


@dataclass
class ProcessSearchRequest(JSONSerializable):
    startTimeEpoch: int = field(default_factory=lambda: int(time.time() * 1000) - (60 * 1000 * 60 * 24))
    endTimeEpoch: Optional[int] = field(default=None)

    namespace: Optional[str] = field(default=None)
    orgId: Optional[int] = field(default=None)
    processTypes: Optional[List[ProcessType]] = field(default=None)
    triggerTypes: Optional[List[ProcessTriggerType]] = field(default=None)
    names: Optional[List[str]] = field(default=None)
    stepNames: Optional[List[str]] = field(default=None)
    stepRefs: Optional[List[str]] = field(default=None)
    processIds: Optional[List[int]] = field(default=None)
    correlationIds: Optional[List[str]] = field(default=None)
    requestIds: Optional[List[str]] = field(default=None)
    tags: Optional[List[TagValue]] = field(default=None)
    statuses: Optional[List[ProcessStatus]] = field(default=None)
    fullTextSearchQuery: Optional[str] = field(default=None)

    limit: int = field(default=10)
    offset: int = field(default=0)
