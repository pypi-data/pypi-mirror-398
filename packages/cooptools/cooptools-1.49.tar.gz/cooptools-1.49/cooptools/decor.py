import functools
import time
import logging
import inspect
from typing import Protocol, Dict
from typing_extensions import runtime_checkable

@runtime_checkable
class TimeableProtocol(Protocol):
    internally_tracked_times: Dict


def try_handler(logger: logging.Logger = None):
    def wrapper(func):
        @functools.wraps(func)
        def wrapper_handler(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except NotImplementedError as e:
                error = f"Inherited class should implement logic for {func.__name__}"
                logger.debug(error)
            except Exception as e:
                logger.exception(e)

        return wrapper_handler

    return wrapper

def timer(logger: logging.Logger = None,
          log_level: int = logging.DEBUG,
          time_tracking_class: TimeableProtocol = None):
    """Print the runtime of the decorated function"""

    if logger is None:
        logger = logging.getLogger()

    def wrap(func):

        @functools.wraps(func)
        def wrapper_timer(*args, **kwargs):
            # capture time
            start_time = time.perf_counter()  # 1
            value = func(*args, **kwargs)
            end_time = time.perf_counter()  # 2
            run_time = end_time - start_time  # 3

            # handle if a time tracker was passed
            if time_tracking_class is not None:
                time_tracking_class.internally_tracked_times.setdefault(func.__name__, 0)
                time_tracking_class.internally_tracked_times[func.__name__] += run_time

            # handle if the decorated function is a member of a time_tracking class. Need to be careful... There
            # are weird situations where the argument provided (presumably a self reference) has an overridden
            # __get_item__ that makes the hasattr call fail. It is safer to directly check for the name in the dir
            # of the object.
            if len(args) > 0 and 'internally_tracked_times' in dir(args[0]):
                args[0].internally_tracked_times.setdefault(func.__name__, 0)
                args[0].internally_tracked_times[func.__name__] += run_time


            logger.log(level=log_level, msg=f"Finished {func.__name__!r} in {run_time:.4f} secs")
            return value

        return wrapper_timer
    return wrap


def debug(func,
          logger: logging.Logger = None,
          log_level: int = logging.DEBUG,
          ):
    """Print the function signature and return value"""
    if logger is None:
        logger = logging.getLogger()

    @functools.wraps(func)
    def wrapper_debug(*args, **kwargs):
        args_repr = [repr(a) for a in args]  # 1
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]  # 2
        signature = ", ".join(args_repr + kwargs_repr)  # 3
        logger.log(level=log_level, msg=f"Caller {inspect.stack()[1][3]} is calling {func.__name__}({signature})")
        value = func(*args, **kwargs)
        logger.log(level=log_level, msg=f"{func.__name__!r} returned {value!r}")  # 4
        return value

    return wrapper_debug