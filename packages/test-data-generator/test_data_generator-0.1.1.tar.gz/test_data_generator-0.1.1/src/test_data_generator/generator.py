"""
Core data generator with deterministic seeding.
"""

import random
from typing import Any

from .generators import GENERATOR_REGISTRY
from .schema import get_field_constraints, get_field_type, validate_schema


class DataGenerator:
    """
    Deterministic test data generator.

    Uses a seed to ensure reproducible data generation for testing.
    """

    def __init__(self, schema: dict, seed: int | None = None):
        """
        Initialize the data generator.

        Args:
            schema: Schema dictionary defining the data structure
            seed: Random seed for deterministic generation (default: 42)
        """
        # Validate schema
        validate_schema(schema)

        self.schema = schema
        self.seed = seed if seed is not None else 42
        self.random = random.Random(self.seed)

        # Initialize type generators
        self.generators = {}
        for field_name in schema["fields"]:
            field_type = get_field_type(schema, field_name)
            generator_class = GENERATOR_REGISTRY.get(field_type)
            if generator_class:
                self.generators[field_name] = generator_class(self.random)

    def generate_record(self) -> dict[str, Any]:
        """
        Generate a single data record.

        Returns:
            dict: Generated data record with all fields
        """
        record = {}
        for field_name, generator in self.generators.items():
            constraints = get_field_constraints(self.schema, field_name)
            record[field_name] = generator.generate(constraints)
        return record

    def generate(self, count: int = 1) -> list[dict[str, Any]]:
        """
        Generate multiple data records.

        Args:
            count: Number of records to generate

        Returns:
            list: List of generated data records
        """
        return [self.generate_record() for _ in range(count)]

    def reset_seed(self, seed: int | None = None):
        """
        Reset the random seed to regenerate the same data.

        Args:
            seed: New seed value (uses original seed if None)
        """
        new_seed = seed if seed is not None else self.seed
        self.random = random.Random(new_seed)

        # Reinitialize all generators with the new random instance
        for field_name in self.schema["fields"]:
            field_type = get_field_type(self.schema, field_name)
            generator_class = GENERATOR_REGISTRY.get(field_type)
            if generator_class:
                self.generators[field_name] = generator_class(self.random)
