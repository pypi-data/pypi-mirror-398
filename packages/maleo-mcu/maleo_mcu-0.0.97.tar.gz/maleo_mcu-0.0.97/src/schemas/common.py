import json
from datetime import date
from pydantic import BaseModel, Field, model_validator
from typing import Annotated, Generic, Self, Type, TypeVar
from nexo.enums.identity import (
    OptRhesus,
    RhesusMixin,
    OptBloodType,
    BloodTypeMixin,
    Gender,
    GenderMixin,
)
from nexo.schemas.document import DocumentName, DocumentURL
from nexo.schemas.mixins.identity import (
    DataIdentifier,
    DateOfBirth,
)
from nexo.types.integer import OptInt
from nexo.types.string import OptStr, OptListOfStrs, ManyStrs
from ..enums.ascvd_risk import IdentifierType as ASCVDRiskIdentifierType
from ..enums.analysis import IdentifierType as AnalysisIdentifierType
from ..enums.checkup import (
    IdentifierType as CheckupIdentifierType,
    CheckupType as CheckupTypeEnum,
    OptCheckupType,
    CheckupStatus as CheckupStatusEnum,
)
from ..enums.client import IdentifierType as ClientIdentifierType
from ..enums.examination import (
    IdentifierType as ExaminationIdentifierType,
    OptExaminationStatus,
)
from ..enums.finding_parameter import Criteria as CriteriaEnum
from ..enums.finding import IdentifierType as FindingIdentifierType, Logic as LogicEnum
from ..enums.parameter import (
    IdentifierType as ParameterIdentifierType,
    ParameterGroup,
    ValueType as ValueTypeEnum,
)
from ..enums.patient import IdentifierType as PatientIdentifierType
from ..enums.rule import IdentifierType as RuleIdentifierType
from ..mixins.common import CheckupId, Recommendation
from ..mixins.ascvd_risk import (
    AgeRange,
    AgeRangeMixin,
    Diabetes,
    Smoker,
    TotalCholesterolRange,
    TotalCholesterolRangeMixin,
    SystolicBloodPressureRange,
    SystolicBloodPressureRangeMixin,
    Score,
)
from ..mixins.analysis import (
    Summary,
    SummaryMixin,
)
from ..mixins.checkup import (
    CheckupType,
    CheckupDate,
    CheckupStatus,
)
from ..mixins.client import Name as ClientName
from ..mixins.examination import (
    OrganExaminations,
    ExaminationStatus,
    Value,
    Unit as ExaminationUnit,
)
from ..mixins.finding_parameter import Criteria, Weight
from ..mixins.finding import (
    Name as FindingName,
    Aliases as FindingAliases,
    Recommendation as FindingRecommendation,
    Logic,
)
from ..mixins.parameter import (
    _validate_value_type_and_options,
    Group,
    IsMandatory,
    Name as ParameterName,
    Aliases,
    ValueType,
    Options,
    IsNullable,
    Unit as ParameterUnit,
)
from ..mixins.patient import IdCard, FullName, PlaceOfBirth
from ..mixins.rule import RuleData
from ..types.ascvd_risk import IdentifierValueType as ASCVDRiskIdentifierValueType
from ..types.analysis import IdentifierValueType as AnalysisIdentifierValueType
from ..types.checkup import IdentifierValueType as CheckupIdentifierValueType
from ..types.client import IdentifierValueType as ClientIdentifierValueType
from ..types.examination import IdentifierValueType as ExaminationIdentifierValueType
from ..types.finding import IdentifierValueType as FindingIdentifierValueType
from ..types.parameter import IdentifierValueType as ParameterIdentifierValueType
from ..types.patient import IdentifierValueType as PatientIdentifierValueType
from ..types.rule import IdentifierValueType as RuleIdentifierValueType


