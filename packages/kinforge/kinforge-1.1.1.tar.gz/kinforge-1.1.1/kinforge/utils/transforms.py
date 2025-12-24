"""Transform utilities for converting vectors to string representations."""

from typing import Optional, Tuple

Vec3 = Tuple[float, float, float]


def xyz_str(xyz: Optional[Vec3]) -> str:
    if xyz is None:
        return "0 0 0"
    return " ".join(str(v) for v in xyz)


def rpy_str(rpy: Optional[Vec3]) -> str:
    if rpy is None:
        return "0 0 0"
    return " ".join(str(v) for v in rpy)
