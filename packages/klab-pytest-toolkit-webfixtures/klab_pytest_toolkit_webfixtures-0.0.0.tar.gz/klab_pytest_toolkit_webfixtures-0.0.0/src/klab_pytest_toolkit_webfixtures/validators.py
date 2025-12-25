from typing import Dict, Any, Optional
from jsonschema import validate, ValidationError
from jsonschema.exceptions import SchemaError


class JsonResponseValidator:
    """Validator for JSON responses with schema validation and additional checks."""

    def __init__(
        self,
        schema: Optional[Dict[str, Any]] = None,
        raise_on_error: Optional[bool] = None,
    ):
        """
        Initialize the JSON response validator.

        Args:
            schema: JSON schema to validate against (can be set later)
            strict_mode: If True, disallow additional properties not in schema
            raise_on_error: If True, raise ValidationError instead of returning False
        """
        self.schema = schema
        self.raise_on_error = raise_on_error
        self.last_error: Optional[str] = None

    def validate_response(self, response_data: Dict[str, Any]) -> bool:
        """
        Validate response data against the schema.

        Args:
            response_data: The JSON response data to validate

        Returns:
            True if valid, False otherwise (unless raise_on_error=True)

        Raises:
            ValidationError: If raise_on_error=True and validation fails
            ValueError: If no schema is set
        """
        if self.schema is None:
            raise ValueError("No schema set for validation")

        try:
            validate(instance=response_data, schema=self.schema)
            self.last_error = None
            return True
        except ValidationError as e:
            self.last_error = str(e)
            if self.raise_on_error:
                raise
            return False
        except SchemaError as e:
            self.last_error = f"Invalid schema: {str(e)}"
            if self.raise_on_error:
                raise
            return False

    def get_last_error(self) -> str:
        """Get the last validation error message."""
        if self.last_error is None:
            return ""

        return self.last_error


class ResponseValidatorFactory:
    """Factory to create different Response Validators instances with different configurations."""

    def create_json_validator(
        self,
        schema: Optional[Dict[str, Any]] = None,
        raise_on_error: Optional[bool] = None,
    ) -> JsonResponseValidator:
        """
        Create a new JsonResponseValidator instance.

        Args:
            schema: JSON schema for the validator
            strict_mode: Override default strict mode
            raise_on_error: Override default error handling

        Returns:
            JsonResponseValidator: Configured validator instance
        """
        return JsonResponseValidator(
            schema=schema,
            raise_on_error=raise_on_error,
        )
