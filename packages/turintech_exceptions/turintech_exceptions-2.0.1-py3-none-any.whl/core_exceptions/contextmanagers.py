"""
Module providing context managers related to exceptions.
"""

import contextlib
from typing import Type, Union


@contextlib.contextmanager
def map_exception(source_exc: Type[Exception], target_exc: Union[Type[Exception], Exception]):
    """Maps one type of exception to another. Useful when cathing exceptions from a given layer (e.g. DAO) in another
    (e.g. application).

    Args:
        source_exc (Type[Exception]):
            Exception to catch.
        target_exc (Type[Exception]):
            Exception class or instance to raise. If an instance is provided, it
            will be raised as is. If it's a class, it will be given the original
            exception's message as positional argument.

    """
    try:
        yield
    except source_exc as exc:
        if isinstance(target_exc, Exception):
            raise target_exc from exc
        raise target_exc(str(exc)) from exc
