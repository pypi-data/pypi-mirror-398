import re
import json
from typing import Any, Dict, Callable

from .exceptions import ValidationError


_custom_validators: Dict[str, Callable] = {}


def register_validator(name: str, validator_func: Callable[[Any, str], None]):
    _custom_validators[name] = validator_func


def validate_value(
    key: str,
    value: Any,
    validators: Dict[str, str],
    file: str = None,
    line: int = None
) -> None:
    
    for validator_name, validator_arg in validators.items():
        if validator_name == "required":
            if value is None or (isinstance(value, str) and value == ""):
                raise ValidationError(f"Required key '{key}' is missing or empty", file, line)
        
        elif validator_name == "non_empty":
            if isinstance(value, str) and not value:
                raise ValidationError(f"Key '{key}' cannot be empty", file, line)
            elif isinstance(value, (list, dict)) and len(value) == 0:
                raise ValidationError(f"Key '{key}' cannot be empty", file, line)
        
        elif validator_name == "one_of":
            allowed = [v.strip() for v in validator_arg.split(",")]
            if str(value) not in allowed:
                raise ValidationError(
                    f"Key '{key}' value '{value}' not in allowed values: {allowed}",
                    file,
                    line
                )
        
        elif validator_name == "regex":
            if not isinstance(value, str):
                raise ValidationError(
                    f"Key '{key}': regex validator only works with strings",
                    file,
                    line
                )
            if not re.match(validator_arg, value):
                raise ValidationError(
                    f"Key '{key}' value '{value}' does not match pattern '{validator_arg}'",
                    file,
                    line
                )
        
        elif validator_name == "min":
            try:
                min_val = float(validator_arg)
                if float(value) < min_val:
                    raise ValidationError(
                        f"Key '{key}' value {value} is less than minimum {min_val}",
                        file,
                        line
                    )
            except (ValueError, TypeError):
                raise ValidationError(
                    f"Key '{key}': cannot compare value {value} with min {validator_arg}",
                    file,
                    line
                )
        
        elif validator_name == "max":
            try:
                max_val = float(validator_arg)
                if float(value) > max_val:
                    raise ValidationError(
                        f"Key '{key}' value {value} is greater than maximum {max_val}",
                        file,
                        line
                    )
            except (ValueError, TypeError):
                raise ValidationError(
                    f"Key '{key}': cannot compare value {value} with max {validator_arg}",
                    file,
                    line
                )
        
        elif validator_name == "json_schema":
            if not isinstance(value, (dict, list)):
                raise ValidationError(
                    f"Key '{key}': json_schema validator requires json type",
                    file,
                    line
                )
            try:
                import jsonschema
                schema = json.loads(validator_arg)
                jsonschema.validate(value, schema)
            except ImportError:
                raise ValidationError(
                    f"Key '{key}': jsonschema library not installed",
                    file,
                    line
                )
            except json.JSONDecodeError as e:
                raise ValidationError(
                    f"Key '{key}': invalid JSON schema: {e}",
                    file,
                    line
                )
            except jsonschema.ValidationError as e:
                raise ValidationError(
                    f"Key '{key}': JSON validation failed: {e.message}",
                    file,
                    line
                )
        
        elif validator_name in _custom_validators:
            try:
                _custom_validators[validator_name](value, validator_arg)
            except Exception as e:
                raise ValidationError(
                    f"Key '{key}': custom validator '{validator_name}' failed: {e}",
                    file,
                    line
                )
        
        else:
            raise ValidationError(f"Unknown validator: {validator_name}", file, line)
