# import libs
from pydantic import BaseModel, Field
from typing import Optional, Literal
from pythermodb_settings.models import Temperature, Pressure
import pycuc


# NOTE: Antoine Calculation Result Model
class AntoineVaporPressureResult(BaseModel):
    """
    Model to represent the result of vapor pressure calculation using the Antoine equation.

    Attributes
    ----------
    A : float
        Antoine equation constant A
    B : float
        Antoine equation constant B
    C : float
        Antoine equation constant C
    base : Literal['log10', 'ln']
        Logarithmic base used in the Antoine equation ('log10' or 'ln')
    temperature : Temperature
        Temperature at which to calculate vapor pressure
    pressure : Pressure
        Calculated vapor pressure
    """
    A: float = Field(..., description="Antoine equation constant A")
    B: float = Field(..., description="Antoine equation constant B")
    C: float = Field(..., description="Antoine equation constant C")
    base: Literal['log10', 'ln'] = Field(
        'log10', description="Logarithmic base used in the Antoine equation ('log10' or 'ln')"
    )
    temperature: Temperature = Field(
        ...,
        description="Temperature at which to calculate vapor pressure"
    )
    pressure: Pressure = Field(
        ...,
        description="Calculated vapor pressure"
    )
    message: Optional[str] = Field(
        None, description="Optional message regarding the calculation"
    )


# NOTE: Wagner Calculation Result Model
class WagnerVaporPressureResult(BaseModel):
    """
    Model to represent the result of vapor pressure calculation using the Wagner equation.

    Attributes
    ----------
    A : float
        Wagner equation constant A
    B : float
        Wagner equation constant B
    C : float
        Wagner equation constant C
    D : float
        Wagner equation constant D
    critical_temperature : Temperature
        Critical temperature of the substance
    critical_pressure : Pressure
        Critical pressure of the substance
    temperature : Temperature
        Temperature at which to calculate vapor pressure
    pressure : Pressure
        Calculated vapor pressure
    """
    A: float = Field(..., description="Wagner equation constant A")
    B: float = Field(..., description="Wagner equation constant B")
    C: float = Field(..., description="Wagner equation constant C")
    D: float = Field(..., description="Wagner equation constant D")
    critical_temperature: Temperature = Field(
        ..., description="Critical temperature of the substance"
    )
    critical_pressure: Pressure = Field(
        ..., description="Critical pressure of the substance"
    )
    temperature: Temperature = Field(
        ...,
        description="Temperature at which to calculate vapor pressure"
    )
    pressure: Pressure = Field(
        ...,
        description="Calculated vapor pressure"
    )
    message: Optional[str] = Field(
        None, description="Optional message regarding the calculation"
    )
