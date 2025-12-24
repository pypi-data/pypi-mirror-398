"""Tests for compiled module."""

import pytest

from kinforge.compiler.compiled import CompiledInstance, CompiledModel
from kinforge.model.body import Body
from kinforge.model.joint import Joint


class TestCompiledModel:
    """Tests for CompiledModel."""

    def test_graph_method(self):
        """Test that graph() method creates and validates graph."""
        bodies = {
            "base": Body(name="base", mass=1.0),
            "link1": Body(name="link1", mass=1.0),
        }
        joints = {
            "j1": Joint(
                name="j1",
                type="revolute",
                parent="base",
                child="link1",
                axis=(0.0, 0.0, 1.0),
            )
        }
        model = CompiledModel(
            bodies=bodies,
            joints=joints,
            frames={},
            instances={},
        )
        graph = model.graph()
        assert graph.bodies == bodies
        assert graph.joints == joints

    def test_graph_method_invalid_raises(self):
        """Test that graph() method raises on invalid model."""
        bodies = {
            "base": Body(name="base", mass=1.0),
            "link1": Body(name="link1", mass=1.0),
        }
        # Invalid joint - parent doesn't exist
        joints = {
            "j1": Joint(
                name="j1",
                type="revolute",
                parent="nonexistent",
                child="link1",
                axis=(0.0, 0.0, 1.0),
            )
        }
        model = CompiledModel(
            bodies=bodies,
            joints=joints,
            frames={},
            instances={},
        )
        with pytest.raises(ValueError):
            model.graph()


class TestCompiledInstance:
    """Tests for CompiledInstance."""

    def test_compiled_instance_defaults(self):
        """Test CompiledInstance with defaults."""
        inst = CompiledInstance(
            name="robot",
            namespace=None,
            root_body="base",
        )
        assert inst.name == "robot"
        assert inst.namespace is None
        assert inst.root_body == "base"
        assert inst.pose is None
        assert inst.initial_joints is None

    def test_compiled_instance_with_all_fields(self):
        """Test CompiledInstance with all fields."""
        from kinforge.model.instance import Pose as InstancePose

        pose = InstancePose(xyz=(1.0, 2.0, 3.0), rpy=(0.0, 0.0, 1.57))
        inst = CompiledInstance(
            name="robot",
            namespace="ns",
            root_body="base",
            pose=pose,
            initial_joints={"j1": 0.5},
        )
        assert inst.name == "robot"
        assert inst.namespace == "ns"
        assert inst.root_body == "base"
        assert inst.pose == pose
        assert inst.initial_joints == {"j1": 0.5}
