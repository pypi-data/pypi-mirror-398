# import libs
import logging
from typing import Optional, Literal, Tuple
from pythermodb_settings.models import Temperature, Pressure
import pycuc
from math import exp
# local
from ..models.vapor_pressure import AntoineVaporPressureResult, WagnerVaporPressureResult

# setup logger
logger = logging.getLogger(__name__)


def antoine(
    A: float,
    B: float,
    C: float,
    temperature: Temperature,
    temperature_range: Optional[Tuple[Temperature, Temperature]] = None,
    output_unit: Optional[Literal[
        'Pa', 'kPa', 'MPa', 'bar', 'atm', 'psi', 'mmHg'
    ]] = None,
    base: Literal['log10', 'ln'] = "log10",
    message: Optional[str] = None
) -> Optional[AntoineVaporPressureResult]:
    '''
    Calculate vapor pressure using the Antoine equation with specified constants and temperature. The result can be returned in various pressure units.

    The Antoine equation is given by:
    - log10(P) = A - B / (T + C)   (if base is "log10")
    - ln(P)   = A - B / (T + C)    (if base is "ln")

    Parameters
    ----------
    A : float
        Antoine equation constant A
    B : float
        Antoine equation constant B
    C : float
        Antoine equation constant C
    temperature : Temperature
        Temperature at which to calculate vapor pressure defined in pythermodb_settings.models.Temperature
    temperature_range : Optional[Tuple[Temperature, Temperature]], optional
        Optional temperature range for validity check, default is None. The tuple should contain (T_min, T_max).
    output_unit : Literal['Pa', 'kPa', 'MPa', 'bar', 'atm', 'psi', 'mmHg'], optional
        Desired output unit for vapor pressure ('Pa', 'kPa', 'MPa', 'bar', 'atm', 'psi', 'mmHg'), default is None.
    base : Literal['log10', 'ln'], optional
        Logarithmic base used in the Antoine equation ('log10' or 'ln', default is 'log10')
    message : str, optional
        Optional message regarding the calculation

    Returns
    -------
    Optional[AntoineVaporPressureResult]
        An instance of AntoineVaporPressureResult containing the calculation results, or None if an error occurs.
    '''
    try:
        # SECTION: Input Validation
        if not isinstance(temperature, Temperature):
            logger.error(
                "Invalid temperature input. Must be of type Temperature."
            )
            return None

        # NOTE: check empty A, B, C
        if A is None or B is None or C is None:
            logger.error("Antoine constants A, B, and C must be provided.")
            return None

        # >> check for A, B, C being numbers
        if not all(isinstance(param, (int, float)) for param in [A, B, C]):
            logger.error(
                "Antoine constants A, B, and C must be numeric values.")
            return None

        # SECTION: Calculation
        # NOTE: check temperature unit
        temperature_value = temperature.value
        temperature_unit = temperature.unit

        # NOTE: check temperature range validity
        if temperature_range:
            T_min, T_max = temperature_range
            if not (T_min.value <= temperature_value <= T_max.value):
                logger.error(
                    f"Temperature {temperature_value} {temperature_unit} is out of the valid range: "
                    f"{T_min.value} {T_min.unit} to {T_max.value} {T_max.unit}."
                )
                return None

        # NOTE: Antoine equation calculation with log10 or ln
        if base == "log10":
            log_pressure = A - (B / (temperature_value + C))
            # unit
            pressure_value = 10 ** log_pressure
        elif base == "ln":
            ln_pressure = A - (B / (temperature_value + C))
            pressure_value = exp(ln_pressure)
        else:
            logger.error(
                "Invalid base for logarithm. Use 'log10' or 'ln'.")
            return None

        # SECTION: Result preparation
        pressure_unit = output_unit if output_unit else "N/A"

        # >> prepare result dict
        res = {
            "A": A,
            "B": B,
            "C": C,
            "base": base,
            "temperature": {
                "value": temperature_value,
                "unit": temperature_unit
            },
            "temperature_range": temperature_range,
            "pressure": {
                "value": pressure_value,
                "unit": pressure_unit
            },
            "message": message
        }

        # >> convert to AntoineVaporPressureResult model
        res = AntoineVaporPressureResult(**res)

        return res
    except Exception as e:
        logger.error(f"Error in Antoine vapor pressure calculation: {e}")
        return None


