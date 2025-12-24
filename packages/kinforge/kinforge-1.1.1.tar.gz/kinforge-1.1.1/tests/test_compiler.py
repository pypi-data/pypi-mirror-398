"""Tests for compiler modules."""

import json
from pathlib import Path

import pytest

from kinforge.compiler.compiler_v0 import compile_v0
from kinforge.parser.loader import load_document


class TestCompilerV0:
    """Tests for compiler_v0 module."""

    def test_compile_with_unknown_assembly(self, tmp_path):
        """Test that instance referencing unknown assembly raises error during validation."""
        from kinforge.errors import SchemaValidationError

        doc_path = tmp_path / "test.json"
        doc_data = {
            "version": "0.1",
            "model": {
                "bodies": [{"name": "base", "mass": 1.0}],
                "joints": [],
                "frames": [],
            },
            "assemblies": [
                {"name": "robot", "root": "base", "bodies": ["base"], "joints": []}
            ],
            "instances": [
                {
                    "name": "inst1",
                    "assembly": "unknown_assembly",  # This doesn't exist
                    "namespace": None,
                    "pose": {"xyz": [0.0, 0.0, 0.0], "rpy": [0.0, 0.0, 0.0]},
                }
            ],
        }
        doc_path.write_text(json.dumps(doc_data))

        # Validation happens in parser, not compiler
        with pytest.raises(SchemaValidationError, match="references unknown assembly"):
            load_document(doc_path)

    def test_compile_implicit_no_instances(self, tmp_path):
        """Test compilation with no instances (implicit compilation)."""
        doc_path = tmp_path / "test.json"
        doc_data = {
            "version": "0.1",
            "model": {
                "bodies": [{"name": "base", "mass": 1.0}],
                "joints": [],
                "frames": [],
            },
            "assemblies": [],
            "instances": [],
        }
        doc_path.write_text(json.dumps(doc_data))
        doc = load_document(doc_path)

        compiled = compile_v0(doc)
        assert len(compiled.instances) == 0
        assert "base" in compiled.bodies
