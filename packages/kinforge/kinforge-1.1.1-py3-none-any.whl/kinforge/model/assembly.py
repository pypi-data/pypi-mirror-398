from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Assembly:
    """
    Logical grouping of bodies and joints.

    Assemblies are NOT physical entities.
    They are used only during compilation.
    """

    name: str
    root: str
    bodies: List[str]
    joints: List[str]

    def validate(self) -> None:
        if self.root not in self.bodies:
            raise ValueError(
                f"Assembly {self.name!r} root {self.root!r} must be listed in bodies"
            )
