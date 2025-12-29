from dataclasses import dataclass, field
from typing import Any, Optional

from ..common.step_size import StepQueueNameData


@dataclass
class PollRequestData:
    _step_queue_name_data: Optional[StepQueueNameData] = field(default=None)
    _size: Optional[int] = field(default=0)

    def __init__(self, step_queue_name_data: StepQueueNameData, size: int):
        self._step_queue_name_data = step_queue_name_data
        self._size = size

    @property
    def get_step_queue_name_data(self) -> StepQueueNameData:
        return self._step_queue_name_data

    def set_step_queue_name_data(self, value: StepQueueNameData) -> None:
        self._step_queue_name_data = value

    @property
    def size(self) -> int:
        return self._size

    @size.setter
    def size(self, value: int) -> None:
        self._size = value

    def to_dict(self) -> dict[str, Any]:
        return {
            "_step_queue_name_data": self._step_queue_name_data,
            "size": self._size
        }