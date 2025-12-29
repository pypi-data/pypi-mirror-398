import time
from dataclasses import dataclass, field
from typing import Optional

from .json_decorator import JSONSerializable
from .step_queue_poll_state import StepQueuePollState
from .work_response import WorkResponse


@dataclass
class WorkResponseTracker(JSONSerializable):
    work_response: WorkResponse
    retry_count: int = field(default=0)
    queued_time: float = field(default_factory=time.time)
    step_poll_state: Optional[StepQueuePollState] = field(default=None)

    @classmethod
    def from_dict(cls, data: dict):
        if "work_response" in data and isinstance(data["work_response"], dict):
            data["work_response"] = WorkResponse.from_dict(data["work_response"])
        return cls(**data)
