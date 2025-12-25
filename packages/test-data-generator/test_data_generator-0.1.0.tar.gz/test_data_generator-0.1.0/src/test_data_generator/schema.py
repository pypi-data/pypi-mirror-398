"""
Schema specification for test data generation.

Schema Format:
{
    "fields": {
        "field_name": {
            "type": "string|integer|float|boolean|date|email|uuid",
            "constraints": {
                "min": <value>,      # For numeric/string length
                "max": <value>,      # For numeric/string length
                "pattern": "<regex>", # For strings
                "enum": [values],    # Fixed set of values
                "format": "<format>" # For dates (iso, timestamp, etc.)
            }
        }
    }
}
"""

from typing import Any


def validate_schema(schema: dict) -> bool:
    """
    Validate that a schema is well-formed.
    
    Args:
        schema: Schema dictionary to validate
        
    Returns:
        bool: True if valid
        
    Raises:
        ValueError: If schema is invalid
    """
    if not isinstance(schema, dict):
        raise ValueError("Schema must be a dictionary")
    
    if "fields" not in schema:
        raise ValueError("Schema must contain 'fields' key")
    
    if not isinstance(schema["fields"], dict):
        raise ValueError("Schema 'fields' must be a dictionary")
    
    valid_types = {"string", "integer", "float", "boolean", "date", "email", "uuid"}
    
    for field_name, field_spec in schema["fields"].items():
        if not isinstance(field_spec, dict):
            raise ValueError(f"Field '{field_name}' specification must be a dictionary")
        
        if "type" not in field_spec:
            raise ValueError(f"Field '{field_name}' must have a 'type'")
        
        field_type = field_spec["type"]
        if field_type not in valid_types:
            raise ValueError(
                f"Field '{field_name}' has invalid type '{field_type}'. "
                f"Must be one of: {', '.join(valid_types)}"
            )
        
        # Validate constraints if present
        if "constraints" in field_spec:
            constraints = field_spec["constraints"]
            if not isinstance(constraints, dict):
                raise ValueError(f"Field '{field_name}' constraints must be a dictionary")
            
            # Type-specific constraint validation
            if field_type in ("integer", "float"):
                if "min" in constraints and "max" in constraints:
                    if constraints["min"] > constraints["max"]:
                        raise ValueError(
                            f"Field '{field_name}' min ({constraints['min']}) "
                            f"cannot be greater than max ({constraints['max']})"
                        )
            
            if "enum" in constraints:
                if not isinstance(constraints["enum"], list):
                    raise ValueError(f"Field '{field_name}' enum must be a list")
                if len(constraints["enum"]) == 0:
                    raise ValueError(f"Field '{field_name}' enum cannot be empty")
    
    return True


def get_field_type(schema: dict, field_name: str) -> str:
    """Get the type of a specific field."""
    return schema["fields"][field_name]["type"]


def get_field_constraints(schema: dict, field_name: str) -> dict[str, Any]:
    """Get the constraints for a specific field."""
    return schema["fields"][field_name].get("constraints", {})
