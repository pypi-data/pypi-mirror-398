# import libs
import logging
from typing import Optional, Tuple, Dict, Any
from pythermodb_settings.models import Temperature
import pycuc
# locals


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
) -> Optional[Dict[str, Any]]:
    """
    Calculate the ideal gas heat capacity (Cp_IG) using a polynomial equation. The polynomial equation is defined as:

    Cp_IG(T) = A + B*T + C*T^2 + D*T^3 + E/T^2

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
    Optional[Dict[str, Any]]
        Dictionary containing the calculated ideal gas heat capacity at constant pressure and related information. If an error occurs, returns None.
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
            "result": {
                "value": Cp_value,
                "unit": Cp_unit,
                "symbol": 'Cp_IG'
            },
            "message": message
        }

        return res
    except Exception as e:
        logger.error(f"Error in heat capacity calculation: {e}")
        return None


def Cp_IG_NASA9_polynomial(
        a1: float,
        a2: float,
        a3: float,
        a4: float,
        a5: float,
        a6: float,
        a7: float,
        temperature: Temperature,
        temperature_range: Optional[Tuple[Temperature, Temperature]] = None,
        output_unit: Optional[str] = None,
        universal_gas_constant: float = 8.31446261815324,  # J/mol.K
        message: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Calculate the ideal gas heat capacity (Cp_IG) using NASA polynomial coefficients (NASA-9). The NASA polynomial equation is defined as:

    Cp_IG(T) = a1*T^-2 + a2*T^-1 + a3 + a4*T + a5*T^2 + a6*T^3 + a7*T^4

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
    a6 : float
        NASA polynomial coefficient a6
    a7 : float
        NASA polynomial coefficient a7
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
    Optional[Dict[str, Any]]
        Dictionary containing the calculated ideal gas heat capacity at constant pressure and related information. If an error occurs, returns None.
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
        coeffs = [a1, a2, a3, a4, a5, a6, a7]

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
            a1*T_value**-2 +
            a2*T_value**-1 +
            a3 +
            a4*T_value +
            a5*T_value**2 +
            a6*T_value**3 +
            a7*T_value**4
        )

        # set unit
        Cp_unit = output_unit if output_unit else "J/mol.K"

        # SECTION: Result preparation
        res = {
            "result": {
                "value": Cp_value,
                "unit": Cp_unit,
                "symbol": 'Cp_IG'
            },
            "message": message
        }

        return res
    except Exception as e:
        logger.error(f"Error in heat capacity calculation: {e}")
        return None


def Cp_IG_shomate(
    A: float,
    B: float,
    C: float,
    D: float,
    E: float,
    temperature: Temperature,
    temperature_range: Optional[Tuple[Temperature, Temperature]] = None,
    output_unit: Optional[str] = None,
    message: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Calculate the ideal gas heat capacity (Cp_IG) using the Shomate equation. The Shomate equation is defined as:

    Cp_IG(T) = A + B*t + C*t^2 + D*t^3 + E/t^2, where t = T/1000,

    where Cp is the heat capacity at constant pressure in J/mol.K and T is the temperature in Kelvin.

    Parameters
    ----------
    A : float
        Shomate coefficient A
    B : float
        Shomate coefficient B
    C : float
        Shomate coefficient C
    D : float
        Shomate coefficient D
    E : float
        Shomate coefficient E
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

        # >> convert to K if necessary
        if T_unit != "K":
            T_value = pycuc.convert_from_to(
                value=T_value,
                from_unit=T_unit,
                to_unit="K",
            )
            T_unit = "K"

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
        # ! t is in K for shomate equation
        t = T_value / 1000.0

        Cp_value = (
            A + B * t + C * t**2 + D * t**3 + E / t**2
        )

        # set unit
        Cp_unit = output_unit if output_unit else "J/mol.K"

        # SECTION: Result preparation
        res = {
            "result": {
                "value": Cp_value,
                "unit": Cp_unit,
                "symbol": 'Cp_IG'
            },
            "message": message
        }

        return res
    except Exception as e:
        logger.error(f"Error in heat capacity calculation: {e}")
        return None
