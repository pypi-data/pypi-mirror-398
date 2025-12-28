from pydantic import BaseModel, Field
from typing import Annotated, Generic, Literal, Self, TypeVar, overload
from uuid import UUID
from nexo.enums.identity import (
    Gender,
    OptGender,
    GenderMixin,
    OptListOfGenders,
    GendersMixin,
)
from nexo.enums.status import (
    ListOfDataStatuses,
    FULL_DATA_STATUSES,
)
from nexo.schemas.mixins.filter import ListOfDateFilters, convert as convert_filter
from nexo.schemas.mixins.identity import IdentifierMixin, Ids, UUIDs
from nexo.schemas.mixins.sort import ListOfSortColumns, convert as convert_sort
from nexo.schemas.operation.enums import ResourceOperationStatusUpdateType
from nexo.schemas.pagination import Limit
from nexo.schemas.parameter import (
    ReadSingleParameter as BaseReadSingleParameter,
    ReadPaginatedMultipleParameter,
    StatusUpdateParameter as BaseStatusUpdateParameter,
    DeleteSingleParameter as BaseDeleteSingleParameter,
)
from nexo.types.boolean import OptBool
from nexo.types.dict import StrToAnyDict
from nexo.types.integer import OptInt, OptListOfInts
from nexo.types.string import OptStr
from nexo.types.uuid import OptListOfUUIDs
from ..enums.ascvd_risk import IdentifierType
from ..mixins.ascvd_risk import (
    AgeRange,
    OptAgeRange,
    AgeRangeMixin,
    Diabetes,
    Smoker,
    TotalCholesterolRange,
    OptTotalCholesterolRange,
    TotalCholesterolRangeMixin,
    SystolicBloodPressureRange,
    OptSystolicBloodPressureRange,
    SystolicBloodPressureRangeMixin,
    Score,
    ASCVDRiskIdentifier,
)
from ..types.ascvd_risk import IdentifierValueType


class CreateParameter(
    Score[int],
    SystolicBloodPressureRangeMixin[SystolicBloodPressureRange],
    TotalCholesterolRangeMixin[TotalCholesterolRange],
    Smoker[bool],
    Diabetes[bool],
    AgeRangeMixin[AgeRange],
    GenderMixin[Gender],
):
    pass


class ReadMultipleParameter(
    ReadPaginatedMultipleParameter,
    Smoker[OptBool],
    Diabetes[OptBool],
    GendersMixin[OptListOfGenders],
    UUIDs[OptListOfUUIDs],
    Ids[OptListOfInts],
):
    ids: Annotated[OptListOfInts, Field(None, description="Ids")] = None
    uuids: Annotated[OptListOfUUIDs, Field(None, description="UUIDs")] = None
    genders: Annotated[OptListOfGenders, Field(None, description="Genders")] = None
    diabetes: Annotated[OptBool, Field(None, description="Diabetes")] = None
    smoker: Annotated[OptBool, Field(None, description="Smoker")] = None

    @classmethod
    def new(
        cls,
        ids: OptListOfInts = None,
        uuids: OptListOfUUIDs = None,
        date_filters: ListOfDateFilters = ListOfDateFilters(),
        statuses: ListOfDataStatuses = FULL_DATA_STATUSES,
        genders: OptListOfGenders = None,
        diabetes: OptBool = None,
        smoker: OptBool = None,
        search: OptStr = None,
        sort_columns: ListOfSortColumns = ListOfSortColumns(),
        page: int = 1,
        limit: Limit = Limit.LIM_10,
        use_cache: bool = True,
    ) -> Self:
        return cls(
            ids=ids,
            uuids=uuids,
            date_filters=date_filters,
            statuses=statuses,
            genders=genders,
            diabetes=diabetes,
            smoker=smoker,
            search=search,
            sort_columns=sort_columns,
            page=page,
            limit=limit,
            use_cache=use_cache,
        )

    @property
    def _query_param_fields(self) -> set[str]:
        return {
            "ids",
            "uuids",
            "statuses",
            "genders",
            "diabetes",
            "smoker",
            "search",
            "page",
            "limit",
            "use_cache",
        }

    def to_query_params(self) -> StrToAnyDict:
        params = self.model_dump(
            mode="json", include=self._query_param_fields, exclude_none=True
        )
        params["filters"] = convert_filter(self.date_filters)
        params["sorts"] = convert_sort(self.sort_columns)
        params = {k: v for k, v in params.items()}
        return params


