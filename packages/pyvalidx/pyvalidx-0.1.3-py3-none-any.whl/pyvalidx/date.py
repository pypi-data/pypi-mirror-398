'''
Date validation functions
'''

from datetime import datetime
from collections.abc import Callable
from typing import Any, Optional, Dict


def is_date(
    format: str = "%Y-%m-%d", message: str = "Invalid date format"
) -> Callable[[Any, Optional[Dict[str, Any]]], bool]:
    '''
    Validates that the field is a valid date.

    Args:
        format (str, optional): The date format to use. Defaults to "%Y-%m-%d".
        message (str, optional): The error message to return if the validation fails.

    Returns:
        Callable[[Any, Optional[Dict[str, Any]]], bool]: A validator function that returns True if the field is a
        valid date.
    '''

    def validator(
        value: Any, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        if value is None:
            return True
        try:
            datetime.strptime(str(value), format)
            return True
        except Exception:
            return False

    validator.__message__ = message
    return validator


def is_future_date(
    format: str = "%Y-%m-%d", message: str = "Date must be in the future"
) -> Callable[[Any, Optional[Dict[str, Any]]], bool]:
    '''
    Validates that the field is a future date.

    Args:
        format (str, optional): The date format to use. Defaults to "%Y-%m-%d".
        message (str, optional): The error message to return if the validation fails.

    Returns:
        Callable[[Any, Optional[Dict[str, Any]]], bool]: A validator function that returns True if the field is a
        future date.
    '''

    def validator(
        value: Any, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        if value is None:
            return True
        try:
            return datetime.strptime(str(value), format) > datetime.now()
        except Exception:
            return False

    validator.__message__ = message
    return validator


def is_past_date(
    format: str = "%Y-%m-%d", message: str = "Date must be in the past"
) -> Callable[[Any, Optional[Dict[str, Any]]], bool]:
    '''
    Validates that the field is a past date.

    Args:
        format (str, optional): The date format to use. Defaults to "%Y-%m-%d".
        message (str, optional): The error message to return if the validation fails.

    Returns:
        Callable[[Any, Optional[Dict[str, Any]]], bool]: A validator function that returns True if the field is a
        past date.
    '''

    def validator(
        value: Any, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        if value is None:
            return True
        try:
            return datetime.strptime(str(value), format) < datetime.now()
        except Exception:
            return False

    validator.__message__ = message
    return validator


def is_today(
    format: str = "%Y-%m-%d", message: str = "Date must be today"
) -> Callable[[Any, Optional[Dict[str, Any]]], bool]:
    '''
    Validates that the field is today's date.

    Args:
        format (str, optional): The date format to use. Defaults to "%Y-%m-%d".
        message (str, optional): The error message to return if the validation fails.

    Returns:
        Callable[[Any, Optional[Dict[str, Any]]], bool]: A validator function that returns True if the field is
        today's date.
    '''

    def validator(
        value: Any, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        if value is None:
            return True
        try:
            return (
                datetime.strptime(str(value), format).date()
                == datetime.now().date()
            )
        except Exception:
            return False

    validator.__message__ = message
    return validator
