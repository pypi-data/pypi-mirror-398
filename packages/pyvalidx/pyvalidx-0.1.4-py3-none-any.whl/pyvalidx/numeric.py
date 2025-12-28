'''
Numeric validation functions
'''

from collections.abc import Callable
from typing import Any, Optional, Dict, Union


def is_positive(
    message: str = "Must be a positive number",
) -> Callable[[Any, Optional[Dict[str, Any]]], bool]:
    '''
    Validates that the field is a positive number.

    Args:
        message (str, optional): The error message to return if the validation fails.

    Returns:
        Callable[[Any, Optional[Dict[str, Any]]], bool]: A validator function that returns True if the field is a
        positive number.
    '''

    def validator(
        value: Any, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        if value is None:
            return True
        try:
            return float(value) > 0
        except Exception:
            return False

    validator.__message__ = message
    return validator


def is_integer(
    message: str = "Must be an integer",
) -> Callable[[Any, Optional[Dict[str, Any]]], bool]:
    '''
    Validates that the field is an integer.

    Args:
        message (str, optional): The error message to return if the validation fails.

    Returns:
        Callable[[Any, Optional[Dict[str, Any]]], bool]: A validator function that returns True if the field is an
        integer.
    '''

    def validator(
        value: Any, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        if value is None:
            return True
        return isinstance(value, int)

    validator.__message__ = message
    return validator


def is_float(
    message: str = "Must be a float",
) -> Callable[[Any, Optional[Dict[str, Any]]], bool]:
    '''
    Validates that the field is a float.

    Args:
        message (str, optional): The error message to return if the validation fails.

    Returns:
        Callable[[Any, Optional[Dict[str, Any]]], bool]: A validator function that returns True if the field is a
        float.
    '''

    def validator(
        value: Any, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        if value is None:
            return True
        return isinstance(value, float)

    validator.__message__ = message
    return validator


def max_value(
    max_val: Union[int, float], message: Optional[str] = None
) -> Callable[[Any, Optional[Dict[str, Any]]], bool]:
    '''
    Validates that the field has a value less than or equal to the specified maximum value.

    Args:
        max_val (Union[int, float]): The maximum value allowed.
        message (str, optional): The error message to return if the validation fails.

    Returns:
        Callable[[Any, Optional[Dict[str, Any]]], bool]: A validator function that returns True if the field has
        a value less than or equal to the specified maximum value.
    '''
    message = message or f"Must be less than or equal to {max_val}"

    def validator(
        value: Any, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        if value is None:
            return True
        try:
            return float(value) <= max_val
        except Exception:
            return False

    validator.__message__ = message
    return validator


def min_value(
    min_val: Union[int, float], message: Optional[str] = None
) -> Callable[[Any, Optional[Dict[str, Any]]], bool]:
    '''
    Validates that the field has a value greater than or equal to the specified minimum value.

    Args:
        min_val (Union[int, float]): The minimum value allowed.
        message (str, optional): The error message to return if the validation fails.

    Returns:
        Callable[[Any, Optional[Dict[str, Any]]], bool]: A validator function that returns True if the field has
        a value greater than or equal to the specified minimum value.
    '''
    message = message or f"Must be greater than or equal to {min_val}"

    def validator(
        value: Any, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        if value is None:
            return True
        try:
            return float(value) >= min_val
        except Exception:
            return False

    validator.__message__ = message
    return validator
