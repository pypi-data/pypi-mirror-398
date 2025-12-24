# import libs
import logging
from typing import Dict, Optional, Any
from pythermodb_settings.models import (
    Temperature,
    Pressure,
    CustomProp,
)
import pycuc
# locals


# NOTE: set up logger
logger = logging.getLogger(__name__)


def rackett(
        temperature: Temperature,
        critical_temperature: Temperature,
        critical_pressure: Pressure,
        molecular_weight: CustomProp,
        critical_compressibility: CustomProp,
        message: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Calculate the density of a substance using the Rackett equation.

    Parameters
    ----------
    temperature : Temperature
        The temperature at which to calculate the density.
    critical_temperature : Temperature
        The critical temperature of the substance.
    critical_pressure : Pressure
        The critical pressure of the substance.
    molecular_weight : CustomProp
        The molecular weight of the substance, in kg/mol.
    critical_compressibility : CustomProp
        The critical compressibility factor of the substance, dimensionless.
    message : Optional[Dict], optional
        A dictionary to store messages or warnings.

    Returns
    -------
    Optional[Dict[str, Any]]
        A dictionary containing the calculation results, or None if an error occurs.
    """
    try:
        # SECTION: Input validation
        # NOTE: check for valid temperature
        if temperature.value <= 0 or critical_temperature.value <= 0:
            logger.warning("Temperature values must be greater than zero.")
            return None

        # NOTE: check for valid pressure
        if critical_pressure.value <= 0:
            logger.warning("Critical pressure must be greater than zero.")
            return None

        # SECTION: Unit conversions
        T_value = temperature.value
        T_unit = temperature.unit

        # >> to K
        if T_unit != "K":
            T_value = pycuc.convert_from_to(
                value=T_value,
                from_unit=T_unit,
                to_unit="K",
            )

        # NOTE: critical temperature to [K]
        Tc_value = critical_temperature.value
        Tc_unit = critical_temperature.unit

        if Tc_unit != "K":
            Tc_value = pycuc.convert_from_to(
                value=Tc_value,
                from_unit=Tc_unit,
                to_unit="K",
            )

        # NOTE: critical pressure to [bar]
        Pc_value = critical_pressure.value
        Pc_unit = critical_pressure.unit
        if Pc_unit != "bar":
            Pc_value = pycuc.convert_from_to(
                value=Pc_value,
                from_unit=Pc_unit,
                to_unit="bar",
            )

        # NOTE: molecular weight to [kg/mol]
        MW_value = float(molecular_weight.value)  # kg/mol
        MW_unit = molecular_weight.unit

        # NOTE: compressibility factor (dimensionless)
        Z_value = float(critical_compressibility.value)
        Z_unit = critical_compressibility.unit

        # ! >> to kg/mol
        if MW_unit != "kg/mol":
            if MW_unit == "g/mol":
                MW_value = MW_value / 1000  # kg/mol
            elif MW_unit == "kg/kmol":
                MW_value = MW_value / 1000  # kg/mol
            else:
                logger.warning(
                    f"Unsupported molecular weight unit: {MW_unit}. Expected 'kg/mol'."
                )
                return None

        # SECTION: Rackett equation calculation
        # ! Gas constant R = 8.314 J/mol·K = 8.314e-5 bar·m³/mol·K
        R = 8.31446261815324e-5  # bar·m³/mol·K

        Tr = T_value / Tc_value  # Reduced temperature
        exponent = 1 + (1 - Tr)**(2/7)

        # ! >> Saturated molar volume in m³/mol
        V_sat = (R * Tc_value / Pc_value) * Z_value**exponent

        # NOTE: Density: ρ = M / V_sat
        # ! >> kg/m³
        rho = MW_value / V_sat

        res = {
            "result": {
                "value": rho,
                "unit": "kg/m3",
                "symbol": 'rho_LIQ'
            },
            "message": message,
        }

        # res
        return res
    except Exception as e:
        logger.error(f"Error in rackett calculation: {e}")
        return None
