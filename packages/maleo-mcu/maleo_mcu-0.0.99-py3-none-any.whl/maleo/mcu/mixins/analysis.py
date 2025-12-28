from pydantic import BaseModel, Field
from typing import Annotated, Generic, Literal, TypeGuard, TypeVar
from uuid import UUID
from nexo.schemas.mixins.identity import Identifier
from nexo.types.string import ListOfStrs
from ..enums.analysis import IdentifierType
from ..types.analysis import IdentifierValueType


class Overview(BaseModel):
    overview: Annotated[str, Field(..., description="Orverview")]


class PriorityActions(BaseModel):
    priority_actions: Annotated[ListOfStrs, Field(..., description="Priority Actions")]


class NextSteps(BaseModel):
    next_steps: Annotated[str, Field(..., description="Next Steps")]


class Summary(NextSteps, PriorityActions, Overview):
    pass


DEFAULT_SUMMARY = Summary(
    overview="No Overview Yet", priority_actions=[], next_steps="No Next Steps"
)


OptSummary = Summary | None
OptSummaryT = TypeVar("OptSummaryT", bound=OptSummary)


class SummaryMixin(BaseModel, Generic[OptSummaryT]):
    summary: Annotated[OptSummaryT, Field(..., description="Summary")]


class AnalysisIdentifier(Identifier[IdentifierType, IdentifierValueType]):
    @property
    def column_and_value(self) -> tuple[str, IdentifierValueType]:
        return self.type.column, self.value


class IdAnalysisIdentifier(Identifier[Literal[IdentifierType.ID], int]):
    type: Annotated[
        Literal[IdentifierType.ID],
        Field(IdentifierType.ID, description="Identifier's type"),
    ] = IdentifierType.ID
    value: Annotated[int, Field(..., description="Identifier's value", ge=1)]


class UUIDAnalysisIdentifier(Identifier[Literal[IdentifierType.UUID], UUID]):
    type: Annotated[
        Literal[IdentifierType.UUID],
        Field(IdentifierType.UUID, description="Identifier's type"),
    ] = IdentifierType.UUID


class CheckupIdAnalysisIdentifier(Identifier[Literal[IdentifierType.CHECKUP_ID], int]):
    type: Annotated[
        Literal[IdentifierType.CHECKUP_ID],
        Field(IdentifierType.CHECKUP_ID, description="Identifier's type"),
    ] = IdentifierType.CHECKUP_ID
    value: Annotated[int, Field(..., description="Identifier's value", ge=1)]


AnyAnalysisIdentifier = (
    AnalysisIdentifier
    | IdAnalysisIdentifier
    | UUIDAnalysisIdentifier
    | CheckupIdAnalysisIdentifier
)


def is_id_identifier(
    identifier: AnyAnalysisIdentifier,
) -> TypeGuard[IdAnalysisIdentifier]:
    return identifier.type is IdentifierType.ID and isinstance(identifier.value, int)


def is_uuid_identifier(
    identifier: AnyAnalysisIdentifier,
) -> TypeGuard[UUIDAnalysisIdentifier]:
    return identifier.type is IdentifierType.UUID and isinstance(identifier.value, UUID)


def is_checkup_id_identifier(
    identifier: AnyAnalysisIdentifier,
) -> TypeGuard[CheckupIdAnalysisIdentifier]:
    return identifier.type is IdentifierType.CHECKUP_ID and isinstance(
        identifier.value, int
    )
