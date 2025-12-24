"""Tests for URDF exporter."""

from pathlib import Path

import pytest

from kinforge.compiler.compiled import CompiledInstance, CompiledModel
from kinforge.exporters.urdf import export_urdf
from kinforge.model.body import Body, Geometry
from kinforge.model.frame import Frame, Pose
from kinforge.model.joint import Joint, JointLimits


class TestExportURDF:
    """Tests for URDF export functionality."""

    def test_simple_robot(self, tmp_path):
        """Test export of simple robot."""
        out_path = tmp_path / "robot.urdf"
        body = Body(name="base", mass=1.0)
        instance = CompiledInstance(name="robot", namespace=None, root_body="base")
        model = CompiledModel(
            bodies={"base": body},
            joints={},
            frames={},
            instances={"robot": instance},
        )
        export_urdf(model, str(out_path), robot_name="test_robot")
        assert out_path.exists()
        content = out_path.read_text()
        assert '<robot name="test_robot">' in content
        assert '<link name="base">' in content

    def test_robot_with_joint(self, tmp_path):
        """Test export with joint."""
        out_path = tmp_path / "robot.urdf"
        bodies = {
            "base": Body(name="base", mass=1.0),
            "link1": Body(name="link1", mass=1.0),
        }
        joint = Joint(
            name="j1",
            type="revolute",
            parent="base",
            child="link1",
            axis=(0.0, 0.0, 1.0),
        )
        instance = CompiledInstance(name="robot", namespace=None, root_body="base")
        model = CompiledModel(
            bodies=bodies,
            joints={"j1": joint},
            frames={},
            instances={"robot": instance},
        )
        export_urdf(model, str(out_path))
        content = out_path.read_text()
        assert '<joint name="j1" type="revolute">' in content
        assert '<parent link="base" />' in content
        assert '<child link="link1" />' in content

    def test_joint_with_origin(self, tmp_path):
        """Test joint with origin pose."""
        out_path = tmp_path / "robot.urdf"
        bodies = {
            "base": Body(name="base", mass=1.0),
            "link1": Body(name="link1", mass=1.0),
        }
        joint = Joint(
            name="j1",
            type="revolute",
            parent="base",
            child="link1",
            axis=(0.0, 0.0, 1.0),
            origin=Pose(xyz=(1.0, 2.0, 3.0), rpy=(0.0, 0.0, 1.57)),
        )
        instance = CompiledInstance(name="robot", namespace=None, root_body="base")
        model = CompiledModel(
            bodies=bodies,
            joints={"j1": joint},
            frames={},
            instances={"robot": instance},
        )
        export_urdf(model, str(out_path))
        content = out_path.read_text()
        assert 'xyz="1.0 2.0 3.0"' in content
        assert 'rpy="0.0 0.0 1.57"' in content

    def test_joint_with_limits(self, tmp_path):
        """Test joint with limits."""
        out_path = tmp_path / "robot.urdf"
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
        export_urdf(model, str(out_path))
        content = out_path.read_text()
        assert '<limit lower="-1.57" upper="1.57"' in content
        assert 'effort="1.0"' in content
        assert 'velocity="1.0"' in content

    def test_joint_with_partial_limits(self, tmp_path):
        """Test joint with only lower or upper limit."""
        out_path = tmp_path / "robot.urdf"
        bodies = {
            "base": Body(name="base", mass=1.0),
            "link1": Body(name="link1", mass=1.0),
        }
        limits = JointLimits(lower=-1.57)
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
        export_urdf(model, str(out_path))
        content = out_path.read_text()
        assert 'lower="-1.57"' in content

    def test_prismatic_joint_with_limits(self, tmp_path):
        """Test prismatic joint with limits."""
        out_path = tmp_path / "robot.urdf"
        bodies = {
            "base": Body(name="base", mass=1.0),
            "link1": Body(name="link1", mass=1.0),
        }
        limits = JointLimits(lower=0.0, upper=1.0)
        joint = Joint(
            name="j1",
            type="prismatic",
            parent="base",
            child="link1",
            axis=(1.0, 0.0, 0.0),
            limits=limits,
        )
        instance = CompiledInstance(name="robot", namespace=None, root_body="base")
        model = CompiledModel(
            bodies=bodies,
            joints={"j1": joint},
            frames={},
            instances={"robot": instance},
        )
        export_urdf(model, str(out_path))
        content = out_path.read_text()
        assert '<joint name="j1" type="prismatic">' in content
        assert "<limit" in content

    def test_fixed_joint_no_limits(self, tmp_path):
        """Test that fixed joints don't get limits."""
        out_path = tmp_path / "robot.urdf"
        bodies = {
            "base": Body(name="base", mass=1.0),
            "link1": Body(name="link1", mass=1.0),
        }
        joint = Joint(
            name="j1",
            type="fixed",
            parent="base",
            child="link1",
        )
        instance = CompiledInstance(name="robot", namespace=None, root_body="base")
        model = CompiledModel(
            bodies=bodies,
            joints={"j1": joint},
            frames={},
            instances={"robot": instance},
        )
        export_urdf(model, str(out_path))
        content = out_path.read_text()
        assert '<joint name="j1" type="fixed">' in content
        # Fixed joints shouldn't have limits
        assert "<limit" not in content

    def test_frame_export(self, tmp_path):
        """Test that frames are exported."""
        out_path = tmp_path / "robot.urdf"
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
        export_urdf(model, str(out_path))
        content = out_path.read_text()
        assert '<link name="tool0" />' in content or '<link name="tool0">' in content
        assert '<joint name="tool0__fixed" type="fixed">' in content
        assert '<parent link="base" />' in content
        assert '<child link="tool0" />' in content

    def test_geometry_types(self, tmp_path):
        """Test all geometry types."""
        out_path = tmp_path / "robot.urdf"

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
        export_urdf(model, str(out_path))
        content = out_path.read_text()
        assert "<box size=" in content
        assert (
            '<sphere radius="0.5" />' in content or '<sphere radius="0.5"/>' in content
        )
        assert (
            '<cylinder radius="0.3" length="1.5" />' in content
            or '<cylinder radius="0.3" length="1.5"/>' in content
        )
        assert (
            '<mesh filename="file://model.stl" />' in content
            or '<mesh filename="file://model.stl"/>' in content
        )

    def test_mesh_with_scale(self, tmp_path):
        """Test mesh geometry with scale."""
        out_path = tmp_path / "robot.urdf"
        body = Body(
            name="base",
            mass=1.0,
            visual=Geometry(type="mesh", uri="file://model.stl", scale=(2.0, 2.0, 2.0)),
        )
        instance = CompiledInstance(name="robot", namespace=None, root_body="base")
        model = CompiledModel(
            bodies={"base": body},
            joints={},
            frames={},
            instances={"robot": instance},
        )
        export_urdf(model, str(out_path))
        content = out_path.read_text()
        assert 'scale="2.0 2.0 2.0"' in content

    def test_collision_geometry(self, tmp_path):
        """Test collision geometry."""
        out_path = tmp_path / "robot.urdf"
        body = Body(
            name="base",
            mass=1.0,
            visual=Geometry(type="box", size=(1.0, 1.0, 1.0)),
            collision=Geometry(type="sphere", radius=0.5),
        )
        instance = CompiledInstance(name="robot", namespace=None, root_body="base")
        model = CompiledModel(
            bodies={"base": body},
            joints={},
            frames={},
            instances={"robot": instance},
        )
        export_urdf(model, str(out_path))
        content = out_path.read_text()
        assert "<visual>" in content
        assert "<collision>" in content
        assert "<box" in content
        assert "<sphere" in content

    def test_body_without_mass(self, tmp_path):
        """Test body without mass."""
        out_path = tmp_path / "robot.urdf"
        body = Body(name="base", mass=None)
        instance = CompiledInstance(name="robot", namespace=None, root_body="base")
        model = CompiledModel(
            bodies={"base": body},
            joints={},
            frames={},
            instances={"robot": instance},
        )
        export_urdf(model, str(out_path))
        content = out_path.read_text()
        assert '<link name="base"' in content
        # Should not have inertial if no mass
        assert "<inertial>" not in content

    def test_mesh_without_uri_raises_error(self, tmp_path):
        """Test that mesh without URI raises error."""
        out_path = tmp_path / "robot.urdf"
        body = Body(name="base", mass=1.0, visual=Geometry(type="mesh"))
        instance = CompiledInstance(name="robot", namespace=None, root_body="base")
        model = CompiledModel(
            bodies={"base": body},
            joints={},
            frames={},
            instances={"robot": instance},
        )
        with pytest.raises(ValueError, match="Mesh geometry requires uri"):
            export_urdf(model, str(out_path))

    def test_unsupported_geometry_raises_error(self, tmp_path):
        """Test that unsupported geometry type raises error."""
        out_path = tmp_path / "robot.urdf"
        # Create a geometry with invalid type by directly constructing it
        geom = Geometry(type="invalid")  # type: ignore[assignment]
        body = Body(name="base", mass=1.0, visual=geom)
        instance = CompiledInstance(name="robot", namespace=None, root_body="base")
        model = CompiledModel(
            bodies={"base": body},
            joints={},
            frames={},
            instances={"robot": instance},
        )
        with pytest.raises(ValueError, match="Unsupported geometry type"):
            export_urdf(model, str(out_path))