def wagner(
    A: float,
    B: float,
    C: float,
    D: float,
    temperature: Temperature,
    critical_temperature: Temperature,
    critical_pressure: Pressure,
    temperature_range: Optional[Tuple[Temperature, Temperature]] = None,
    output_unit: Optional[Literal[
        'Pa', 'kPa', 'MPa', 'bar', 'atm', 'psi', 'mmHg'
    ]] = None,
    message: Optional[str] = None
) -> Optional[WagnerVaporPressureResult]:
    '''
    Calculate vapor pressure using the Wagner equation with specified constants, temperature, critical temperature, and critical pressure. The result can be returned in various pressure units.

    The Wagner equation is given by:
    - ln(P/Pc) = (A * τ + B * τ^1.5 + C * τ^2.5 + D * τ^5)

    where τ = 1 - (T / Tc)

    Parameters
    ----------
    A : float
        Wagner equation constant A
    B : float
        Wagner equation constant B
    C : float
        Wagner equation constant C
    D : float
        Wagner equation constant D
    temperature : Temperature
        Temperature at which to calculate vapor pressure defined in pythermodb_settings.models.Temperature
    critical_temperature : Temperature
        Critical temperature of the substance defined in pythermodb_settings.models.Temperature
    critical_pressure : Pressure
        Critical pressure of the substance defined in pythermodb_settings.models.Pressure
    temperature_range : Optional[Tuple[Temperature, Temperature]], optional
        Optional temperature range for validity check, default is None. The tuple should contain (T_min, T_max).
    output_unit : Literal['Pa', 'kPa', 'MPa', 'bar', 'atm', 'psi', 'mmHg'], optional
        Desired output unit for vapor pressure ('Pa', 'kPa', 'MPa', 'bar', 'atm', 'psi', 'mmHg'), default is None.
    message : str, optional
        Optional message regarding the calculation

    Returns
    -------
    Optional[WagnerVaporPressureResult]
        An instance of WagnerVaporPressureResult containing the calculation results, or None if an error occurs.

    References
    ----------
    - Forero G, Luis A., and Jorge A. Velásquez J. "Wagner liquid-vapour pressure equation constants from a simple methodology." The Journal of Chemical Thermodynamics 43.8 (2011): 1235-1251.
    '''
    try:
        # SECTION: Input Validation
        if not all(isinstance(param, (int, float)) for param in [A, B, C, D]):
            logger.error(
                "Wagner constants A, B, C, and D must be numeric values."
            )
            return None

        if not isinstance(temperature, Temperature):
            logger.error(
                "Invalid temperature input. Must be of type Temperature."
            )
            return None

        if not isinstance(critical_temperature, Temperature):
            logger.error(
                "Invalid critical temperature input. Must be of type Temperature."
            )
            return None

        if not isinstance(critical_pressure, Pressure):
            logger.error(
                "Invalid critical pressure input. Must be of type Pressure."
            )
            return None

        # SECTION: Calculation
        T = temperature.value
        Tc = critical_temperature.value

        # NOTE: check temperature range validity
        if temperature_range:
            T_min, T_max = temperature_range
            if not (T_min.value <= T <= T_max.value):
                logger.error(
                    f"Temperature {T} {temperature.unit} is out of the valid range: "
                    f"{T_min.value} {T_min.unit} to {T_max.value} {T_max.unit}."
                )
                return None

        # >> check T < Tc
        if T >= Tc:
            logger.error(
                "Temperature must be less than critical temperature for Wagner equation."
            )
            return None

        # set Pc
        Pc = critical_pressure.value
        # calculate tau
        tau = 1 - (T / Tc)

        ln_P_over_Pc = (
            A * tau + B * tau**1.5 + C * tau**2.5 + D * tau**5
        )/(1-tau)
        pressure_value = Pc * exp(ln_P_over_Pc)
        # set unit
        pressure_unit = output_unit if output_unit else "N/A"

        # SECTION: Result preparation
        res = {
            "A": A,
            "B": B,
            "C": C,
            "D": D,
            "temperature": {
                "value": T,
                "unit": temperature.unit
            },
            "temperature_range": temperature_range,
            "critical_temperature": {
                "value": Tc,
                "unit": critical_temperature.unit
            },
            "critical_pressure": {
                "value": Pc,
                "unit": critical_pressure.unit
            },
            "pressure": {
                "value": pressure_value,
                "unit": pressure_unit
            },
            "message": message
        }

        # >> convert to WagnerVaporPressureResult model
        res = WagnerVaporPressureResult(**res)

        return res
    except Exception as e:
        logger.error(f"Error in Wagner vapor pressure calculation: {e}")
        return None
