from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

Vec3 = Tuple[float, float, float]


@dataclass(frozen=True)
class Pose:
    xyz: Optional[Vec3] = None
    rpy: Optional[Vec3] = None


@dataclass(frozen=True)
class Frame:
    """
    Canonical frame representation.

    Frames are attached to a body but do not affect kinematics.
    """

    name: str
    attached_to: str
    pose: Optional[Pose] = None
