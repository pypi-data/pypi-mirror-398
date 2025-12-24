"""Tests for parser and loader modules."""

import json
from pathlib import Path

import pytest

from kinforge.errors import SchemaValidationError
from kinforge.parser.loader import load_document


class TestLoadDocument:
    """Tests for load_document function."""

    def test_load_v0_document(self, tmp_path):
        """Test loading a v0 document."""
        doc_path = tmp_path / "test_v0.json"
        doc_data = {
            "version": "0.1",
            "model": {
                "bodies": [{"name": "base", "mass": 1.0}],
                "joints": [],
            },
        }
        doc_path.write_text(json.dumps(doc_data))
        doc = load_document(doc_path)
        assert doc.version == "0.1"

    def test_load_v1_document(self, tmp_path):
        """Test loading a v1 document."""
        doc_path = tmp_path / "test_v1.json"
        doc_data = {
            "version": "1.0",
            "model": {
                "bodies": [{"name": "base", "mass": 1.0}],
                "joints": [],
            },
            "assemblies": [],
            "instances": [],
        }
        doc_path.write_text(json.dumps(doc_data))
        doc = load_document(doc_path)
        assert doc.version == "1.0"

    def test_invalid_json(self, tmp_path):
        """Test that invalid JSON raises error."""
        doc_path = tmp_path / "invalid.json"
        doc_path.write_text("{ invalid json }")
        with pytest.raises(SchemaValidationError, match="Failed to read JSON"):
            load_document(doc_path)

    def test_missing_file(self):
        """Test that missing file raises error."""
        with pytest.raises(SchemaValidationError, match="Failed to read JSON"):
            load_document("/nonexistent/file.json")

    def test_unsupported_version(self, tmp_path):
        """Test that unsupported version raises error."""
        doc_path = tmp_path / "bad_version.json"
        doc_data = {"version": "2.0", "model": {}}
        doc_path.write_text(json.dumps(doc_data))
        with pytest.raises(SchemaValidationError, match="Unsupported version"):
            load_document(doc_path)

    def test_no_version(self, tmp_path):
        """Test that missing version raises error."""
        doc_path = tmp_path / "no_version.json"
        doc_data = {"model": {}}
        doc_path.write_text(json.dumps(doc_data))
        with pytest.raises(SchemaValidationError, match="Unsupported version"):
            load_document(doc_path)

    def test_invalid_schema(self, tmp_path):
        """Test that schema validation errors are caught."""
        doc_path = tmp_path / "invalid_schema.json"
        # Missing required 'model' field
        doc_data = {"version": "0.1"}
        doc_path.write_text(json.dumps(doc_data))
        with pytest.raises(SchemaValidationError):
            load_document(doc_path)

    def test_path_as_string(self, tmp_path):
        """Test that path can be passed as string."""
        doc_path = tmp_path / "test.json"
        doc_data = {
            "version": "0.1",
            "model": {"bodies": [{"name": "base", "mass": 1.0}], "joints": []},
        }
        doc_path.write_text(json.dumps(doc_data))
        doc = load_document(str(doc_path))
        assert doc.version == "0.1"

    def test_path_as_path_object(self, tmp_path):
        """Test that path can be passed as Path object."""
        doc_path = tmp_path / "test.json"
        doc_data = {
            "version": "0.1",
            "model": {"bodies": [{"name": "base", "mass": 1.0}], "joints": []},
        }
        doc_path.write_text(json.dumps(doc_data))
        doc = load_document(doc_path)
        assert doc.version == "0.1"
