# import libs
import logging
from typing import Literal, Optional, Tuple
from pythermodb_settings.models import Component, Temperature, Pressure
from pyThermoLinkDB.models import ModelSource
from pyThermoLinkDB.thermo import Source
# local
from ..utils.tools import measure_time
from ..models import CalcResult
from ..core.component_vapr import ComponentVaporPressure

# NOTE: Logger
logger = logging.getLogger(__name__)

# SECTION: Vapor Pressure


@measure_time
def calc_vapor_pressure_at_temperature(
    component: Component,
    model_source: ModelSource,
    temperature: Temperature,
    component_key: Literal[
        'Name-State',
        'Formula-State',
        'Name',
        'Formula',
        'Name-Formula-State',
        'Formula-Name-State'
    ] = 'Name-State',
    **kwargs
) -> Optional[CalcResult]:
    """
    Calculate the vapor pressure at a given temperature for a component.

    Calculates the saturation pressure of a pure substance at a given temperature. Vapor pressure indicates the tendency of a liquid to evaporate and is fundamental in boiling, evaporation, and phase-equilibrium calculations.

    Parameters
    ----------
    component : Component
        The chemical component for which to calculate the vapor pressure.
    model_source : ModelSource
        The source model containing necessary data.
    temperature : Temperature
        The temperature at which to calculate the vapor pressure.
    component_key : Literal[..., optional]
        The key to identify the component, by default 'Name-State'.
    **kwargs
        Additional keyword arguments.
        - mode : Literal['silent', 'log', 'attach'], optional
            Mode for time measurement logging. Default is 'log'.

    Returns
    -------
    Optional[CalcResult]
        A CalcResult object containing the vapor pressure value, unit, and symbol, or None if calculation fails.

    Notes
    -----
    - Model source must contain vapor pressure equations for the specified component.
    - `Vapor pressure` should be returned in `Pa` unit.
    - `Temperature` should be provided in `K` unit.
    """
    try:
        # SECTION: Input validation
        if not isinstance(component, Component):
            logger.error("Invalid component provided.")
            return None

        if not isinstance(model_source, ModelSource):
            logger.error("Invalid model_source provided.")
            return None

        if not isinstance(temperature, Temperature):
            logger.error("Invalid temperature provided.")
            return None

        # SECTION: Prepare source
        Source_ = Source(model_source=model_source)

        # SECTION: Initialize ComponentVaporPressure
        vapr_props = ComponentVaporPressure(
            component=component,
            source=Source_,
            component_key=component_key
        )

        # NOTE: calculate
        VaPr_result = vapr_props.calc_VaPr(
            temperature=temperature
        )

        return VaPr_result
    except Exception as e:
        logger.error(
            f"Error calculating vapor pressure for component '{component.name}': {e}")
        return None


@measure_time
def calc_vapor_pressure_range_at_temperature(
    component: Component,
    model_source: ModelSource,
    temperatures: list[Temperature],
    component_key: Literal[
        'Name-State',
        'Formula-State',
        'Name',
        'Formula',
        'Name-Formula-State',
        'Formula-Name-State'
    ] = 'Name-State',
    **kwargs
) -> Optional[list[CalcResult]]:
    """
    Calculate the vapor pressure over a range of temperatures for a component.

    Parameters
    ----------
    component : Component
        The chemical component for which to calculate the vapor pressure.
    model_source : ModelSource
        The source model containing necessary data.
    temperatures : list[Temperature]
        The list of temperatures at which to calculate the vapor pressure.
    component_key : Literal[..., optional]
        The key to identify the component, by default 'Name-State'.
    **kwargs
        Additional keyword arguments.
        - mode : Literal['silent', 'log', 'attach'], optional
            Mode for time measurement logging. Default is 'log'.

    Returns
    -------
    Optional[list[CalcResult]]
        A list of CalcResult objects containing the vapor pressure values, units, and symbols, or None if calculation fails.

    Notes
    -----
    - Model source must contain vapor pressure equations for the specified component.
    - `Vapor pressure` should be returned in `Pa` unit.
    - `Temperature` should be provided in `K` unit.
    """
    try:
        # SECTION: Input validation
        if not isinstance(component, Component):
            logger.error("Invalid component provided.")
            return None

        if not isinstance(model_source, ModelSource):
            logger.error("Invalid model_source provided.")
            return None

        if not all(isinstance(temp, Temperature) for temp in temperatures):
            logger.error("Invalid temperatures provided.")
            return None

        # SECTION: Prepare source
        Source_ = Source(model_source=model_source)

        # SECTION: Initialize ComponentVaporPressure
        vapr_props = ComponentVaporPressure(
            component=component,
            source=Source_,
            component_key=component_key
        )

        # NOTE: calculate
        res = vapr_props.calc_VaPr_range(
            temperature_range=temperatures
        )
        return res
    except Exception as e:
        logger.error(
            f"Error calculating vapor pressure range for component '{component.name}': {e}")
        return None

