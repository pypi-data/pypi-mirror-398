"""Tests for CLI module."""

import json
from pathlib import Path

import pytest

from kinforge.cli import main


class TestCLI:
    """Tests for CLI functionality."""

    def test_build_sdf_v0(self, tmp_path):
        """Test building SDF from v0 JSON."""
        input_file = tmp_path / "input.json"
        output_file = tmp_path / "output.sdf"

        input_file.write_text(
            json.dumps(
                {
                    "version": "0.1",
                    "model": {
                        "bodies": [
                            {
                                "name": "base",
                                "mass": 1.0,
                                "visual": {"type": "box", "size": [1.0, 1.0, 1.0]},
                            }
                        ],
                        "joints": [],
                        "frames": [],
                    },
                    "assemblies": [
                        {
                            "name": "robot",
                            "root": "base",
                            "bodies": ["base"],
                            "joints": [],
                        }
                    ],
                    "instances": [
                        {
                            "name": "robot1",
                            "assembly": "robot",
                            "namespace": None,
                            "pose": {"xyz": [0.0, 0.0, 0.0], "rpy": [0.0, 0.0, 0.0]},
                        }
                    ],
                }
            )
        )

        result = main(
            ["build", str(input_file), "--out", str(output_file), "--format", "sdf"]
        )
        assert result == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert '<model name="robot1">' in content

    def test_build_sdf_v1(self, tmp_path):
        """Test building SDF from v1 JSON."""
        input_file = tmp_path / "input.json"
        output_file = tmp_path / "output.sdf"

        input_file.write_text(
            json.dumps(
                {
                    "version": "1.0",
                    "model": {
                        "bodies": [
                            {
                                "name": "base",
                                "mass": 1.0,
                                "visual": {"type": "box", "size": [1.0, 1.0, 1.0]},
                            }
                        ],
                        "joints": [],
                        "frames": [],
                    },
                    "assemblies": [
                        {
                            "name": "robot",
                            "root": "base",
                            "bodies": ["base"],
                            "joints": [],
                        }
                    ],
                    "instances": [
                        {
                            "name": "robot1",
                            "assembly": "robot",
                            "namespace": None,
                            "pose": {"xyz": [0.0, 0.0, 0.0], "rpy": [0.0, 0.0, 0.0]},
                        }
                    ],
                }
            )
        )

        result = main(
            ["build", str(input_file), "--out", str(output_file), "--format", "sdf"]
        )
        assert result == 0
        assert output_file.exists()

    def test_build_urdf(self, tmp_path):
        """Test building URDF from JSON."""
        input_file = tmp_path / "input.json"
        output_file = tmp_path / "output.urdf"

        input_file.write_text(
            json.dumps(
                {
                    "version": "0.1",
                    "model": {
                        "bodies": [
                            {
                                "name": "base",
                                "mass": 1.0,
                                "visual": {"type": "box", "size": [1.0, 1.0, 1.0]},
                            }
                        ],
                        "joints": [],
                        "frames": [],
                    },
                    "assemblies": [
                        {
                            "name": "robot",
                            "root": "base",
                            "bodies": ["base"],
                            "joints": [],
                        }
                    ],
                    "instances": [
                        {
                            "name": "robot1",
                            "assembly": "robot",
                            "namespace": None,
                            "pose": {"xyz": [0.0, 0.0, 0.0], "rpy": [0.0, 0.0, 0.0]},
                        }
                    ],
                }
            )
        )

        result = main(
            ["build", str(input_file), "--out", str(output_file), "--format", "urdf"]
        )
        assert result == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert '<robot name="output">' in content

    def test_build_auto_format_from_extension(self, tmp_path):
        """Test that format is auto-detected from file extension."""
        input_file = tmp_path / "input.json"
        output_file = tmp_path / "output.sdf"

        input_file.write_text(
            json.dumps(
                {
                    "version": "0.1",
                    "model": {
                        "bodies": [
                            {
                                "name": "base",
                                "mass": 1.0,
                                "visual": {"type": "box", "size": [1.0, 1.0, 1.0]},
                            }
                        ],
                        "joints": [],
                        "frames": [],
                    },
                    "assemblies": [
                        {
                            "name": "robot",
                            "root": "base",
                            "bodies": ["base"],
                            "joints": [],
                        }
                    ],
                    "instances": [
                        {
                            "name": "robot1",
                            "assembly": "robot",
                            "namespace": None,
                            "pose": {"xyz": [0.0, 0.0, 0.0], "rpy": [0.0, 0.0, 0.0]},
                        }
                    ],
                }
            )
        )

        result = main(["build", str(input_file), "--out", str(output_file)])
        assert result == 0
        assert output_file.exists()

    def test_build_with_initial_joints(self, tmp_path):
        """Test building with initial joint states."""
        input_file = tmp_path / "input.json"
        output_file = tmp_path / "output.sdf"

        input_file.write_text(
            json.dumps(
                {
                    "version": "1.0",
                    "model": {
                        "bodies": [
                            {
                                "name": "base",
                                "mass": 1.0,
                                "visual": {"type": "box", "size": [1.0, 1.0, 1.0]},
                            },
                            {
                                "name": "link1",
                                "mass": 1.0,
                                "visual": {"type": "box", "size": [1.0, 1.0, 1.0]},
                            },
                        ],
                        "joints": [
                            {
                                "name": "j1",
                                "type": "revolute",
                                "parent": "base",
                                "child": "link1",
                                "axis": [0.0, 0.0, 1.0],
                                "limits": {"lower": -1.57, "upper": 1.57},
                            }
                        ],
                        "frames": [],
                    },
                    "assemblies": [
                        {
                            "name": "robot",
                            "root": "base",
                            "bodies": ["base", "link1"],
                            "joints": ["j1"],
                        }
                    ],
                    "instances": [
                        {
                            "name": "robot1",
                            "assembly": "robot",
                            "namespace": None,
                            "pose": {"xyz": [0.0, 0.0, 0.0], "rpy": [0.0, 0.0, 0.0]},
                            "initial_joints": {"j1": 0.5},
                        }
                    ],
                }
            )
        )

        result = main(["build", str(input_file), "--out", str(output_file)])
        assert result == 0
        assert output_file.exists()

        sidecar = tmp_path / "output.robot1.joint_states.json"
        assert sidecar.exists()
        sidecar_data = json.loads(sidecar.read_text())
        assert sidecar_data == {"j1": 0.5}

    def test_build_invalid_format(self, tmp_path):
        """Test that invalid format raises error."""
        input_file = tmp_path / "input.json"
        output_file = tmp_path / "output.xyz"

        input_file.write_text(
            json.dumps(
                {
                    "version": "0.1",
                    "model": {
                        "bodies": [
                            {
                                "name": "base",
                                "mass": 1.0,
                                "visual": {"type": "box", "size": [1.0, 1.0, 1.0]},
                            }
                        ],
                        "joints": [],
                        "frames": [],
                    },
                    "assemblies": [
                        {
                            "name": "robot",
                            "root": "base",
                            "bodies": ["base"],
                            "joints": [],
                        }
                    ],
                    "instances": [
                        {
                            "name": "robot1",
                            "assembly": "robot",
                            "namespace": None,
                            "pose": {"xyz": [0.0, 0.0, 0.0], "rpy": [0.0, 0.0, 0.0]},
                        }
                    ],
                }
            )
        )

        result = main(["build", str(input_file), "--out", str(output_file)])
        assert result == 1

    def test_build_invalid_input_file(self, tmp_path):
        """Test that invalid input file raises error."""
        input_file = tmp_path / "nonexistent.json"
        output_file = tmp_path / "output.sdf"

        result = main(["build", str(input_file), "--out", str(output_file)])
        assert result == 1

    def test_build_invalid_json(self, tmp_path):
        """Test that invalid JSON raises error."""
        input_file = tmp_path / "input.json"
        output_file = tmp_path / "output.sdf"

        input_file.write_text("invalid json")

        result = main(["build", str(input_file), "--out", str(output_file)])
        assert result == 1

    def test_build_no_instances_raises_error(self, tmp_path):
        """Test that building with no instances raises error (exporter requires instances)."""
        input_file = tmp_path / "input.json"
        output_file = tmp_path / "output.sdf"

        input_file.write_text(
            json.dumps(
                {
                    "version": "0.1",
                    "model": {
                        "bodies": [
                            {
                                "name": "base",
                                "mass": 1.0,
                                "visual": {"type": "box", "size": [1.0, 1.0, 1.0]},
                            }
                        ],
                        "joints": [],
                        "frames": [],
                    },
                    "assemblies": [],
                    "instances": [],
                }
            )
        )

        result = main(["build", str(input_file), "--out", str(output_file)])
        assert result == 1  # Should fail because exporter requires instances
