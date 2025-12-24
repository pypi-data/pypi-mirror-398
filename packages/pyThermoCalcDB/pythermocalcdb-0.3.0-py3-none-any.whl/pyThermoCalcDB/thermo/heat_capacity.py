# import libs
import logging
from typing import Optional, Tuple
from pythermodb_settings.models import Temperature
import pycuc
# locals
from ..models.heat_capacity import (
    PolynomialCpIGResult,
    NASAPolynomialCpIGResult
)

# NOTE: logger setup
logger = logging.getLogger(__name__)


def Cp_IG_polynomial(
    A: float,
    B: float,
    C: float,
    D: float,
    E: float,
    temperature: Temperature,
    temperature_range: Optional[Tuple[Temperature, Temperature]] = None,
    output_unit: Optional[str] = None,
    message: Optional[str] = None
) -> Optional[PolynomialCpIGResult]:
    """
    Calculate the ideal gas heat capacity (Cp_IG) using a polynomial equation. The polynomial equation is defined as:

    Cp(T) = A + B*T + C*T^2 + D*T^3 + E/T^2

    where Cp is the heat capacity at constant pressure and T is the temperature.

    Parameters
    ----------
    A : float
        Polynomial coefficient A
    B : float
        Polynomial coefficient B
    C : float
        Polynomial coefficient C
    D : float
        Polynomial coefficient D
    E : float
        Polynomial coefficient E
    temperature : Temperature
        Temperature at which to calculate heat capacity defined in pythermodb_settings.models.Temperature
    temperature_range : Optional[Tuple[Temperature, Temperature]], optional
        Optional temperature range for validity check, default is None. The tuple should contain (T_min, T_max).
    output_unit : str, optional
        Desired output unit for heat capacity, default is None.
    message : str, optional
        Optional message to include in the result, default is None.

    Returns
    -------
    Optional[PolynomialCpIGResult]
        Pydantic model containing the calculated ideal gas heat capacity at constant pressure and related information. If an error occurs, returns None.
    """
    try:
        # SECTION: Input Validation
        T_value = temperature.value  # Temperature in desired unit
        T_unit = temperature.unit

        # NOTE: check coefficients
        coeffs = [A, B, C, D, E]

        # iterate and check each coefficient
        for i, coeff in enumerate(coeffs):
            if not isinstance(coeff, (int, float)):
                logger.error(f"Coefficient {i} is not a valid number: {coeff}")
                return None

        # SECTION: Temperature Range Check
        if temperature_range:
            T_min, T_max = temperature_range
            if not (T_min.value <= T_value <= T_max.value):
                logger.warning(
                    f"Temperature {T_value} {T_unit} is out of the valid range "
                    f"({T_min.value} {T_min.unit} - {T_max.value} {T_max.unit})"
                )
                return None

        # SECTION: Calculation
        Cp_value = (
            A + B * T_value + C * T_value**2 + D * T_value**3 + E / T_value**2
        )

        # set unit
        Cp_unit = output_unit if output_unit else "N/A"

        # SECTION: Result preparation
        res = {
            "ideal_gas_heat_capacity_at_constant_pressure": {
                "value": Cp_value,
                "unit": Cp_unit
            },
            "temperature": {
                "value": T_value,
                "unit": T_unit
            },
            "temperature_range": temperature_range,
            "equation": "Cp(T) = A + B*T + C*T^2 + D*T^3 + E/T^2",
            "A": A,
            "B": B,
            "C": C,
            "D": D,
            "message": message
        }

        # >> convert to pydantic model
        res = PolynomialCpIGResult(**res)

        return res
    except Exception as e:
        logger.error(f"Error in heat capacity calculation: {e}")
        return None


