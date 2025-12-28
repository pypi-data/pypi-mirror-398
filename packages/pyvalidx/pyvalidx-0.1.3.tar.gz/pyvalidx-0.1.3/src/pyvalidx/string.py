'''
String validation functions
'''

import re
from collections.abc import Callable
from typing import Any, Optional, Dict, Union, List, Set


def is_email(
    message: str = "Invalid email format",
) -> Callable[[Any, Optional[Dict[str, Any]]], bool]:
    '''
    Validates that the field is a valid email.

    Args:
        message (str, optional): The error message to return if the validation fails.

    Returns:
        Callable[[Any, Optional[Dict[str, Any]]], bool]: A validator function that returns True if the field is a
        valid email.
    '''

    def validator(
        value: Any, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        if value is None:
            return True
        return (
            re.match(
                r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', str(value)
            )
            is not None
        )

    validator.__message__ = message
    return validator


def is_strong_password(
    message: str = "Password must be strong",
) -> Callable[[Any, Optional[Dict[str, Any]]], bool]:
    '''
    Validates that the field is a strong password.

    Args:
        message (str, optional): The error message to return if the validation fails.

    Returns:
        Callable[[Any, Optional[Dict[str, Any]]], bool]: A validator function that returns True if the field is a
        strong password.
    '''

    def validator(
        value: Any, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        if value is None:
            return True
        value = str(value)
        return (
            len(value) >= 8
            and re.search(r'[A-Z]', value) is not None
            and re.search(r'[a-z]', value) is not None
            and re.search(r'\d', value) is not None
            and re.search(r'[!@#$%^&*(),.?":{}\|<>]', value) is not None
        )

    validator.__message__ = message
    return validator


def matches_regex(
    pattern: str, message: str = "Invalid format"
) -> Callable[[Any, Optional[Dict[str, Any]]], bool]:
    '''
    Validates that the field matches a regular expression.

    Args:
        pattern (str): The regular expression to match.
        message (str, optional): The error message to return if the validation fails.

    Returns:
        Callable[[Any, Optional[Dict[str, Any]]], bool]: A validator function that returns True if the field matches
        the regular expression.
    '''

    def validator(
        value: Any, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        if value is None:
            return True
        return re.match(pattern, str(value)) is not None

    validator.__message__ = message
    return validator


def no_whitespace(
    message: str = "Must not contain spaces",
) -> Callable[[Any, Optional[Dict[str, Any]]], bool]:
    '''
    Validates that the field does not contain any whitespace.

    Args:
        message (str, optional): The error message to return if the validation fails.

    Returns:
        Callable[[Any, Optional[Dict[str, Any]]], bool]: A validator function that returns True if the field does
        not contain any whitespace.
    '''

    def validator(
        value: Any, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        if value is None:
            return True
        return ' ' not in str(value)

    validator.__message__ = message
    return validator


def is_phone(
    message: str = "Invalid phone format",
) -> Callable[[Any, Optional[Dict[str, Any]]], bool]:
    '''
    Validates that the field is a valid phone number.

    Args:
        message (str, optional): The error message to return if the validation fails.

    Returns:
        Callable[[Any, Optional[Dict[str, Any]]], bool]: A validator function that returns True if the field is a
        valid phone number.
    '''

    def validator(
        value: Any, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        if value is None:
            return True
        clean = re.sub(r'[^\d+]', '', str(value))
        patterns = [r'^\+57[39]\d{9}$', r'^3\d{9}$', r'^[1-8]\d{6,7}$']
        return any(re.match(p, clean) for p in patterns)

    validator.__message__ = message
    return validator


def has_no_common_password(
    dictionary: Union[List[str], Set[str]],
    message: str = "Password is too common",
) -> Callable[[Any, Optional[Dict[str, Any]]], bool]:
    '''
    Validates that the field does not contain a common password.

    Args:
        dictionary (Union[List[str], Set[str]]): The list or set of common passwords to check against.
        message (str, optional): The error message to return if the validation fails.

    Returns:
        Callable[[Any, Optional[Dict[str, Any]]], bool]: A validator function that returns True if the field does
        not contain a common password.
    '''

    def validator(
        value: Any, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        if value is None:
            return True
        return str(value).lower() not in dictionary

    validator.__message__ = message
    return validator
