'''
Model for validation
'''

from pydantic import BaseModel, ConfigDict
from .exception import ValidationException
from collections.abc import Callable
from typing import Any, Dict, List, Union, Optional


class ValidatedModel(BaseModel):
    '''
    Model for validation.

    Args:
        **data (Any): The data to validate.

    Raises:
        ValidationException: If the validation fails.
    '''

    model_config = ConfigDict(
        validate_assignment=True,
        extra='forbid',
        str_strip_whitespace=True,
    )

    def __init__(self, **data: Any) -> None:
        self._run_custom_validations(data)
        super().__init__(**data)

    def _run_custom_validations(self, values: Dict[str, Any]) -> None:
        '''
        Runs the custom validations.

        Args:
            values (Dict[str, Any]): The values to validate.

        Raises:
            ValidationException: If the validation fails.
        '''
        errors: Dict[str, Union[str, List[str]]] = {}
        model_fields = self.__class__.model_fields

        for field_name, field_info in model_fields.items():
            field_value = values.get(field_name)
            field_errors: List[str] = []
            custom_validators: List[Callable[[Any, Optional[Dict[str, Any]]], bool]] = []
            if hasattr(field_info, 'metadata') and field_info.metadata:
                for meta_item in field_info.metadata:
                    if isinstance(meta_item, dict) and "custom_validators" in meta_item:
                        custom_validators = meta_item["custom_validators"]
                        break
            if not custom_validators:
                extra = field_info.json_schema_extra or {}
                if isinstance(extra, dict):
                    custom_validators = extra.get("custom_validators", [])  # type: ignore

            for validator_func in custom_validators:
                if not hasattr(validator_func, '__message__'):
                    continue
                try:
                    if (
                        isinstance(field_value, (int, float, bool))
                        or field_value is None
                    ):
                        if not validator_func(field_value, values):
                            field_errors.append(
                                getattr(
                                    validator_func,
                                    '__message__',
                                    "Validation failed",
                                )
                            )
                    else:
                        if not validator_func(field_value, values):
                            field_errors.append(
                                getattr(
                                    validator_func,
                                    '__message__',
                                    "Validation failed",
                                )
                            )
                except Exception:
                    field_errors.append(
                        getattr(
                            validator_func, '__message__', "Validation failed"
                        )
                    )

            if field_errors:
                errors[field_name] = (
                    field_errors[0] if len(field_errors) == 1 else field_errors
                )

        if errors:
            raise ValidationException(errors)

    def validate(self) -> Dict[str, Any]:
        '''
        Validates the model.

        Returns:
            Dict[str, Any]: The validated data.
        '''
        current_data = self.model_dump()
        self._run_custom_validations(current_data)
        return current_data

    @classmethod
    def validate_data(cls, data: Dict[str, Any]) -> 'ValidatedModel':
        '''
        Validates the data.

        Args:
            data (Dict[str, Any]): The data to validate.

        Returns:
            ValidatedModel: The validated model.
        '''
        return cls(**data)
