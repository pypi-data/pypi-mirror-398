'''
Field validation functions
'''

from pydantic import Field
from collections.abc import Callable
from typing import Any, Optional, Dict


def field_validated(
    *validators: Callable[[Any, Optional[Dict[str, Any]]], bool], **kwargs: Any
) -> Any:
    '''
    Creates a Pydantic field with custom validators.

    Args:
        *validators (Callable[[Any, Optional[Dict[str, Any]]], bool]): The custom validation functions.
        **kwargs (Any): The keyword arguments to pass to the Pydantic Field function.

    Returns:
        Any: A Pydantic field with the custom validators.
    '''
    field_obj = Field(**kwargs)
    if not hasattr(field_obj, 'metadata'):
        field_obj.metadata = []

    field_obj.metadata.append({"custom_validators": validators})
    return field_obj