class ASCVDRiskSchema(
    Score[int],
    SystolicBloodPressureRangeMixin[SystolicBloodPressureRange],
    TotalCholesterolRangeMixin[TotalCholesterolRange],
    Smoker[bool],
    Diabetes[bool],
    AgeRangeMixin[AgeRange],
    GenderMixin[Gender],
    DataIdentifier,
):
    @property
    def _identifiers(
        self,
    ) -> tuple[tuple[ASCVDRiskIdentifierType, ASCVDRiskIdentifierValueType | str], ...]:
        return (
            (ASCVDRiskIdentifierType.ID, self.id),
            (ASCVDRiskIdentifierType.UUID, str(self.uuid)),
        )

    @property
    def cache_key_identifiers(self) -> ManyStrs:
        return tuple(
            '"identifier": '
            + json.dumps(
                {
                    "type": type.value,
                    "value": value,
                }
            )
            for type, value in self._identifiers
        )


ListOfASCVDRiskSchemas = list[ASCVDRiskSchema]


class ASCVDRiskSchemaMixin(BaseModel):
    ascvd_risk: Annotated[ASCVDRiskSchema, Field(..., description="ASCVD Risk")]


class SimpleASCVDRiskSchemaMixin(BaseModel):
    risk: Annotated[ASCVDRiskSchema, Field(..., description="ASCVD Risk")]


class ClientSchema(
    ClientName[str],
    DataIdentifier,
):
    @property
    def _identifiers(
        self,
    ) -> tuple[tuple[ClientIdentifierType, ClientIdentifierValueType | str], ...]:
        return (
            (ClientIdentifierType.ID, self.id),
            (ClientIdentifierType.UUID, str(self.uuid)),
        )

    @property
    def cache_key_identifiers(self) -> ManyStrs:
        return tuple(
            '"identifier": '
            + json.dumps(
                {
                    "type": type.value,
                    "value": value,
                }
            )
            for type, value in self._identifiers
        )


OptClientSchema = ClientSchema | None
OptClientSchemaT = TypeVar("OptClientSchemaT", bound=OptClientSchema)


class ClientSchemaMixin(BaseModel, Generic[OptClientSchemaT]):
    client: Annotated[OptClientSchemaT, Field(..., description="Client")]


class PatientSchema(
    RhesusMixin[OptRhesus],
    BloodTypeMixin[OptBloodType],
    GenderMixin[Gender],
    DateOfBirth[date],
    PlaceOfBirth[OptStr],
    FullName[str],
    IdCard[str],
    DataIdentifier,
):
    @property
    def _identifiers(
        self,
    ) -> tuple[tuple[PatientIdentifierType, PatientIdentifierValueType | str], ...]:
        return (
            (PatientIdentifierType.ID, self.id),
            (PatientIdentifierType.UUID, str(self.uuid)),
        )

    @property
    def cache_key_identifiers(self) -> ManyStrs:
        return tuple(
            '"identifier": '
            + json.dumps(
                {
                    "type": type.value,
                    "value": value,
                }
            )
            for type, value in self._identifiers
        )


class PatientSchemaMixin(BaseModel):
    patient: Annotated[PatientSchema, Field(..., description="Patient")]


class StandardParameterSchema(
    ParameterUnit[OptStr],
    IsNullable[bool],
    Options[OptListOfStrs],
    ValueType[ValueTypeEnum],
    Aliases[OptListOfStrs],
    ParameterName[str],
    Group[ParameterGroup],
    IsMandatory[bool],
    DataIdentifier,
):
    @model_validator(mode="after")
    def validate_value_type_and_options(self) -> Self:
        _validate_value_type_and_options(self.value_type, self.options)
        return self

    @property
    def _identifiers(
        self,
    ) -> tuple[tuple[ParameterIdentifierType, ParameterIdentifierValueType], ...]:
        return (
            (ParameterIdentifierType.ID, self.id),
            (ParameterIdentifierType.UUID, str(self.uuid)),
            (ParameterIdentifierType.NAME, self.name),
        )

    @property
    def cache_key_identifiers(self) -> ManyStrs:
        return tuple(
            '"identifier": '
            + json.dumps(
                {
                    "type": type.value,
                    "value": value,
                }
            )
            for type, value in self._identifiers
        )


OptStandardParameterSchema = StandardParameterSchema | None
ListOfStandardParameterSchemas = list[StandardParameterSchema]


class StandardParameterSchemaMixin(BaseModel):
    parameter: Annotated[StandardParameterSchema, Field(..., description="Parameter")]


