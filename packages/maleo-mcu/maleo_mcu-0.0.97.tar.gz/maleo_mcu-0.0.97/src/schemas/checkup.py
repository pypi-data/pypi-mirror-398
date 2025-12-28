from pydantic import BaseModel, Field, computed_field, model_validator
from typing import Annotated, Generic, Literal, Self, TypeVar, overload
from uuid import UUID
from nexo.enums.identity import OptListOfGenders, GendersMixin
from nexo.enums.status import (
    ListOfDataStatuses,
    FULL_DATA_STATUSES,
)
from nexo.schemas.document import DocumentMixin, DocumentName
from nexo.schemas.error.enums import ErrorCode
from nexo.schemas.mixins.filter import convert as convert_filter
from nexo.schemas.mixins.identity import (
    IdentifierMixin,
    Ids,
    UUIDs,
    UUIDOrganizationId,
    UUIDOrganizationIds,
    PatientIds,
    UUIDUserId,
    UUIDUserIds,
)
from nexo.schemas.mixins.sort import convert as convert_sort
from nexo.schemas.operation.enums import ResourceOperationStatusUpdateType
from nexo.schemas.parameter import (
    ReadSingleParameter as BaseReadSingleParameter,
    ReadPaginatedMultipleParameter,
    StatusUpdateParameter as BaseStatusUpdateParameter,
    DeleteSingleParameter as BaseDeleteSingleParameter,
)
from nexo.schemas.security.authentication import (
    AnyAuthenticatedAuthentication,
    AuthenticationMixin,
)
from nexo.schemas.security.authorization import AnyAuthorization, AuthorizationMixin
from nexo.types.dict import StrToAnyDict
from nexo.types.integer import OptListOfInts
from nexo.types.string import OptStr
from nexo.types.uuid import OptUUID, ListOfUUIDs, OptListOfUUIDs
from ..enums.checkup import (
    IdentifierType,
    CheckupType as CheckupTypeEnum,
    CheckupStatus as CheckupStatusEnum,
    OptCheckupStatus,
    OptFeedback,
)
from ..mixins.common import IncludeURL, ClientId, ClientIds, ParameterIds
from ..mixins.checkup import (
    CheckupType,
    CheckupTypes,
    CheckupStatus,
    CheckupStatuses,
    CheckupIdentifier,
)
from ..types.checkup import IdentifierValueType
from .document import GroupedPatientData, OptGroupCSVDocument


class OperationtId(BaseModel):
    operation_id: Annotated[UUID, Field(..., description="Operation's ID")]


class RequestId(BaseModel):
    request_id: Annotated[UUID, Field(..., description="Request's ID")]


class CreateData(
    ParameterIds[ListOfUUIDs],
    ClientId[OptUUID],
    CheckupType[CheckupTypeEnum],
    UUIDOrganizationId[UUID],
    UUIDUserId[UUID],
):
    @model_validator(mode="after")
    def validate_type_and_client(self) -> Self:
        if self.type is CheckupTypeEnum.GROUP:
            if self.client_id is None:
                raise ValueError(
                    ErrorCode.BAD_REQUEST, "Client ID can not be None for Group Checkup"
                )
        elif self.type is CheckupTypeEnum.INDIVIDUAL:
            if self.client_id is not None:
                raise ValueError(
                    ErrorCode.BAD_REQUEST,
                    "Client ID must be None for Individual Checkup",
                )
        return self


class CreateParameter(
    DocumentMixin[OptGroupCSVDocument],
    PatientIds[OptListOfUUIDs],
    CreateData,
):
    @model_validator(mode="after")
    def validate_patient_ids_and_document(self) -> Self:
        if self.patient_ids is None and self.document is None:
            raise ValueError(
                ErrorCode.BAD_REQUEST, "Either patient_ids or document must be given"
            )
        return self

    @computed_field
    @property
    def patient_count(self) -> int:
        document_patient_count = (
            self.document.patient_count if self.document is not None else 0
        )
        manual_patient_count = (
            len(self.patient_ids) if self.patient_ids is not None else 0
        )
        patient_count = document_patient_count + manual_patient_count
        return patient_count


