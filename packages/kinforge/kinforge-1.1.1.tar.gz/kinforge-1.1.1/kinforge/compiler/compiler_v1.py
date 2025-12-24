from __future__ import annotations

from dataclasses import replace
from typing import Dict

from kinforge.compiler.compiled import CompiledInstance, CompiledModel
from kinforge.compiler.compiler_v0 import compile_v0
from kinforge.parser.models_v1 import DocumentV1


def compile_v1(doc: DocumentV1) -> CompiledModel:
    # Compile using v0 logic by converting doc shape:
    # (The ModelDef/Assembly/Joint/Body are identical. Only Instance differs.)
    v0_like = doc.model_dump()
    v0_like["version"] = "0.1"
    # strip initial_joints for v0 parser compatibility
    for inst in v0_like.get("instances", []):
        inst.pop("initial_joints", None)

    from kinforge.parser.models_v0 import DocumentV0

    compiled = compile_v0(DocumentV0.model_validate(v0_like))

    # Re-attach initial_joints per instance
    inst_map: Dict[str, CompiledInstance] = dict(compiled.instances)
    for inst in doc.instances:
        if inst.name in inst_map:
            inst_map[inst.name] = replace(
                inst_map[inst.name],
                initial_joints=dict(inst.initial_joints),
            )

    return CompiledModel(
        bodies=compiled.bodies,
        joints=compiled.joints,
        frames=compiled.frames,
        instances=inst_map,
    )
