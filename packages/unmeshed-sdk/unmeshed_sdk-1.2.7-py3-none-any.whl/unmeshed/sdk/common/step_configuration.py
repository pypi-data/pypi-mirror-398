from dataclasses import dataclass, field
from typing import Optional

from ..common.json_decorator import JSONSerializable

@dataclass
class StepConfiguration(JSONSerializable):
    errorPolicyName: Optional[str] = field(default=None)

    useCache: bool = field(default=False)
    cacheKey: Optional[str] = field(default=None)
    cacheTimeoutSeconds: int = field(default=0)

    stream: bool = field(default=False)
    streamAllStatuses: bool = field(default=False)
    preExecutionScript: Optional[str] = field(default=None)
    constructInputFromScript: bool = field(default=False)
    scriptLanguage: Optional[str] = field(default=None)

    jqTransformer: Optional[str] = field(default=None)
    rateLimitMaxRequests: int = field(default=0)
    rateLimitWindowSeconds: int = field(default=0)