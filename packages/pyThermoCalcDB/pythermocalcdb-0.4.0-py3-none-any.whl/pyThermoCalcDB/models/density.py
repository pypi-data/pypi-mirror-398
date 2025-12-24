# import libs
from pydantic import BaseModel, Field
from typing import Optional
from pythermodb_settings.models import (
    Temperature,
    Pressure,
    CustomProp
)

# NOTE: Density model


class RackettDensityResult(BaseModel):
    density: CustomProp = Field(
        ...,
        description="Density of the substance"
    )
    molar_volume: CustomProp = Field(
        ...,
        description="Molar volume of the substance"
    )
    temperature: Temperature = Field(
        ...,
        description="Temperature at which density is measured"
    )
    critical_temperature: Temperature = Field(
        ...,
        description="Critical temperature of the substance"
    )
    critical_pressure: Pressure = Field(
        ...,
        description="Critical pressure of the substance"
    )
    critical_compressibility: CustomProp = Field(
        ...,
        description="Critical compressibility factor of the substance"
    )
    message: Optional[str] = Field(
        ...,
        description="Optional messages or warnings"
    )
