from typing import Literal, Type, overload
from ..schemas.common import (
    StandardExaminationSchema,
    FullExaminationSchema,
    AnyExaminationSchemaType,
)
from ..enums.examination import Granularity


@overload
def get_schema_model(
    granularity: Literal[Granularity.STANDARD],
    /,
) -> Type[StandardExaminationSchema]: ...
@overload
def get_schema_model(
    granularity: Literal[Granularity.FULL],
    /,
) -> Type[FullExaminationSchema]: ...
@overload
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyExaminationSchemaType: ...
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyExaminationSchemaType:
    if granularity is Granularity.STANDARD:
        return StandardExaminationSchema
    elif granularity is Granularity.FULL:
        return FullExaminationSchema
