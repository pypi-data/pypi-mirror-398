from pydantic import BaseModel, Field
from typing import Annotated, Generic, Literal, TypeGuard
from uuid import UUID
from nexo.schemas.mixins.identity import Identifier
from nexo.types.string import OptStr
from ..enums.examination import (
    IdentifierType,
    OrganSystem,
    OptExaminationStatusT,
    OptListOfExaminationStatuses,
)
from ..types.examination import IdentifierValueType, OptValueType


class OrganExamination(BaseModel):
    organ_system: Annotated[OrganSystem, Field(..., description="Organ system")]
    finding: Annotated[str, Field(..., description="Finding")]


ListOfOrganExaminations = list[OrganExamination]
OptListOfOrganExaminations = ListOfOrganExaminations | None


class OrganExaminations(BaseModel):
    organ_examinations: Annotated[
        OptListOfOrganExaminations, Field(None, description="Organ examinations")
    ] = None


class ExaminationStatus(BaseModel, Generic[OptExaminationStatusT]):
    examination_status: Annotated[
        OptExaminationStatusT, Field(..., description="Examination's status")
    ]


class ExaminationStatuses(BaseModel):
    examination_statuses: Annotated[
        OptListOfExaminationStatuses, Field(None, description="Examination's statuses")
    ] = None


class Value(BaseModel):
    value: Annotated[OptValueType, Field(None, description="Examination's Value")] = (
        None
    )


class Unit(BaseModel):
    unit: Annotated[OptStr, Field(None, description="Examination's unit")] = None


class ExaminationIdentifier(Identifier[IdentifierType, IdentifierValueType]):
    @property
    def column_and_value(self) -> tuple[str, IdentifierValueType]:
        return self.type.column, self.value


class IdExaminationIdentifier(Identifier[Literal[IdentifierType.ID], int]):
    type: Annotated[
        Literal[IdentifierType.ID],
        Field(IdentifierType.ID, description="Identifier's type"),
    ] = IdentifierType.ID
    value: Annotated[int, Field(..., description="Identifier's value", ge=1)]


class UUIDExaminationIdentifier(Identifier[Literal[IdentifierType.UUID], UUID]):
    type: Annotated[
        Literal[IdentifierType.UUID],
        Field(IdentifierType.UUID, description="Identifier's type"),
    ] = IdentifierType.UUID


AnyExaminationIdentifier = (
    ExaminationIdentifier | IdExaminationIdentifier | UUIDExaminationIdentifier
)


def is_id_identifier(
    identifier: AnyExaminationIdentifier,
) -> TypeGuard[IdExaminationIdentifier]:
    return identifier.type is IdentifierType.ID and isinstance(identifier.value, int)


def is_uuid_identifier(
    identifier: AnyExaminationIdentifier,
) -> TypeGuard[UUIDExaminationIdentifier]:
    return identifier.type is IdentifierType.UUID and isinstance(identifier.value, UUID)
