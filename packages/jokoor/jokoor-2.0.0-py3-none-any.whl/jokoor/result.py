"""
Result type for Go-style error handling in Python

This module provides a Result type that represents either a successful value
or an error, similar to Go's (value, error) pattern or Rust's Result<T, E>.
"""

from typing import TypeVar, Tuple, Optional, Union

# Type variable for the success value
T = TypeVar("T")

# Result type alias for (data, error) tuple pattern
Result = Tuple[Optional[T], Optional[str]]


def Ok(data: T) -> Result[T]:
    """
    Create a successful result

    Args:
        data: The successful value

    Returns:
        A Result tuple with (data, None)
    """
    return (data, None)


def Err(error: Union[str, Exception]) -> Result[None]:
    """
    Create an error result

    Args:
        error: The error message or exception

    Returns:
        A Result tuple with (None, error_message)
    """
    if isinstance(error, Exception):
        # Convert exception to string, preserving the error type info
        error_type = type(error).__name__
        error_message = str(error)
        if error_type != "Exception":
            return (None, f"{error_type}: {error_message}")
        return (None, error_message)
    return (None, str(error))


def is_ok(result: Result[T]) -> bool:
    """
    Check if a Result represents success

    Args:
        result: The Result tuple to check

    Returns:
        True if the result is successful (no error)
    """
    _, error = result
    return error is None


def is_err(result: Result[T]) -> bool:
    """
    Check if a Result represents an error

    Args:
        result: The Result tuple to check

    Returns:
        True if the result contains an error
    """
    _, error = result
    return error is not None


def unwrap(result: Result[T]) -> T:
    """
    Extract the value from a Result, raising an exception if it's an error

    Args:
        result: The Result tuple to unwrap

    Returns:
        The successful value

    Raises:
        RuntimeError: If the result contains an error
    """
    data, error = result
    if error is not None:
        raise RuntimeError(f"Called unwrap on an error Result: {error}")
    return data  # type: ignore


def unwrap_or(result: Result[T], default: T) -> T:
    """
    Extract the value from a Result, or return a default if it's an error

    Args:
        result: The Result tuple to unwrap
        default: The default value to return on error

    Returns:
        The successful value or the default
    """
    data, error = result
    if error is not None:
        return default
    return data  # type: ignore
