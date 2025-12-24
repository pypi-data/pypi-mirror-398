import json
from pathlib import Path
from typing import Any, Union

from kinforge.errors import SchemaValidationError
from kinforge.parser.models_v0 import DocumentV0
from kinforge.parser.models_v1 import DocumentV1

DocumentAny = Union[DocumentV0, DocumentV1]


def load_document(path: str | Path) -> DocumentAny:
    p = Path(path)
    try:
        data: dict[str, Any] = json.loads(p.read_text())
    except Exception as e:
        raise SchemaValidationError(f"Failed to read JSON: {e}") from e

    ver = data.get("version")
    try:
        if ver == "0.1":
            return DocumentV0.model_validate(data)
        if ver == "1.0":
            return DocumentV1.model_validate(data)
        raise SchemaValidationError(
            f"Unsupported version {ver!r} (expected '0.1' or '1.0')"
        )
    except Exception as e:
        raise SchemaValidationError(str(e)) from e
