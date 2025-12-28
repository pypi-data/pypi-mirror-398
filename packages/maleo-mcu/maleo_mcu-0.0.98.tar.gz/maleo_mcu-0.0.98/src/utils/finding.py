from typing import Literal, Type, overload
from ..schemas.common import (
    StandardFindingSchema,
    FullFindingSchema,
    AnyFindingSchemaType,
)
from ..enums.finding import Granularity


@overload
def get_schema_model(
    granularity: Literal[Granularity.STANDARD],
    /,
) -> Type[StandardFindingSchema]: ...
@overload
def get_schema_model(
    granularity: Literal[Granularity.FULL],
    /,
) -> Type[FullFindingSchema]: ...
@overload
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyFindingSchemaType: ...
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyFindingSchemaType:
    if granularity is Granularity.STANDARD:
        return StandardFindingSchema
    elif granularity is Granularity.FULL:
        return FullFindingSchema
