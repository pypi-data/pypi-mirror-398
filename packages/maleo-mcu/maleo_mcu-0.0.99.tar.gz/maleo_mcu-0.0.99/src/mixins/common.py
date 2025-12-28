from pydantic import BaseModel, Field
from typing import Annotated, Generic
from nexo.types.integer import OptIntT, OptListOfIntsT
from nexo.types.misc import (
    OptIntOrUUIDT,
    OptListOfIntsOrUUIDsT,
)
from nexo.types.string import OptStrT


class IncludeURL(BaseModel):
    include_url: Annotated[bool, Field(False, description="Whether to include URL")] = (
        False
    )


class CheckupId(BaseModel, Generic[OptIntT]):
    checkup_id: Annotated[OptIntT, Field(..., description="Checkup's Id")]


class CheckupIds(BaseModel, Generic[OptListOfIntsT]):
    checkup_ids: Annotated[OptListOfIntsT, Field(..., description="Checkup's Ids")]


class ClientId(BaseModel, Generic[OptIntOrUUIDT]):
    client_id: Annotated[OptIntOrUUIDT, Field(..., description="Client's Id")]


class ClientIds(BaseModel, Generic[OptListOfIntsOrUUIDsT]):
    client_ids: Annotated[OptListOfIntsOrUUIDsT, Field(..., description="Client's Ids")]


class ParameterIds(BaseModel, Generic[OptListOfIntsOrUUIDsT]):
    parameter_ids: Annotated[
        OptListOfIntsOrUUIDsT, Field(..., description="Parameter's Ids")
    ]


class Recommendation(BaseModel, Generic[OptStrT]):
    recommendation: Annotated[OptStrT, Field(..., description="Recommendation")]
