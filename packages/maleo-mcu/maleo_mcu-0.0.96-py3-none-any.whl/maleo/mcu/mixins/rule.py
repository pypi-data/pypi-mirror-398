from pydantic import BaseModel, Field
from typing import Annotated, Generic, Literal, TypeGuard, TypeVar
from uuid import UUID
from nexo.enums.identity import (
    ListOfGenders,
    OptListOfGendersT,
    GendersMixin as BaseGendersMixin,
)
from nexo.schemas.mixins.identity import Identifier
from nexo.types.float import OptFloat
from nexo.types.string import OptStr, OptStrT
from ..enums.rule import (
    IdentifierType,
    RuleType as RuleTypeEnum,
    OptRuleTypeT,
    OptListOfRuleTypes,
)
from ..types.rule import IdentifierValueType


class Unit(BaseModel, Generic[OptStrT]):
    unit: Annotated[OptStrT, Field(..., description="Rule's unit", max_length=30)]


class RuleType(BaseModel, Generic[OptRuleTypeT]):
    type: Annotated[OptRuleTypeT, Field(..., description="Rule's type")]


class RuleTypes(BaseModel):
    types: Annotated[OptListOfRuleTypes, Field(None, description="Rule's types")] = None


class GendersMixin(BaseGendersMixin, Generic[OptListOfGendersT]):
    genders: Annotated[
        OptListOfGendersT, Field(..., description="Genders", min_length=1)
    ]


class AgeRange(BaseModel):
    min: Annotated[int, Field(0, description="Minimum Age", ge=0)]
    max: Annotated[int, Field(150, description="Maximum Age", le=150)]


OptAgeRange = AgeRange | None
OptAgeRangeT = TypeVar("OptAgeRangeT", bound=OptAgeRange)


class AgeRangeMixin(BaseModel, Generic[OptAgeRangeT]):
    age: Annotated[OptAgeRangeT, Field(..., description="Age range")]


class CriticalLow(BaseModel):
    critical_low: Annotated[
        OptFloat, Field(None, description="Critical Low", ge=0.0)
    ] = None


class BorderlineLow(BaseModel):
    borderline_low: Annotated[
        OptFloat, Field(None, description="Borderline Low", ge=0.0)
    ] = None


NormalMinT = TypeVar("NormalMinT", bound=OptFloat)


class NormalMin(BaseModel, Generic[NormalMinT]):
    normal_min: Annotated[NormalMinT, Field(..., description="Normal Min", ge=0.0)]


NormalMaxT = TypeVar("NormalMaxT", bound=OptFloat)


class NormalMax(BaseModel, Generic[NormalMaxT]):
    normal_max: Annotated[NormalMaxT, Field(..., description="Normal Max", ge=0.0)]


class BorderlineHigh(BaseModel):
    borderline_high: Annotated[
        OptFloat, Field(None, description="Borderline High", ge=0.0)
    ] = None


class CriticalHigh(BaseModel):
    critical_high: Annotated[
        OptFloat, Field(None, description="Critial High", ge=0.0)
    ] = None


class BorderlineReactive(BaseModel):
    borderline_reactive: Annotated[
        OptFloat, Field(None, description="Borderline Reactive", ge=0.0)
    ] = None


class Reactive(BaseModel):
    reactive: Annotated[OptFloat, Field(None, description="Reactive", ge=0.0)] = None


class Positive(BaseModel):
    positive: Annotated[OptFloat, Field(None, description="Positive", ge=0.0)] = None


class RuleData(
    Positive,
    Reactive,
    BorderlineReactive,
    CriticalHigh,
    BorderlineHigh,
    NormalMax[float],
    NormalMin[float],
    BorderlineLow,
    CriticalLow,
    AgeRangeMixin[AgeRange],
    GendersMixin[ListOfGenders],
    RuleType[RuleTypeEnum],
    Unit[OptStr],
):
    pass


class RuleIdentifier(Identifier[IdentifierType, IdentifierValueType]):
    @property
    def column_and_value(self) -> tuple[str, IdentifierValueType]:
        return self.type.column, self.value


class IdRuleIdentifier(Identifier[Literal[IdentifierType.ID], int]):
    type: Annotated[
        Literal[IdentifierType.ID],
        Field(IdentifierType.ID, description="Identifier's type"),
    ] = IdentifierType.ID
    value: Annotated[int, Field(..., description="Identifier's value", ge=1)]


class UUIDRuleIdentifier(Identifier[Literal[IdentifierType.UUID], UUID]):
    type: Annotated[
        Literal[IdentifierType.UUID],
        Field(IdentifierType.UUID, description="Identifier's type"),
    ] = IdentifierType.UUID


AnyRuleIdentifier = RuleIdentifier | IdRuleIdentifier | UUIDRuleIdentifier


def is_id_identifier(
    identifier: AnyRuleIdentifier,
) -> TypeGuard[IdRuleIdentifier]:
    return identifier.type is IdentifierType.ID and isinstance(identifier.value, int)


def is_uuid_identifier(
    identifier: AnyRuleIdentifier,
) -> TypeGuard[UUIDRuleIdentifier]:
    return identifier.type is IdentifierType.UUID and isinstance(identifier.value, UUID)
