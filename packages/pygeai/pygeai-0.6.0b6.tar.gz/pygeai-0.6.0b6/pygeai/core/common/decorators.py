import functools
import sys
import time

from pygeai.core.common.exceptions import ServerResponseError


def measure_execution_time(func):
    """
    Measure execution time of method or function.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        sys.stdout.write(f"Measuring execution time for: {func.__name__}")
        try:
            start_time = time.time()
            result = func(*args, **kwargs)
            finish_time = time.time()
            time_difference = finish_time - start_time
            execution_time = round(time_difference, 6)
        except Exception as e:
            sys.stdout.write(f"Error measuring execution time: {e}")
        else:
            sys.stdout.write(f"Function {func.__name__} executed in {execution_time} s")
            return result

    return wrapper


def handler_server_error(func):
    """
    Intercepts server errors
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if "error" in result:
            raise ServerResponseError(
                f"There was an error communicating with the server: {result.get('error')}"
            )

        return result

    return wrapper
