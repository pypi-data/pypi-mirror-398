from pydantic import BaseModel, Field
from typing import Annotated, Generic, Literal, TypeGuard
from uuid import UUID
from nexo.schemas.mixins.identity import Identifier, Name as BaseName
from nexo.types.boolean import OptBoolT
from nexo.types.string import OptStrT, OptListOfStrs, OptListOfStrsT
from ..enums.parameter import (
    IdentifierType,
    OptParameterGroupT,
    OptListOfParameterGroups,
    ValueType as ValueTypeEnum,
    OptValueTypeT,
    OptListOfValueTypes,
)
from ..types.parameter import IdentifierValueType


def _validate_value_type_and_options(value_type: ValueTypeEnum, options: OptListOfStrs):
    if value_type is ValueTypeEnum.ENUM:
        if options is None:
            raise ValueError("Options can not be None if value type is enum")
    else:
        if options is not None:
            raise ValueError("Options must be None if value type is not enum")


class Group(BaseModel, Generic[OptParameterGroupT]):
    group: Annotated[OptParameterGroupT, Field(..., description="Parameter's group")]


class Groups(BaseModel):
    groups: Annotated[
        OptListOfParameterGroups, Field(None, description="Parameter's groups")
    ] = None


class IsMandatory(BaseModel, Generic[OptBoolT]):
    is_mandatory: Annotated[OptBoolT, Field(..., description="Whether is mandatory")]


class Name(BaseName, Generic[OptStrT]):
    name: Annotated[OptStrT, Field(..., description="Parameter's name", max_length=50)]


class Aliases(BaseModel, Generic[OptListOfStrsT]):
    aliases: Annotated[OptListOfStrsT, Field(..., description="Parameter's Aliases")]


class ValueType(BaseModel, Generic[OptValueTypeT]):
    value_type: Annotated[
        OptValueTypeT, Field(..., description="Parameter's value type")
    ]


class ValueTypes(BaseModel):
    value_types: Annotated[
        OptListOfValueTypes, Field(None, description="Parameter's value types")
    ] = None


class Options(BaseModel, Generic[OptListOfStrsT]):
    options: Annotated[
        OptListOfStrsT, Field(..., description="Parameter's value's options")
    ]


class IsNullable(BaseModel, Generic[OptBoolT]):
    is_nullable: Annotated[OptBoolT, Field(..., description="Whether is nullable")]


class Unit(BaseModel, Generic[OptStrT]):
    unit: Annotated[OptStrT, Field(..., description="Parameter's unit", max_length=30)]


class Units(BaseModel):
    units: Annotated[OptListOfStrs, Field(None, description="Parameter's units")] = None


class ParameterIdentifier(Identifier[IdentifierType, IdentifierValueType]):
    @property
    def column_and_value(self) -> tuple[str, IdentifierValueType]:
        return self.type.column, self.value


class IdParameterIdentifier(Identifier[Literal[IdentifierType.ID], int]):
    type: Annotated[
        Literal[IdentifierType.ID],
        Field(IdentifierType.ID, description="Identifier's type"),
    ] = IdentifierType.ID
    value: Annotated[int, Field(..., description="Identifier's value", ge=1)]


class UUIDParameterIdentifier(Identifier[Literal[IdentifierType.UUID], UUID]):
    type: Annotated[
        Literal[IdentifierType.UUID],
        Field(IdentifierType.UUID, description="Identifier's type"),
    ] = IdentifierType.UUID


class NameParameterIdentifier(Identifier[Literal[IdentifierType.NAME], str]):
    type: Annotated[
        Literal[IdentifierType.NAME],
        Field(IdentifierType.NAME, description="Identifier's type"),
    ] = IdentifierType.NAME
    value: Annotated[str, Field(..., description="Identifier's value", max_length=255)]


AnyParameterIdentifier = (
    ParameterIdentifier
    | IdParameterIdentifier
    | UUIDParameterIdentifier
    | NameParameterIdentifier
)


def is_id_identifier(
    identifier: AnyParameterIdentifier,
) -> TypeGuard[IdParameterIdentifier]:
    return identifier.type is IdentifierType.ID and isinstance(identifier.value, int)


def is_uuid_identifier(
    identifier: AnyParameterIdentifier,
) -> TypeGuard[UUIDParameterIdentifier]:
    return identifier.type is IdentifierType.UUID and isinstance(identifier.value, UUID)


def is_name_identifier(
    identifier: AnyParameterIdentifier,
) -> TypeGuard[NameParameterIdentifier]:
    return identifier.type is IdentifierType.NAME and isinstance(identifier.value, str)
