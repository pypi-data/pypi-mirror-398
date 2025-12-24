import logging
from typing import Literal, Dict
import numpy as np
from pyThermoDB.core import TableEquation
from pyThermoDB.models import EquationResult
from scipy.integrate import quad, simpson


# NOTE: Logger
logger = logging.getLogger(__name__)


def integrate_function(
    func: TableEquation,
    var_symbol: str,
    vars: Dict[str, float],
    a: float,
    b: float,
    *,
    integral_mode: Literal["quad", "trapz", "simps"] = "quad",
    n_points: int = 1000,
    decimal_accuracy: int = 4,
    **kwargs
) -> float:
    """
    Integrate a quantity-returning function over [a, b].
    """
    try:
        # SECTION: Validate inputs
        if a >= b:
            logger.error(
                f"Invalid integration limits: a={a} must be less than b={b}")
            return 0.0

        # >> vars
        if var_symbol in vars:
            logger.warning(
                f"Variable symbol '{var_symbol}' is also in vars; it will be overwritten during integration.")

        # >> check vars
        if not isinstance(vars, dict):
            logger.error(
                "vars must be a dictionary of variable names to values.")
            return 0.0

        if all(not isinstance(v, (int, float)) for v in vars.values()):
            logger.warning("vars must contain at least one numeric value.")

        if n_points < 2 and integral_mode in {"trapz", "simps"}:
            logger.error(
                f"n_points must be at least 2 for '{integral_mode}' method; got n_points={n_points}")
            return 0.0

        # >> check
        if integral_mode not in {"quad", "trapz", "simps"}:
            logger.error(
                f"Invalid integral_mode: {integral_mode}. Must be 'quad', 'trapz', or 'simps'.")
            return 0.0

        # NOTE: input settings
        var_symbol = var_symbol.strip()

        # SECTION: Integration methods
        if integral_mode == "quad":
            # SECTION: quad expects a float -> float function
            def integrand(x: float) -> float:
                # NOTE: Set variable
                args = {**vars, var_symbol: x}
                # EVALUATE function
                result: EquationResult = func.cal(
                    message='',
                    decimal_accuracy=decimal_accuracy,
                    **args
                )

                # NOTE: Error handling
                if result['value'] is None:
                    logger.error(
                        f"Function evaluation returned None at x={x}")
                    return 0.0
                # NOTE: Type checking
                if not isinstance(result['value'], (int, float)):
                    logger.error(
                        f"Function evaluation returned non-numeric value at x={x}: {result['value']}")
                    return 0.0

                # NOTE: Return value
                return result['value']

            integral_value, _err = quad(integrand, a, b)
        else:
            # SECTION: Grid-based methods: build x-grid and evaluate func
            x = np.linspace(a, b, n_points)
            y = np.empty_like(x)

            for i, xi in enumerate(x):
                result: EquationResult = func.cal(
                    message='', decimal_accuracy=4, **{**vars, var_symbol: xi})
                # NOTE: Error handling
                if result['value'] is None:
                    logger.error(
                        f"Function evaluation returned None at x={xi}")
                    return 0.0
                # NOTE: Type checking
                if not isinstance(result['value'], (int, float)):
                    logger.error(
                        f"Function evaluation returned non-numeric value at x={xi}: {result['value']}")
                    return 0.0

                # NOTE: Store value
                y[i] = result['value']

            # SECTION: Perform integration
            if integral_mode == "trapz":
                # ! Trapezoidal rule
                integral_value = float(np.trapezoid(y, x))
            elif integral_mode == "simps":
                # ! Simpson's rule
                integral_value = float(simpson(y, x))
            else:
                logger.error(
                    f"Unsupported integral_mode: {integral_mode}")
                return 0.0

        return integral_value
    except Exception as e:
        logger.exception(f"Error during integration: {e}")
        return 0.0