# SECTION: Enthalpy of Vaporization


@measure_time
def calc_enthalpy_of_vaporization_at_temperature(
    component: Component,
    model_source: ModelSource,
    temperature: Temperature,
    component_key: Literal[
        'Name-State',
        'Formula-State',
        'Name',
        'Formula',
        'Name-Formula-State',
        'Formula-Name-State'
    ] = 'Name-State',
    **kwargs
) -> Optional[CalcResult]:
    """
    Calculate the enthalpy of vaporization at a given temperature for a component.

    Computes the heat required to convert liquid into vapor at a given temperature. Essential for energy-balance calculations in boilers, evaporators, and distillation units.

    Parameters
    ----------
    component : Component
        The chemical component for which to calculate the enthalpy of vaporization.
    model_source : ModelSource
        The source model containing necessary data.
    temperature : Temperature
        The temperature at which to calculate the enthalpy of vaporization.
    component_key : Literal[..., optional]
        The key to identify the component, by default 'Name-State'.
    **kwargs
        Additional keyword arguments.
        - mode : Literal['silent', 'log', 'attach'], optional
            Mode for time measurement logging. Default is 'log'.

    Returns
    -------
    Optional[CalcResult]
        A CalcResult object containing the enthalpy of vaporization value, unit, and symbol, or None if calculation fails.

    Notes
    -----
    - Model source must contain vapor pressure equations for the specified component.
    - `Vapor pressure` should be returned in `Pa` unit.
    - `Temperature` should be provided in `K` unit.
    """
    try:
        # SECTION: Input validation
        if not isinstance(component, Component):
            logger.error("Invalid component provided.")
            return None

        if not isinstance(model_source, ModelSource):
            logger.error("Invalid model_source provided.")
            return None

        if not isinstance(temperature, Temperature):
            logger.error("Invalid temperature provided.")
            return None

        # SECTION: Prepare source
        Source_ = Source(model_source=model_source)

        # SECTION: Initialize ComponentVaporPressure
        vapr_props = ComponentVaporPressure(
            component=component,
            source=Source_,
            component_key=component_key
        )

        # NOTE: calculate
        res = vapr_props.calc_EnVap_Clapeyron(
            temperature=temperature
        )

        return res
    except Exception as e:
        logger.error(
            f"Error calculating enthalpy of vaporization for component '{component.name}': {e}")
        return None


@measure_time
def calc_enthalpy_of_vaporization_range_at_temperature(
    component: Component,
    model_source: ModelSource,
    temperatures: list[Temperature],
    component_key: Literal[
        'Name-State',
        'Formula-State',
        'Name',
        'Formula',
        'Name-Formula-State',
        'Formula-Name-State'
    ] = 'Name-State',
    **kwargs
) -> Optional[list[CalcResult]]:
    """
    Calculate the enthalpy of vaporization over a range of temperatures for a component.

    Parameters
    ----------
    component : Component
        The chemical component for which to calculate the enthalpy of vaporization.
    model_source : ModelSource
        The source model containing necessary data.
    temperatures : list[Temperature]
        The list of temperatures at which to calculate the enthalpy of vaporization.
    component_key : Literal[..., optional]
        The key to identify the component, by default 'Name-State'.
    **kwargs
        Additional keyword arguments.
        - mode : Literal['silent', 'log', 'attach'], optional
            Mode for time measurement logging. Default is 'log'.

    Returns
    -------
    Optional[list[CalcResult]]
        A list of CalcResult objects containing the enthalpy of vaporization values, units, and symbols, or None if calculation fails.

    Notes
    -----
    - Model source must contain vapor pressure equations for the specified component.
    - `Vapor pressure` should be returned in `Pa` unit.
    - `Temperature` should be provided in `K` unit.
    """
    try:
        # SECTION: Input validation
        if not isinstance(component, Component):
            logger.error("Invalid component provided.")
            return None

        if not isinstance(model_source, ModelSource):
            logger.error("Invalid model_source provided.")
            return None

        if not all(isinstance(temp, Temperature) for temp in temperatures):
            logger.error("Invalid temperatures provided.")
            return None

        # SECTION: Prepare source
        Source_ = Source(model_source=model_source)

        # SECTION: Initialize ComponentVaporPressure
        vapr_props = ComponentVaporPressure(
            component=component,
            source=Source_,
            component_key=component_key
        )

        # NOTE: calculate
        res = vapr_props.calc_EnVap_Clapeyron_range(
            temperature_range=temperatures
        )
        return res
    except Exception as e:
        logger.error(
            f"Error calculating enthalpy of vaporization range for component '{component.name}': {e}")
        return None

