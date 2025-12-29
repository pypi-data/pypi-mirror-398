from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from ..common.json_decorator import JSONSerializable


@dataclass
class ProcessRequestData(JSONSerializable):
    namespace: Optional[str] = field(default=None)
    name: Optional[str] = field(default=None)
    version: Optional[int] = field(default=None)

    requestId: Optional[str] = field(default=None)
    correlationId: Optional[str] = field(default=None)

    input: Optional[Dict[str, Any]] = field(default=None)  # Equivalent to Java's Map<String, Object>
