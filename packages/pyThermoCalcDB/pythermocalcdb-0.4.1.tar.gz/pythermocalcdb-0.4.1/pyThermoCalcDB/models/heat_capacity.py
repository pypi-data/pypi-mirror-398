# import libs
from pydantic import BaseModel, Field
from typing import Optional
from pythermodb_settings.models import Temperature, CustomProp


class PolynomialCpIGResult(BaseModel):
    """
    Polynomial Heat Capacity Calculation Result Model
    Represents the result of ideal gas heat capacity calculation using a polynomial equation.

    Attributes
    ----------
    ideal_gas_heat_capacity_at_constant_pressure : CustomProp
        Ideal gas heat capacity at constant pressure calculated using polynomial equation
    temperature : Temperature
        Temperature at which the heat capacity is calculated
    temperature_range : Optional[tuple[Temperature, Temperature]]
        Optional temperature range for validity check
    equation : str
        Polynomial equation used for the calculation
    A : float
        Polynomial coefficient A
    B : float
        Polynomial coefficient B
    C : float
        Polynomial coefficient C
    D : float
        Polynomial coefficient D
    message : Optional[str]
        Optional message regarding the calculation
    """
    ideal_gas_heat_capacity_at_constant_pressure: CustomProp = Field(
        ...,
        description="Ideal gas heat capacity at constant pressure calculated using polynomial equation"
    )
    temperature: Temperature = Field(
        ...,
        description="Temperature at which the heat capacity is calculated"
    )
    temperature_range: Optional[tuple[Temperature, Temperature]] = Field(
        None,
        description="Optional temperature range for validity check"
    )
    equation: str = Field(
        ...,
        description="Polynomial equation used for the calculation"
    )
    A: float = Field(
        ...,
        description="Polynomial coefficient A"
    )
    B: float = Field(
        ...,
        description="Polynomial coefficient B"
    )
    C: float = Field(
        ...,
        description="Polynomial coefficient C"
    )
    D: float = Field(
        ...,
        description="Polynomial coefficient D"
    )
    message: Optional[str] = Field(
        None, description="Optional message regarding the calculation"
    )


class NASA9PolynomialCpIGResult(BaseModel):
    """
    NASA Polynomial (NASA-9) Heat Capacity Calculation Result Model
    Represents the result of ideal gas heat capacity calculation using NASA polynomial equation.

    Attributes
    ----------
    ideal_gas_heat_capacity_at_constant_pressure : CustomProp
        Ideal gas heat capacity at constant pressure calculated using NASA polynomial equation
    temperature : Temperature
        Temperature at which the heat capacity is calculated
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
    message : Optional[str]
        Optional message regarding the calculation
    """
    ideal_gas_heat_capacity_at_constant_pressure: CustomProp = Field(
        ...,
        description="Ideal gas heat capacity at constant pressure calculated using NASA polynomial equation"
    )
    temperature: Temperature = Field(
        ...,
        description="Temperature at which the heat capacity is calculated"
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
    message: Optional[str] = Field(
        None, description="Optional message regarding the calculation"
    )
