from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Vec3 = List[float]


class Pose(BaseModel):
    model_config = ConfigDict(extra="forbid")

    xyz: Optional[Vec3] = None
    rpy: Optional[Vec3] = None

    @field_validator("xyz", "rpy")
    @classmethod
    def _vec3_len(cls, v: Optional[Vec3]) -> Optional[Vec3]:
        if v is None:
            return v
        if len(v) != 3:
            raise ValueError("must be a 3-element array")
        return v


GeometryType = Literal["box", "sphere", "cylinder", "mesh"]


class Geometry(BaseModel):
    """
    Semantic geometry. Not XML-shaped.
    """

    model_config = ConfigDict(extra="forbid")

    type: GeometryType
    # box
    size: Optional[Vec3] = None
    # sphere / cylinder
    radius: Optional[float] = None
    length: Optional[float] = None
    # mesh
    uri: Optional[str] = None
    scale: Optional[Vec3] = None  # mesh scale

    @field_validator("size", "scale")
    @classmethod
    def _vec3_len(cls, v: Optional[Vec3]) -> Optional[Vec3]:
        if v is None:
            return v
        if len(v) != 3:
            raise ValueError("must be a 3-element array")
        return v

    @model_validator(mode="after")
    def _validate_by_type(self) -> "Geometry":
        t = self.type
        if t == "box":
            if self.size is None:
                raise ValueError("box geometry requires 'size': [x,y,z]")
        elif t == "sphere":
            if self.radius is None:
                raise ValueError("sphere geometry requires 'radius'")
        elif t == "cylinder":
            if self.radius is None or self.length is None:
                raise ValueError("cylinder geometry requires 'radius' and 'length'")
        elif t == "mesh":
            if not self.uri:
                raise ValueError("mesh geometry requires 'uri'")
            # scale optional; default to [1,1,1] in exporter
        return self


class Body(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    mass: Optional[float] = Field(default=None, ge=0.0)

    visual: Optional[Geometry] = None
    collision: Optional[Geometry] = None

    # future fields (v1+): inertia, material, friction, etc.


JointType = Literal["fixed", "revolute", "prismatic"]


class JointLimits(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lower: Optional[float] = None
    upper: Optional[float] = None


class Joint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    type: JointType
    parent: str
    child: str

    axis: Optional[Vec3] = None
    origin: Optional[Pose] = None
    limits: Optional[JointLimits] = None

    @field_validator("axis")
    @classmethod
    def _axis_len(cls, v: Optional[Vec3]) -> Optional[Vec3]:
        if v is None:
            return v
        if len(v) != 3:
            raise ValueError("axis must be a 3-element array")
        return v

    @model_validator(mode="after")
    def _validate_joint(self) -> "Joint":
        # Axis required for revolute/prismatic (v0 rule)
        if self.type in ("revolute", "prismatic") and self.axis is None:
            raise ValueError(f"{self.type} joint requires 'axis'")
        # Limits optional for v0; could enforce for revolute/prismatic later
        return self


class Frame(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    attached_to: str
    pose: Optional[Pose] = None


class ModelDef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bodies: List[Body]
    joints: List[Joint] = Field(default_factory=list)
    frames: List[Frame] = Field(default_factory=list)


class Assembly(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    root: str
    bodies: List[str]
    joints: List[str] = Field(default_factory=list)


class Instance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    assembly: str
    namespace: Optional[str] = None
    pose: Optional[Pose] = None


class DocumentV0(BaseModel):
    """
    This is the top-level input format Kinforge v0 consumes.
    """

    model_config = ConfigDict(extra="forbid")

    version: Literal["0.1"]
    model: ModelDef
    assemblies: List[Assembly] = Field(default_factory=list)
    instances: List[Instance] = Field(default_factory=list)

    def _check_unique_names(self, names: List[str], error_msg: str) -> None:
        if len(names) != len(set(names)):
            raise ValueError(error_msg)

    def _validate_joint_references(
        self, joints: List[Joint], body_set: set[str]
    ) -> None:
        for j in joints:
            if j.parent not in body_set:
                raise ValueError(
                    f"joint {j.name!r} parent {j.parent!r} not found in bodies"
                )
            if j.child not in body_set:
                raise ValueError(
                    f"joint {j.name!r} child {j.child!r} not found in bodies"
                )
            if j.parent == j.child:
                raise ValueError(
                    f"joint {j.name!r} parent and child cannot be the same"
                )

    def _validate_frame_references(
        self, frames: List[Frame], body_set: set[str]
    ) -> None:
        for f in frames:
            if f.attached_to not in body_set:
                raise ValueError(
                    f"frame {f.name!r} attached_to {f.attached_to!r} not found in bodies"
                )

    def _validate_assembly_references(
        self, assemblies: List[Assembly], body_set: set[str], joints_set: set[str]
    ) -> None:
        for a in assemblies:
            if a.root not in set(a.bodies):
                raise ValueError(
                    f"assembly {a.name!r} root {a.root!r} must be included in its bodies list"
                )
            for bn in a.bodies:
                if bn not in body_set:
                    raise ValueError(
                        f"assembly {a.name!r} references unknown body {bn!r}"
                    )
            for jn in a.joints:
                if jn not in joints_set:
                    raise ValueError(
                        f"assembly {a.name!r} references unknown joint {jn!r}"
                    )

    def _validate_instance_references(
        self, instances: List[Instance], assembly_set: set[str]
    ) -> None:
        for inst in instances:
            if inst.assembly not in assembly_set:
                raise ValueError(
                    f"instance {inst.name!r} references unknown assembly {inst.assembly!r}"
                )

    @model_validator(mode="after")
    def _cross_reference_validation(self) -> "DocumentV0":
        body_names = [b.name for b in self.model.bodies]
        joint_names = [j.name for j in self.model.joints]
        frame_names = [f.name for f in self.model.frames]
        assembly_names = [a.name for a in self.assemblies]

        self._check_unique_names(body_names, "duplicate body names in model.bodies")
        self._check_unique_names(joint_names, "duplicate joint names in model.joints")
        self._check_unique_names(frame_names, "duplicate frame names in model.frames")
        self._check_unique_names(
            assembly_names, "duplicate assembly names in assemblies"
        )

        body_set = set(body_names)
        joints_set = set(joint_names)

        self._validate_joint_references(self.model.joints, body_set)
        self._validate_frame_references(self.model.frames, body_set)
        self._validate_assembly_references(self.assemblies, body_set, joints_set)
        self._validate_instance_references(self.instances, set(assembly_names))

        return self