# SECTION: Saturated Temperature


@measure_time
def calc_saturated_temperature_at_pressure(
    component: Component,
    model_source: ModelSource,
    pressure: Pressure,
    temperature_guess: Temperature | None = None,
    T_bracket: Tuple[Temperature, Temperature] | None = None,
    method: str = "auto",
    tol: float = 0.000001,
    max_iter: int = 50,
    h: float | None = None,
    component_key: Literal[
        'Name-State',
        'Formula-State',
        'Name',
        'Formula',
        'Name-Formula-State',
        'Formula-Name-State'
    ] = 'Name-State',
    **kwargs
) -> Optional[CalcResult]:
    """
    Calculate the saturated temperature at a given pressure for a component.

    Finds the boiling temperature of a pure substance at a specified pressure. Useful for vacuum distillation, steam calculations, and refrigeration cycle analysis.

    Parameters
    ----------
    component : Component
        The chemical component for which to calculate the saturated temperature.
    model_source : ModelSource
        The source model containing necessary data.
    pressure : Pressure
        The pressure at which to calculate the saturated temperature (in Pa).
    temperature_guess : Temperature, optional
        An initial guess for the temperature (in K), by default None.
    T_bracket : Tuple[Temperature, Temperature], optional
        A bracketing interval for the temperature (in K), by default None.
    method : str, optional
        The root-finding method to use, by default "auto".
        - "auto": use brentq if bracket is provided, else Newton with derivative
        - "brentq": robust bracketing method (requires T_bracket)
        - "bisect": slower but very robust (requires T_bracket)
        - "newton": uses derivative dPsat/dT and T_guess
        - "least_squares": minimizes (Psat(T) - P)^2 using least squares optimization
    tol : float, optional
        The tolerance for convergence, by default 0.000001.
    max_iter : int, optional
        The maximum number of iterations, by default 50.
    h : float, optional
        Step size for numerical derivative, by default None.
    component_key : Literal[..., optional]
        The key to identify the component, by default 'Name-State'.
    **kwargs
        Additional keyword arguments.
        - mode : Literal['silent', 'log', 'attach'], optional
            Mode for time measurement logging. Default is 'log'.

    Returns
    -------
    Optional[CalcResult]
        A CalcResult object containing the saturated temperature value, unit, and symbol, or None if calculation fails.

    Notes
    -----
    - Model source must contain vapor pressure equations for the specified component.
    - `Vapor pressure` should be returned in `Pa` unit.
    - `Temperature` should be provided in `K` unit.
    """
    try:
        # SECTION: Input validation
        if not isinstance(component, Component):
            logger.error("Invalid component provided.")
            return None

        if not isinstance(model_source, ModelSource):
            logger.error("Invalid model_source provided.")
            return None

        if not isinstance(pressure, Pressure):
            logger.error("Invalid pressure provided.")
            return None

        # SECTION: Prepare source
        Source_ = Source(model_source=model_source)

        # SECTION: Initialize ComponentVaporPressure
        vapr_props = ComponentVaporPressure(
            component=component,
            source=Source_,
            component_key=component_key
        )

        # NOTE: calculate
        res = vapr_props.calc_TeVaPr(
            pressure=pressure,
            temperature_guess=temperature_guess,
            T_bracket=T_bracket,
            method=method,
            tol=tol,
            max_iter=max_iter,
            h=h
        )

        return res
    except Exception as e:
        logger.error(
            f"Error calculating saturated temperature for component '{component.name}': {e}")
        return None

# SECTION: Vapor Pressure Sensitivity


