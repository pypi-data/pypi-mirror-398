from pydantic import BaseModel, Field, model_validator
from typing import Annotated, Generic, Literal, Self, TypeVar, overload
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
from nexo.types.boolean import OptBool
from nexo.types.dict import StrToAnyDict
from nexo.types.integer import OptListOfInts
from nexo.types.string import OptStr, OptListOfStrs
from nexo.types.uuid import OptListOfUUIDs
from ..enums.parameter import (
    IdentifierType,
    ParameterGroup,
    OptParameterGroup,
    ValueType as ValueTypeEnum,
    OptValueType,
)
from ..mixins.parameter import (
    _validate_value_type_and_options,
    Group,
    Groups,
    IsMandatory,
    Name,
    Aliases,
    ValueType,
    ValueTypes,
    Options,
    IsNullable,
    Unit,
    Units,
    ParameterIdentifier,
)
from ..types.parameter import IdentifierValueType


class CreateParameter(
    Unit[OptStr],
    IsNullable[bool],
    Options[OptListOfStrs],
    ValueType[ValueTypeEnum],
    Aliases[OptListOfStrs],
    Name[str],
    Group[ParameterGroup],
    IsMandatory[bool],
):
    aliases: Annotated[
        OptListOfStrs, Field(None, description="Parameter's Aliases")
    ] = None
    options: Annotated[
        OptListOfStrs, Field(None, description="Parameter's value's options")
    ] = None
    unit: Annotated[
        OptStr, Field(None, description="Parameter's unit", max_length=30)
    ] = None

    @model_validator(mode="after")
    def validate_value_type_and_options(self) -> Self:
        _validate_value_type_and_options(self.value_type, self.options)
        return self


class ReadMultipleParameter(
    ReadPaginatedMultipleParameter,
    Units,
    IsNullable[OptBool],
    ValueTypes,
    Aliases[OptListOfStrs],
    Names[OptListOfStrs],
    IsMandatory[OptBool],
    Groups,
    UUIDs[OptListOfUUIDs],
    Ids[OptListOfInts],
):
    ids: Annotated[OptListOfInts, Field(None, description="Ids")] = None
    uuids: Annotated[OptListOfUUIDs, Field(None, description="UUIDs")] = None
    is_mandatory: Annotated[
        OptBool, Field(None, description="Whether is mandatory")
    ] = None
    names: Annotated[OptListOfStrs, Field(None, description="Names")] = None
    aliases: Annotated[
        OptListOfStrs, Field(None, description="Parameter's Aliases")
    ] = None
    is_nullable: Annotated[OptBool, Field(None, description="Whether is nullable")] = (
        None
    )

    @property
    def _query_param_fields(self) -> set[str]:
        return {
            "ids",
            "uuids",
            "statuses",
            "is_mandatory",
            "groups",
            "names",
            "aliases",
            "value_types",
            "is_nullable",
            "units",
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


class ReadSingleParameter(BaseReadSingleParameter[ParameterIdentifier]):
    @classmethod
    def from_identifier(
        cls,
        identifier: ParameterIdentifier,
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
            identifier=ParameterIdentifier(
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
    Unit[OptStr],
    IsNullable[bool],
    Options[OptListOfStrs],
    ValueType[ValueTypeEnum],
    Aliases[OptListOfStrs],
    Name[str],
    IsMandatory[bool],
    Group[ParameterGroup],
):
    @model_validator(mode="after")
    def validate_value_type_and_options(self) -> Self:
        _validate_value_type_and_options(self.value_type, self.options)
        return self


class PartialUpdateData(
    Unit[OptStr],
    IsNullable[OptBool],
    Options[OptListOfStrs],
    ValueType[OptValueType],
    Aliases[OptListOfStrs],
    Name[OptStr],
    IsMandatory[OptBool],
    Group[OptParameterGroup],
):
    group: Annotated[
        OptParameterGroup, Field(None, description="Parameter's group")
    ] = None
    is_mandatory: Annotated[
        OptBool, Field(None, description="Whether is mandatory")
    ] = None
    key: Annotated[
        OptStr, Field(None, description="Parameter's key", max_length=50)
    ] = None
    name: Annotated[
        OptStr, Field(None, description="Parameter's name", max_length=50)
    ] = None
    aliases: Annotated[
        OptListOfStrs, Field(None, description="Parameter's Aliases")
    ] = None
    value_type: Annotated[
        OptValueType, Field(None, description="Parameter's value type")
    ] = None
    options: Annotated[
        OptListOfStrs, Field(None, description="Parameter's value's options")
    ] = None
    is_nullable: Annotated[OptBool, Field(None, description="Whether is nullable")] = (
        None
    )
    unit: Annotated[
        OptStr, Field(None, description="Parameter's unit", max_length=30)
    ] = None


UpdateDataT = TypeVar("UpdateDataT", FullUpdateData, PartialUpdateData)


class UpdateDataMixin(BaseModel, Generic[UpdateDataT]):
    data: UpdateDataT = Field(..., description="Update data")


class UpdateParameter(
    UpdateDataMixin[UpdateDataT],
    IdentifierMixin[ParameterIdentifier],
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
            identifier=ParameterIdentifier(
                type=identifier_type, value=identifier_value
            ),
            data=data,
        )


class StatusUpdateParameter(
    BaseStatusUpdateParameter[ParameterIdentifier],
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
            identifier=ParameterIdentifier(
                type=identifier_type, value=identifier_value
            ),
            type=type,
        )


class DeleteSingleParameter(BaseDeleteSingleParameter[ParameterIdentifier]):
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
            identifier=ParameterIdentifier(type=identifier_type, value=identifier_value)
        )
