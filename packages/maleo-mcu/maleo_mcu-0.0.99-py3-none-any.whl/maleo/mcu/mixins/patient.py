from pydantic import Field
from typing import Annotated, Generic, Literal, TypeGuard
from uuid import UUID
from nexo.schemas.mixins.identity import (
    Identifier,
    IdCard as BaseIdCard,
    FullName as BaseFullName,
    PlaceOfBirth as BasePlaceOfBirth,
)
from nexo.types.string import OptStrT
from ..enums.patient import IdentifierType
from ..types.patient import IdentifierValueType


class IdCard(BaseIdCard[OptStrT], Generic[OptStrT]):
    id_card: Annotated[
        OptStrT,
        Field(..., description="Id Card", max_length=16, pattern=r"^[0-9]{1,16}$"),
    ]


class FullName(BaseFullName[OptStrT], Generic[OptStrT]):
    full_name: Annotated[OptStrT, Field(..., description="Full Name", max_length=200)]


class PlaceOfBirth(BasePlaceOfBirth[OptStrT], Generic[OptStrT]):
    place_of_birth: Annotated[
        OptStrT, Field(..., description="Place of Birth", max_length=50)
    ]


class PatientIdentifier(Identifier[IdentifierType, IdentifierValueType]):
    @property
    def column_and_value(self) -> tuple[str, IdentifierValueType]:
        return self.type.column, self.value


class IdPatientIdentifier(Identifier[Literal[IdentifierType.ID], int]):
    type: Annotated[
        Literal[IdentifierType.ID],
        Field(IdentifierType.ID, description="Identifier's type"),
    ] = IdentifierType.ID
    value: Annotated[int, Field(..., description="Identifier's value", ge=1)]


class UUIDPatientIdentifier(Identifier[Literal[IdentifierType.UUID], UUID]):
    type: Annotated[
        Literal[IdentifierType.UUID],
        Field(IdentifierType.UUID, description="Identifier's type"),
    ] = IdentifierType.UUID


AnyPatientIdentifier = PatientIdentifier | IdPatientIdentifier | UUIDPatientIdentifier


def is_id_identifier(
    identifier: AnyPatientIdentifier,
) -> TypeGuard[IdPatientIdentifier]:
    return identifier.type is IdentifierType.ID and isinstance(identifier.value, int)


def is_uuid_identifier(
    identifier: AnyPatientIdentifier,
) -> TypeGuard[UUIDPatientIdentifier]:
    return identifier.type is IdentifierType.UUID and isinstance(identifier.value, UUID)
