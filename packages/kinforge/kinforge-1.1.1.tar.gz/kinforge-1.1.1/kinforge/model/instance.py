from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

Vec3 = Tuple[float, float, float]


@dataclass(frozen=True)
class Pose:
    xyz: Optional[Vec3] = None
    rpy: Optional[Vec3] = None


@dataclass(frozen=True)
class Instance:
    """
    Instantiated assembly with optional namespace and pose.
    """

    name: str
    assembly: str
    namespace: Optional[str] = None
    pose: Optional[Pose] = None
