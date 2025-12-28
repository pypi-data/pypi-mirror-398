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


class OrganSystem(StrEnum):
    GENERAL_CONSTITUTIONAL = "General/Constitutional"
    HEENT = "HEENT"
    CARDIOVASCULAR = "Cardiovascular"
    RESPIRATORY = "Respiratory"
    GASTROINTESTINAL = "Gastrointestinal"
    MUSCULOSKELETAL = "Musculoskeletal"
    NEUROLOGICAL = "Neurological"
    SKIN = "Skin"
    LYMPHATIC = "Lymphatic"
    GENITOURINARY = "Genitourinary"
    ENDOCRINE = "Endocrine"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


OrganSystemT = TypeVar("OrganSystemT", bound=OrganSystem)
OptOrganSystem = OrganSystem | None
OptOrganSystemT = TypeVar("OptOrganSystemT", bound=OptOrganSystem)
ListOfOrganSystems = list[OrganSystem]
OptListOfOrganSystems = ListOfOrganSystems | None
OptListOfOrganSystemsT = TypeVar("OptListOfOrganSystemsT", bound=OptListOfOrganSystems)


class ExaminationStatus(StrEnum):
    """Possible examination result statuses"""

    NO_MATCHING_RULE = "no_matching_rule"

    CRITICAL_LOW = "critical_low"
    BORDERLINE_LOW = "borderline_low"
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    BORDERLINE_HIGH = "borderline_high"
    CRITICAL_HIGH = "critical_high"

    NEGATIVE = "negative"
    POSITIVE = "positive"

    NON_REACTIVE = "non_reactive"
    BORDERLINE_REACTIVE = "borderline_reactive"
    REACTIVE = "reactive"

    @classmethod
    def normal_statuses(cls) -> list["ExaminationStatus"]:
        return [cls.NORMAL, cls.NO_MATCHING_RULE, cls.NEGATIVE, cls.NON_REACTIVE]

    @property
    def is_abnormal(self) -> bool:
        """Check if result is abnormal (not normal)"""
        return self not in self.normal_statuses()

    @classmethod
    def critical_statuses(cls) -> list["ExaminationStatus"]:
        return [cls.CRITICAL_HIGH, cls.CRITICAL_LOW]

    @property
    def is_critical(self) -> bool:
        """Check if result is critical"""
        return self in self.critical_statuses()

    @classmethod
    def any_high_statuses(cls) -> list["ExaminationStatus"]:
        return [cls.HIGH, cls.CRITICAL_HIGH]

    @property
    def is_any_high(self) -> bool:
        """Check if result is high (including critical high)"""
        return self in self.any_high_statuses()

    @classmethod
    def any_low_statuses(cls) -> list["ExaminationStatus"]:
        return [cls.LOW, cls.CRITICAL_LOW]

    @property
    def is_any_low(self) -> bool:
        """Check if result is low (including critical low)"""
        return self in self.any_low_statuses()

    @property
    def is_high(self) -> bool:
        """Check if result is high (not critical)"""
        return self is self.HIGH

    @property
    def is_low(self) -> bool:
        """Check if result is low (not critical)"""
        return self is self.LOW

    @property
    def is_critical_high(self) -> bool:
        """Check if result is critically high"""
        return self is self.CRITICAL_HIGH

    @property
    def is_critical_low(self) -> bool:
        """Check if result is critically low"""
        return self is self.CRITICAL_LOW

    @property
    def is_positive(self) -> bool:
        """Check if result is positive (for tests like COVID-19)"""
        return self is self.POSITIVE

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


ExaminationStatusT = TypeVar("ExaminationStatusT", bound=ExaminationStatus)
OptExaminationStatus = ExaminationStatus | None
OptExaminationStatusT = TypeVar("OptExaminationStatusT", bound=OptExaminationStatus)
ListOfExaminationStatuses = list[ExaminationStatus]
OptListOfExaminationStatuses = ListOfExaminationStatuses | None
OptListOfExaminationStatusesT = TypeVar(
    "OptListOfExaminationStatusesT", bound=OptListOfExaminationStatuses
)
