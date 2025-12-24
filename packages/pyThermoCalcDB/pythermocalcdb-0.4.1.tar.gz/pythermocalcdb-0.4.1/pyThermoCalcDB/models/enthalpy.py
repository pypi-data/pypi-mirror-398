# import libs
from pydantic import BaseModel, Field
from typing import Optional
from pythermodb_settings.models import Temperature, CustomProp

# NOTE: enthalpy NASA polynomial result model


class NASA9PolynomialIdealGasEnthalpyResult(BaseModel):
    """
    NASA Polynomial (NASA-9) Enthalpy Calculation Result Model
    Represents the result of ideal gas enthalpy calculation using NASA polynomial coefficients.

    Attributes
    ----------
    ideal_gas_enthalpy : CustomProp
        Ideal gas enthalpy calculated using NASA polynomial coefficients
    temperature : Temperature
        Temperature at which the enthalpy is calculated
    temperature_range : Optional[tuple[Temperature, Temperature]]
        Optional temperature range for validity check
    equation : str
        NASA-9 polynomial equation used for the calculation
    a1 : float
        NASA-9 polynomial coefficient a1
    a2 : float
        NASA-9 polynomial coefficient a2
    a3 : float
        NASA-9 polynomial coefficient a3
    a4 : float
        NASA-9 polynomial coefficient a4
    a5 : float
        NASA-9 polynomial coefficient a5
    a6 : float
        NASA-9 polynomial coefficient a6
    a7 : float
        NASA-9 polynomial coefficient a7
    b1 : float
        NASA-9 polynomial coefficient b1
    message : Optional[str]
        Optional message regarding the calculation
    """
    ideal_gas_enthalpy: CustomProp = Field(
        ...,
        description="Ideal gas enthalpy calculated using NASA polynomial coefficients"
    )
    temperature: Temperature = Field(
        ...,
        description="Temperature at which the enthalpy is calculated"
    )
    temperature_range: Optional[tuple[Temperature, Temperature]] = Field(
        None,
        description="Optional temperature range for validity check"
    )
    equation: str = Field(
        ...,
        description="NASA-9 polynomial equation used for the calculation"
    )
    a1: float = Field(
        ...,
        description="NASA-9 polynomial coefficient a1"
    )
    a2: float = Field(
        ...,
        description="NASA-9 polynomial coefficient a2"
    )
    a3: float = Field(
        ...,
        description="NASA-9 polynomial coefficient a3"
    )
    a4: float = Field(
        ...,
        description="NASA-9 polynomial coefficient a4"
    )
    a5: float = Field(
        ...,
        description="NASA-9 polynomial coefficient a5"
    )
    a6: float = Field(
        ...,
        description="NASA-9 polynomial coefficient a6"
    )
    a7: float = Field(
        ...,
        description="NASA-9 polynomial coefficient a7"
    )
    b1: float = Field(
        ...,
        description="NASA-9 polynomial coefficient b1"
    )
    message: Optional[str] = Field(
        None, description="Optional message regarding the calculation"
    )
