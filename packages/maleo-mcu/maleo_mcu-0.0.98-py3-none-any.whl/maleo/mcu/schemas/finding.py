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
    Names,
)
from nexo.schemas.mixins.sort import convert as convert_sort
from nexo.schemas.operation.enums import ResourceOperationStatusUpdateType
from nexo.schemas.parameter import (
    ReadSingleParameter as BaseReadSingleParameter,
    ReadPaginatedMultipleParameter,
    StatusUpdateParameter as BaseStatusUpdateParameter,
    DeleteSingleParameter as BaseDeleteSingleParameter,
)
from nexo.types.dict import StrToAnyDict
from nexo.types.integer import OptListOfInts
from nexo.types.string import OptStr, OptListOfStrs
from nexo.types.uuid import OptListOfUUIDs
from ..enums.finding import IdentifierType, Logic as LogicEnum, OptLogic
from ..mixins.finding import (
    Name,
    Aliases,
    Recommendation,
    Logic,
    Logics,
    FindingIdentifier,
)
from ..types.finding import IdentifierValueType


class CreateParameter(
    Logic[LogicEnum],
    Recommendation[str],
    Aliases[OptListOfStrs],
    Name[str],
):
    aliases: Annotated[OptListOfStrs, Field(None, description="Finding's Aliases")] = (
        None
    )


class ReadMultipleParameter(
    ReadPaginatedMultipleParameter,
    Logics,
    Aliases[OptListOfStrs],
    Names[OptListOfStrs],
    UUIDs[OptListOfUUIDs],
    Ids[OptListOfInts],
):
    ids: Annotated[OptListOfInts, Field(None, description="Ids")] = None
    uuids: Annotated[OptListOfUUIDs, Field(None, description="UUIDs")] = None
    names: Annotated[OptListOfStrs, Field(None, description="Names")] = None
    aliases: Annotated[OptListOfStrs, Field(None, description="Finding's Aliases")] = (
        None
    )

    @property
    def _query_param_fields(self) -> set[str]:
        return {
            "ids",
            "uuids",
            "statuses",
            "names",
            "aliases",
            "logic",
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


class ReadSingleParameter(BaseReadSingleParameter[FindingIdentifier]):
    @classmethod
    def from_identifier(
        cls,
        identifier: FindingIdentifier,
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
        identifier_type: Literal[IdentifierType.NAME],
        identifier_value: str,
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
            identifier=FindingIdentifier(type=identifier_type, value=identifier_value),
            statuses=statuses,
            use_cache=use_cache,
        )

    def to_query_params(self) -> StrToAnyDict:
        return self.model_dump(
            mode="json", include={"statuses", "use_cache"}, exclude_none=True
        )


class FullUpdateData(
    Logic[LogicEnum],
    Recommendation[str],
    Aliases[OptListOfStrs],
    Name[str],
):
    pass


class PartialUpdateData(
    Logic[OptLogic],
    Recommendation[OptStr],
    Aliases[OptListOfStrs],
    Name[OptStr],
):
    name: Annotated[
        OptStr, Field(None, description="Finding's name", max_length=50)
    ] = None
    aliases: Annotated[OptListOfStrs, Field(None, description="Finding's Aliases")] = (
        None
    )
    recommendation: Annotated[
        OptStr, Field(None, description="Finding's recommendation")
    ] = None
    logic: Annotated[OptLogic, Field(None, description="Finding's logic")] = None


UpdateDataT = TypeVar("UpdateDataT", FullUpdateData, PartialUpdateData)


class UpdateDataMixin(BaseModel, Generic[UpdateDataT]):
    data: UpdateDataT = Field(..., description="Update data")


class UpdateParameter(
    UpdateDataMixin[UpdateDataT],
    IdentifierMixin[FindingIdentifier],
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
        identifier_type: Literal[IdentifierType.NAME],
        identifier_value: str,
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
            identifier=FindingIdentifier(type=identifier_type, value=identifier_value),
            data=data,
        )


class StatusUpdateParameter(
    BaseStatusUpdateParameter[FindingIdentifier],
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
        identifier_type: Literal[IdentifierType.NAME],
        identifier_value: str,
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
            identifier=FindingIdentifier(type=identifier_type, value=identifier_value),
            type=type,
        )


class DeleteSingleParameter(BaseDeleteSingleParameter[FindingIdentifier]):
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
        cls,
        identifier_type: Literal[IdentifierType.NAME],
        identifier_value: str,
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
            identifier=FindingIdentifier(type=identifier_type, value=identifier_value)
        )