class StandardRuleSchema(
    RuleData,
    DataIdentifier,
):
    @property
    def _identifiers(
        self,
    ) -> tuple[tuple[RuleIdentifierType, RuleIdentifierValueType | str], ...]:
        return (
            (RuleIdentifierType.ID, self.id),
            (RuleIdentifierType.UUID, str(self.uuid)),
        )

    @property
    def cache_key_identifiers(self) -> ManyStrs:
        return tuple(
            '"identifier": '
            + json.dumps(
                {
                    "type": type.value,
                    "value": value,
                }
            )
            for type, value in self._identifiers
        )


OptStandardRuleSchema = StandardRuleSchema | None
ListOfStandardRuleSchemas = list[StandardRuleSchema]


class StandardRuleSchemasMixin(BaseModel):
    rules: Annotated[
        ListOfStandardRuleSchemas,
        Field(ListOfStandardRuleSchemas(), description="Rules"),
    ] = ListOfStandardRuleSchemas()


class FullParameterSchema(
    StandardRuleSchemasMixin,
    StandardParameterSchema,
):
    @property
    def _identifiers(
        self,
    ) -> tuple[tuple[ParameterIdentifierType, ParameterIdentifierValueType], ...]:
        return (
            (ParameterIdentifierType.ID, self.id),
            (ParameterIdentifierType.UUID, str(self.uuid)),
            (ParameterIdentifierType.NAME, self.name),
        )

    @property
    def cache_key_identifiers(self) -> ManyStrs:
        return tuple(
            '"identifier": '
            + json.dumps(
                {
                    "type": type.value,
                    "value": value,
                }
            )
            for type, value in self._identifiers
        )


AnyParameterSchemaType = Type[StandardParameterSchema] | Type[FullParameterSchema]
AnyParameterSchema = StandardParameterSchema | FullParameterSchema
AnyParameterSchemaT = TypeVar("AnyParameterSchemaT", bound=AnyParameterSchema)
OptAnyParameterSchema = AnyParameterSchema | None
OptAnyParameterSchemaT = TypeVar("OptAnyParameterSchemaT", bound=OptAnyParameterSchema)


class ParameterSchemaMixin(BaseModel, Generic[OptAnyParameterSchemaT]):
    parameter: Annotated[OptAnyParameterSchemaT, Field(..., description="Parameter")]


class FullRuleSchema(
    RuleData,
    StandardParameterSchemaMixin,
    DataIdentifier,
):
    @property
    def _identifiers(
        self,
    ) -> tuple[tuple[RuleIdentifierType, RuleIdentifierValueType | str], ...]:
        return (
            (RuleIdentifierType.ID, self.id),
            (RuleIdentifierType.UUID, str(self.uuid)),
        )

    @property
    def cache_key_identifiers(self) -> ManyStrs:
        return tuple(
            '"identifier": '
            + json.dumps(
                {
                    "type": type.value,
                    "value": value,
                }
            )
            for type, value in self._identifiers
        )


AnyRuleSchemaType = Type[StandardRuleSchema] | Type[FullRuleSchema]
AnyRuleSchema = StandardRuleSchema | FullRuleSchema
AnyRuleSchemaT = TypeVar("AnyRuleSchemaT", bound=AnyRuleSchema)
OptAnyRuleSchema = AnyRuleSchema | None
OptAnyRuleSchemaT = TypeVar("OptAnyRuleSchemaT", bound=OptAnyRuleSchema)


class RuleSchemaMixin(BaseModel, Generic[OptAnyRuleSchemaT]):
    rule: Annotated[OptAnyRuleSchemaT, Field(..., description="Rule")]


class StandardFindingSchema(
    Logic[LogicEnum],
    FindingRecommendation[str],
    FindingAliases[OptListOfStrs],
    FindingName[str],
    DataIdentifier,
):
    @property
    def _identifiers(
        self,
    ) -> tuple[tuple[FindingIdentifierType, FindingIdentifierValueType], ...]:
        return (
            (FindingIdentifierType.ID, self.id),
            (FindingIdentifierType.UUID, str(self.uuid)),
            (FindingIdentifierType.NAME, self.name),
        )

    @property
    def cache_key_identifiers(self) -> ManyStrs:
        return tuple(
            '"identifier": '
            + json.dumps(
                {
                    "type": type.value,
                    "value": value,
                }
            )
            for type, value in self._identifiers
        )


