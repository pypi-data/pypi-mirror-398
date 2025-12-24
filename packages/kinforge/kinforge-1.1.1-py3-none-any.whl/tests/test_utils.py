"""Tests for utility modules."""

import pytest

from kinforge.utils.names import is_base_link, ns_join, validate_sdf_name
from kinforge.utils.ordering import sorted_items, stable_sort
from kinforge.utils.transforms import rpy_str, xyz_str

# ============================================================
# Test names.py
# ============================================================


class TestNsJoin:
    """Tests for ns_join function."""

    def test_with_namespace(self):
        assert ns_join("robot", "base") == "robot/base"

    def test_with_none_namespace(self):
        assert ns_join(None, "base") == "base"

    def test_with_empty_namespace(self):
        assert ns_join("", "base") == "base"

    def test_nested_namespace(self):
        assert ns_join("robot/arm", "link1") == "robot/arm/link1"


class TestValidateSdfName:
    """Tests for validate_sdf_name function."""

    def test_valid_names(self):
        """Test that valid names pass validation."""
        validate_sdf_name("base")
        validate_sdf_name("base_link")
        validate_sdf_name("robot-1")
        validate_sdf_name("robot.arm")
        validate_sdf_name("robot/arm/link1")
        validate_sdf_name("Link_123")

    def test_empty_name(self):
        """Test that empty names are rejected."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            validate_sdf_name("")

    def test_invalid_characters(self):
        """Test that names with invalid characters are rejected."""
        with pytest.raises(ValueError, match="invalid characters"):
            validate_sdf_name("base link")  # space

        with pytest.raises(ValueError, match="invalid characters"):
            validate_sdf_name("base@link")  # @

        with pytest.raises(ValueError, match="invalid characters"):
            validate_sdf_name("base#link")  # #

        with pytest.raises(ValueError, match="invalid characters"):
            validate_sdf_name("base$link")  # $

    def test_whitespace(self):
        """Test that leading/trailing whitespace is rejected."""
        # Whitespace is caught by the regex check for invalid characters
        with pytest.raises(ValueError, match="invalid characters"):
            validate_sdf_name(" base")

        with pytest.raises(ValueError, match="invalid characters"):
            validate_sdf_name("base ")

        with pytest.raises(ValueError, match="invalid characters"):
            validate_sdf_name(" base ")

    def test_custom_context(self):
        """Test that custom context appears in error messages."""
        with pytest.raises(ValueError, match="Invalid joint name"):
            validate_sdf_name("bad name", context="joint name")


class TestIsBaseLink:
    """Tests for is_base_link function."""

    def test_simple_base(self):
        assert is_base_link("base") is True

    def test_namespaced_base(self):
        assert is_base_link("robot/base") is True
        assert is_base_link("robot/arm/base") is True

    def test_not_base(self):
        assert is_base_link("link1") is False
        assert is_base_link("shoulder") is False

    def test_false_positives(self):
        """Test that we don't match strings that just contain 'base'."""
        assert is_base_link("database") is False
        assert is_base_link("firebase") is False
        assert is_base_link("base_link") is False
        assert is_base_link("robot/database") is False


# ============================================================
# Test transforms.py
# ============================================================


class TestXyzStr:
    """Tests for xyz_str function."""

    def test_none(self):
        assert xyz_str(None) == "0 0 0"

    def test_zero_vector(self):
        """Test that (0, 0, 0) is not treated as None."""
        assert xyz_str((0.0, 0.0, 0.0)) == "0.0 0.0 0.0"

    def test_positive_values(self):
        assert xyz_str((1.0, 2.0, 3.0)) == "1.0 2.0 3.0"

    def test_negative_values(self):
        assert xyz_str((-1.0, -2.0, -3.0)) == "-1.0 -2.0 -3.0"

    def test_mixed_values(self):
        assert xyz_str((1.5, -2.5, 3.14)) == "1.5 -2.5 3.14"

    def test_integers(self):
        assert xyz_str((1, 2, 3)) == "1 2 3"


class TestRpyStr:
    """Tests for rpy_str function."""

    def test_none(self):
        assert rpy_str(None) == "0 0 0"

    def test_zero_rotation(self):
        """Test that (0, 0, 0) is not treated as None."""
        assert rpy_str((0.0, 0.0, 0.0)) == "0.0 0.0 0.0"

    def test_positive_values(self):
        assert rpy_str((1.57, 0.0, 3.14)) == "1.57 0.0 3.14"

    def test_negative_values(self):
        assert rpy_str((-1.57, -0.5, -3.14)) == "-1.57 -0.5 -3.14"


# ============================================================
# Test ordering.py
# ============================================================


class TestSortedItems:
    """Tests for sorted_items function."""

    def test_empty_dict(self):
        assert list(sorted_items({})) == []

    def test_sorted_by_key(self):
        d = {"z": 1, "a": 2, "m": 3}
        result = list(sorted_items(d))
        assert result == [("a", 2), ("m", 3), ("z", 1)]

    def test_preserves_values(self):
        d = {"b": "value_b", "a": "value_a"}
        result = list(sorted_items(d))
        assert result == [("a", "value_a"), ("b", "value_b")]


class TestStableSort:
    """Tests for stable_sort function."""

    def test_empty_list(self):
        assert stable_sort([], key=lambda x: x) == []

    def test_sort_by_attribute(self):
        class Item:
            __slots__ = ("name",)

            def __init__(self, name):
                self.name = name

        items = [Item("z"), Item("a"), Item("m")]
        result = stable_sort(items, key=lambda x: x.name)
        assert [i.name for i in result] == ["a", "m", "z"]

    def test_stable_ordering(self):
        """Test that equal elements maintain their relative order."""
        items = [(1, "a"), (2, "b"), (1, "c"), (2, "d")]
        result = stable_sort(items, key=lambda x: x[0])
        assert result == [(1, "a"), (1, "c"), (2, "b"), (2, "d")]

    def test_sort_integers(self):
        items = [3, 1, 4, 1, 5, 9, 2, 6]
        result = stable_sort(items, key=lambda x: x)
        assert result == [1, 1, 2, 3, 4, 5, 6, 9]
