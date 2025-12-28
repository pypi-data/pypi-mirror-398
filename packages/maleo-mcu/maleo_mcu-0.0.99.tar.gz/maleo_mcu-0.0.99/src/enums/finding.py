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
    NAME = "name"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]

    @property
    def column(self) -> str:
        return self.value


class Logic(StrEnum):
    AND = "and"
    OR = "or"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


OptLogic = Logic | None
OptLogicT = TypeVar("OptLogicT", bound=OptLogic)
ListOfLogics = list[Logic]
OptListOfLogics = ListOfLogics | None
