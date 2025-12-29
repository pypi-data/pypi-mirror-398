from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from ..common.json_decorator import JSONSerializable
from .unmeshed_constants import StepStatus

@dataclass
class WorkResponse(JSONSerializable):
    processId: Optional[int] = field(default=None)
    stepId: Optional[int] = field(default=None)
    stepExecutionId: Optional[int] = field(default=None)
    runCount: Optional[int] = field(default=None)

    output: Optional[Dict[str, Any]] = field(default=None)
    status: Optional[StepStatus] = field(default=None)

    rescheduleAfterSeconds: Optional[int] = field(default=None)
    startedAt: Optional[int] = field(default=None)

    @classmethod
    def from_dict(cls, data: dict):
        if "status" in data and data["status"] is not None:
            try:
                data["status"] = StepStatus[data["status"]]
            except KeyError as e:
                raise ValueError(f"Invalid StepStatus: {data['status']}") from e
        return cls(**data)

    def get_process_id(self) -> Optional[int]:
        return self.processId

    def set_process_id(self, process_id: int) -> None:
        self.processId = process_id

    def get_step_id(self) -> Optional[int]:
        return self.stepId

    def set_step_id(self, step_id: int) -> None:
        self.stepId = step_id

    def get_step_execution_id(self) -> Optional[int]:
        return self.stepExecutionId

    def set_step_execution_id(self, step_execution_id: int) -> None:
        self.stepExecutionId = step_execution_id

    def get_run_count(self) -> Optional[int]:
        return self.runCount

    def set_run_count(self, run_count: int) -> None:
        self.runCount = run_count

    def get_output(self) -> Optional[Dict[str, Any]]:
        return self.output

    def set_output(self, output: Dict[str, Any]) -> None:
        self.output = output

    def get_status(self) -> Optional[StepStatus]:
        return self.status

    def set_status(self, status: StepStatus) -> None:
        self.status = status

    def get_reschedule_after_seconds(self) -> Optional[int]:
        return self.rescheduleAfterSeconds

    def set_reschedule_after_seconds(self, reschedule_after_seconds: int) -> None:
        self.rescheduleAfterSeconds = reschedule_after_seconds

    def get_started_at(self) -> Optional[int]:
        return self.startedAt

    def set_started_at(self, started_at: int) -> None:
        self.startedAt = started_at