from typing import Callable
import functools
import time


def timer(func: Callable) -> Callable:
    """
    Decorator to print the runtime of the decorated function.

    It measures the execution time using `time.perf_counter()` and prints
    the result to stdout.

    Args:
        func: The function to decorate.

    Returns:
        The wrapped function.
    """

    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        start_time = time.perf_counter()
        value = func(*args, **kwargs)
        end_time = time.perf_counter()
        run_time = end_time - start_time
        if run_time <= 60:
            rt = f"{run_time:.4f} secs"
        else:
            rt = f"{int(run_time / 60)} min {run_time % 60:.4f} secs"
        print(f"Finished {func.__name__!r} in {rt}")
        return value

    return wrapper_timer


def debug(func: Callable) -> Callable:
    """
    Decorator to print the function signature and return value.

    It prints the function name, its arguments, and its return value.
    Useful for quick debugging without using a debugger.

    Args:
        func: The function to decorate.

    Returns:
        The wrapped function.
    """

    @functools.wraps(func)
    def wrapper_debug(*args, **kwargs):
        args_repr = [repr(a) for a in args]
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
        signature = ", ".join(args_repr + kwargs_repr)
        print(f"Calling {func.__name__}({signature})")
        value = func(*args, **kwargs)
        print(f"{func.__name__!r} returned {value!r}")
        return value

    return wrapper_debug
