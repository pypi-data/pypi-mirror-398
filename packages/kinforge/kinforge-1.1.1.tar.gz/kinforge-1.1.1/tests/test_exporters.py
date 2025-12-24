"""Tests for exporter modules."""

import os
import tempfile
from pathlib import Path

import pytest

from kinforge.compiler.compiled import CompiledInstance, CompiledModel
from kinforge.errors import ExportError
from kinforge.exporters.sdf import export_sdf
from kinforge.model.body import Body, Geometry
from kinforge.model.frame import Frame, Pose
from kinforge.model.instance import Pose as InstancePose
from kinforge.model.joint import Joint, JointLimits

# ============================================================
# Test SDF Exporter
# ============================================================


class TestExportSdfValidation:
    """Tests for SDF export validation."""

    def test_empty_instances(self):
        """Test that empty instances dict raises error."""
        model = CompiledModel(bodies={}, joints={}, frames={}, instances={})
        # Validation happens in order: bodies first, then instances
        fd, path = tempfile.mkstemp(suffix=".sdf")
        try:
            with pytest.raises(ExportError, match="no bodies|no instances"):
                export_sdf(model, path)
        finally:
            os.close(fd)

    def test_no_bodies(self):
        """Test that model with no bodies raises error."""
        instance = CompiledInstance(name="test", namespace=None, root_body="base")
        model = CompiledModel(
            bodies={}, joints={}, frames={}, instances={"test": instance}
        )
        fd, path = tempfile.mkstemp(suffix=".sdf")
        try:
            with pytest.raises(ExportError, match="no bodies"):
                export_sdf(model, path)
        finally:
            os.close(fd)

    def test_invalid_body_name(self):
        """Test that invalid body names are caught."""
        body = Body(name="bad name", mass=1.0)  # Space in name
        instance = CompiledInstance(name="test", namespace=None, root_body="base")
        model = CompiledModel(
            bodies={"bad name": body},
            joints={},
            frames={},
            instances={"test": instance},
        )
        # Validation can catch either instance or body name first
        fd, path = tempfile.mkstemp(suffix=".sdf")
        try:
            with pytest.raises((ExportError, ValueError)):
                export_sdf(model, path)
        finally:
            os.close(fd)

    def test_invalid_instance_name(self):
        """Test that invalid instance names are caught."""
        body = Body(name="base", mass=1.0)
        instance = CompiledInstance(name="bad name", namespace=None, root_body="base")
        model = CompiledModel(
            bodies={"base": body},
            joints={},
            frames={},
            instances={"bad name": instance},
        )
        fd, path = tempfile.mkstemp(suffix=".sdf")
        try:
            with pytest.raises((ExportError, ValueError)):
                export_sdf(model, path)
        finally:
            os.close(fd)

    def test_invalid_namespace(self):
        """Test that invalid namespaces are caught."""
        body = Body(name="base", mass=1.0)
        instance = CompiledInstance(name="test", namespace="bad ns", root_body="base")
        model = CompiledModel(
            bodies={"base": body},
            joints={},
            frames={},
            instances={"test": instance},
        )
        fd, path = tempfile.mkstemp(suffix=".sdf")
        try:
            with pytest.raises((ExportError, ValueError)):
                export_sdf(model, path)
        finally:
            os.close(fd)

    def test_invalid_joint(self):
        """Test that invalid joints are caught."""
        body = Body(name="base", mass=1.0)
        # Revolute joint without axis
        joint = Joint(name="j1", type="revolute", parent="base", child="link1")
        instance = CompiledInstance(name="test", namespace=None, root_body="base")
        model = CompiledModel(
            bodies={"base": body, "link1": Body(name="link1", mass=1.0)},
            joints={"j1": joint},
            frames={},
            instances={"test": instance},
        )
        fd, path = tempfile.mkstemp(suffix=".sdf")
        try:
            with pytest.raises(ExportError, match="requires axis"):
                export_sdf(model, path)
        finally:
            os.close(fd)

    def test_invalid_body_geometry(self):
        """Test that invalid body geometry is caught."""
        # Box without size
        geom = Geometry(type="box")
        body = Body(name="base", mass=1.0, visual=geom)
        instance = CompiledInstance(name="test", namespace=None, root_body="base")
        model = CompiledModel(
            bodies={"base": body},
            joints={},
            frames={},
            instances={"test": instance},
        )
        fd, path = tempfile.mkstemp(suffix=".sdf")
        try:
            with pytest.raises(ExportError, match="requires size"):
                export_sdf(model, path)
        finally:
            os.close(fd)


