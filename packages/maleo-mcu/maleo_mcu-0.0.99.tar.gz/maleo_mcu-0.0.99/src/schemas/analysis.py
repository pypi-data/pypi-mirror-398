from pydantic import BaseModel, Field
from typing import Annotated, Generic, Literal, TypeVar, overload
from uuid import UUID
from nexo.enums.status import (
    ListOfDataStatuses,
    FULL_DATA_STATUSES,
)
from nexo.schemas.mixins.filter import convert as convert_filter
from nexo.schemas.mixins.identity import (
    IdentifierMixin,
    Ids,
    UUIDs,
    UUIDOrganizationIds,
    UUIDUserIds,
)
from nexo.schemas.mixins.sort import convert as convert_sort
from nexo.schemas.operation.enums import ResourceOperationStatusUpdateType
from nexo.schemas.parameter import (
    ReadSingleParameter as BaseReadSingleParameter,
    ReadPaginatedMultipleParameter,
    StatusUpdateParameter as BaseStatusUpdateParameter,
)
from nexo.types.dict import StrToAnyDict
from nexo.types.integer import OptListOfInts
from nexo.types.string import OptStr, OptStrT
from nexo.types.uuid import OptListOfUUIDs
from ..enums.analysis import IdentifierType
from ..mixins.common import CheckupIds
from ..mixins.analysis import Summary, OptSummary, SummaryMixin, AnalysisIdentifier
from ..mixins.examination import OrganExaminations
from ..types.analysis import IdentifierValueType


class ReadMultipleParameter(
    ReadPaginatedMultipleParameter,
    CheckupIds[OptListOfInts],
    UUIDOrganizationIds[OptListOfUUIDs],
    UUIDUserIds[OptListOfUUIDs],
    UUIDs[OptListOfUUIDs],
    Ids[OptListOfInts],
):
    ids: Annotated[OptListOfInts, Field(None, description="Ids")] = None
    uuids: Annotated[OptListOfUUIDs, Field(None, description="UUIDs")] = None
    user_ids: Annotated[OptListOfUUIDs, Field(None, description="User's IDs")] = None
    organization_ids: Annotated[
        OptListOfUUIDs, Field(None, description="Organization's IDs")
    ] = None
    checkup_ids: Annotated[OptListOfInts, Field(None, description="Checkup's Ids")] = (
        None
    )

    @property
    def _query_param_fields(self) -> set[str]:
        return {
            "ids",
            "uuids",
            "statuses",
            "user_ids",
            "organization_ids",
            "checkup_ids",
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


class ReadSingleParameter(BaseReadSingleParameter[AnalysisIdentifier]):
    @classmethod
    def from_identifier(
        cls,
        identifier: AnalysisIdentifier,
        statuses: ListOfDataStatuses = FULL_DATA_STATUSES,
        use_cache: bool = True,
    ) -> "ReadSingleParameter":
        return cls(
            identifier=identifier,
            statuses=statuses,
            use_cache=use_cache,
        )

    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.ID, IdentifierType.CHECKUP_ID],
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
            identifier=AnalysisIdentifier(type=identifier_type, value=identifier_value),
            statuses=statuses,
            use_cache=use_cache,
        )

    def to_query_params(self) -> StrToAnyDict:
        return self.model_dump(
            mode="json",
            include={"statuses", "use_cache"},
            exclude_none=True,
        )


class UpdatedFinding(BaseModel):
    id: Annotated[int, Field(..., description="Finding's ID", ge=1)]
    recommendation: Annotated[str, Field(..., description="Recommendation")]


ListOfUpdatedFindings = list[UpdatedFinding]
OptListOfUpdatedFindings = ListOfUpdatedFindings | None


class UpdatedFindingsMixin(BaseModel):
    findings: Annotated[
        OptListOfUpdatedFindings,
        Field(None, description="Finding updates", min_length=1),
    ] = None


class ASCVDRecommendation(BaseModel, Generic[OptStrT]):
    ascvd_recommendation: Annotated[
        OptStrT, Field(..., description="ASCVD's Recommendation")
    ]


class FullUpdateData(
    SummaryMixin[Summary],
    ASCVDRecommendation[str],
    UpdatedFindingsMixin,
    OrganExaminations,
):
    pass


class PartialUpdateData(
    SummaryMixin[OptSummary],
    ASCVDRecommendation[OptStr],
    UpdatedFindingsMixin,
    OrganExaminations,
):
    ascvd_recommendation: Annotated[
        OptStr, Field(None, description="ASCVD's Recommendation")
    ] = None
    summary: Annotated[OptSummary, Field(None, description="Summary")] = None


UpdateDataT = TypeVar("UpdateDataT", FullUpdateData, PartialUpdateData)


class UpdateDataMixin(BaseModel, Generic[UpdateDataT]):
    data: UpdateDataT = Field(..., description="Update data")


class UpdateParameter(
    UpdateDataMixin[UpdateDataT],
    IdentifierMixin[AnalysisIdentifier],
    Generic[UpdateDataT],
):
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.ID, IdentifierType.CHECKUP_ID],
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
            identifier=AnalysisIdentifier(type=identifier_type, value=identifier_value),
            data=data,
        )


class StatusUpdateParameter(
    BaseStatusUpdateParameter[AnalysisIdentifier],
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
            identifier=AnalysisIdentifier(type=identifier_type, value=identifier_value),
            type=type,
        )
