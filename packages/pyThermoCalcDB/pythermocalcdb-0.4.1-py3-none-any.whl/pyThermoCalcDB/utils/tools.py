import time
import logging
from functools import wraps
from typing import Literal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ModeType = Literal["silent", "log", "attach"]


def measure_time(func):
    '''Decorator to measure the execution time of a function.

    Parameters
    ----------
    func : Callable
        The function to be decorated.

    Returns
    -------
    Callable
        The wrapped function with time measurement.

    Notes
    -----
    - The decorator adds a 'mode' keyword argument to the decorated function.
    - 'mode' can be 'silent', 'log', or 'attach':
        - 'silent': No logging or attachment of time.
        - 'log': Logs the execution time.
        - 'attach': Logs and attaches the execution time to the result.
    - default mode is 'silent'.
    '''
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Extract mode safely
        mode: ModeType = kwargs.pop("mode", "silent")

        start = time.process_time()
        result = func(*args, **kwargs)
        end = time.process_time()

        elapsed = end - start

        if mode == "silent":
            return result

        if mode == "log":
            logger.info(
                f"{func.__name__} executed in {elapsed:.6f} seconds (CPU time)")
            return result

        if mode == "attach":
            logger.info(
                f"{func.__name__} executed in {elapsed:.6f} seconds (CPU time)")
            if isinstance(result, dict):
                result["computation_time"] = elapsed
            else:
                result = {
                    "result": result,
                    "computation_time": elapsed
                }
            return result

        raise ValueError("mode must be 'silent', 'log', or 'attach'")
    return wrapper
