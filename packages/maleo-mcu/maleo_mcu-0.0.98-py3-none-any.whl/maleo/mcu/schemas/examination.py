from pydantic import Field
from typing import Annotated, Literal, overload
from uuid import UUID
from nexo.enums.status import (
    ListOfDataStatuses,
    FULL_DATA_STATUSES,
)
from nexo.schemas.mixins.filter import convert as convert_filter
from nexo.schemas.mixins.identity import (
    Ids,
    UUIDs,
    UUIDOrganizationIds,
    UUIDUserIds,
)
from nexo.schemas.mixins.sort import convert as convert_sort
from nexo.schemas.parameter import (
    ReadSingleParameter as BaseReadSingleParameter,
    ReadPaginatedMultipleParameter,
)
from nexo.types.dict import StrToAnyDict
from nexo.types.integer import OptListOfInts
from nexo.types.uuid import OptListOfUUIDs
from ..enums.examination import IdentifierType
from ..mixins.common import CheckupIds, ParameterIds
from ..mixins.examination import (
    ExaminationStatuses,
    ExaminationIdentifier,
)
from ..types.examination import IdentifierValueType


class ReadMultipleParameter(
    ReadPaginatedMultipleParameter,
    ExaminationStatuses,
    ParameterIds[OptListOfInts],
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
    parameter_ids: Annotated[
        OptListOfInts, Field(None, description="Parameter's Ids")
    ] = None

    @property
    def _query_param_fields(self) -> set[str]:
        return {
            "ids",
            "uuids",
            "statuses",
            "user_ids",
            "organization_ids",
            "checkup_ids",
            "parameter_ids",
            "examination_statuses",
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


class ReadSingleParameter(BaseReadSingleParameter[ExaminationIdentifier]):
    @classmethod
    def from_identifier(
        cls,
        identifier: ExaminationIdentifier,
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
            identifier=ExaminationIdentifier(
                type=identifier_type, value=identifier_value
            ),
            statuses=statuses,
            use_cache=use_cache,
        )

    def to_query_params(self) -> StrToAnyDict:
        return self.model_dump(
            mode="json",
            include={"statuses", "use_cache"},
            exclude_none=True,
        )
