# pylint: disable=broad-exception-caught
# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
import functools
from typing import Callable, NoReturn, Optional, Type

from core_common_data_types.type_definitions import GenericT
from core_exceptions.core import BaseGenericException, ElementNotFoundException
from core_logging import logger
from core_logging.logger_utils import LoggerType

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                           specifies all modules that shall be loaded and imported into the                           #
#                                current namespace when we use 'from package import *'                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = ["catch_exception", "inner_wrapper"]


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                             Exception handler decorator                                              #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def catch_exception(
    run_func: Optional[Callable[..., GenericT]] = None, *, default: Type[BaseGenericException] = BaseGenericException
) -> Callable[..., GenericT]:
    """
    This function implements a decorator to catch and handle the exceptions that are thrown in the methods of the
    services.
    """

    if run_func is None:
        return functools.partial(catch_exception, default=default)  # type: ignore

    @functools.wraps(run_func)
    def func(*args, **kwargs) -> GenericT:
        return inner_wrapper(
            logger_=logger, logger_depth=2, default=default, run_func=run_func, args=args, kwargs=kwargs
        )

    return func


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                      Utilities                                                       #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def inner_wrapper(
    logger_: LoggerType,
    logger_depth: int,
    default: Type[BaseGenericException],
    run_func: Callable[..., GenericT],
    args,
    kwargs,
) -> GenericT:
    try:
        return run_func(*args, **kwargs)
    except (FileNotFoundError, ModuleNotFoundError) as error:
        _raise_exception_args(
            error=error,
            service_error=ElementNotFoundException(message=str(error)),
            logger_=logger_,
            logger_depth=logger_depth,
        )
    except BaseGenericException as error:
        _raise_exception_args(error=error, service_error=error, logger_=logger_, logger_depth=logger_depth)
    except Exception as error:
        _raise_exception_args(
            error=error, service_error=default(message=str(error)), logger_=logger_, logger_depth=logger_depth
        )


def _raise_exception_args(
    error: Exception,
    service_error: BaseGenericException,
    logger_: LoggerType,
    logger_depth: int,
    trace: bool = False,
) -> NoReturn:
    _logger = logger_.opt(depth=logger_depth)
    logger_fcn = _logger.exception if trace else _logger.error
    logger_fcn(f"[{error.__class__.__name__} → {service_error.__class__.__name__}] {str(service_error)}")
    raise service_error
