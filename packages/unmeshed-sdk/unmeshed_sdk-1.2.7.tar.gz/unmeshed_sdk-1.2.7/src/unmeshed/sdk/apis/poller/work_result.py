from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ...common.work_request import WorkRequest

@dataclass
class WorkResult:
    output: Any
    task_execution_id: str
    start_time: datetime
    end_time: datetime
    work_request: 'WorkRequest'