@measure_time
def calc_vapor_pressure_sensitivity_at_temperature(
    component: Component,
    model_source: ModelSource,
    temperature: Temperature,
    component_key: Literal[
        'Name-State',
        'Formula-State',
        'Name',
        'Formula',
        'Name-Formula-State',
        'Formula-Name-State'
    ] = 'Name-State',
    **kwargs
) -> Optional[CalcResult]:
    """
    Calculate the sensitivity of vapor pressure with respect to temperature at a given temperature for a component.

    Shows how quickly the vapor pressure of a substance changes with temperature. This derivative, dPsat/dT, is essential in boiling calculations, phase-equilibrium modeling, and estimating enthalpy of vaporization.

    Parameters
    ----------
    component : Component
        The chemical component for which to calculate the vapor pressure sensitivity.
    model_source : ModelSource
        The source model containing necessary data.
    temperature : Temperature
        The temperature at which to calculate the vapor pressure sensitivity.
    component_key : Literal[..., optional]
        The key to identify the component, by default 'Name-State'.
    **kwargs
        Additional keyword arguments.
        - mode : Literal['silent', 'log', 'attach'], optional
            Mode for time measurement logging. Default is 'log'.

    Returns
    -------
    Optional[CalcResult]
        A CalcResult object containing the vapor pressure sensitivity value, unit, and symbol, or None if calculation fails.

    Notes
    -----
    - Model source must contain vapor pressure equations for the specified component.
    - `Vapor pressure` should be returned in `Pa` unit.
    - `Temperature` should be provided in `K` unit.
    """
    try:
        # SECTION: Input validation
        if not isinstance(component, Component):
            logger.error("Invalid component provided.")
            return None

        if not isinstance(model_source, ModelSource):
            logger.error("Invalid model_source provided.")
            return None

        if not isinstance(temperature, Temperature):
            logger.error("Invalid temperature provided.")
            return None

        # SECTION: Prepare source
        Source_ = Source(model_source=model_source)

        # SECTION: Initialize ComponentVaporPressure
        vapr_props = ComponentVaporPressure(
            component=component,
            source=Source_,
            component_key=component_key
        )

        # NOTE: calculate
        res = vapr_props.calc_dPsat__dT(
            temperature=temperature
        )

        return res
    except Exception as e:
        logger.error(
            f"Error calculating vapor pressure sensitivity for component '{component.name}': {e}")
        return None


@measure_time
def calc_vapor_pressure_sensitivity_range_at_temperature(
    component: Component,
    model_source: ModelSource,
    temperatures: list[Temperature],
    component_key: Literal[
        'Name-State',
        'Formula-State',
        'Name',
        'Formula',
        'Name-Formula-State',
        'Formula-Name-State'
    ] = 'Name-State',
    **kwargs
) -> Optional[list[CalcResult]]:
    """
    Calculate the sensitivity of vapor pressure with respect to temperature over a range of temperatures for a component.

    Parameters
    ----------
    component : Component
        The chemical component for which to calculate the vapor pressure sensitivity.
    model_source : ModelSource
        The source model containing necessary data.
    temperatures : list[Temperature]
        The list of temperatures at which to calculate the vapor pressure sensitivity.
    component_key : Literal[..., optional]
        The key to identify the component, by default 'Name-State'.
    **kwargs
        Additional keyword arguments.
        - mode : Literal['silent', 'log', 'attach'], optional
            Mode for time measurement logging. Default is 'log'.

    Returns
    -------
    Optional[list[CalcResult]]
        A list of CalcResult objects containing the vapor pressure sensitivity values, units, and symbols, or None if calculation fails.

    Notes
    -----
    - Model source must contain vapor pressure equations for the specified component.
    - `Vapor pressure` should be returned in `Pa` unit.
    - `Temperature` should be provided in `K` unit.
    """
    try:
        # SECTION: Input validation
        if not isinstance(component, Component):
            logger.error("Invalid component provided.")
            return None

        if not isinstance(model_source, ModelSource):
            logger.error("Invalid model_source provided.")
            return None

        if not all(isinstance(temp, Temperature) for temp in temperatures):
            logger.error("Invalid temperatures provided.")
            return None

        # SECTION: Prepare source
        Source_ = Source(model_source=model_source)

        # SECTION: Initialize ComponentVaporPressure
        vapr_props = ComponentVaporPressure(
            component=component,
            source=Source_,
            component_key=component_key
        )

        # NOTE: calculate
        res = vapr_props.calc_dPsat__dT_range(
            temperature_range=temperatures
        )
        return res
    except Exception as e:
        logger.error(
            f"Error calculating vapor pressure sensitivity range for component '{component.name}': {e}")
        return None
