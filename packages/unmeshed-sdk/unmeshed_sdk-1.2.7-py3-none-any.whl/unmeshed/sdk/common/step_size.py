from dataclasses import dataclass, field
from typing import Optional

from .unmeshed_constants import StepType

@dataclass
class StepQueueNameData:
    orgId: Optional[int] = field(default=None)  # Keeping JSON-compatible field names
    namespace: Optional[str] = field(default=None)
    stepType: Optional[StepType] = field(default=None)
    name: Optional[str] = field(default=None)

@dataclass
class StepSize:
    stepQueueNameData: StepQueueNameData
    size: Optional[int] = None
