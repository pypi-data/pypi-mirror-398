"""Schema validation for TOON format."""

from typing import Any, Dict, List, Optional, Union, Callable
from enum import Enum


class FieldType(Enum):
    """Supported field types for schema validation."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    NUMBER = "number"  # int or float
    ANY = "any"


class ValidationError(Exception):
    """Exception raised when schema validation fails."""

    pass


class Field:
    """Schema field definition."""

    def __init__(
        self,
        name: str,
        field_type: FieldType = FieldType.ANY,
        required: bool = True,
        nullable: bool = False,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        pattern: Optional[str] = None,
        enum: Optional[List[Any]] = None,
        validator: Optional[Callable[[Any], bool]] = None,
    ):
        """
        Define a schema field.

        Args:
            name: Field name
            field_type: Expected type
            required: Whether field must be present
            nullable: Whether field can be null
            min_value: Minimum value for numbers
            max_value: Maximum value for numbers
            pattern: Regex pattern for strings
            enum: List of allowed values
            validator: Custom validation function
        """
        self.name = name
        self.field_type = field_type
        self.required = required
        self.nullable = nullable
        self.min_value = min_value
        self.max_value = max_value
        self.pattern = pattern
        self.enum = enum
        self.validator = validator

    def validate(self, value: Any) -> None:
        """
        Validate a value against this field definition.

        Args:
            value: Value to validate

        Raises:
            ValidationError: If validation fails
        """
        # Check null
        if value is None:
            if not self.nullable:
                raise ValidationError(f"Field '{self.name}' cannot be null")
            return

        # Check type
        if self.field_type == FieldType.STRING:
            if not isinstance(value, str):
                raise ValidationError(f"Field '{self.name}' must be a string, got {type(value).__name__}")
        elif self.field_type == FieldType.INTEGER:
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValidationError(f"Field '{self.name}' must be an integer, got {type(value).__name__}")
        elif self.field_type == FieldType.FLOAT:
            if not isinstance(value, float):
                raise ValidationError(f"Field '{self.name}' must be a float, got {type(value).__name__}")
        elif self.field_type == FieldType.BOOLEAN:
            if not isinstance(value, bool):
                raise ValidationError(f"Field '{self.name}' must be a boolean, got {type(value).__name__}")
        elif self.field_type == FieldType.NUMBER:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValidationError(f"Field '{self.name}' must be a number, got {type(value).__name__}")

        # Check range for numbers
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if self.min_value is not None and value < self.min_value:
                raise ValidationError(f"Field '{self.name}' value {value} is less than minimum {self.min_value}")
            if self.max_value is not None and value > self.max_value:
                raise ValidationError(f"Field '{self.name}' value {value} is greater than maximum {self.max_value}")

        # Check pattern for strings
        if isinstance(value, str) and self.pattern is not None:
            import re
            if not re.match(self.pattern, value):
                raise ValidationError(f"Field '{self.name}' value '{value}' does not match pattern '{self.pattern}'")

        # Check enum
        if self.enum is not None and value not in self.enum:
            raise ValidationError(f"Field '{self.name}' value '{value}' not in allowed values: {self.enum}")

        # Custom validator
        if self.validator is not None:
            try:
                if not self.validator(value):
                    raise ValidationError(f"Field '{self.name}' failed custom validation")
            except Exception as e:
                raise ValidationError(f"Field '{self.name}' validation error: {str(e)}")


class Schema:
    """Schema definition for TOON arrays."""

    def __init__(self, array_name: str, fields: List[Field], strict: bool = True):
        """
        Define a schema for a TOON array.

        Args:
            array_name: Name of the array to validate
            fields: List of field definitions
            strict: If True, reject extra fields not in schema
        """
        self.array_name = array_name
        self.fields = {field.name: field for field in fields}
        self.strict = strict

    def validate_item(self, item: Dict[str, Any], item_index: int = 0) -> None:
        """
        Validate a single item against the schema.

        Args:
            item: Item to validate
            item_index: Index of item in array (for error messages)

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(item, dict):
            raise ValidationError(
                f"Array '{self.array_name}' item {item_index} must be a dict, got {type(item).__name__}"
            )

        # Check required fields
        for field_name, field in self.fields.items():
            if field.required and field_name not in item:
                raise ValidationError(
                    f"Array '{self.array_name}' item {item_index} missing required field '{field_name}'"
                )

        # Validate present fields
        for field_name, value in item.items():
            if field_name not in self.fields:
                if self.strict:
                    raise ValidationError(
                        f"Array '{self.array_name}' item {item_index} has unexpected field '{field_name}'"
                    )
                continue

            self.fields[field_name].validate(value)

    def validate_array(self, items: List[Dict[str, Any]]) -> None:
        """
        Validate an entire array against the schema.

        Args:
            items: Array items to validate

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(items, list):
            raise ValidationError(f"Array '{self.array_name}' must be a list, got {type(items).__name__}")

        for i, item in enumerate(items):
            self.validate_item(item, i)

    def validate(self, data: Dict[str, Any]) -> None:
        """
        Validate data containing this array.

        Args:
            data: Data to validate (should contain array with array_name key)

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(data, dict):
            raise ValidationError(f"Data must be a dict, got {type(data).__name__}")

        if self.array_name not in data:
            raise ValidationError(f"Data does not contain array '{self.array_name}'")

        self.validate_array(data[self.array_name])


