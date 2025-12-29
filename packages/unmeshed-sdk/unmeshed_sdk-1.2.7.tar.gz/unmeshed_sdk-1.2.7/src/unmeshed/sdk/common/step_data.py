from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

from .json_decorator import JSONSerializable
from .unmeshed_constants import StepType, StepStatus


@dataclass
class StepId:
    id: Optional[int] = field(default=None)
    processId: Optional[int] = field(default=None)
    ref: Optional[str] = field(default=None)


# Define StepExecutionData with its custom from_dict (if needed)
@dataclass
class StepExecutionData(JSONSerializable):
    id: int = 0
    scheduled: int = 0
    polled: int = 0
    start: int = 0
    updated: int = 0
    executor: Optional[str] = field(default=None)
    ref: Optional[str] = field(default=None)
    runs: int = 0
    output: Optional[Dict[str, Any]] = field(default=None)

    @classmethod
    def from_dict(cls, data: dict):
        # In this case no special conversion is needed; simply return an instance.
        return cls(**data)

# Define StepData and override from_dict to convert enum fields and nested dataclasses
@dataclass
class StepData(JSONSerializable):
    id: Optional[int] = field(default=None)
    processId: Optional[int] = field(default=None)
    ref: Optional[str] = field(default=None)
    parentId: Optional[int] = field(default=None)
    parentRef: Optional[str] = field(default=None)
    namespace: Optional[str] = field(default=None)
    name: Optional[str] = field(default=None)
    type: Optional[StepType] = field(default=None)
    stepDefinitionHistoryId: Optional[int] = field(default=None)
    status: Optional[StepStatus] = field(default=None)
    input: Optional[Dict[str, Any]] = field(default=None)
    output: Optional[Dict[str, Any]] = field(default=None)
    workerId: Optional[str] = field(default=None)
    start: int = 0
    schedule: int = 0
    priority: int = 0
    updated: int = 0
    optional: bool = False
    executionList: Optional[List[StepExecutionData]] = field(default=None)

    @classmethod
    def from_dict(cls, data: dict):
        # Convert the enum fields from their string representation back to an enum instance.
        if "type" in data and data["type"] is not None:
            try:
                data["type"] = StepType[data["type"]]
            except KeyError as e:
                raise ValueError(f"Invalid StepType: {data['type']}") from e

        if "status" in data and data["status"] is not None:
            try:
                data["status"] = StepStatus[data["status"]]
            except KeyError as e:
                raise ValueError(f"Invalid StepStatus: {data['status']}") from e

        # For nested StepExecutionData objects in executionList, convert each dictionary to a StepExecutionData instance.
        if "executionList" in data and data["executionList"] is not None:
            data["executionList"] = [
                StepExecutionData.from_dict(item) if isinstance(item, dict) else item
                for item in data["executionList"]
            ]
        return cls(**data)
