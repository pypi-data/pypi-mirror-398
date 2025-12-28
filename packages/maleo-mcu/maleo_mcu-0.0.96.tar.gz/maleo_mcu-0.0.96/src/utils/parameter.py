from typing import Literal, Type, overload
from ..schemas.common import (
    StandardParameterSchema,
    FullParameterSchema,
    AnyParameterSchemaType,
)
from ..enums.parameter import Granularity


@overload
def get_schema_model(
    granularity: Literal[Granularity.STANDARD],
    /,
) -> Type[StandardParameterSchema]: ...
@overload
def get_schema_model(
    granularity: Literal[Granularity.FULL],
    /,
) -> Type[FullParameterSchema]: ...
@overload
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyParameterSchemaType: ...
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyParameterSchemaType:
    if granularity is Granularity.STANDARD:
        return StandardParameterSchema
    elif granularity is Granularity.FULL:
        return FullParameterSchema
