# import libs
import logging
import numpy as np
from typing import Optional, Dict, Any
from pythermodb_settings.models import Temperature
import pycuc
# locals

# NOTE: logger setup
logger = logging.getLogger(__name__)


# SECTION: enthalpy calculations using NASA 9-coefficient polynomial
def En_IG_NASA9_polynomial(
    a1: float,
    a2: float,
    a3: float,
    a4: float,
    a5: float,
    a6: float,
    a7: float,
    b1: float,
    temperature: Temperature,
    temperature_range: Optional[tuple[Temperature, Temperature]] = None,
    output_unit: Optional[str] = None,
    universal_gas_constant: float = 8.31446261815324,  # J/mol.K
    message: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Calculate the ideal gas enthalpy (En_IG) using NASA 9-coefficient polynomial coefficients. The NASA polynomial equation is defined as:

    En_IG(T) = R * T * [-a1*T^-2 + a2*ln(T) + a3 + a4*T/2 + a5*T^2/3 + a6*T^3/4 + a7*T^4/5 + b1/T]

    where En is the enthalpy at temperature T.

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
    b1 : float
        NASA polynomial coefficient b1
    temperature : Temperature
        Temperature at which to calculate enthalpy defined in pythermodb_settings.models.Temperature, should be in Kelvin
    output_unit : Optional[str], optional
        Desired output unit for enthalpy (default is None, which returns J/mol)
    universal_gas_constant : float, optional
        Universal gas constant in J/mol.K (default is 8.31446261815324 J/mol.K)
    message : Optional[str], optional
        Optional message regarding the calculation

    Returns
    -------
    Optional[NASA9PolynomialIdealGasEnthalpyResult]
        Result model containing the calculated ideal gas enthalpy and related information, or None if an error occurs.
    """
    try:
        # SECTION: Input Validation
        # NOTE: extract temperature value in [K]
        T_value = temperature.value  # assuming temperature is in Kelvin
        T_unit = temperature.unit

        # >> check temperature unit
        if T_unit != "K":
            T_value = pycuc.convert_from_to(
                value=T_value, from_unit=T_unit, to_unit="K"
            )

        # NOTE: check temperature range validity
        if temperature_range is not None:
            T_low = temperature_range[0].value
            T_high = temperature_range[1].value
            T_low_unit = temperature_range[0].unit.strip()
            T_high_unit = temperature_range[1].unit.strip()

            # >> convert to K if necessary
            if T_low_unit != "K":
                T_low = pycuc.convert_from_to(
                    value=T_low, from_unit=T_low_unit, to_unit="K"
                )
            if T_high_unit != "K":
                T_high = pycuc.convert_from_to(
                    value=T_high, from_unit=T_high_unit, to_unit="K"
                )

            # >> check validity
            if not (T_low <= T_value <= T_high):
                logger.warning(
                    f"Temperature {T_value} K is out of the specified range [{T_low} K, {T_high} K]."
                )
                return None

        # NOTE: check coefficients
        coeffs = [a1, a2, a3, a4, a5, a6, a7, b1]
        for i, coeff in enumerate(coeffs):
            if not isinstance(coeff, (int, float)):
                logger.error(
                    f"Coefficient a{i+1} is not a valid number: {coeff}")
                return None

        # SECTION: calculate En using NASA 9-coefficient polynomial equation, temperature in K, and R in J/mol.K
        # En in J/mol
        En_value = universal_gas_constant * T_value * (
            -a1 * T_value**-2 +
            a2 * np.log(T_value) +
            a3 +
            a4 * T_value / 2 +
            a5 * T_value**2 / 3 +
            a6 * T_value**3 / 4 +
            a7 * T_value**4 / 5 +
            b1 / T_value
        )
        En_value = float(En_value)

        # set unit
        if output_unit is None:
            En_unit = "J/mol"
        else:
            En_unit = output_unit

        # return result model
        res = {
            "result": {
                "value": En_value,
                "unit": En_unit,
                "symbol": "En_IG"
            },
            "message": message if message is not None else "Ideal gas enthalpy calculation using NASA-9 successful"
        }

        return res
    except Exception as e:
        logger.error(f"Error in ideal gas enthalpy calculation: {e}")
        return None


def En_IG_shomate(
    A: float,
    B: float,
    C: float,
    D: float,
    E: float,
    F: float,
    G: float,
    temperature: Temperature,
    temperature_range: Optional[tuple[Temperature, Temperature]] = None,
    output_unit: Optional[str] = None,
    universal_gas_constant: float = 8.31446261815324,  # J/mol.K
    message: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Calculate the ideal gas enthalpy (En_IG) using Shomate equation coefficients. The Shomate equation is defined as:

    En_IG(T) = A*t + B*t^2/2 + C*t^3/3 + D*t^4/4 - E/t + F, where t = T/1000

    where En is the enthalpy [kJ/mol] at temperature T [K].

    Parameters
    ----------
    A : float
        Shomate equation coefficient A
    B : float
        Shomate equation coefficient B
    C : float
        Shomate equation coefficient C
    D : float
        Shomate equation coefficient D
    E : float
        Shomate equation coefficient E
    F : float
        Shomate equation coefficient F
    G : float
        Shomate equation coefficient G
    temperature : Temperature
        Temperature at which to calculate enthalpy defined in pythermodb_settings.models.Temperature, should be in Kelvin
    output_unit : Optional[str], optional
        Desired output unit for enthalpy (default is None, which returns J/mol)
    universal_gas_constant : float, optional
        Universal gas constant in J/mol.K (default is 8.31446261815324 J/mol.K)
    message : Optional[str], optional
        Optional message regarding the calculation

    Returns
    -------
    Optional[Dict[str, Any]]
        A dictionary containing the calculated ideal gas enthalpy and related information, or None if an error occurs.
    """
    try:
        # SECTION: Input Validation
        # NOTE: extract temperature value in [K]
        T_value = temperature.value  # assuming temperature is in Kelvin
        T_unit = temperature.unit

        # >> check temperature unit
        if T_unit != "K":
            T_value = pycuc.convert_from_to(
                value=T_value, from_unit=T_unit, to_unit="K"
            )
            T_unit = "K"

        # NOTE: check temperature range validity
        if temperature_range is not None:
            T_low = temperature_range[0].value
            T_high = temperature_range[1].value
            T_low_unit = temperature_range[0].unit.strip()
            T_high_unit = temperature_range[1].unit.strip()

            # >> convert to K if necessary
            if T_low_unit != "K":
                T_low = pycuc.convert_from_to(
                    value=T_low, from_unit=T_low_unit, to_unit="K"
                )
            if T_high_unit != "K":
                T_high = pycuc.convert_from_to(
                    value=T_high, from_unit=T_high_unit, to_unit="K"
                )

            # >> check validity
            if not (T_low <= T_value <= T_high):
                logger.warning(
                    f"Temperature {T_value} K is out of the specified range [{T_low} K, {T_high} K]."
                )
                return None

        # NOTE: check coefficients
        coeffs = [A, B, C, D, E, F, G]
        for i, coeff in enumerate(coeffs):
            if not isinstance(coeff, (int, float)):
                logger.error(
                    f"Coefficient {['A','B','C','D','E','F','G'][i]} is not a valid number: {coeff}")
                return None

        # SECTION: calculate En using Shomate equation, temperature in K
        # En in kJ/mol
        t = T_value / 1000.0

        En_value = (A * t +
                    B * t**2 / 2 +
                    C * t**3 / 3 +
                    D * t**4 / 4 -
                    E / t +
                    F)
        En_value = float(En_value)

        # set unit
        if output_unit is None:
            En_unit = "kJ/mol"
        else:
            En_unit = output_unit

        # return result model
        res = {
            "result": {
                "value": En_value,
                "unit": En_unit,
                "symbol": "En_IG"
            },
            "message": message if message is not None else "Ideal gas enthalpy calculation using Shomate equation successful"
        }

        return res
    except Exception as e:
        logger.error(f"Error in ideal gas enthalpy calculation: {e}")
        return None
