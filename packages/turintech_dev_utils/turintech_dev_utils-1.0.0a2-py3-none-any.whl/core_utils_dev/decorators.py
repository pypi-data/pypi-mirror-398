# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
import time
from functools import wraps
from typing import Callable, List, Optional

# Core Source imports
from core_logging import logger

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                   Time decorators                                                    #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def timeit(func):
    """
    Measure execution time of a method.
    """

    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        time_msg = f"{total_time * 1000:.4f} ms" if total_time < 1 else f"{total_time:.4f} s"
        logger.debug(f"{time_msg} - Method {func.__name__}{args} with kwargs={kwargs}")
        return result

    return timeit_wrapper


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                  Generic decorators                                                  #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def for_all_methods(decorator: Callable, exclude: Optional[List[str]] = None):
    """This method implements a class decorator that allows decorating all the methods of said class with the indicated
    decorator. Decorate the class with a function that walks through the class's attributes and decorates callables.

    Args:
        decorator (Callable): Decorator to apply to all methods of the class.
        exclude (List[str]): List with the names of the methods that do not
            want to be decorated

    Returns:
        cls (Type[Class]]): The instance of the class.

    """
    if exclude is None:
        exclude = ["__init__"]

    def decorate(cls):
        for attr in cls.__dict__:
            if callable(getattr(cls, attr)) and attr not in exclude:
                setattr(cls, attr, decorator(getattr(cls, attr)))
        return cls

    return decorate
