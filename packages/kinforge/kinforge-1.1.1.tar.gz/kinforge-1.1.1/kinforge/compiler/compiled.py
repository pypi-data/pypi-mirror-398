from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from kinforge.model.body import Body
from kinforge.model.frame import Frame
from kinforge.model.graph import KinematicGraph
from kinforge.model.instance import Pose as InstancePose
from kinforge.model.joint import Joint


@dataclass(frozen=True)
class CompiledInstance:
    """
    Metadata for an instantiated assembly.
    """

    name: str
    namespace: Optional[str]
    root_body: str
    pose: Optional[InstancePose] = None
    initial_joints: Optional[Dict[str, float]] = None


@dataclass
class CompiledModel:
    """
    Flattened model produced by the compiler.
    """

    bodies: Dict[str, Body]
    joints: Dict[str, Joint]
    frames: Dict[str, Frame]
    instances: Dict[str, CompiledInstance]

    def graph(self) -> KinematicGraph:
        g = KinematicGraph(bodies=self.bodies, joints=self.joints)
        g.validate()
        return g