class MultiSchema:
    """Schema for validating multiple arrays."""

    def __init__(self, schemas: List[Schema], allow_extra_arrays: bool = False):
        """
        Define schemas for multiple arrays.

        Args:
            schemas: List of schema definitions
            allow_extra_arrays: If True, allow arrays not defined in schemas
        """
        self.schemas = {schema.array_name: schema for schema in schemas}
        self.allow_extra_arrays = allow_extra_arrays

    def validate(self, data: Dict[str, Any]) -> None:
        """
        Validate data containing multiple arrays.

        Args:
            data: Data to validate

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(data, dict):
            raise ValidationError(f"Data must be a dict, got {type(data).__name__}")

        # Check for unexpected arrays
        if not self.allow_extra_arrays:
            for array_name in data.keys():
                if array_name not in self.schemas:
                    raise ValidationError(f"Unexpected array '{array_name}' in data")

        # Validate each defined array
        for array_name, schema in self.schemas.items():
            if array_name in data:
                schema.validate_array(data[array_name])


def infer_schema(data: Dict[str, Any], array_name: str, strict: bool = True) -> Schema:
    """
    Infer schema from example data.

    Args:
        data: Example data containing the array
        array_name: Name of array to infer schema for
        strict: Whether inferred schema should be strict

    Returns:
        Inferred Schema object

    Raises:
        ValidationError: If data is invalid for schema inference
    """
    if array_name not in data:
        raise ValidationError(f"Data does not contain array '{array_name}'")

    items = data[array_name]
    if not isinstance(items, list) or not items:
        raise ValidationError(f"Array '{array_name}' must be a non-empty list for schema inference")

    # Collect all field names and types
    field_types: Dict[str, set] = {}
    field_nullables: Dict[str, bool] = {}

    for item in items:
        if not isinstance(item, dict):
            raise ValidationError(f"Cannot infer schema from non-dict items")

        for field_name, value in item.items():
            if field_name not in field_types:
                field_types[field_name] = set()
                field_nullables[field_name] = False

            if value is None:
                field_nullables[field_name] = True
            elif isinstance(value, bool):
                field_types[field_name].add(FieldType.BOOLEAN)
            elif isinstance(value, int):
                field_types[field_name].add(FieldType.INTEGER)
            elif isinstance(value, float):
                field_types[field_name].add(FieldType.FLOAT)
            elif isinstance(value, str):
                field_types[field_name].add(FieldType.STRING)

    # Create fields
    fields = []
    all_field_names = set()
    for item in items:
        all_field_names.update(item.keys())

    for field_name in sorted(all_field_names):
        types = field_types.get(field_name, set())

        # Determine field type
        if len(types) == 0:
            field_type = FieldType.ANY
        elif len(types) == 1:
            field_type = list(types)[0]
        elif types == {FieldType.INTEGER, FieldType.FLOAT}:
            field_type = FieldType.NUMBER
        else:
            field_type = FieldType.ANY

        # Check if required (present in all items)
        required = all(field_name in item for item in items)

        fields.append(
            Field(
                name=field_name,
                field_type=field_type,
                required=required,
                nullable=field_nullables.get(field_name, False),
            )
        )

    return Schema(array_name, fields, strict=strict)
