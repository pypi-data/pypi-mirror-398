import json
from pathlib import Path


def load_schema(schema_input: str | Path) -> dict:
    """
    Load schema from either a file path or a raw JSON string.
    
    Args:
        schema_input: Either a file path (str or Path) or a raw JSON string
        
    Returns:
        dict: Parsed schema dictionary
        
    Raises:
        ValueError: If the schema format is unsupported or invalid JSON
        FileNotFoundError: If the file path doesn't exist
    """
    # Try to parse as JSON string first
    if isinstance(schema_input, str):
        # Check if it looks like JSON (starts with { or [)
        stripped = schema_input.strip()
        if stripped.startswith(('{', '[')):
            try:
                return json.loads(schema_input)
            except json.JSONDecodeError:
                pass  # Fall through to try as file path
    
    # Treat as file path
    path = Path(schema_input)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    
    if path.suffix == ".json":
        return json.loads(path.read_text())
    
    raise ValueError(f"Unsupported schema format: {path.suffix}. Only .json files are supported.")
