"""
Type-specific generators for test data.
Each generator uses a seeded random instance for deterministic output.
"""

import random
import string
import uuid
from datetime import datetime, timedelta
from typing import Any


class TypeGenerator:
    """Base class for type-specific generators."""
    
    def __init__(self, random_instance: random.Random):
        """
        Initialize generator with a seeded random instance.
        
        Args:
            random_instance: Seeded random.Random instance for deterministic output
        """
        self.random = random_instance
    
    def generate(self, constraints: dict[str, Any]) -> Any:
        """Generate a value based on constraints."""
        raise NotImplementedError


class StringGenerator(TypeGenerator):
    """Generate random strings."""
    
    def generate(self, constraints: dict[str, Any]) -> str:
        """Generate a string value."""
        # Check for enum first
        if "enum" in constraints:
            return self.random.choice(constraints["enum"])
        
        # Get length constraints
        min_length = constraints.get("min", 5)
        max_length = constraints.get("max", 20)
        length = self.random.randint(min_length, max_length)
        
        # Check for pattern (simplified - just use charset)
        charset = string.ascii_letters + string.digits
        return ''.join(self.random.choice(charset) for _ in range(length))


class IntegerGenerator(TypeGenerator):
    """Generate random integers."""
    
    def generate(self, constraints: dict[str, Any]) -> int:
        """Generate an integer value."""
        # Check for enum first
        if "enum" in constraints:
            return self.random.choice(constraints["enum"])
        
        min_val = constraints.get("min", 0)
        max_val = constraints.get("max", 1000)
        return self.random.randint(min_val, max_val)


class FloatGenerator(TypeGenerator):
    """Generate random floats."""
    
    def generate(self, constraints: dict[str, Any]) -> float:
        """Generate a float value."""
        # Check for enum first
        if "enum" in constraints:
            return self.random.choice(constraints["enum"])
        
        min_val = constraints.get("min", 0.0)
        max_val = constraints.get("max", 1000.0)
        return self.random.uniform(min_val, max_val)


class BooleanGenerator(TypeGenerator):
    """Generate random booleans."""
    
    def generate(self, constraints: dict[str, Any]) -> bool:
        """Generate a boolean value."""
        # Check for enum first
        if "enum" in constraints:
            return self.random.choice(constraints["enum"])
        
        return self.random.choice([True, False])


class DateGenerator(TypeGenerator):
    """Generate random dates."""
    
    def generate(self, constraints: dict[str, Any]) -> str:
        """Generate a date value as ISO format string."""
        # Check for enum first
        if "enum" in constraints:
            return self.random.choice(constraints["enum"])
        
        # Generate a date within a reasonable range
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2025, 12, 31)
        
        # Override with constraints if provided
        if "min" in constraints:
            if isinstance(constraints["min"], str):
                start_date = datetime.fromisoformat(constraints["min"])
        if "max" in constraints:
            if isinstance(constraints["max"], str):
                end_date = datetime.fromisoformat(constraints["max"])
        
        # Calculate random date
        time_delta = end_date - start_date
        random_days = self.random.randint(0, time_delta.days)
        random_date = start_date + timedelta(days=random_days)
        
        # Format based on constraints
        fmt = constraints.get("format", "iso")
        if fmt == "timestamp":
            return str(int(random_date.timestamp()))
        else:  # Default to ISO format
            return random_date.date().isoformat()


class EmailGenerator(TypeGenerator):
    """Generate random email addresses."""
    
    DOMAINS = ["example.com", "test.com", "email.com", "mail.com"]
    
    def generate(self, constraints: dict[str, Any]) -> str:
        """Generate an email address."""
        # Check for enum first
        if "enum" in constraints:
            return self.random.choice(constraints["enum"])
        
        # Generate username part
        username_length = self.random.randint(5, 12)
        username = ''.join(
            self.random.choice(string.ascii_lowercase + string.digits)
            for _ in range(username_length)
        )
        
        # Select domain
        domain = self.random.choice(self.DOMAINS)
        
        return f"{username}@{domain}"


class UuidGenerator(TypeGenerator):
    """Generate UUIDs."""
    
    def generate(self, constraints: dict[str, Any]) -> str:
        """Generate a UUID."""
        # Check for enum first
        if "enum" in constraints:
            return self.random.choice(constraints["enum"])
        
        # Generate deterministic UUID using random bytes
        random_bytes = bytes(self.random.randint(0, 255) for _ in range(16))
        return str(uuid.UUID(bytes=random_bytes))


# Generator registry
GENERATOR_REGISTRY = {
    "string": StringGenerator,
    "integer": IntegerGenerator,
    "float": FloatGenerator,
    "boolean": BooleanGenerator,
    "date": DateGenerator,
    "email": EmailGenerator,
    "uuid": UuidGenerator,
}