class CreateInitializationMessageData(
    DocumentName[OptStr],
    PatientIds[OptListOfUUIDs],
    CreateData,
    AuthorizationMixin[AnyAuthorization],
    AuthenticationMixin[AnyAuthenticatedAuthentication],
    RequestId,
    OperationtId,
):
    patient_count: Annotated[int, Field(..., description="Patient count", ge=1)]

    @model_validator(mode="after")
    def validate_patient_ids_and_document_name(self) -> Self:
        if self.patient_ids is None and self.document_name is None:
            raise ValueError(
                ErrorCode.BAD_REQUEST,
                "Either patient_ids or document_name must be given",
            )
        return self

    @classmethod
    def from_parameters(
        cls,
        operation_id: UUID,
        request_id: UUID,
        authentication: AnyAuthenticatedAuthentication,
        authorization: AnyAuthorization,
        parameters: CreateParameter,
        document_name: OptStr,
    ):
        return cls(
            operation_id=operation_id,
            request_id=request_id,
            authentication=authentication,
            authorization=authorization,
            **parameters.model_dump(exclude={"document"}),
            document_name=document_name,
        )


class PatientData(BaseModel):
    patient_data: Annotated[
        GroupedPatientData | UUID, Field(..., description="Patient's data")
    ]


class Current(BaseModel):
    current: Annotated[int, Field(0, description="Current data", ge=0)] = 0


class Total(BaseModel):
    total: Annotated[int, Field(0, description="Total data", ge=0)] = 0


class CreateIndividualMessageData(
    Total,
    Current,
    PatientData,
    DocumentName[OptStr],
    CreateData,
    AuthorizationMixin[AnyAuthorization],
    AuthenticationMixin[AnyAuthenticatedAuthentication],
    RequestId,
    OperationtId,
):
    @classmethod
    def from_initialization_data(
        cls,
        initialization_data: CreateInitializationMessageData,
        patient_data: GroupedPatientData | UUID,
        current: int = 0,
    ):
        return cls(
            **initialization_data.model_dump(exclude={"patient_ids", "patient_count"}),
            patient_data=patient_data,
            current=current,
            total=initialization_data.patient_count,
        )


class CreateResponseData(
    ClientId[OptUUID],
    CheckupType[CheckupTypeEnum],
):
    parameters: Annotated[int, Field(0, description="Parameters", ge=0)] = 0
    patients: Annotated[int, Field(0, description="Patients", ge=0)] = 0


class CreateEventData(
    Total,
    Current,
    UUIDOrganizationId[UUID],
    UUIDUserId[UUID],
    RequestId,
):
    pass


OptCreateEventData = CreateEventData | None


class ReadMultipleParameter(
    IncludeURL,
    ReadPaginatedMultipleParameter,
    GendersMixin[OptListOfGenders],
    PatientIds[OptListOfInts],
    CheckupStatuses,
    ClientIds[OptListOfInts],
    CheckupTypes,
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
    client_ids: Annotated[OptListOfInts, Field(None, description="Client's Ids")] = None
    patient_ids: Annotated[OptListOfInts, Field(None, description="Patient's IDs")] = (
        None
    )
    genders: Annotated[
        OptListOfGenders, Field(None, description="Patient's Genders")
    ] = None

    @property
    def _query_param_fields(self) -> set[str]:
        return {
            "ids",
            "uuids",
            "statuses",
            "user_ids",
            "organization_ids",
            "checkup_types",
            "client_ids",
            "checkup_statuses",
            "session_ids",
            "patient_ids",
            "genders" "search",
            "page",
            "limit",
            "use_cache",
            "include_url",
        }

    def to_query_params(self) -> StrToAnyDict:
        params = self.model_dump(
            mode="json", include=self._query_param_fields, exclude_none=True
        )
        params["filters"] = convert_filter(self.date_filters)
        params["sorts"] = convert_sort(self.sort_columns)
        params = {k: v for k, v in params.items()}
        return params


class ReadSingleParameter(IncludeURL, BaseReadSingleParameter[CheckupIdentifier]):
    @classmethod
    def from_identifier(
        cls,
        identifier: CheckupIdentifier,
        statuses: ListOfDataStatuses = FULL_DATA_STATUSES,
        use_cache: bool = True,
        include_url: bool = False,
    ) -> "ReadSingleParameter":
        return cls(
            identifier=identifier,
            statuses=statuses,
            use_cache=use_cache,
            include_url=include_url,
        )

    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.ID],
        identifier_value: int,
        statuses: ListOfDataStatuses = FULL_DATA_STATUSES,
        use_cache: bool = True,
        include_url: bool = False,
    ) -> "ReadSingleParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.UUID],
        identifier_value: UUID,
        statuses: ListOfDataStatuses = FULL_DATA_STATUSES,
        use_cache: bool = True,
        include_url: bool = False,
    ) -> "ReadSingleParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        statuses: ListOfDataStatuses = FULL_DATA_STATUSES,
        use_cache: bool = True,
        include_url: bool = False,
    ) -> "ReadSingleParameter": ...
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        statuses: ListOfDataStatuses = FULL_DATA_STATUSES,
        use_cache: bool = True,
        include_url: bool = False,
    ) -> "ReadSingleParameter":
        return cls(
            identifier=CheckupIdentifier(type=identifier_type, value=identifier_value),
            statuses=statuses,
            use_cache=use_cache,
            include_url=include_url,
        )

    def to_query_params(self) -> StrToAnyDict:
        return self.model_dump(
            mode="json",
            include={"statuses", "use_cache", "include_url"},
            exclude_none=True,
        )


