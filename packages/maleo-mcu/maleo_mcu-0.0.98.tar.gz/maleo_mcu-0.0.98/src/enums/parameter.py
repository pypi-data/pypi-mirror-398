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


class ParameterGroup(StrEnum):
    """Enum for parameter groups."""

    ANAMNESIS = "anamnesis"
    CLINICAL_CHEMISTRY = "clinical_chemistry"
    HEMATOLOGY = "hematology"
    IMMUNOLOGY = "immunology"
    PHYSICAL = "physical"
    RADIOLOGY = "radiology"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]

    @property
    def alias(self) -> str:
        if self is ParameterGroup.ANAMNESIS:
            return "Anamnesis"
        elif self is ParameterGroup.CLINICAL_CHEMISTRY:
            return "Clinical Chemistry"
        elif self is ParameterGroup.HEMATOLOGY:
            return "Hematology"
        elif self is ParameterGroup.IMMUNOLOGY:
            return "Immunology"
        elif self is ParameterGroup.PHYSICAL:
            return "Physical Examination"
        elif self is ParameterGroup.RADIOLOGY:
            return "Radiology"
        raise ValueError(f"Unknown parameter group: {self}")


OptParameterGroup = ParameterGroup | None
OptParameterGroupT = TypeVar("OptParameterGroupT", bound=OptParameterGroup)
ListOfParameterGroups = list[ParameterGroup]
OptListOfParameterGroups = ListOfParameterGroups | None


class ValueType(StrEnum):
    BOOLEAN = "boolean"
    ENUM = "enum"
    FLOAT = "float"
    INTEGER = "integer"
    STRING = "string"
    UUID = "uuid"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


OptValueType = ValueType | None
OptValueTypeT = TypeVar("OptValueTypeT", bound=OptValueType)
ListOfValueTypes = list[ValueType]
OptListOfValueTypes = ListOfValueTypes | None
