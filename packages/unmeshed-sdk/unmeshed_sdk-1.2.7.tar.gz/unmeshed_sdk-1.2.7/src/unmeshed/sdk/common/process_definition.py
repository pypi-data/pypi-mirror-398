from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from ..common.process_configuration import ProcessConfiguration
from ..common.step_definition import StepDefinition

from ..common.step_dependency import StepDependency
from ..common.tag_value import TagValue
from ..common.unmeshed_constants import ProcessType

from ..common.json_decorator import JSONSerializable


@dataclass
class ProcessDefinition(JSONSerializable):
    orgId: Optional[int] = field(default=None)
    namespace: Optional[str] = field(default=None)
    name: Optional[str] = field(default=None)
    version: Optional[int] = field(default=None)
    type: Optional[ProcessType] = field(default=None)
    description: Optional[str] = field(default=None)
    createdBy: Optional[str] = field(default=None)
    updatedBy: Optional[str] = field(default=None)
    created: int = field(default=0)
    updated: int = field(default=0)
    configuration: Optional[ProcessConfiguration] = field(default=None)
    steps: Optional[List[StepDefinition]] = field(default_factory=list)
    defaultInput: Optional[Dict[str, Any]] = field(default_factory=dict)
    defaultOutput: Optional[Dict[str, Any]] = field(default_factory=dict)
    outputMapping: Optional[Dict[str, Any]] = field(default_factory=dict)
    metadata: Optional[Dict[str, List[StepDependency]]] = field(default_factory=dict)
    tags: Optional[List[TagValue]] = field(default_factory=list)