def Cp_IG_NASA_polynomial(
        a1: float,
        a2: float,
        a3: float,
        a4: float,
        a5: float,
        temperature: Temperature,
        temperature_range: Optional[Tuple[Temperature, Temperature]] = None,
        output_unit: Optional[str] = None,
        universal_gas_constant: float = 8.31446261815324,  # J/mol.K
        message: Optional[str] = None,
) -> Optional[NASAPolynomialCpIGResult]:
    """
    Calculate the ideal gas heat capacity (Cp_IG) using NASA polynomial coefficients. The NASA polynomial equation is defined as:

    Cp(T) = a1 + a2*T + a3*T^2 + a4*T^3 + a5*T^4

    where Cp is the heat capacity at constant pressure and T is the temperature.

    Parameters
    ----------
    a1 : float
        NASA polynomial coefficient a1
    a2 : float
        NASA polynomial coefficient a2
    a3 : float
        NASA polynomial coefficient a3
    a4 : float
        NASA polynomial coefficient a4
    a5 : float
        NASA polynomial coefficient a5
    temperature : Temperature
        Temperature at which to calculate heat capacity defined in pythermodb_settings.models.Temperature, should be in Kelvin
    temperature_range : Optional[Tuple[Temperature, Temperature]], optional
        Optional temperature range for validity check, default is None. The tuple should contain (T_min, T_max), in Kelvin.
    output_unit : str, optional
        Desired output unit for heat capacity, default is None, the unit will be "J/mol.K".
    universal_gas_constant : float, optional
        Universal gas constant in J/mol.K, default is 8.31446261815324 J/mol.K.
    message : str, optional
        Optional message to include in the result, default is None.

    Returns
    -------
    Optional[NASAPolynomialCpIGResult]
        Pydantic model containing the calculated ideal gas heat capacity at constant pressure and related information. If an error occurs, returns None.
    """
    try:
        # SECTION: Input Validation
        T_value = temperature.value  # Temperature in desired unit
        T_unit = temperature.unit

        # >> convert to K if necessary
        if T_unit != "K":
            T_value = pycuc.convert_from_to(
                value=T_value,
                from_unit=T_unit,
                to_unit="K",
            )
            T_unit = "K"

        # NOTE: check coefficients
        coeffs = [a1, a2, a3, a4, a5]

        # iterate and check each coefficient
        for i, coeff in enumerate(coeffs):
            if not isinstance(coeff, (int, float)):
                logger.error(f"Coefficient {i} is not a valid number: {coeff}")
                return None

        # SECTION: Temperature Range Check
        if temperature_range:
            T_min, T_max = temperature_range

            # >> convert to K if necessary
            if T_min.unit != "K":
                T_min_value = pycuc.convert_from_to(
                    value=T_min.value,
                    from_unit=T_min.unit,
                    to_unit="K",
                )
                T_min = Temperature(value=T_min_value, unit="K")

            if T_max.unit != "K":
                T_max_value = pycuc.convert_from_to(
                    value=T_max.value,
                    from_unit=T_max.unit,
                    to_unit="K",
                )
                T_max = Temperature(value=T_max_value, unit="K")

            # >> check range
            if not (T_min.value <= T_value <= T_max.value):
                logger.warning(
                    f"Temperature {T_value} {T_unit} is out of the valid range "
                    f"({T_min.value} {T_min.unit} - {T_max.value} {T_max.unit})"
                )
                return None

        # SECTION: Calculation
        # calculate Cp using NASA polynomial equation, temperature in K, and R in J/mol.K
        # Cp in J/mol.K
        Cp_value = universal_gas_constant*(
            a1 + a2 * T_value + a3 * T_value**2 +
            a4 * T_value**3 + a5 * T_value**4
        )

        # set unit
        Cp_unit = output_unit if output_unit else "J/mol.K"

        # SECTION: Result preparation
        res = {
            "ideal_gas_heat_capacity_at_constant_pressure": {
                "value": Cp_value,
                "unit": Cp_unit
            },
            "temperature": {
                "value": T_value,
                "unit": T_unit
            },
            "temperature_range": temperature_range,
            "equation": "Cp(T) = R*(a1 + a2*T + a3*T^2 + a4*T^3 + a5*T^4)",
            "a1": a1,
            "a2": a2,
            "a3": a3,
            "a4": a4,
            "a5": a5,
            "message": message
        }

        # >> convert to pydantic model
        res = NASAPolynomialCpIGResult(**res)

        return res
    except Exception as e:
        logger.error(f"Error in heat capacity calculation: {e}")
        return None
