from __future__ import annotations

from typing import Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from kinforge.parser.models_v0 import Assembly, ModelDef, Pose


class InstanceV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    assembly: str
    namespace: Optional[str] = None
    pose: Optional[Pose] = None

    # NEW in v1:
    initial_joints: Dict[str, float] = Field(default_factory=dict)


class DocumentV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal["1.0"]
    model: ModelDef
    assemblies: list[Assembly] = Field(default_factory=list)
    instances: list[InstanceV1] = Field(default_factory=list)

    @model_validator(mode="after")
    def _basic_checks(self) -> "DocumentV1":
        # Reuse v0 document validation logic by “pretending” we’re v0:
        # (Alternatively: copy v0 validation functions; keeping it small here.)
        # Ensure instance initial_joints refer to known joints names (template level).
        joint_names = {j.name for j in self.model.joints}
        for inst in self.instances:
            for jn in inst.initial_joints.keys():
                if jn not in joint_names:
                    raise ValueError(
                        f"instance {inst.name!r} initial_joints references unknown joint {jn!r}"
                    )
        return self
