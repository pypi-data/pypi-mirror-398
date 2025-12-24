from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set

from .body import Body
from .joint import Joint


@dataclass
class KinematicGraph:
    """
    Directed graph of bodies connected by joints.

    Nodes: bodies
    Edges: joints (parent -> child)
    """

    bodies: Dict[str, Body]
    joints: Dict[str, Joint]

    def validate(self) -> None:
        self._validate_references()
        self._validate_no_cycles()

    def roots(self) -> List[str]:
        """
        Returns bodies with no incoming joints.
        """
        incoming: Set[str] = set()
        for joint in self.joints.values():
            incoming.add(joint.child)

        return [name for name in self.bodies if name not in incoming]

    def require_single_root(self) -> str:
        """
        Enforce URDF-style single-root constraint.
        """
        roots = self.roots()
        if len(roots) != 1:
            raise ValueError(
                f"Expected exactly one root body, found {len(roots)}: {roots}"
            )
        return roots[0]

    # --------------------
    # Internal validation
    # --------------------

    def _validate_references(self) -> None:
        for joint in self.joints.values():
            if joint.parent not in self.bodies:
                raise ValueError(
                    f"Joint {joint.name!r} references unknown parent body {joint.parent!r}"
                )
            if joint.child not in self.bodies:
                raise ValueError(
                    f"Joint {joint.name!r} references unknown child body {joint.child!r}"
                )

    def _validate_no_cycles(self) -> None:
        """
        Detect directed cycles using DFS.
        """
        visited: Set[str] = set()
        stack: Set[str] = set()

        def visit(node: str) -> None:
            if node in stack:
                raise ValueError(f"Cycle detected in kinematic graph at {node!r}")
            if node in visited:
                return

            stack.add(node)
            for child in self._children_of(node):
                visit(child)
            stack.remove(node)
            visited.add(node)

        for root in self.roots():
            visit(root)

    def _children_of(self, body_name: str) -> List[str]:
        return [j.child for j in self.joints.values() if j.parent == body_name]
