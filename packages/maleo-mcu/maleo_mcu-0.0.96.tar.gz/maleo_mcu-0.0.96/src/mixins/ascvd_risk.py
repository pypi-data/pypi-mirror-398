from pydantic import BaseModel, Field
from typing import Annotated, Generic, Literal, TypeGuard, TypeVar
from uuid import UUID
from nexo.schemas.mixins.identity import Identifier
from nexo.types.boolean import OptBoolT
from nexo.types.integer import OptIntT
from ..enums.ascvd_risk import IdentifierType
from ..types.ascvd_risk import IdentifierValueType


class AgeRange(BaseModel):
    min: Annotated[int, Field(..., description="Minimum Age", ge=40)]
    max: Annotated[int, Field(..., description="Maximum Age", le=74)]


OptAgeRange = AgeRange | None
OptAgeRangeT = TypeVar("OptAgeRangeT", bound=OptAgeRange)


class AgeRangeMixin(BaseModel, Generic[OptAgeRangeT]):
    age: Annotated[OptAgeRangeT, Field(..., description="Age range")]


class Diabetes(BaseModel, Generic[OptBoolT]):
    diabetes: Annotated[OptBoolT, Field(..., description="Diabetes")]


class Smoker(BaseModel, Generic[OptBoolT]):
    smoker: Annotated[OptBoolT, Field(..., description="Smoker")]


class TotalCholesterolRange(BaseModel):
    min: Annotated[float, Field(0, description="Minimum Total Cholesterol", ge=0)]
    max: Annotated[float, Field(99.9, description="Maximum Total Cholesterol", le=99.9)]


OptTotalCholesterolRange = TotalCholesterolRange | None
OptTotalCholesterolRangeT = TypeVar(
    "OptTotalCholesterolRangeT", bound=OptTotalCholesterolRange
)


class TotalCholesterolRangeMixin(BaseModel, Generic[OptTotalCholesterolRangeT]):
    total_cholesterol: Annotated[
        OptTotalCholesterolRangeT, Field(..., description="Total Cholesterol range")
    ]


class SystolicBloodPressureRange(BaseModel):
    min: Annotated[int, Field(0, description="Minimum Systolic Blood Pressure", ge=0)]
    max: Annotated[
        int, Field(999, description="Maximum Systolic Blood Pressure", le=999)
    ]


OptSystolicBloodPressureRange = SystolicBloodPressureRange | None
OptSystolicBloodPressureRangeT = TypeVar(
    "OptSystolicBloodPressureRangeT", bound=OptSystolicBloodPressureRange
)


class SystolicBloodPressureRangeMixin(
    BaseModel, Generic[OptSystolicBloodPressureRangeT]
):
    systolic_blood_pressure: Annotated[
        OptSystolicBloodPressureRangeT,
        Field(..., description="Systolic Blood Pressure range"),
    ]


class Score(BaseModel, Generic[OptIntT]):
    score: Annotated[OptIntT, Field(..., description="Score", ge=1, le=59)]


class ASCVDRiskIdentifier(Identifier[IdentifierType, IdentifierValueType]):
    @property
    def column_and_value(self) -> tuple[str, IdentifierValueType]:
        return self.type.column, self.value


class IdASCVDRiskIdentifier(Identifier[Literal[IdentifierType.ID], int]):
    type: Annotated[
        Literal[IdentifierType.ID],
        Field(IdentifierType.ID, description="Identifier's type"),
    ] = IdentifierType.ID
    value: Annotated[int, Field(..., description="Identifier's value", ge=1)]


class UUIDASCVDRiskIdentifier(Identifier[Literal[IdentifierType.UUID], UUID]):
    type: Annotated[
        Literal[IdentifierType.UUID],
        Field(IdentifierType.UUID, description="Identifier's type"),
    ] = IdentifierType.UUID


AnyASCVDRiskIdentifier = (
    ASCVDRiskIdentifier | IdASCVDRiskIdentifier | UUIDASCVDRiskIdentifier
)


def is_id_identifier(
    identifier: AnyASCVDRiskIdentifier,
) -> TypeGuard[IdASCVDRiskIdentifier]:
    return identifier.type is IdentifierType.ID and isinstance(identifier.value, int)


def is_uuid_identifier(
    identifier: AnyASCVDRiskIdentifier,
) -> TypeGuard[UUIDASCVDRiskIdentifier]:
    return identifier.type is IdentifierType.UUID and isinstance(identifier.value, UUID)
