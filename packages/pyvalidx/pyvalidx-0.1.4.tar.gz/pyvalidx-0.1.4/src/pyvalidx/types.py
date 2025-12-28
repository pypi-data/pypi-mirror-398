'''
Type validation functions
'''

from collections.abc import Callable
from typing import Any, Optional, Dict, Union, List, Set


def is_dict(
    message: str = "Must be a dictionary",
) -> Callable[[Any, Optional[Dict[str, Any]]], bool]:
    '''
    Validates that the field is a dictionary.

    Args:
        message (str, optional): The error message to return if the validation fails.

    Returns:
        Callable[[Any, Optional[Dict[str, Any]]], bool]: A validator function that returns True if the field is a
        dictionary.
    '''

    def validator(
        value: Any, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        if value is None:
            return True
        return isinstance(value, dict)

    validator.__message__ = message
    return validator


def is_list(
    message: str = "Must be a list",
) -> Callable[[Any, Optional[Dict[str, Any]]], bool]:
    '''
    Validates that the field is a list.

    Args:
        message (str, optional): The error message to return if the validation fails.

    Returns:
        Callable[[Any, Optional[Dict[str, Any]]], bool]: A validator function that returns True if the field is a
        list.
    '''

    def validator(
        value: Any, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        if value is None:
            return True
        return isinstance(value, list)

    validator.__message__ = message
    return validator


def is_boolean(
    message: str = "Must be a boolean",
) -> Callable[[Any, Optional[Dict[str, Any]]], bool]:
    '''
    Validates that the field is a boolean.

    Args:
        message (str, optional): The error message to return if the validation fails.

    Returns:
        Callable[[Any, Optional[Dict[str, Any]]], bool]: A validator function that returns True if the field is a
        boolean.
    '''

    def validator(
        value: Any, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        if value is None:
            return True
        return isinstance(value, bool)

    validator.__message__ = message
    return validator


def is_in(
    choices: Union[List[Any], Set[Any]], message: Optional[str] = None
) -> Callable[[Any, Optional[Dict[str, Any]]], bool]:
    '''
    Validates that the field is in a list or set of choices.

    Args:
        choices (Union[List[Any], Set[Any]]): The list or set of choices to check against.
        message (str, optional): The error message to return if the validation fails.

    Returns:
        Callable[[Any, Optional[Dict[str, Any]]], bool]: A validator function that returns True if the field is in
        the list or set of choices.
    '''
    message = message or f"Must be one of: {choices}"

    def validator(
        value: Any, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        if value is None:
            return True
        return value in choices

    validator.__message__ = message
    return validator
