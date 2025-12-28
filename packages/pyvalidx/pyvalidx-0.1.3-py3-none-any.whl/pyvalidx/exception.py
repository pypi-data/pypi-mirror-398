'''
Exception for validation errors
'''

import json
from typing import Any, Dict, List, Union


class ValidationException(Exception):
    '''
    Exception for validation errors.

    Args:
        validations (Dict[str, Union[str, List[str]]]): A dictionary containing the validation errors.
        status_code (int, optional): The HTTP status code to return. Defaults to 400.
    '''

    def __init__(
        self,
        validations: Dict[str, Union[str, List[str]]],
        status_code: int = 400,
    ):
        self.status_code = status_code
        self.validations = validations
        self.response = {
            "status_code": status_code,
            "validations": validations,
        }
        super().__init__(json.dumps(self.response))

    def to_dict(self) -> Dict[str, Any]:
        '''
        Returns the exception as a dictionary.

        Returns:
            Dict[str, Any]: A dictionary containing the exception information.
        '''
        return self.response

    def to_json(self) -> str:
        '''
        Returns the exception as a JSON string.

        Returns:
            str: A JSON string containing the exception information.
        '''
        return json.dumps(self.response)