ListOfStandardFindingSchemas = list[StandardFindingSchema]


class FindingParameterSchema(
    Weight[OptInt],
    Criteria[CriteriaEnum],
    StandardParameterSchemaMixin,
    DataIdentifier,
):
    pass


ListOfFindingParameterSchemas = list[FindingParameterSchema]


class FindingParameterSchemasMixin(BaseModel):
    parameters: Annotated[
        ListOfFindingParameterSchemas,
        Field(ListOfFindingParameterSchemas(), description="Finding Parameters"),
    ] = ListOfFindingParameterSchemas()


class FullFindingSchema(
    FindingParameterSchemasMixin,
    StandardFindingSchema,
):
    @property
    def _identifiers(
        self,
    ) -> tuple[tuple[FindingIdentifierType, FindingIdentifierValueType], ...]:
        return (
            (FindingIdentifierType.ID, self.id),
            (FindingIdentifierType.UUID, str(self.uuid)),
            (FindingIdentifierType.NAME, self.name),
        )

    @property
    def cache_key_identifiers(self) -> ManyStrs:
        return tuple(
            '"identifier": '
            + json.dumps(
                {
                    "type": type.value,
                    "value": value,
                }
            )
            for type, value in self._identifiers
        )


ListOfFullFindingSchemas = list[FullFindingSchema]


AnyFindingSchemaType = Type[StandardFindingSchema] | Type[FullFindingSchema]
AnyFindingSchema = StandardFindingSchema | FullFindingSchema
AnyFindingSchemaT = TypeVar("AnyFindingSchemaT", bound=AnyFindingSchema)
OptAnyFindingSchema = AnyFindingSchema | None
OptAnyFindingSchemaT = TypeVar("OptAnyFindingSchemaT", bound=OptAnyFindingSchema)


class FindingSchemaMixin(BaseModel, Generic[OptAnyFindingSchemaT]):
    finding: Annotated[OptAnyFindingSchemaT, Field(..., description="Finding")]


class LabExtractedExaminationData(BaseModel):
    parameter: Annotated[str, Field(..., description="Parameter's name")]
    value: Annotated[str, Field(..., description="Parameter's value")]
    unit: Annotated[str, Field(..., description="Parameter's unit")]


ListOfLabExtractedExaminationData = list[LabExtractedExaminationData]


class BareExaminationSchema(
    ExaminationUnit,
    Value,
    ParameterSchemaMixin[OptAnyParameterSchemaT],
    Generic[OptAnyParameterSchemaT],
):
    pass


class RawExaminationSchema(
    BareExaminationSchema[FullParameterSchema],
):
    pass


OptRawExaminationSchema = RawExaminationSchema | None
ListOfRawExaminationSchemas = list[RawExaminationSchema]


class BaseExaminationSchema(
    ExaminationStatus[OptExaminationStatus],
    BareExaminationSchema[StandardParameterSchema],
):
    pass


class StandardExaminationSchema(
    BaseExaminationSchema,
    CheckupId[int],
    DataIdentifier,
):
    @property
    def _identifiers(
        self,
    ) -> tuple[
        tuple[ExaminationIdentifierType, ExaminationIdentifierValueType | str], ...
    ]:
        return (
            (ExaminationIdentifierType.ID, self.id),
            (ExaminationIdentifierType.UUID, str(self.uuid)),
        )

    @property
    def cache_key_identifiers(self) -> ManyStrs:
        return tuple(
            '"identifier": '
            + json.dumps(
                {
                    "type": type.value,
                    "value": value,
                }
            )
            for type, value in self._identifiers
        )


ListOfStandardExaminationSchemas = list[StandardExaminationSchema]


