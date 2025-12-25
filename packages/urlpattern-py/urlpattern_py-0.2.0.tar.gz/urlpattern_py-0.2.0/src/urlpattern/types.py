from dataclasses import dataclass
from enum import IntEnum


class Modifier(IntEnum):
    "Ordering mirrors the URLPattern comparator expectations."

    ZERO_OR_MORE = 0
    OPTIONAL = 1
    ONE_OR_MORE = 2
    NONE = 3

    def to_string(self) -> str:
        if self == Modifier.ZERO_OR_MORE:
            return "*"
        if self == Modifier.OPTIONAL:
            return "?"
        if self == Modifier.ONE_OR_MORE:
            return "+"
        return ""


class PartType(IntEnum):
    "Ordering mirrors the URLPattern comparator expectations."

    FULL_WILDCARD = 0
    SEGMENT_WILDCARD = 1
    REGEX = 2
    FIXED = 3


@dataclass(frozen=True)
class Part:
    type: PartType
    name: object
    prefix: str
    value: str
    suffix: str
    modifier: Modifier

    def has_custom_name(self) -> bool:
        return self.name != "" and not isinstance(self.name, int)
