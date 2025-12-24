import json
from pathlib import Path
from typing import Any

from kinforge.errors import SchemaValidationError
from kinforge.parser.models_v0 import DocumentV0


def validate_document(data: dict[str, Any]) -> DocumentV0:
    try:
        return DocumentV0.model_validate(data)
    except Exception as e:
        raise SchemaValidationError(str(e)) from e


def load_and_validate(path: Path) -> DocumentV0:
    try:
        data = json.loads(path.read_text())
    except Exception as e:
        raise SchemaValidationError(f"Failed to read JSON: {e}") from e

    return validate_document(data)
