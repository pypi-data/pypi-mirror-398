"""
genericlib.exceptions
=====================

Custom exception classes for the `genericlib` package.

This module defines specialized exceptions used primarily by the
`text.Line` class to provide more granular and descriptive error
handling. By extending Python's built-in `Exception` type, these
exceptions allow developers to catch and handle errors in a structured,
semantic way rather than relying on generic exceptions.

Design Notes
------------
- These exceptions are intended to make error handling more explicit
  and self-documenting.
- Using custom exceptions improves clarity in debugging and allows
  consumers of the library to distinguish between generic runtime
  errors and domain-specific issues.

"""

from typing import Type, Optional


class LineError(Exception):
    """Base exception for errors raised by the `text.Line` class."""


class LineArgumentError(LineError):
    """Exception raised when invalid arguments are provided to `text.Line`."""


class InvalidExceptionType(Exception):
    """Raised when an invalid exception type is encountered."""


def raise_exception(
    ex: Exception,
    cls: Optional[Type[Exception]] = None,
    fmt: str = "{} - {}",
    msg: str = "",
    is_skipped: bool = False
):
    """
    Raise a formatted exception or skip raising.

    Parameters
    ----------
    ex : Exception
        The original exception instance.
    cls : Type[Exception], optional
        The exception class to raise. Defaults to None.
    fmt : str, optional
        Format string for the failure message. Defaults to "{}: {}".
    msg : str, optional
        Custom message to raise instead of formatting `ex`. Defaults to "".
    is_skipped : bool, optional
        If True, no exception is raised. Defaults to False.

    Raises
    ------
    InvalidExceptionType
        If `ex` is not an instance of Exception.
    Exception
        Raised with either the custom message or a formatted message.
    """

    if not is_skipped:
        fmt = str(fmt)

        if not isinstance(ex, Exception):   # if ex is NOT instance of Exception
            ex_type_name = ex.__name__ if isinstance(ex, type) else type(ex).__name__
            failure = f"Invalid argument: expected an Exception instance, got {ex_type_name}."
            raise InvalidExceptionType(failure)

        # Determine which exception class to use

        is_cls_exception = isinstance(cls, type) and issubclass(cls, Exception)
        exception_cls = cls if is_cls_exception else type(ex)
        if msg:
            raise exception_cls(msg)
        try:
            ex_name = type(ex).__name__
            failure = fmt.format(ex_name, ex)
            raise exception_cls(failure)
        except Exception as other_ex:
            other_failure = f"{type(other_ex).__name__} - {other_ex}"
            raise other_ex.__class__(other_failure)
