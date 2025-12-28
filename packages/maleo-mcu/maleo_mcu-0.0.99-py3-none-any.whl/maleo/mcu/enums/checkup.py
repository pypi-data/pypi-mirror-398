from enum import StrEnum
from typing import TypeVar
from nexo.types.string import ListOfStrs


class IdentifierType(StrEnum):
    ID = "id"
    UUID = "uuid"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]

    @property
    def column(self) -> str:
        return self.value


class Process(StrEnum):
    START = "start"
    REVIEW = "review"
    APPROVE = "approve"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


class CheckupType(StrEnum):
    GROUP = "group"
    INDIVIDUAL = "individual"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


OptCheckupType = CheckupType | None
OptCheckupTypeT = TypeVar("OptCheckupTypeT", bound=OptCheckupType)
ListOfCheckupTypes = list[CheckupType]
OptListOfCheckupTypes = ListOfCheckupTypes | None
OptListOfCheckupTypesT = TypeVar("OptListOfCheckupTypesT", bound=OptListOfCheckupTypes)


class CheckupStatus(StrEnum):
    DRAFT = "draft"
    ONGOING = "ongoing"
    REVIEWED = "reviewed"
    APPROVED = "approved"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


OptCheckupStatus = CheckupStatus | None
OptCheckupStatusT = TypeVar("OptCheckupStatusT", bound=OptCheckupStatus)
ListOfCheckupStatuses = list[CheckupStatus]
OptListOfCheckupStatuses = ListOfCheckupStatuses | None
OptListOfCheckupStatusesT = TypeVar(
    "OptListOfCheckupStatusesT", bound=OptListOfCheckupStatuses
)


class Feedback(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


OptFeedback = Feedback | None
