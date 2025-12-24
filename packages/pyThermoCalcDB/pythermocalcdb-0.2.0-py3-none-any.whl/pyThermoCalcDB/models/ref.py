# import libs
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# NOTE: calc result


class CalcResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    value: float = Field(
        ...,
        description="Calculated value"
    )
    unit: str = Field(
        ...,
        description="Unit of the calculated value"
    )
    symbol: str = Field(
        ...,
        description="Symbol representing the calculated property"
    )
