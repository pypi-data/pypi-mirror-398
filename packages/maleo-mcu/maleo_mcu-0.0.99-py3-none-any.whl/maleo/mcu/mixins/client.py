from pydantic import Field
from typing import Annotated, Generic, Literal, TypeGuard
from uuid import UUID
from nexo.schemas.mixins.identity import Identifier, Name as BaseName
from nexo.types.string import OptStrT
from ..enums.client import IdentifierType
from ..types.client import IdentifierValueType


class Name(BaseName, Generic[OptStrT]):
    name: Annotated[OptStrT, Field(..., description="Name", max_length=100)]


class ClientIdentifier(Identifier[IdentifierType, IdentifierValueType]):
    @property
    def column_and_value(self) -> tuple[str, IdentifierValueType]:
        return self.type.column, self.value


class IdClientIdentifier(Identifier[Literal[IdentifierType.ID], int]):
    type: Annotated[
        Literal[IdentifierType.ID],
        Field(IdentifierType.ID, description="Identifier's type"),
    ] = IdentifierType.ID
    value: Annotated[int, Field(..., description="Identifier's value", ge=1)]


class UUIDClientIdentifier(Identifier[Literal[IdentifierType.UUID], UUID]):
    type: Annotated[
        Literal[IdentifierType.UUID],
        Field(IdentifierType.UUID, description="Identifier's type"),
    ] = IdentifierType.UUID


AnyClientIdentifier = ClientIdentifier | IdClientIdentifier | UUIDClientIdentifier


def is_id_identifier(
    identifier: AnyClientIdentifier,
) -> TypeGuard[IdClientIdentifier]:
    return identifier.type is IdentifierType.ID and isinstance(identifier.value, int)


def is_uuid_identifier(
    identifier: AnyClientIdentifier,
) -> TypeGuard[UUIDClientIdentifier]:
    return identifier.type is IdentifierType.UUID and isinstance(identifier.value, UUID)
