from enum import StrEnum
from typing import TypeVar
from nexo.types.string import ListOfStrs


class Granularity(StrEnum):
    STANDARD = "standard"
    FULL = "full"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


class IdentifierType(StrEnum):
    ID = "id"
    UUID = "uuid"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]

    @property
    def column(self) -> str:
        return self.value


class RuleType(StrEnum):
    HIGHER_BETTER = "higher_better"
    POSITIVE = "positive"
    REACTIVE = "reactive"
    STANDARD = "standard"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


OptRuleType = RuleType | None
OptRuleTypeT = TypeVar("OptRuleTypeT", bound=OptRuleType)
ListOfRuleTypes = list[RuleType]
OptListOfRuleTypes = ListOfRuleTypes | None
OptListOfRuleTypesT = TypeVar("OptListOfRuleTypesT", bound=OptListOfRuleTypes)