class FullExaminationSchema(
    RuleSchemaMixin[OptStandardRuleSchema],
    StandardExaminationSchema,
):
    @property
    def _identifiers(
        self,
    ) -> tuple[
        tuple[ExaminationIdentifierType, ExaminationIdentifierValueType | str], ...
    ]:
        return (
            (ExaminationIdentifierType.ID, self.id),
            (ExaminationIdentifierType.UUID, str(self.uuid)),
        )

    @property
    def cache_key_identifiers(self) -> ManyStrs:
        return tuple(
            '"identifier": '
            + json.dumps(
                {
                    "type": type.value,
                    "value": value,
                }
            )
            for type, value in self._identifiers
        )


ListOfFullExaminationSchemas = list[FullExaminationSchema]


AnyExaminationSchemaType = Type[StandardExaminationSchema] | Type[FullExaminationSchema]
AnyExaminationSchema = StandardExaminationSchema | FullExaminationSchema
AnyExaminationSchemaT = TypeVar("AnyExaminationSchemaT", bound=AnyExaminationSchema)
OptAnyExaminationSchema = AnyExaminationSchema | None
OptAnyExaminationSchemaT = TypeVar(
    "OptAnyExaminationSchemaT", bound=OptAnyExaminationSchema
)


class AnalysisFindingSchema(
    Recommendation[str],
    FindingSchemaMixin[StandardFindingSchema],
    DataIdentifier,
):
    pass


ListOfAnalysisFindingSchemas = list[AnalysisFindingSchema]


class AnalysisFindingSchemasMixin(BaseModel):
    findings: Annotated[
        ListOfAnalysisFindingSchemas,
        Field(ListOfAnalysisFindingSchemas(), description="Findings"),
    ] = ListOfAnalysisFindingSchemas()


class AnalysisASCVDRiskSchema(
    Recommendation[str],
    ASCVDRiskSchemaMixin,
):
    pass


OptAnalysisASCVDRiskSchema = AnalysisASCVDRiskSchema | None


class AnalysisASCVDRiskSchemaMixin(BaseModel):
    ascvd_risk: Annotated[
        OptAnalysisASCVDRiskSchema, Field(None, description="ASCVD Risk")
    ] = None


class AnalysisSchema(
    SummaryMixin[Summary],
    AnalysisASCVDRiskSchemaMixin,
    AnalysisFindingSchemasMixin,
    OrganExaminations,
    CheckupId[int],
    DataIdentifier,
):
    @property
    def _identifiers(
        self,
    ) -> tuple[tuple[AnalysisIdentifierType, AnalysisIdentifierValueType | str], ...]:
        return (
            (AnalysisIdentifierType.ID, self.id),
            (AnalysisIdentifierType.UUID, str(self.uuid)),
            (AnalysisIdentifierType.CHECKUP_ID, self.checkup_id),
        )

    @property
    def cache_key_identifiers(self) -> ManyStrs:
        return tuple(
            '"identifier": '
            + json.dumps(
                {
                    "type": type.value,
                    "value": value,
                }
            )
            for type, value in self._identifiers
        )


class CheckupSchema(
    PatientSchemaMixin,
    DocumentURL[OptStr],
    DocumentName[OptStr],
    CheckupStatus[CheckupStatusEnum],
    CheckupDate[date],
    ClientSchemaMixin[OptClientSchema],
    CheckupType[OptCheckupType],
    DataIdentifier,
):
    document_name: Annotated[OptStr, Field(None, description="Document's name")] = None
    document_url: Annotated[OptStr, Field(None, description="Document's URL")] = None

    @model_validator(mode="after")
    def validate_type_client(self) -> Self:
        if self.type is not None:
            if self.type is CheckupTypeEnum.GROUP:
                if self.client is None:
                    raise ValueError("Client can not be None for Group Checkup")
            elif self.type is CheckupTypeEnum.INDIVIDUAL:
                if self.client is not None:
                    raise ValueError("Client must be None for Individual Checkup")
        return self

    @property
    def _identifiers(
        self,
    ) -> tuple[tuple[CheckupIdentifierType, CheckupIdentifierValueType | str], ...]:
        return (
            (CheckupIdentifierType.ID, self.id),
            (CheckupIdentifierType.UUID, str(self.uuid)),
        )

    @property
    def cache_key_identifiers(self) -> ManyStrs:
        return tuple(
            '"identifier": '
            + json.dumps(
                {
                    "type": type.value,
                    "value": value,
                }
            )
            for type, value in self._identifiers
        )
