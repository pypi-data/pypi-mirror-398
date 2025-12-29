from dataclasses import dataclass
from typing import Callable

@dataclass
class Worker:
    execution_method: Callable
    name: str
    namespace: str = "default"
    max_in_progress: int = 10
