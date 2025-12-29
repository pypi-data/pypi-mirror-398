from dataclasses import dataclass, field
from typing import List, Optional

from ..common.json_decorator import JSONSerializable


@dataclass
class ProcessActionResponseDetailData(JSONSerializable):
    id: str
    message: str
    error: str


@dataclass
class ProcessActionResponseData(JSONSerializable):
    count: int = 0
    details: Optional[List[ProcessActionResponseDetailData]] = field(default=None)

    @classmethod
    def from_dict(cls, data: dict):
        if "details" in data and data["details"] is not None:
            data["details"] = [
                ProcessActionResponseDetailData.from_dict(item)
                if isinstance(item, dict) else item
                for item in data["details"]
            ]
        return cls(**data)
