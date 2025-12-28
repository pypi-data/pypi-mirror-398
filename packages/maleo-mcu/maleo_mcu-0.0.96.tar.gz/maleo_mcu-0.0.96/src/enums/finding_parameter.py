from enum import StrEnum
from typing import TypeVar
from nexo.types.string import ListOfStrs, ManyStrs


class IdentifierType(StrEnum):
    ID = "id"
    UUID = "uuid"
    COMPOSITE = "composite"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]

    @property
    def columns(self) -> ManyStrs:
        if self is IdentifierType.ID:
            return ("id",)
        elif self is IdentifierType.UUID:
            return ("uuid",)
        elif self is IdentifierType.COMPOSITE:
            return ("finding_id", "parameter_id")
        raise ValueError(f"Unknown column(s) for identifier type: {self}")


class Criteria(StrEnum):
    ANY_LOW = "any_low"
    CRITICAL_LOW = "critical_low"
    BORDERLINE_LOW = "borderline_low"
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    BORDERLINE_HIGH = "borderline_high"
    CRITICAL_HIGH = "critical_high"
    ANY_HIGH = "any_high"

    NEGATIVE = "negative"
    POSITIVE = "positive"

    NON_REACTIVE = "non_reactive"
    BORDERLINE_REACTIVE = "borderline_reactive"
    REACTIVE = "reactive"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


OptCriteria = Criteria | None
OptCriteriaT = TypeVar("OptCriteriaT", bound=OptCriteria)
ListOfCriterias = list[Criteria]
OptListOfCriterias = ListOfCriterias | None
