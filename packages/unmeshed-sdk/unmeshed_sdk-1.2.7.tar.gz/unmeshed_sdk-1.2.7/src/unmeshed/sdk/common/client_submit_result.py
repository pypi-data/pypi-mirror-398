from dataclasses import dataclass, field
from typing import Optional

from ..common.json_decorator import JSONSerializable


@dataclass
class ClientSubmitResult(JSONSerializable):
    processId: Optional[int] = field(default=None)  # Keeping JSON-compatible field names
    stepId: Optional[int] = field(default=None)
    errorMessage: Optional[str] = field(default=None)
    httpStatusCode: Optional[int] = field(default=None)
