from dataclasses import dataclass, field
from typing import Optional

from ..common.json_decorator import JSONSerializable
from ..common.process_request_data import ProcessRequestData


@dataclass
class ProcessConfiguration(JSONSerializable):
    completionTimeout: int = field(default=180000)

    onTimeoutProcess: Optional["ProcessRequestData"] = field(default=None)
    onFailProcess: Optional["ProcessRequestData"] = field(default=None)
    onCompleteProcess: Optional["ProcessRequestData"] = field(default=None)
    onCancelProcess: Optional["ProcessRequestData"] = field(default=None)
