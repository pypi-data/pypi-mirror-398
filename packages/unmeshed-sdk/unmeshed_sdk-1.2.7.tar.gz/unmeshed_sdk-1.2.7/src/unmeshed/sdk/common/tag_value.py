from dataclasses import dataclass

from ..common.json_decorator import JSONSerializable

@dataclass
class TagValue(JSONSerializable):
    name: str = ""
    value: str = ""

    @staticmethod
    def of(name: str, value: str):
        return TagValue(name, value)