class TransitionExamination(BaseModel):
    parameter_id: Annotated[UUID, Field(..., description="Parameter's ID")]
    value: Annotated[bool | float | int | str | None, Field(..., description="Value")]


ListOfTransitionExaminations = list[TransitionExamination]
OptListOfTransitionExaminations = ListOfTransitionExaminations | None


class BaseTransitionData(BaseModel):
    feedback: Annotated[OptFeedback, Field(None, description="Feedback")] = None


class TransitionData(BaseTransitionData):
    examinations: Annotated[
        OptListOfTransitionExaminations,
        Field(None, description="Transition examination"),
    ] = None


class FullUpdateData(TransitionData, CheckupStatus[CheckupStatusEnum]):
    pass


class PartialUpdateData(TransitionData, CheckupStatus[OptCheckupStatus]):
    checkup_status: Annotated[
        OptCheckupStatus, Field(None, description="Checkup's status")
    ] = None


UpdateDataT = TypeVar("UpdateDataT", FullUpdateData, PartialUpdateData)


class UpdateDataMixin(BaseModel, Generic[UpdateDataT]):
    data: UpdateDataT = Field(..., description="Update data")


class UpdateParameter(
    IncludeURL,
    UpdateDataMixin[UpdateDataT],
    IdentifierMixin[CheckupIdentifier],
    Generic[UpdateDataT],
):
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.ID],
        identifier_value: int,
        data: UpdateDataT,
        include_url: bool = False,
    ) -> "UpdateParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.UUID],
        identifier_value: UUID,
        data: UpdateDataT,
        include_url: bool = False,
    ) -> "UpdateParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        data: UpdateDataT,
        include_url: bool = False,
    ) -> "UpdateParameter": ...
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        data: UpdateDataT,
        include_url: bool = False,
    ) -> "UpdateParameter":
        return cls(
            identifier=CheckupIdentifier(type=identifier_type, value=identifier_value),
            data=data,
            include_url=include_url,
        )


class StatusUpdateParameter(
    IncludeURL,
    BaseStatusUpdateParameter[CheckupIdentifier],
):
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.ID],
        identifier_value: int,
        type: ResourceOperationStatusUpdateType,
        include_url: bool = False,
    ) -> "StatusUpdateParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.UUID],
        identifier_value: UUID,
        type: ResourceOperationStatusUpdateType,
        include_url: bool = False,
    ) -> "StatusUpdateParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        type: ResourceOperationStatusUpdateType,
        include_url: bool = False,
    ) -> "StatusUpdateParameter": ...
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        type: ResourceOperationStatusUpdateType,
        include_url: bool = False,
    ) -> "StatusUpdateParameter":
        return cls(
            identifier=CheckupIdentifier(type=identifier_type, value=identifier_value),
            type=type,
            include_url=include_url,
        )


class DeleteSingleParameter(BaseDeleteSingleParameter[CheckupIdentifier]):
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
            identifier=CheckupIdentifier(type=identifier_type, value=identifier_value)
        )
