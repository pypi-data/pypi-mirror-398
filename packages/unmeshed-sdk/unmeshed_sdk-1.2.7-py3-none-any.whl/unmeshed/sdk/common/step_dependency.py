from dataclasses import dataclass

from ..common.json_decorator import JSONSerializable

@dataclass
class StepDependency(JSONSerializable):
    ref: str = ""
    deps: str = ""
