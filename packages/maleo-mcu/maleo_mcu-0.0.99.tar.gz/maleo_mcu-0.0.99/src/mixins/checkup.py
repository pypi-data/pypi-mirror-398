from pydantic import BaseModel, Field
from typing import Annotated, Generic, Literal, TypeGuard
from uuid import UUID
from nexo.schemas.mixins.identity import Identifier
from nexo.types.datetime import OptDateT
from ..enums.checkup import (
    IdentifierType,
    OptCheckupTypeT,
    OptListOfCheckupTypes,
    OptCheckupStatusT,
    OptListOfCheckupStatuses,
)
from ..types.checkup import IdentifierValueType


class CheckupType(BaseModel, Generic[OptCheckupTypeT]):
    type: Annotated[OptCheckupTypeT, Field(..., description="Checkup's type")]


class CheckupTypes(BaseModel):
    types: Annotated[
        OptListOfCheckupTypes, Field(None, description="Checkup's types")
    ] = None


class CheckupDate(BaseModel, Generic[OptDateT]):
    checkup_date: Annotated[OptDateT, Field(..., description="Checkup's date")]


class CheckupStatus(BaseModel, Generic[OptCheckupStatusT]):
    checkup_status: Annotated[
        OptCheckupStatusT, Field(..., description="Checkup's status")
    ]


class CheckupStatuses(BaseModel):
    checkup_statuses: Annotated[
        OptListOfCheckupStatuses, Field(None, description="Checkup's statuses")
    ] = None


class CheckupIdentifier(Identifier[IdentifierType, IdentifierValueType]):
    @property
    def column_and_value(self) -> tuple[str, IdentifierValueType]:
        return self.type.column, self.value


class IdCheckupIdentifier(Identifier[Literal[IdentifierType.ID], int]):
    type: Annotated[
        Literal[IdentifierType.ID],
        Field(IdentifierType.ID, description="Identifier's type"),
    ] = IdentifierType.ID
    value: Annotated[int, Field(..., description="Identifier's value", ge=1)]


class UUIDCheckupIdentifier(Identifier[Literal[IdentifierType.UUID], UUID]):
    type: Annotated[
        Literal[IdentifierType.UUID],
        Field(IdentifierType.UUID, description="Identifier's type"),
    ] = IdentifierType.UUID


AnyCheckupIdentifier = CheckupIdentifier | IdCheckupIdentifier | UUIDCheckupIdentifier


def is_id_identifier(
    identifier: AnyCheckupIdentifier,
) -> TypeGuard[IdCheckupIdentifier]:
    return identifier.type is IdentifierType.ID and isinstance(identifier.value, int)


def is_uuid_identifier(
    identifier: AnyCheckupIdentifier,
) -> TypeGuard[UUIDCheckupIdentifier]:
    return identifier.type is IdentifierType.UUID and isinstance(identifier.value, UUID)
