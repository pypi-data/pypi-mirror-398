# import libs
import logging
from typing import Dict, Literal, Optional, Any
from pyThermoDB.core import TableEquation
import pycuc
from scipy import integrate
from pyThermoLinkDB.models.component_models import ComponentEquationSource
# locals

# NOTE: Logger
logger = logging.getLogger(__name__)


def Cp_integral(
    eq_src: ComponentEquationSource,
    T_ref: float,
    T: float,
):
    """
    Integrate the heat capacity equation from T_ref to T (J/mol).

    Parameters
    ----------
    eq_src : ComponentEquationSource
        The heat capacity equation to integrate.
    T_ref : float
        The reference temperature (lower limit of integration).
    T : float
        The target temperature (upper limit of integration).

    Returns
    -------
    Optional[float]
        The integrated heat capacity value, or None if an error occurs.
    """
    try:
        # SECTION: equation expression
        # NOTE: extract Cp equation
        # ! args
        eq_args = eq_src.args
        # ! arg symbols
        eq_arg_symbols = eq_src.arg_symbols
        # ! returns
        eq_returns = eq_src.returns
        # >> get return units
        returns_outer_key, returns_inner = next(
            iter(eq_returns.items()))
        eq_return_unit: str = returns_inner['unit']

        # ! return symbols
        eq_return_symbols = eq_src.return_symbols
        # ! equation
        Cp_eq = eq_src.source

        # NOTE: Cp integral
        # unit: [J/mol]
        # init unit_
        unit_ = None

        # scipy integrate method
        def integrand_1(T):
            '''
            Integral of Cp equation, unit: [J/mol]
            '''
            nonlocal unit_
            res_ = Cp_eq.cal(T=T)
            cal_ = res_.get('value', None)
            unit_ = res_.get('unit', None)

            # >> check
            if cal_ is None:
                logger.error(
                    f"Failed to calculate Cp for equation at T={T} K.")
                raise

            if not isinstance(cal_, str) and not isinstance(cal_, float):
                logger.error(
                    f"Invalid Cp value at T={T} K: {cal_}")
                raise

            if unit_ is None:
                logger.error(
                    f"Equation does not have a unit for Cp at T={T} K.")
                raise

            return cal_

        # ! check integral
        function_integral = Cp_eq.body_integral

        # check
        if function_integral:
            # calc
            # method 1
            _eq_Cp_integral = Cp_eq.cal_integral(
                T1=T_ref,
                T2=T
            )
        else:
            # calc
            # method 2
            _eq_Cp_integral, _ = integrate.quad(
                integrand_1,
                T_ref,
                T
            )

            # check
            if unit_ is None:
                logger.error(
                    f"Equation does not have a unit for Cp integral.")
                raise

            # >> check
            if _eq_Cp_integral is None:
                logger.error(
                    f"Failed to calculate Cp integral from T={T_ref} K to T={T} K.")
                return None

            # TODO: FINALLY convert Cp equation to [J/mol.K] (after integration means the unit is [J/mol])
            _eq_Cp_integral = pycuc.to(
                _eq_Cp_integral,
                f"{unit_} => J/mol.K"
            )

        return _eq_Cp_integral
    except Exception as e:
        logger.error(
            f"Error integrating Cp equation from T={T_ref} K to T={T} K: {e}")
        return None


def Cp__RT_integral(
    eq_src: ComponentEquationSource,
    T_ref: float,
    T: float,
    R: float,
):
    """
    Integrate the dimensionless heat capacity equation Cp/RT from T_ref to T.

    Parameters
    ----------
    eq_src : ComponentEquationSource
        The heat capacity equation to integrate.
    T_ref : float
        The reference temperature (lower limit of integration).
    T : float
        The target temperature (upper limit of integration).
    R : float
        The universal gas constant.

    Returns
    -------
    Optional[float]
        The integrated dimensionless heat capacity value, or None if an error occurs.
    """
    try:
        # SECTION: equation expression
        # NOTE: extract Cp equation
        # ! args
        eq_args = eq_src.args
        # ! arg symbols
        eq_arg_symbols = eq_src.arg_symbols
        # ! returns
        eq_returns = eq_src.returns
        # >> get return units
        returns_outer_key, returns_inner = next(
            iter(eq_returns.items()))
        eq_return_unit: str = returns_inner['unit']

        # ! return symbols
        eq_return_symbols = eq_src.return_symbols
        # ! equation
        Cp_eq = eq_src.source

        # NOTE: integral [Cp/RT]
        # unit: [dimensionless]
        # init unit
        unit_ = None
        # scipy integrate method

        def integrand_0(T):
            '''
            Dimensionless integrand for Cp/RT calculation.
            '''
            # modify the nonlocal variable
            nonlocal unit_
            res_ = Cp_eq.cal(T=T)
            cal_ = res_.get('value', None)
            unit_ = res_.get('unit', None)
            if cal_ is None:
                logger.error(
                    f"Failed to calculate Cp for equation at T={T} K.")
                raise

            if not isinstance(cal_, str) and not isinstance(cal_, float):
                logger.error(
                    f"Invalid Cp value at T={T} K: {cal_}")
                raise

            if unit_ is None:
                logger.error(
                    f"Equation does not have a unit for Cp at T={T} K.")
                raise

            res = cal_/(T*R)
            return res

        # ! check custom
        custom_integral = Cp_eq.custom_integral

        # >> check
        if custom_integral.get('Cp/RT', None) is not None:
            # calc
            # method 1
            _eq_Cp_integral_Cp__RT = Cp_eq.cal_custom_integral(
                'Cp/RT',
                T1=T_ref,
                T2=T
            )
        else:
            # calc
            # method 2
            _eq_Cp_integral_Cp__RT, _ = integrate.quad(
                integrand_0,
                T_ref,
                T
            )

            # >> check
            if _eq_Cp_integral_Cp__RT is None:
                logger.error(
                    f"Failed to calculate Cp/RT integral from T={T_ref} K to T={T} K.")
                return None

            # check
            if unit_ is None:
                logger.error(
                    f"Equation does not have a unit for Cp/RT integral.")
                raise

            # TODO: FINALLY convert Cp equation to [J/mol.K]
            _eq_Cp_integral_Cp__RT = pycuc.to(
                _eq_Cp_integral_Cp__RT,
                f"{unit_} => J/mol.K"
            )

        return _eq_Cp_integral_Cp__RT
    except Exception as e:
        logger.error(
            f"Error integrating Cp/RT equation from T={T_ref} K to T={T} K: {e}")
        return None