class TestExportSdfFileHandling:
    """Tests for SDF export file handling."""

    def test_creates_parent_directory(self, tmp_path):
        """Test that parent directories are created."""
        out_path = tmp_path / "subdir" / "test.sdf"
        body = Body(name="base", mass=1.0)
        instance = CompiledInstance(name="test", namespace=None, root_body="base")
        model = CompiledModel(
            bodies={"base": body},
            joints={},
            frames={},
            instances={"test": instance},
        )
        export_sdf(model, str(out_path))
        assert out_path.exists()

    def test_invalid_output_path(self, tmp_path):
        """Test that writing to a directory raises error."""
        body = Body(name="base", mass=1.0)
        instance = CompiledInstance(name="test", namespace=None, root_body="base")
        model = CompiledModel(
            bodies={"base": body},
            joints={},
            frames={},
            instances={"test": instance},
        )
        # Try to write to a directory
        with pytest.raises(ExportError, match="not a file"):
            export_sdf(model, str(tmp_path))


class TestExportSdfFeatures:
    """Tests for specific SDF export features."""

    def test_single_instance(self, tmp_path):
        """Test export of single instance."""
        out_path = tmp_path / "single.sdf"
        body = Body(name="base", mass=1.0)
        instance = CompiledInstance(name="robot", namespace=None, root_body="base")
        model = CompiledModel(
            bodies={"base": body},
            joints={},
            frames={},
            instances={"robot": instance},
        )
        export_sdf(model, str(out_path))
        assert out_path.exists()
        content = out_path.read_text()
        assert '<model name="robot">' in content
        assert "<world" not in content  # No world for single instance

    def test_multiple_instances(self, tmp_path):
        """Test export of multiple instances creates world."""
        out_path = tmp_path / "multi.sdf"
        body = Body(name="base", mass=1.0)
        inst1 = CompiledInstance(name="robot1", namespace=None, root_body="base")
        inst2 = CompiledInstance(name="robot2", namespace=None, root_body="base")
        model = CompiledModel(
            bodies={"base": body},
            joints={},
            frames={},
            instances={"robot1": inst1, "robot2": inst2},
        )
        export_sdf(model, str(out_path))
        assert out_path.exists()
        content = out_path.read_text()
        assert '<world name="generated">' in content
        assert '<model name="robot1">' in content
        assert '<model name="robot2">' in content

    def test_custom_world_name(self, tmp_path):
        """Test that custom world name is used."""
        out_path = tmp_path / "custom.sdf"
        body = Body(name="base", mass=1.0)
        inst1 = CompiledInstance(name="robot1", namespace=None, root_body="base")
        inst2 = CompiledInstance(name="robot2", namespace=None, root_body="base")
        model = CompiledModel(
            bodies={"base": body},
            joints={},
            frames={},
            instances={"robot1": inst1, "robot2": inst2},
        )
        export_sdf(model, str(out_path), world_name="my_world")
        content = out_path.read_text()
        assert '<world name="my_world">' in content

    def test_instance_with_pose(self, tmp_path):
        """Test that instance poses are exported."""
        out_path = tmp_path / "pose.sdf"
        body = Body(name="base", mass=1.0)
        pose = InstancePose(xyz=(1.0, 2.0, 3.0), rpy=(0.0, 0.0, 1.57))
        instance = CompiledInstance(
            name="robot", namespace=None, root_body="base", pose=pose
        )
        model = CompiledModel(
            bodies={"base": body},
            joints={},
            frames={},
            instances={"robot": instance},
        )
        export_sdf(model, str(out_path))
        content = out_path.read_text()
        assert "1.0 2.0 3.0" in content
        assert "1.57" in content

    def test_namespace_in_names(self, tmp_path):
        """Test that namespaces are applied to link/joint names."""
        out_path = tmp_path / "ns.sdf"
        body = Body(name="base", mass=1.0)
        instance = CompiledInstance(name="robot", namespace="my_ns", root_body="base")
        model = CompiledModel(
            bodies={"base": body},
            joints={},
            frames={},
            instances={"robot": instance},
        )
        export_sdf(model, str(out_path))
        content = out_path.read_text()
        assert "my_ns/base" in content

    def test_frame_export(self, tmp_path):
        """Test that frames are exported as fixed links."""
        out_path = tmp_path / "frame.sdf"
        body = Body(name="base", mass=1.0)
        frame_pose = Pose(xyz=(0.1, 0.0, 0.0))
        frame = Frame(name="tool0", attached_to="base", pose=frame_pose)
        instance = CompiledInstance(name="robot", namespace=None, root_body="base")
        model = CompiledModel(
            bodies={"base": body},
            joints={},
            frames={"tool0": frame},
            instances={"robot": instance},
        )
        export_sdf(model, str(out_path))
        content = out_path.read_text()
        assert '<link name="tool0">' in content
        assert "::frame_fixed" in content  # Check for frame joint naming

    def test_joint_with_limits(self, tmp_path):
        """Test that joint limits are exported."""
        out_path = tmp_path / "limits.sdf"
        bodies = {
            "base": Body(name="base", mass=1.0),
            "link1": Body(name="link1", mass=1.0),
        }
        limits = JointLimits(lower=-1.57, upper=1.57)
        joint = Joint(
            name="j1",
            type="revolute",
            parent="base",
            child="link1",
            axis=(0.0, 0.0, 1.0),
            limits=limits,
        )
        instance = CompiledInstance(name="robot", namespace=None, root_body="base")
        model = CompiledModel(
            bodies=bodies,
            joints={"j1": joint},
            frames={},
            instances={"robot": instance},
        )
        export_sdf(model, str(out_path))
        content = out_path.read_text()
        assert "<lower>-1.57</lower>" in content
        assert "<upper>1.57</upper>" in content

    def test_geometry_types(self, tmp_path):
        """Test all geometry types are exported correctly."""
        out_path = tmp_path / "geom.sdf"

        bodies = {
            "box_body": Body(
                name="box_body",
                mass=1.0,
                visual=Geometry(type="box", size=(1.0, 2.0, 3.0)),
            ),
            "sphere_body": Body(
                name="sphere_body", mass=1.0, visual=Geometry(type="sphere", radius=0.5)
            ),
            "cylinder_body": Body(
                name="cylinder_body",
                mass=1.0,
                visual=Geometry(type="cylinder", radius=0.3, length=1.5),
            ),
            "mesh_body": Body(
                name="mesh_body",
                mass=1.0,
                visual=Geometry(type="mesh", uri="file://model.stl"),
            ),
        }
        instance = CompiledInstance(name="robot", namespace=None, root_body="box_body")
        model = CompiledModel(
            bodies=bodies, joints={}, frames={}, instances={"robot": instance}
        )
        export_sdf(model, str(out_path))
        content = out_path.read_text()
        assert "<box>" in content
        assert "<sphere>" in content
        assert "<cylinder>" in content
        assert "<mesh>" in content
        assert "file://model.stl" in content

    def test_base_link_geometry_positioning(self, tmp_path):
        """Test that base links get proper geometry offsets."""
        out_path = tmp_path / "base.sdf"
        # Create a body named 'base' with box geometry
        box_geom = Geometry(type="box", size=(1.0, 1.0, 0.5))
        body = Body(name="base", mass=10.0, visual=box_geom)
        instance = CompiledInstance(name="robot", namespace=None, root_body="base")
        model = CompiledModel(
            bodies={"base": body},
            joints={},
            frames={},
            instances={"robot": instance},
        )
        export_sdf(model, str(out_path))
        content = out_path.read_text()
        # Base box should have pose offset
        assert "0 0 0.25" in content  # Half the z-size
