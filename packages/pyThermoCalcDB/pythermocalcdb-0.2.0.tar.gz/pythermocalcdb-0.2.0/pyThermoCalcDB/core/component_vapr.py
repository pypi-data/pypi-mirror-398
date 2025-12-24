# import libs
import logging
import numpy as np
from typing import Optional, Dict, List, Literal, Any, Tuple
from pythermodb_settings.models import Component, Temperature, Pressure
from pyThermoDB.core import TableEquation
from pythermodb_settings.utils import set_component_id
from pyThermoDB.models import EquationResult
from scipy.optimize import root_scalar, least_squares
import pycuc
from math import pow
from pyThermoLinkDB.thermo import Source
from pyThermoLinkDB.models.component_models import ComponentEquationSource
# local
from ..configs.thermo_props import VaPr_SYMBOL, VaPr_UNIT
from ..configs.constants import R_J_molK, T_ref_K
from ..models import CalcResult

# NOTE: logger
logger = logging.getLogger(__name__)


class ComponentVaporPressure:
    """
    Component vapor pressure class used to calculate the following properties:
    - Saturation pressure VaPr(T)
    - Enthalpy of vaporization EnVap(T)
    - Temperature at given vapor pressure TeVaPr(P)

    Notes
    -----
    - All calculations are based on the vapor pressure equation retrieved from the source for the given component.
    - `Pressure` unit defined in the model source should be in `Pa`.
    - `Temperature` unit defined in the model source should be in `K`.
    """

    # NOTE: attributes
    T_ref = T_ref_K  # reference temperature in K
    R = R_J_molK  # universal gas constant in J/mol.K

    def __init__(
        self,
        component: Component,
        source: Source,
        component_key: Literal[
            'Name-State',
            'Formula-State',
            'Name',
            'Formula',
            'Name-Formula-State',
            'Formula-Name-State'
        ] = 'Name-State',
    ) -> None:
        """
        Initialize HSGProperties with a component and source.

        Parameters
        ----------
        component : Component
            The chemical component for which HSG properties are to be calculated, it consists of the following attributes:
                - name: str
                - formula: str
                - state: str
                - mole_fraction: float, optional
        source : Source
            The source containing data for calculations.
        component_key : Literal
            The key to identify the component in the source data. Defaults to 'Name-State'.
        """
        # NOTE: component
        self.component = component
        # NOTE: source
        self.source = source
        # NOTE: component key
        self.component_key = component_key

        # SECTION: set component id
        self.component_id = set_component_id(
            component=self.component,
            component_key=self.component_key
        )

        # SECTION: get vapor pressure equation source
        self.vapor_pressure_equation: ComponentEquationSource = self._get_vapor_pressure_equation()

        # NOTE: equation
        # ! vapor pressure equation
        self.VaPr_eq: TableEquation = self.vapor_pressure_equation.source
        # ! vapor pressure equation args/returns/symbols
        self.VaPr_args: Dict[
            str,
            Any
        ] = self.vapor_pressure_equation.args or {}
        self.VaPr_arg_symbols: Dict[
            str,
            Any
        ] = self.vapor_pressure_equation.arg_symbols or {}
        self.VaPr_returns: Dict[
            str,
            Any
        ] = self.vapor_pressure_equation.returns or {}
        self.VaPr_return_symbols: Dict[
            str,
            Any
        ] = self.vapor_pressure_equation.return_symbols or {}

        # >> get return units
        returns_outer_key, returns_inner = next(
            iter(self.VaPr_returns.items()))
        self.VaPr_return_unit: str = returns_inner['unit']

    def _get_vapor_pressure_equation(self) -> ComponentEquationSource:
        """
        Retrieve the vapor pressure equation for the component from the source.

        Returns
        -------
        ComponentEquationSource
            The vapor pressure equation source for the component.
        """
        try:
            # SECTION: get equations for component
            equations = self.source.eq_builder(
                components=[self.component],
                prop_name=VaPr_SYMBOL,
                component_key=self.component_key  # type: ignore
            )

            if not equations:
                logger.warning(
                    f'No vapor pressure equation found for component ID: {self.component_id}'
                )
                raise ValueError(
                    f'No vapor pressure equation found for component ID: {self.component_id}'
                )

            # SECTION: select for component
            eq: ComponentEquationSource | None = equations.get(
                self.component_id
            )

            # >> check
            if eq is None:
                logger.warning(
                    f'No vapor pressure equation found for component ID: {self.component_id}'
                )
                raise ValueError(
                    f'No vapor pressure equation found for component ID: {self.component_id}')

            return eq
        except Exception as e:
            logger.error(
                f'Error retrieving vapor pressure equation for component ID: {self.component_id} - {e}'
            )
            raise e

    def calc_VaPr(
            self,
            temperature: Temperature
    ) -> CalcResult:
        """
        Calculate the saturation vapor pressure at a given temperature.

        Parameters
        ----------
        temperature : Temperature
            Temperature in Kelvin.

        Returns
        -------
        CalcResult
            Saturation vapor pressure in Pa, encapsulated in CalcResult as:
            - value: float
            - unit: str
            - symbol: str
        """
        try:
            # SECTION: validate temperature
            T_value = temperature.value
            T_unit = temperature.unit

            # NOTE: check unit from args
            if "T" in self.VaPr_arg_symbols:
                # ! >> get expected unit from args >>
                # ? as pycuc handle unit conversion for temperature (careful with other units)
                arg_T_unit = self.VaPr_arg_symbols["T"].get(
                    "unit",
                    "K"
                )

                if T_unit != arg_T_unit:
                    T_value = pycuc.to(T_value, f"{T_unit} => {arg_T_unit}")
                    T_unit = arg_T_unit
            else:
                logger.warning(
                    "Temperature unit not specified in vapor pressure equation arguments. Assuming Kelvin."
                )
                raise

            # >> check temperature value
            if T_value <= 0.0:
                raise ValueError(
                    "Temperature must be greater than zero Kelvin.")

            # SECTION: calculate vapor pressure
            VaPr_result: EquationResult = self.VaPr_eq.cal(
                **{**self.VaPr_args, **{"T": T_value}}
            )
            # >> value
            VaPr_value = float(VaPr_result['value']) if isinstance(
                VaPr_result['value'], (float, int)) else None
            # >> check
            if VaPr_value is None:
                raise ValueError(
                    f"Failed to calculate vapor pressure at T={temperature} K."
                )

            # NOTE: unit conversion to Pa
            VaPr_value = pycuc.to(
                VaPr_value,
                f"{self.VaPr_return_unit} => Pa"
            )

            # res
            res = {
                'value': VaPr_value,
                'unit': 'Pa',
                'symbol': 'VaPr'
            }

            # >> set
            res = CalcResult(**res)

            return res
        except Exception as e:
            logger.error(
                f"Error calculating vapor pressure at T={temperature} K: {e}")
            raise e

    def calc_VaPr_range(
            self,
            temperature_range: List[Temperature]
    ) -> List[CalcResult]:
        """
        Calculate the saturation vapor pressure over a range of temperatures.

        Parameters
        ----------
        temperature_range : List[Temperature]
            List of temperatures in Kelvin.

        Returns
        -------
        List[CalcResult]
            List of saturation vapor pressures in Pa, each encapsulated in CalcResult as:
            - value: float
            - unit: str
            - symbol: str
        """
        try:
            results: List[CalcResult] = []

            for T in temperature_range:
                VaPr_result = self.calc_VaPr(temperature=T)
                results.append(VaPr_result)

            return results
        except Exception as e:
            logger.error(
                f"Error calculating vapor pressure range: {e}")
            raise e

    def calc_dPsat__dT(
            self,
            temperature: Temperature,
            h: Optional[float] = None
    ) -> CalcResult:
        """
        Calculate the derivative of saturation pressure with respect to temperature.

        Parameters
        ----------
        temperature : float
            Temperature in Kelvin.
        h : Optional[float]
            Small temperature increment for numerical differentiation. If None, a default value is used.

        Returns
        -------
        CalcResult
            The derivative dPsat/dT in Pa/K encapsulated in CalcResult as:
            - value: float
            - unit: str
            - symbol: str
        """
        try:
            # SECTION: get temperature value
            T_value = temperature.value
            T_unit = temperature.unit

            # NOTE: check unit from args
            if "T" in self.VaPr_arg_symbols:
                arg_T_unit = self.VaPr_arg_symbols["T"].get(
                    "unit",
                    "K"
                )

                if T_unit != arg_T_unit:
                    T_value = pycuc.to(T_value, f"{T_unit} => {arg_T_unit}")
                    T_unit = arg_T_unit
            else:
                logger.warning(
                    "Temperature unit not specified in vapor pressure equation arguments. Assuming Kelvin."
                )
                raise

            # SECTION: validate temperature
            if T_value <= 0.0:
                raise ValueError(
                    "Temperature must be greater than zero Kelvin."
                )

            # SECTION: numerical derivative
            # NOTE: central difference
            delta_T = 1e-5 if h is None else h

            # NOTE: calculate Psat at T + delta_T and T - delta_T
            T_plus = T_value + delta_T
            T_minus = T_value - delta_T

            # >> calculate Psat values
            # ! same unit as args
            VaPr_plus = self.calc_VaPr(
                Temperature(value=T_plus, unit='K')
            )
            # >> value
            VaPr_plus_value = float(VaPr_plus.value)

            # ! same unit as args
            VaPr_minus = self.calc_VaPr(
                Temperature(value=T_minus, unit='K')
            )
            # >> value
            VaPr_minus_value = float(VaPr_minus.value)

            # NOTE: unit conversion to Pa
            VaPr_plus_value = pycuc.to(
                VaPr_plus_value,
                f"{self.VaPr_return_unit} => Pa"
            )
            VaPr_minus_value = pycuc.to(
                VaPr_minus_value,
                f"{self.VaPr_return_unit} => Pa"
            )

            res_val = (VaPr_plus_value - VaPr_minus_value) / (2 * delta_T)

            res = {
                'value': res_val,
                'unit': 'Pa/K',
                'symbol': 'dPsat/dT'
            }

            # >> set
            res = CalcResult(**res)

            return res
        except Exception as e:
            logger.error(
                f"Error calculating dPsat/dT at T={temperature} K: {e}")
            raise e

    def calc_dPsat__dT_range(
            self,
            temperature_range: List[Temperature],
            h: Optional[float] = None
    ) -> List[CalcResult]:
        """
        Calculate the derivative of saturation pressure with respect to temperature over a range of temperatures.

        Parameters
        ----------
        temperature_range : List[Temperature]
            List of temperatures in Kelvin.
        h : Optional[float]
            Small temperature increment for numerical differentiation. If None, a default value is used.

        Returns
        -------
        List[CalcResult]
            List of derivatives dPsat/dT in Pa/K, each encapsulated in CalcResult as:
            - value: float
            - unit: str
            - symbol: str
        """
        try:
            results: List[CalcResult] = []

            for T in temperature_range:
                dPsat_dT_result = self.calc_dPsat__dT(
                    temperature=T,
                    h=h
                )
                results.append(dPsat_dT_result)

            return results
        except Exception as e:
            logger.error(
                f"Error calculating dPsat/dT range: {e}")
            raise e

    def calc_EnVap_Clapeyron(
            self,
            temperature: Temperature,
            h: Optional[float] = None
    ) -> CalcResult:
        """
        Calculate the enthalpy of vaporization using the Clausius-Clapeyron relation.

        Parameters
        ----------
        temperature : Temperature
            Temperature in Kelvin.
        h : Optional[float]
            Small temperature increment for numerical differentiation. If None, a default value is used.

        Returns
        -------
        CalcResult
            Enthalpy of vaporization in J/mol encapsulated in CalcResult as:
            - value: float
            - unit: str
            - symbol: str
        """
        try:
            # SECTION: get temperature value
            T_value = temperature.value
            T_unit = temperature.unit

            # NOTE: check unit from args
            if "T" in self.VaPr_arg_symbols:
                arg_T_unit = self.VaPr_arg_symbols["T"].get(
                    "unit",
                    "K"
                )

                if T_unit != arg_T_unit:
                    T_value = pycuc.to(T_value, f"{T_unit} => {arg_T_unit}")
                    T_unit = arg_T_unit

            # SECTION: validate temperature
            if T_value <= 0.0:
                raise ValueError(
                    "Temperature must be greater than zero Kelvin.")

            # SECTION: calculate Psat at T
            VaPr_result = self.calc_VaPr(
                Temperature(value=T_value, unit='K')
            )
            # >> value
            VaPr_value = float(VaPr_result.value)

            # NOTE: unit conversion to Pa
            VaPr_value = pycuc.to(
                VaPr_value,
                f"{self.VaPr_return_unit} => Pa"
            )

            # SECTION: calculate dPsat/dT
            dPsat_dT = self.calc_dPsat__dT(temperature, h=h)
            # >> value
            dPsat_dT_value = float(dPsat_dT.value)

            # SECTION: Clausius–Clapeyron relation
            R = self.R  # J/mol.K

            EnVap = (R * pow(T_value, 2) / VaPr_value) * dPsat_dT_value

            # res
            res = {
                'value': EnVap,
                'unit': 'J/mol',
                'symbol': 'EnVap'
            }

            # >> set
            res = CalcResult(**res)

            return res
        except Exception as e:
            logger.error(
                f"Error calculating EnVap via Clausius–Clapeyron at T={temperature} K: {e}")
            raise e

    def calc_EnVap_Clapeyron_range(
            self,
            temperature_range: List[Temperature],
            h: Optional[float] = None
    ) -> List[CalcResult]:
        """
        Calculate the enthalpy of vaporization using the Clausius-Clapeyron relation over a range of temperatures.

        Parameters
        ----------
        temperature_range : List[Temperature]
            List of temperatures in Kelvin.
        h : Optional[float]
            Small temperature increment for numerical differentiation. If None, a default value is used.

        Returns
        -------
        List[CalcResult]
            List of enthalpies of vaporization in J/mol, each encapsulated in CalcResult as:
            - value: float
            - unit: str
            - symbol: str
        """
        try:
            results: List[CalcResult] = []

            for T in temperature_range:
                EnVap_result = self.calc_EnVap_Clapeyron(
                    temperature=T,
                    h=h
                )
                results.append(EnVap_result)

            return results
        except Exception as e:
            logger.error(
                f"Error calculating EnVap via Clausius–Clapeyron range: {e}")
            raise e

    def calc_TeVaPr(
            self,
            pressure: Pressure,
            temperature_guess: Optional[Temperature] = None,
            T_bracket: Optional[Tuple[Temperature, Temperature]] = None,
            method: str = "auto",
            tol: float = 1e-6,
            max_iter: int = 50,
            h: Optional[float] = None
    ) -> CalcResult:
        """
        Calculate the temperature at a given vapor pressure using the bisection method.

        Parameters
        ----------
        pressure : Pressure
            Vapor pressure in Pa.
        temperature_guess : Temperature, optional
            Initial guess for temperature in Kelvin.
        T_bracket : Tuple[Temperature, Temperature], optional
            Bracket (min, max) for temperature in Kelvin.
        method : str
            Method to use for root finding. Defaults to "auto".
            - "auto": use brentq if bracket is provided, else Newton with derivative
            - "brentq": robust bracketing method (requires T_bracket)
            - "bisect": slower but very robust (requires T_bracket)
            - "newton": uses derivative dPsat/dT and T_guess
            - "least_squares": minimizes (Psat(T) - P)^2 using least squares optimization
        tol : float
            Tolerance for convergence.
        max_iter : int
            Maximum number of iterations.
        h : Optional[float]
            Small temperature increment for numerical differentiation in dPsat/dT. If None, a default value is used.

        Returns
        -------
        CalcResult
            Temperature in Kelvin corresponding to the given vapor pressure encapsulated in CalcResult as:
            - value: float
            - unit: str
            - symbol: str

        Notes
        -----
        - The temperature is found by solving Psat(T) - P = 0 using root scalar method.
        - Bracketing interval [K] such that Psat(T_low) - P and Psat(T_high) - P have opposite signs. Used for robust bracketing methods.
        """
        try:
            # SECTION: validate pressure
            P_value = pressure.value
            P_unit = pressure.unit

            # NOTE: check unit
            if P_unit != "Pa":
                P_value = pycuc.to(P_value, f"{P_unit} => Pa")
                P_unit = "Pa"

            # SECTION: process temperature guess
            if temperature_guess is not None:
                T_guess_value = temperature_guess.value
                T_guess_unit = temperature_guess.unit

                # NOTE: check unit from args
                if "T" in self.VaPr_arg_symbols:
                    arg_T_unit = self.VaPr_arg_symbols["T"].get(
                        "unit",
                        "K"
                    )

                    if T_guess_unit != arg_T_unit:
                        T_guess_value = pycuc.to(
                            T_guess_value,
                            f"{T_guess_unit} => {arg_T_unit}"
                        )
                        T_guess_unit = arg_T_unit
                else:
                    logger.warning(
                        "Temperature unit not specified in vapor pressure equation arguments. Assuming Kelvin."
                    )
                    raise
            else:
                T_guess_value = None

            # SECTION: process T_bracket
            if T_bracket is not None:
                T_low, T_high = T_bracket

                T_low_value = T_low.value
                T_low_unit = T_low.unit

                T_high_value = T_high.value
                T_high_unit = T_high.unit

                # NOTE: check unit from args
                if "T" in self.VaPr_arg_symbols:
                    arg_T_unit = self.VaPr_arg_symbols["T"].get(
                        "unit",
                        "K"
                    )

                    if T_low_unit != arg_T_unit:
                        T_low_value = pycuc.to(
                            T_low_value,
                            f"{T_low_unit} => {arg_T_unit}"
                        )
                        T_low_unit = arg_T_unit

                    if T_high_unit != arg_T_unit:
                        T_high_value = pycuc.to(
                            T_high_value,
                            f"{T_high_unit} => {arg_T_unit}"
                        )
                        T_high_unit = arg_T_unit
                else:
                    logger.warning(
                        "Temperature unit not specified in vapor pressure equation arguments. Assuming Kelvin."
                    )
                    raise

                T_bracket_values = (T_low_value, T_high_value)
            else:
                T_bracket_values = None

            # SECTION: define function to find root

            def func(T: float) -> float:
                '''
                Function for root finding: Psat(T) - P = 0

                Parameters
                ----------
                T : float
                    Temperature in Kelvin.
                '''
                VaPr_result = self.calc_VaPr(
                    Temperature(value=T, unit='K')
                )
                # >> value
                VaPr_value = float(VaPr_result.value)

                # NOTE: unit conversion to Pa
                VaPr_value = pycuc.to(
                    VaPr_value,
                    f"{self.VaPr_return_unit} => Pa"
                )

                return VaPr_value - P_value

            # SECTION: define derivative function
            def func_prime(T: float) -> float:
                '''
                Derivative of function for root finding: dPsat/dT
                Parameters
                ----------
                T : float
                    Temperature in Kelvin.
                '''
                return self.calc_dPsat__dT(
                    Temperature(value=T, unit='K'),
                    h=h
                ).value

            # SECTION: select method
            method = method.lower()

            # NOTE: auto-selection
            if method == "auto":
                if T_bracket is not None:
                    method = "brentq"
                else:
                    method = "newton"

            # NOTE: root finding
            if method == "newton":
                if temperature_guess is None:
                    raise ValueError(
                        "temperature_guess must be provided for method 'newton'."
                    )

                # ! root finding using Newton's method
                sol = root_scalar(
                    func,
                    fprime=func_prime,
                    method='newton',
                    x0=temperature_guess,
                    xtol=tol,
                    maxiter=max_iter
                )
            elif method in ("brentq", "bisect"):
                # >> check bracket
                if T_bracket is None:
                    raise ValueError(
                        f"T_bracket must be provided for method '{method}'."
                    )

                # ! root finding using bracketing method
                sol = root_scalar(
                    func,
                    bracket=T_bracket_values,
                    method=method,
                    xtol=tol,
                    maxiter=max_iter
                )
            elif method in ("lsq", "least_squares"):
                if temperature_guess is None:
                    raise ValueError(
                        "temperature_guess must be provided for method 'least_squares'."
                    )

                T_bounds = None
                if T_bracket_values is not None:
                    T_bounds = (T_bracket_values[0], T_bracket_values[1])

                # >> check temperature guess
                if T_guess_value is None:
                    raise ValueError(
                        "temperature_guess must be provided for method 'least_squares'."
                    )

                # ! root finding using least_squares
                Tsat_value = self._Tsat_least_squares(
                    P=P_value,
                    T_guess=T_guess_value,
                    T_bounds=T_bounds,
                    tol=tol,
                    max_iter=max_iter
                )

                # >> set solution object
                class Sol:
                    def __init__(self, root: float, converged: bool):
                        self.root = root
                        self.converged = converged

                sol = Sol(root=Tsat_value, converged=True)

            else:
                raise ValueError(
                    "method must be 'auto', 'newton', 'brentq', or 'bisect'."
                )

            if not sol.converged:
                raise RuntimeError(
                    f"Root finding did not converge for pressure={pressure} Pa."
                )

            res = {
                'value': sol.root,
                'unit': 'K',
                'symbol': 'Tsat'
            }

            # >> set
            res = CalcResult(**res)

            return res
        except Exception as e:
            logger.error(
                f"Error calculating TeVaPr for P={pressure} Pa: {e}"
            )
            raise e

    def _Tsat_least_squares(
        self,
        P: float,
        T_guess: float,
        T_bounds: Optional[Tuple[float, float]] = None,
        tol: float = 1e-6,
        max_iter: int = 50,
    ) -> float:
        """
        Saturation temperature at given pressure P using least_squares.

        Minimizes (Psat(T) - P)^2 with T as the only variable.

        Parameters
        ----------
        P : float
            Target pressure [Pa].
        T_guess : float
            Initial guess for temperature [K].
        T_bounds : (T_min, T_max), optional
            Bounds for temperature [K]. If None, unbounded.
        tol : float
            Tolerance on the residual (Psat - P) [Pa].
        max_iter : int
            Maximum number of iterations.

        Returns
        -------
        float
            Tsat [K].

        Raises
        ------
        RuntimeError
            If the least-squares solver does not converge.
        """
        try:
            # SECTION: define residual function
            def residual(T_arr: np.ndarray) -> np.ndarray:
                T = float(T_arr[0])
                return np.array([self.calc_VaPr(Temperature(
                    value=T,
                    unit='K'
                )).value - P],
                    dtype=float
                )

            # SECTION: set bounds
            if T_bounds is None:
                bounds = (-np.inf, np.inf)
            else:
                bounds = (T_bounds[0], T_bounds[1])

            # SECTION: perform least-squares optimization
            result = least_squares(
                residual,
                x0=np.array([T_guess], dtype=float),
                bounds=bounds,
                xtol=tol,
                ftol=tol,
                max_nfev=max_iter,
            )

            # >> check convergence
            if not result.success:
                raise RuntimeError(
                    f"Tsat least_squares did not converge: {result.message}")

            # res
            return float(result.x[0])
        except Exception as e:
            logger.error(
                f"Error in tsat_least_squares for P={P} Pa: {e}"
            )
            raise e
