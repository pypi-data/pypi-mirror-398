from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from ..common.json_decorator import JSONSerializable


@dataclass
class WorkRequest(JSONSerializable):
    processId: Optional[int] = field(default=None)  # Keeping JSON-compatible field names
    stepId: Optional[int] = field(default=None)
    stepExecutionId: int = 0
    runCount: int = 0

    stepName: Optional[str] = field(default=None)
    stepNamespace: Optional[str] = field(default=None)
    stepRef: Optional[str] = field(default=None)

    inputParam: Optional[Dict[str, Any]] = field(default=None)  # Equivalent to Java's Map<String, Object>

    isOptional: Optional[bool] = field(default=None)

    polled: int = 0
    scheduled: int = 0
    updated: int = 0
    priority: int = 0

    def get_process_id(self) -> Optional[int]:
        return self.processId

    def set_process_id(self, process_id: int) -> None:
        self.processId = process_id

    def get_step_id(self) -> Optional[int]:
        return self.stepId

    def set_step_id(self, step_id: int) -> None:
        self.stepId = step_id

    def get_step_execution_id(self) -> int:
        return self.stepExecutionId

    def set_step_execution_id(self, step_execution_id: int) -> None:
        self.stepExecutionId = step_execution_id

    def get_run_count(self) -> int:
        return self.runCount

    def set_run_count(self, run_count: int) -> None:
        self.runCount = run_count

    def get_step_name(self) -> Optional[str]:
        return self.stepName

    def set_step_name(self, step_name: str) -> None:
        self.stepName = step_name

    def get_step_namespace(self) -> Optional[str]:
        return self.stepNamespace

    def set_step_namespace(self, step_namespace: str) -> None:
        self.stepNamespace = step_namespace

    def get_step_ref(self) -> Optional[str]:
        return self.stepRef

    def set_step_ref(self, step_ref: str) -> None:
        self.stepRef = step_ref

    def get_input_param(self) -> Optional[Dict[str, Any]]:
        return self.inputParam

    def set_input_param(self, input_param: Dict[str, Any]) -> None:
        self.inputParam = input_param

    def get_is_optional(self) -> Optional[bool]:
        return self.isOptional

    def set_is_optional(self, is_optional: bool) -> None:
        self.isOptional = is_optional

    def get_polled(self) -> int:
        return self.polled

    def set_polled(self, polled: int) -> None:
        self.polled = polled

    def get_scheduled(self) -> int:
        return self.scheduled

    def set_scheduled(self, scheduled: int) -> None:
        self.scheduled = scheduled

    def get_updated(self) -> int:
        return self.updated

    def set_updated(self, updated: int) -> None:
        self.updated = updated

    def get_priority(self) -> int:
        return self.priority

    def set_priority(self, priority: int) -> None:
        self.priority = priority