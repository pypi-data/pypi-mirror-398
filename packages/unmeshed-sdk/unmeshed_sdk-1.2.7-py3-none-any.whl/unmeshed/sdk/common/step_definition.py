from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from ..common.json_decorator import JSONSerializable
from ..common.step_configuration import StepConfiguration
from ..common.unmeshed_constants import StepType

@dataclass
class StepDefinition(JSONSerializable):
    orgId: Optional[int] = field(default=None)
    namespace: Optional[str] = field(default=None)
    name: Optional[str] = field(default=None)
    type: Optional[StepType] = field(default=None)
    ref: Optional[str] = field(default=None)
    optional: bool = field(default=False)
    createdBy: Optional[str] = field(default=None)
    updatedBy: Optional[str] = field(default=None)
    description: Optional[str] = field(default=None)
    label: Optional[str] = field(default=None)
    created: int = field(default=0)
    updated: int = field(default=0)
    configuration: Optional[StepConfiguration] = field(default=None)
    children: Optional[List["StepDefinition"]] = field(default_factory=list)
    input: Optional[Dict[str, Any]] = field(default_factory=dict)
    output: Optional[Dict[str, Any]] = field(default_factory=dict)