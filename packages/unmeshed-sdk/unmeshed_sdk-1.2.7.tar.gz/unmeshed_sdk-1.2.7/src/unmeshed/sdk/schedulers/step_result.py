from dataclasses import dataclass

@dataclass(frozen=True)
class StepResult:
    result: object = None
    keep_running: bool = False
    reschedule_after_seconds: int = 0

    def get_result(self):
        return self.result