class ReadSingleParameter(BaseReadSingleParameter[ASCVDRiskIdentifier]):
    @classmethod
    def from_identifier(
        cls,
        identifier: ASCVDRiskIdentifier,
        statuses: ListOfDataStatuses = FULL_DATA_STATUSES,
        use_cache: bool = True,
    ) -> "ReadSingleParameter":
        return cls(identifier=identifier, statuses=statuses, use_cache=use_cache)

    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.ID],
        identifier_value: int,
        statuses: ListOfDataStatuses = FULL_DATA_STATUSES,
        use_cache: bool = True,
    ) -> "ReadSingleParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.UUID],
        identifier_value: UUID,
        statuses: ListOfDataStatuses = FULL_DATA_STATUSES,
        use_cache: bool = True,
    ) -> "ReadSingleParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        statuses: ListOfDataStatuses = FULL_DATA_STATUSES,
        use_cache: bool = True,
    ) -> "ReadSingleParameter": ...
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        statuses: ListOfDataStatuses = FULL_DATA_STATUSES,
        use_cache: bool = True,
    ) -> "ReadSingleParameter":
        return cls(
            identifier=ASCVDRiskIdentifier(
                type=identifier_type, value=identifier_value
            ),
            statuses=statuses,
            use_cache=use_cache,
        )

    def to_query_params(self) -> StrToAnyDict:
        return self.model_dump(
            mode="json", include={"statuses", "use_cache"}, exclude_none=True
        )


class FullUpdateData(
    Score[int],
    SystolicBloodPressureRangeMixin[SystolicBloodPressureRange],
    TotalCholesterolRangeMixin[TotalCholesterolRange],
    Smoker[bool],
    Diabetes[bool],
    AgeRangeMixin[AgeRange],
    GenderMixin[Gender],
):
    pass


class PartialUpdateData(
    Score[OptInt],
    SystolicBloodPressureRangeMixin[OptSystolicBloodPressureRange],
    TotalCholesterolRangeMixin[OptTotalCholesterolRange],
    Smoker[OptBool],
    Diabetes[OptBool],
    AgeRangeMixin[OptAgeRange],
    GenderMixin[OptGender],
):
    gender: Annotated[OptGender, Field(None, description="Gender")] = None
    age: Annotated[OptAgeRange, Field(None, description="Age range")] = None
    diabetes: Annotated[OptBool, Field(None, description="Diabetes")] = None
    smoker: Annotated[OptBool, Field(None, description="Smoker")] = None
    total_cholesterol: Annotated[
        OptTotalCholesterolRange, Field(None, description="Total Cholesterol range")
    ] = None
    systolic_blood_pressure: Annotated[
        OptSystolicBloodPressureRange,
        Field(None, description="Systolic Blood Pressure range"),
    ] = None
    score: Annotated[OptInt, Field(None, description="Score", ge=1, le=59)] = None


UpdateDataT = TypeVar("UpdateDataT", FullUpdateData, PartialUpdateData)


class UpdateDataMixin(BaseModel, Generic[UpdateDataT]):
    data: UpdateDataT = Field(..., description="Update data")


class UpdateParameter(
    UpdateDataMixin[UpdateDataT],
    IdentifierMixin[ASCVDRiskIdentifier],
    Generic[UpdateDataT],
):
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.ID],
        identifier_value: int,
        data: UpdateDataT,
    ) -> "UpdateParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.UUID],
        identifier_value: UUID,
        data: UpdateDataT,
    ) -> "UpdateParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        data: UpdateDataT,
    ) -> "UpdateParameter": ...
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        data: UpdateDataT,
    ) -> "UpdateParameter":
        return cls(
            identifier=ASCVDRiskIdentifier(
                type=identifier_type, value=identifier_value
            ),
            data=data,
        )


class StatusUpdateParameter(
    BaseStatusUpdateParameter[ASCVDRiskIdentifier],
):
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.ID],
        identifier_value: int,
        type: ResourceOperationStatusUpdateType,
    ) -> "StatusUpdateParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.UUID],
        identifier_value: UUID,
        type: ResourceOperationStatusUpdateType,
    ) -> "StatusUpdateParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        type: ResourceOperationStatusUpdateType,
    ) -> "StatusUpdateParameter": ...
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        type: ResourceOperationStatusUpdateType,
    ) -> "StatusUpdateParameter":
        return cls(
            identifier=ASCVDRiskIdentifier(
                type=identifier_type, value=identifier_value
            ),
            type=type,
        )


class DeleteSingleParameter(BaseDeleteSingleParameter[ASCVDRiskIdentifier]):
    @overload
    @classmethod
    def new(
        cls, identifier_type: Literal[IdentifierType.ID], identifier_value: int
    ) -> "DeleteSingleParameter": ...
    @overload
    @classmethod
    def new(
        cls, identifier_type: Literal[IdentifierType.UUID], identifier_value: UUID
    ) -> "DeleteSingleParameter": ...
    @overload
    @classmethod
    def new(
        cls, identifier_type: IdentifierType, identifier_value: IdentifierValueType
    ) -> "DeleteSingleParameter": ...
    @classmethod
    def new(
        cls, identifier_type: IdentifierType, identifier_value: IdentifierValueType
    ) -> "DeleteSingleParameter":
        return cls(
            identifier=ASCVDRiskIdentifier(type=identifier_type, value=identifier_value)
        )
