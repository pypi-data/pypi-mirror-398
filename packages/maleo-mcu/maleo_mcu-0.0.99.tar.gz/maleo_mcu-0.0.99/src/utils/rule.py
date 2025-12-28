from typing import Literal, Type, overload
from ..schemas.common import (
    StandardRuleSchema,
    FullRuleSchema,
    AnyRuleSchemaType,
)
from ..enums.rule import Granularity


@overload
def get_schema_model(
    granularity: Literal[Granularity.STANDARD],
    /,
) -> Type[StandardRuleSchema]: ...
@overload
def get_schema_model(
    granularity: Literal[Granularity.FULL],
    /,
) -> Type[FullRuleSchema]: ...
@overload
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyRuleSchemaType: ...
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyRuleSchemaType:
    if granularity is Granularity.STANDARD:
        return StandardRuleSchema
    elif granularity is Granularity.FULL:
        return FullRuleSchema
