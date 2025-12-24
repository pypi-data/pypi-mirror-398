from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional, Tuple

Vec3 = Tuple[float, float, float]


GeometryType = Literal["box", "sphere", "cylinder", "mesh"]


@dataclass(frozen=True)
class Geometry:
    type: GeometryType

    # box
    size: Optional[Vec3] = None

    # sphere / cylinder
    radius: Optional[float] = None
    length: Optional[float] = None

    # mesh
    uri: Optional[str] = None
    scale: Optional[Vec3] = None

    def validate(self) -> None:
        t = self.type
        if t == "box":
            if self.size is None:
                raise ValueError("Geometry(box) requires size")
        elif t == "sphere":
            if self.radius is None:
                raise ValueError("Geometry(sphere) requires radius")
        elif t == "cylinder":
            if self.radius is None or self.length is None:
                raise ValueError("Geometry(cylinder) requires radius and length")
        elif t == "mesh":
            if not self.uri:
                raise ValueError("Geometry(mesh) requires uri")


@dataclass(frozen=True)
class Body:
    """
    Canonical internal rigid body representation.

    Notes:
    - This is NOT the input schema model.
    - Exporters consume this.
    - In v0 we keep geometry simple (one visual + one collision).
    """

    name: str
    mass: Optional[float] = None

    visual: Optional[Geometry] = None
    collision: Optional[Geometry] = None

    def validate(self) -> None:
        if self.mass is not None and self.mass < 0:
            raise ValueError(f"Body {self.name!r} mass must be >= 0.0, got {self.mass}")
        if self.visual is not None:
            self.visual.validate()
        if self.collision is not None:
            self.collision.validate()
