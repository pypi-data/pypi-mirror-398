'''
Core functions for field validation
'''

from collections.abc import Callable
from typing import Any, Optional, Dict


def is_required(
    message: str = "This field is required",
) -> Callable[[Any, Optional[Dict[str, Any]]], bool]:
    '''
    Validates that the field is not None, not an empty string, and not an empty list.

    Args:
        message (str, optional): The error message to return if the validation fails.

    Returns:
        Callable[[Any, Optional[Dict[str, Any]]], bool]: A validator function that returns True if the field is not
        None, not an empty string, and not an empty list.
    '''

    def validator(
        value: Any, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        return value is not None and value != '' and value != []

    validator.__message__ = message
    return validator


def min_length(
    length: int, message: Optional[str] = None
) -> Callable[[Any, Optional[Dict[str, Any]]], bool]:
    '''
    Validates that the field has at least the specified length.

    Args:
        length (int): The minimum length required.
        message (str, optional): The error message to return if the validation fails.

    Returns:
        Callable[[Any, Optional[Dict[str, Any]]], bool]: A validator function that returns True if the field has
        at least the specified length.
    '''
    message = message or f"Must have at least {length} characters"

    def validator(
        value: Any, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        if value is None:
            return True
        return len(str(value)) >= length

    validator.__message__ = message
    return validator


def max_length(
    length: int, message: Optional[str] = None
) -> Callable[[Any, Optional[Dict[str, Any]]], bool]:
    '''
    Validates that the field has at most the specified length.

    Args:
        length (int): The maximum length allowed.
        message (str, optional): The error message to return if the validation fails.

    Returns:
        Callable[[Any, Optional[Dict[str, Any]]], bool]: A validator function that returns True if the field has
        at most the specified length.
    '''
    message = message or f"Must have at most {length} characters"

    def validator(
        value: Any, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        if value is None:
            return True
        return len(str(value)) <= length

    validator.__message__ = message
    return validator


def custom(
    validator_func: Callable[[Any, Optional[Dict[str, Any]]], bool],
    message: str = "Custom validation failed",
) -> Callable[[Any, Optional[Dict[str, Any]]], bool]:
    '''
    Wraps a custom validation function with a message.

    Args:
        validator_func (Callable[[Any, Optional[Dict[str, Any]]], bool]): The custom validation function.
        message (str, optional): The error message to return if the validation fails.

    Returns:
        Callable[[Any, Optional[Dict[str, Any]]], bool]: A validator function that returns True if the custom
        validation function returns True.
    '''
    validator_func.__message__ = message
    return validator_func


def same_as(
    other_field: str, message: Optional[str] = None
) -> Callable[[Any, Optional[Dict[str, Any]]], bool]:
    '''
    Validates that the field has the same value as another field.

    Args:
        other_field (str): The name of the other field to compare with.
        message (str, optional): The error message to return if the validation fails.

    Returns:
        Callable[[Any, Optional[Dict[str, Any]]], bool]: A validator function that returns True if the field has
        the same value as the other field.
    '''

    def validator(
        value: Any, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        if context is None:
            return False
        return value == context.get(other_field)

    validator.__message__ = message or f"Must be the same as {other_field}"
    return validator


def is_not_empty(
    message: str = "Cannot be empty",
) -> Callable[[Any, Optional[Dict[str, Any]]], bool]:
    '''
    Validates that the field is not empty.

    Args:
        message (str, optional): The error message to return if the validation fails.

    Returns:
        Callable[[Any, Optional[Dict[str, Any]]], bool]: A validator function that returns True if the field is not
        empty.
    '''

    def validator(
        value: Any, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        if value is None:
            return True
        return len(value) > 0

    validator.__message__ = message
    return validator


def required_if(
    other_field: str,
    other_value: Any,
    message: str = "This field is required due to other field",
) -> Callable[[Any, Optional[Dict[str, Any]]], bool]:
    '''
    Validates that the field is required if another field has a specific value.

    Args:
        other_field (str): The name of the other field to compare with.
        other_value (Any): The value of the other field that makes this field required.
        message (str, optional): The error message to return if the validation fails.

    Returns:
        Callable[[Any, Optional[Dict[str, Any]]], bool]: A validator function that returns True if the field is not
        required or if it has a value.
    '''

    def validator(
        value: Any, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        if context is None:
            return True
        if context.get(other_field) == other_value:
            return value is not None and value != ''
        return True

    validator.__message__ = message
    return validator
