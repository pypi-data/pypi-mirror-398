"""Tests for error classes."""

import pytest

from kinforge.errors import (
    CompileError,
    ExportError,
    KinforgeError,
    SchemaValidationError,
)


class TestErrors:
    """Tests for error classes."""

    def test_kinforge_error(self):
        """Test base KinforgeError."""
        with pytest.raises(KinforgeError, match="test message"):
            raise KinforgeError("test message")

    def test_schema_validation_error(self):
        """Test SchemaValidationError."""
        with pytest.raises(SchemaValidationError, match="invalid schema"):
            raise SchemaValidationError("invalid schema")

    def test_schema_validation_error_is_kinforge_error(self):
        """Test that SchemaValidationError is a KinforgeError."""
        with pytest.raises(KinforgeError):
            raise SchemaValidationError("test")

    def test_compile_error(self):
        """Test CompileError."""
        with pytest.raises(CompileError, match="compile failed"):
            raise CompileError("compile failed")

    def test_compile_error_is_kinforge_error(self):
        """Test that CompileError is a KinforgeError."""
        with pytest.raises(KinforgeError):
            raise CompileError("test")

    def test_export_error(self):
        """Test ExportError."""
        with pytest.raises(ExportError, match="export failed"):
            raise ExportError("export failed")

    def test_export_error_is_kinforge_error(self):
        """Test that ExportError is a KinforgeError."""
        with pytest.raises(KinforgeError):
            raise ExportError("test")
