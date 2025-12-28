from pydantic import BaseModel, Field
from typing import Annotated, Generic, Literal, TypeGuard
from uuid import UUID
from nexo.schemas.mixins.identity import Identifier, Name as BaseName
from nexo.types.string import OptStrT, OptListOfStrsT
from ..enums.finding import (
    IdentifierType,
    OptLogicT,
    OptListOfLogics,
)
from ..types.finding import IdentifierValueType


class Name(BaseName, Generic[OptStrT]):
    name: Annotated[OptStrT, Field(..., description="Finding's name", max_length=50)]


class Aliases(BaseModel, Generic[OptListOfStrsT]):
    aliases: Annotated[OptListOfStrsT, Field(..., description="Finding's aliases")]


class Recommendation(BaseModel, Generic[OptStrT]):
    recommendation: Annotated[
        OptStrT, Field(..., description="Finding's recommendation")
    ]


class Logic(BaseModel, Generic[OptLogicT]):
    logic: Annotated[OptLogicT, Field(..., description="Finding's logic")]


class Logics(BaseModel):
    logics: Annotated[OptListOfLogics, Field(None, description="Finding's logics")] = (
        None
    )


class FindingIdentifier(Identifier[IdentifierType, IdentifierValueType]):
    @property
    def column_and_value(self) -> tuple[str, IdentifierValueType]:
        return self.type.column, self.value


class IdFindingIdentifier(Identifier[Literal[IdentifierType.ID], int]):
    type: Annotated[
        Literal[IdentifierType.ID],
        Field(IdentifierType.ID, description="Identifier's type"),
    ] = IdentifierType.ID
    value: Annotated[int, Field(..., description="Identifier's value", ge=1)]


class UUIDFindingIdentifier(Identifier[Literal[IdentifierType.UUID], UUID]):
    type: Annotated[
        Literal[IdentifierType.UUID],
        Field(IdentifierType.UUID, description="Identifier's type"),
    ] = IdentifierType.UUID


class NameFindingIdentifier(Identifier[Literal[IdentifierType.NAME], str]):
    type: Annotated[
        Literal[IdentifierType.NAME],
        Field(IdentifierType.NAME, description="Identifier's type"),
    ] = IdentifierType.NAME
    value: Annotated[str, Field(..., description="Identifier's value", max_length=255)]


AnyFindingIdentifier = (
    FindingIdentifier
    | IdFindingIdentifier
    | UUIDFindingIdentifier
    | NameFindingIdentifier
)


def is_id_identifier(
    identifier: AnyFindingIdentifier,
) -> TypeGuard[IdFindingIdentifier]:
    return identifier.type is IdentifierType.ID and isinstance(identifier.value, int)


def is_uuid_identifier(
    identifier: AnyFindingIdentifier,
) -> TypeGuard[UUIDFindingIdentifier]:
    return identifier.type is IdentifierType.UUID and isinstance(identifier.value, UUID)


def is_name_identifier(
    identifier: AnyFindingIdentifier,
) -> TypeGuard[NameFindingIdentifier]:
    return identifier.type is IdentifierType.NAME and isinstance(identifier.value, str)
