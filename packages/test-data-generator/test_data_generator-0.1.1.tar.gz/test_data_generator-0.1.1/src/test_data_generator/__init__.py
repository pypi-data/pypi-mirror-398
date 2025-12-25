"""
Test Data Generator - Deterministic test data generation from schemas.

Main exports:
    - generate_test_data: Main API function
    - DataGenerator: Core generator class
    - load_schema: Schema loading utility
"""

from pathlib import Path
from typing import Any

from .generator import DataGenerator
from .load_schema import load_schema

__version__ = "0.1.0"
__all__ = ["generate_test_data", "DataGenerator", "load_schema"]


def generate_test_data(
    schema_input: str | Path | dict,
    count: int = 1,
    seed: int | None = None,
) -> list[dict[str, Any]]:
    """
    Generate deterministic test data from a schema.

    This is the main high-level API for the test data generator.
    It accepts either a file path, raw JSON string, or dict as schema input,
    validates the schema, and generates the requested number of records
    using a deterministic seed.

    Args:
        schema_input: Either a file path to a JSON schema, a raw JSON string, or a dict
        count: Number of records to generate (default: 1)
        seed: Random seed for deterministic generation (default: 42)

    Returns:
        list: List of generated data records

    Raises:
        ValueError: If schema is invalid
        FileNotFoundError: If schema file doesn't exist

    Examples:
        >>> # Using a file path
        >>> data = generate_test_data("schema.json", count=10, seed=123)

        >>> # Using a raw JSON string
        >>> schema = '{"fields": {"name": {"type": "string"}}}'
        >>> data = generate_test_data(schema, count=5)

        >>> # Using a dict directly
        >>> schema = {"fields": {"name": {"type": "string"}}}
        >>> data = generate_test_data(schema, count=5)

        >>> # Regenerating the same data
        >>> data1 = generate_test_data(schema, count=5, seed=42)
        >>> data2 = generate_test_data(schema, count=5, seed=42)
        >>> assert data1 == data2  # Same seed produces same data
    """
    # Load schema from file, string, or use dict directly
    if isinstance(schema_input, dict):
        schema = schema_input
    else:
        schema = load_schema(schema_input)

    # Create generator and generate data
    generator = DataGenerator(schema, seed=seed)
    return generator.generate(count)
