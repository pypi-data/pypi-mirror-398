import json
import time
from concurrent.futures import Future
from typing import Any, Optional

from ...common.unmeshed_constants import StepStatus
from ...common.work_request import WorkRequest
from ...common.work_response import WorkResponse
from ...logger_config import get_logger
from ...schedulers.step_result import StepResult

logger = get_logger(__name__)

class WorkResponseBuilder:

    @staticmethod
    def __result_to_map(obj: Any) -> dict[str, Any]:
        if isinstance(obj, (bool, bytes, str, int, float)):
            return {"result": obj}

        if isinstance(obj, (tuple, list, set)):
            return {"result": [WorkResponseBuilder.__convert_item(item) for item in list(obj)]}

        return json.loads(json.dumps(obj, default=WorkResponseBuilder.__default_serializer))

    @staticmethod
    def __convert_item(item: Any) -> Any:
        if isinstance(item, (bool, bytes, str, int, float)):
            return item
        return json.loads(json.dumps(item, default=WorkResponseBuilder.__default_serializer))

    @staticmethod
    def __default_serializer(o: Any) -> Any:
        if isinstance(o, set):
            return list(o)
        return o.__dict__ if hasattr(o, '__dict__') else str(o)

    def fail_response(self, work_request: WorkRequest, context: Optional[Exception]) -> WorkResponse:  # type: ignore
        if isinstance(context, Exception):
            context = self.__try_peel_irrelevant_exceptions(context)

        output = {"lastError": str(context)}
        return self.create_work_response(output, work_request, StepStatus.FAILED)

    def running_response(self, work_request: WorkRequest, step_result: StepResult) -> WorkResponse:
        output = self.__result_to_map(step_result.get_result())
        work_response = self.create_work_response(output, work_request, StepStatus.RUNNING)
        work_response.set_reschedule_after_seconds(step_result.reschedule_after_seconds)
        return work_response

    @staticmethod
    def create_work_response(output, work_request, status):
        work_response = WorkResponse()
        work_response.set_process_id(work_request.get_process_id())
        work_response.set_step_id(work_request.get_step_id())
        work_response.set_step_execution_id(work_request.get_step_execution_id())
        work_response.set_output(output)
        current_millis = int(time.time_ns() / 1_000_000)
        work_response.set_started_at(current_millis)
        work_response.set_status(status.name)
        return work_response

    @staticmethod
    def __try_peel_irrelevant_exceptions(context: Exception) -> Exception:
        actual_cause = context
        if isinstance(context, Future):
            if context.exception() is not None:
                actual_cause = context.exception()
                if isinstance(actual_cause, Exception):
                    actual_cause = actual_cause.__cause__ or actual_cause
        return actual_cause

    def success_response(self, work_request: WorkRequest, step_result: StepResult) -> WorkResponse:
        output = self.__result_to_map(step_result.get_result())
        return self.create_work_response(output, work_request, StepStatus.COMPLETED)