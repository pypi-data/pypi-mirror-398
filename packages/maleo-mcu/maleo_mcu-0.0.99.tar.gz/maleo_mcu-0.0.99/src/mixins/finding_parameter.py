from pydantic import BaseModel, Field
from typing import Annotated, Generic, Literal, TypeGuard
from uuid import UUID
from nexo.schemas.mixins.identity import Identifier
from nexo.types.any import ManyAny
from nexo.types.string import ManyStrs
from nexo.types.integer import OptIntT
from ..enums.finding_parameter import IdentifierType, OptCriteriaT
from ..types.finding_parameter import CompositeIdentifierType, IdentifierValueType


class Criteria(BaseModel, Generic[OptCriteriaT]):
    criteria: Annotated[OptCriteriaT, Field(..., description="Criteria")]


class Weight(BaseModel, Generic[OptIntT]):
    weight: Annotated[OptIntT, Field(..., description="Weight")]


class FindingParameterIdentifier(Identifier[IdentifierType, IdentifierValueType]):
    @property
    def columns_and_values(self) -> tuple[ManyStrs, ManyAny]:
        values = self.value if isinstance(self.value, tuple) else (self.value,)
        return self.type.columns, values


class IdFindingParameterIdentifier(Identifier[Literal[IdentifierType.ID], int]):
    type: Annotated[
        Literal[IdentifierType.ID],
        Field(IdentifierType.ID, description="Identifier's type"),
    ] = IdentifierType.ID
    value: Annotated[int, Field(..., description="Identifier's value", ge=1)]


class UUIDFindingParameterIdentifier(Identifier[Literal[IdentifierType.UUID], UUID]):
    type: Annotated[
        Literal[IdentifierType.UUID],
        Field(IdentifierType.UUID, description="Identifier's type"),
    ] = IdentifierType.UUID


class CompositeFindingParameterIdentifier(
    Identifier[Literal[IdentifierType.COMPOSITE], CompositeIdentifierType]
):
    type: Annotated[
        Literal[IdentifierType.COMPOSITE],
        Field(IdentifierType.COMPOSITE, description="Identifier's type"),
    ] = IdentifierType.COMPOSITE
    value: Annotated[
        CompositeIdentifierType, Field(..., description="Identifier's value")
    ]


AnyFindingParameterIdentifier = (
    FindingParameterIdentifier
    | IdFindingParameterIdentifier
    | UUIDFindingParameterIdentifier
    | CompositeFindingParameterIdentifier
)


def is_id_identifier(
    identifier: AnyFindingParameterIdentifier,
) -> TypeGuard[IdFindingParameterIdentifier]:
    return identifier.type is IdentifierType.ID and isinstance(identifier.value, int)


def is_uuid_identifier(
    identifier: AnyFindingParameterIdentifier,
) -> TypeGuard[UUIDFindingParameterIdentifier]:
    return identifier.type is IdentifierType.UUID and isinstance(identifier.value, UUID)


def is_composite_identifier(
    identifier: AnyFindingParameterIdentifier,
) -> TypeGuard[CompositeFindingParameterIdentifier]:
    return identifier.type is IdentifierType.COMPOSITE and isinstance(
        identifier.value, tuple
    )
