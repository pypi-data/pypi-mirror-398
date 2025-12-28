from datetime import date
from pydantic import BaseModel, Field
from typing import Annotated, Generic, Literal, TypeVar, overload
from uuid import UUID
from nexo.enums.identity import (
    OptRhesus,
    RhesusMixin,
    OptListOfRhesuses,
    RhesusesMixin,
    OptBloodType,
    BloodTypeMixin,
    OptListOfBloodTypes,
    BloodTypesMixin,
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
from nexo.schemas.mixins.filter import convert as convert_filter
from nexo.schemas.mixins.identity import (
    IdentifierMixin,
    Ids,
    UUIDs,
    FullNames,
    UUIDOrganizationId,
    UUIDOrganizationIds,
    UUIDUserId,
    UUIDUserIds,
    DateOfBirth,
)
from nexo.schemas.mixins.sort import convert as convert_sort
from nexo.schemas.operation.enums import ResourceOperationStatusUpdateType
from nexo.schemas.parameter import (
    ReadSingleParameter as BaseReadSingleParameter,
    ReadPaginatedMultipleParameter,
    StatusUpdateParameter as BaseStatusUpdateParameter,
    DeleteSingleParameter as BaseDeleteSingleParameter,
)
from nexo.types.datetime import OptDate
from nexo.types.dict import StrToAnyDict
from nexo.types.integer import OptListOfInts
from nexo.types.string import OptStr, OptListOfStrs
from nexo.types.uuid import OptListOfUUIDs
from ..enums.patient import IdentifierType
from ..mixins.patient import IdCard, FullName, PlaceOfBirth, PatientIdentifier
from ..types.patient import IdentifierValueType


class CreateData(
    RhesusMixin[OptRhesus],
    BloodTypeMixin[OptBloodType],
    GenderMixin[Gender],
    DateOfBirth[date],
    PlaceOfBirth[OptStr],
    FullName[str],
    IdCard[str],
    UUIDOrganizationId[UUID],
):
    place_of_birth: Annotated[
        OptStr, Field(None, description="Place of Birth", max_length=50)
    ] = None
    blood_type: Annotated[OptBloodType, Field(None, description="Blood Type")] = None
    rhesus: Annotated[OptRhesus, Field(None, description="Rhesus")] = None


class CreateParameter(CreateData, UUIDUserId[UUID]):
    pass


class ReadMultipleParameter(
    ReadPaginatedMultipleParameter,
    RhesusesMixin[OptListOfRhesuses],
    BloodTypesMixin[OptListOfBloodTypes],
    GendersMixin[OptListOfGenders],
    FullNames[OptListOfStrs],
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
    full_names: Annotated[OptListOfStrs, Field(None, description="Full Names")] = None
    genders: Annotated[OptListOfGenders, Field(None, description="Genders")] = None
    blood_types: Annotated[
        OptListOfBloodTypes, Field(None, description="Blood Types")
    ] = None
    rhesuses: Annotated[OptListOfRhesuses, Field(None, description="Rhesuses")] = None
    excluded_ids: Annotated[OptListOfInts, Field(None, description="Excluded Ids")] = (
        None
    )
    excluded_uuids: Annotated[
        OptListOfUUIDs, Field(None, description="Excluded UUIDs")
    ] = None

    @property
    def _query_param_fields(self) -> set[str]:
        return {
            "ids",
            "uuids",
            "statuses",
            "user_ids",
            "organization_ids",
            "full_names",
            "genders",
            "blood_types",
            "rhesuses",
            "search",
            "page",
            "limit",
            "use_cache",
            "excluded_ids",
            "excluded_uuids",
        }

    def to_query_params(self) -> StrToAnyDict:
        params = self.model_dump(
            mode="json", include=self._query_param_fields, exclude_none=True
        )
        params["filters"] = convert_filter(self.date_filters)
        params["sorts"] = convert_sort(self.sort_columns)
        params = {k: v for k, v in params.items()}
        return params


class ReadSingleParameter(BaseReadSingleParameter[PatientIdentifier]):
    @classmethod
    def from_identifier(
        cls,
        identifier: PatientIdentifier,
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
        statuses: ListOfDataStatuses = list(FULL_DATA_STATUSES),
        use_cache: bool = True,
    ) -> "ReadSingleParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.UUID],
        identifier_value: UUID,
        statuses: ListOfDataStatuses = list(FULL_DATA_STATUSES),
        use_cache: bool = True,
    ) -> "ReadSingleParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        statuses: ListOfDataStatuses = list(FULL_DATA_STATUSES),
        use_cache: bool = True,
    ) -> "ReadSingleParameter": ...
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        statuses: ListOfDataStatuses = list(FULL_DATA_STATUSES),
        use_cache: bool = True,
    ) -> "ReadSingleParameter":
        return cls(
            identifier=PatientIdentifier(
                type=identifier_type,
                value=identifier_value,
            ),
            statuses=statuses,
            use_cache=use_cache,
        )

    def to_query_params(self) -> StrToAnyDict:
        return self.model_dump(
            mode="json", include={"statuses", "use_cache"}, exclude_none=True
        )


class FullUpdateData(
    RhesusMixin[OptRhesus],
    BloodTypeMixin[OptBloodType],
    GenderMixin[Gender],
    DateOfBirth[date],
    PlaceOfBirth[OptStr],
    FullName[str],
    IdCard[str],
):
    pass


class PartialUpdateData(
    RhesusMixin[OptRhesus],
    BloodTypeMixin[OptBloodType],
    GenderMixin[OptGender],
    DateOfBirth[OptDate],
    PlaceOfBirth[OptStr],
    FullName[OptStr],
    IdCard[OptStr],
):
    pass


UpdateDataT = TypeVar("UpdateDataT", FullUpdateData, PartialUpdateData)


class UpdateDataMixin(BaseModel, Generic[UpdateDataT]):
    data: UpdateDataT = Field(..., description="Update data")


class UpdateParameter(
    UpdateDataMixin[UpdateDataT],
    IdentifierMixin[PatientIdentifier],
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
            identifier=PatientIdentifier(type=identifier_type, value=identifier_value),
            data=data,
        )


class StatusUpdateParameter(
    BaseStatusUpdateParameter[PatientIdentifier],
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
            identifier=PatientIdentifier(type=identifier_type, value=identifier_value),
            type=type,
        )


class DeleteSingleParameter(BaseDeleteSingleParameter[PatientIdentifier]):
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
            identifier=PatientIdentifier(type=identifier_type, value=identifier_value)
        )
