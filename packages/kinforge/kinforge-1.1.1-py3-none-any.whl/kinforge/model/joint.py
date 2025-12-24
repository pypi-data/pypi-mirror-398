from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional, Tuple

Vec3 = Tuple[float, float, float]
JointType = Literal["fixed", "revolute", "prismatic"]


@dataclass(frozen=True)
class Pose:
    """
    Minimal pose representation for v0.
    """

    xyz: Optional[Vec3] = None
    rpy: Optional[Vec3] = None


@dataclass(frozen=True)
class JointLimits:
    lower: Optional[float] = None
    upper: Optional[float] = None


@dataclass(frozen=True)
class Joint:
    """
    Canonical internal joint representation.

    Parent/child refer to Body names in the compiled/flattened model.
    """

    name: str
    type: JointType
    parent: str
    child: str

    origin: Optional[Pose] = None
    axis: Optional[Vec3] = None
    limits: Optional[JointLimits] = None

    def validate(self) -> None:
        if self.parent == self.child:
            raise ValueError(f"Joint {self.name!r} parent and child cannot be the same")

        if self.type in ("revolute", "prismatic") and self.axis is None:
            raise ValueError(f"Joint {self.name!r} of type {self.type!r} requires axis")

        if self.limits is not None:
            lo = self.limits.lower
            hi = self.limits.upper
            if lo is not None and hi is not None and lo > hi:
                raise ValueError(
                    f"Joint {self.name!r} limits invalid: lower {lo!r} > upper {hi!r}"
                )
