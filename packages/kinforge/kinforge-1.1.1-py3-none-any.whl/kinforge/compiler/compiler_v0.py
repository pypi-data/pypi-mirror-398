from __future__ import annotations

from dataclasses import replace
from typing import Dict, List, Optional, Tuple, cast

from kinforge.compiler.compiled import CompiledInstance, CompiledModel
from kinforge.model.assembly import Assembly
from kinforge.model.body import Body, Geometry
from kinforge.model.frame import Frame
from kinforge.model.frame import Pose as FramePose
from kinforge.model.instance import Instance
from kinforge.model.instance import Pose as InstancePose
from kinforge.model.joint import Joint, JointLimits
from kinforge.model.joint import Pose as JointPose
from kinforge.parser.models_v0 import DocumentV0
from kinforge.parser.models_v0 import JointLimits as InputJointLimits


def _ns_name(namespace: str, name: str) -> str:
    # v0: simple prefix. Later we can allow custom naming policies.
    return f"{namespace}/{name}" if namespace else name


def _build_body_templates(bodies) -> Dict[str, Body]:
    body_templates: Dict[str, Body] = {}
    for b in bodies:
        body_templates[b.name] = Body(
            name=b.name,
            mass=b.mass,
            visual=_geom_from_input(b.visual) if b.visual else None,
            collision=_geom_from_input(b.collision) if b.collision else None,
        )
    return body_templates


def _build_joint_templates(joints) -> Dict[str, Joint]:
    joint_templates: Dict[str, Joint] = {}
    for j in joints:
        joint_templates[j.name] = Joint(
            name=j.name,
            type=j.type,
            parent=j.parent,
            child=j.child,
            origin=_joint_pose_from_input(j.origin) if j.origin else None,
            axis=cast(Tuple[float, float, float], tuple(j.axis)) if j.axis else None,
            limits=_limits_from_input(j.limits) if j.limits else None,
        )
    return joint_templates


def _build_frame_templates(frames) -> Dict[str, Frame]:
    frame_templates: Dict[str, Frame] = {}
    for f in frames:
        frame_templates[f.name] = Frame(
            name=f.name,
            attached_to=f.attached_to,
            pose=_frame_pose_from_input(f.pose) if f.pose else None,
        )
    return frame_templates


def _build_assemblies(assemblies_in) -> Dict[str, Assembly]:
    assemblies: Dict[str, Assembly] = {}
    for a in assemblies_in:
        assemblies[a.name] = Assembly(
            name=a.name,
            root=a.root,
            bodies=list(a.bodies),
            joints=list(a.joints),
        )
        assemblies[a.name].validate()
    return assemblies


def _build_instances(instances_in) -> Dict[str, Instance]:
    instances: Dict[str, Instance] = {}
    for inst in instances_in:
        instances[inst.name] = Instance(
            name=inst.name,
            assembly=inst.assembly,
            namespace=inst.namespace,
            pose=_instance_pose_from_input(inst.pose) if inst.pose else None,
        )
    return instances


def _instantiate_bodies(
    asm_bodies: List[str],
    body_templates: Dict[str, Body],
    namespace: str,
    out_bodies: Dict[str, Body],
    asm_name: str,
) -> None:
    for body_name in asm_bodies:
        if body_name not in body_templates:
            raise ValueError(
                f"Assembly {asm_name!r} references unknown body {body_name!r}"
            )
        template_body = body_templates[body_name]
        new_name = _ns_name(namespace, body_name)
        if new_name in out_bodies:
            raise ValueError(f"Duplicate instantiated body name {new_name!r}")
        out_bodies[new_name] = replace(template_body, name=new_name)


def _instantiate_joints(
    asm_joints: List[str],
    joint_templates: Dict[str, Joint],
    namespace: str,
    out_joints: Dict[str, Joint],
    asm_name: str,
) -> None:
    for joint_name in asm_joints:
        if joint_name not in joint_templates:
            raise ValueError(
                f"Assembly {asm_name!r} references unknown joint {joint_name!r}"
            )
        template_joint = joint_templates[joint_name]
        new_joint_name = _ns_name(namespace, joint_name)
        if new_joint_name in out_joints:
            raise ValueError(f"Duplicate instantiated joint name {new_joint_name!r}")

        parent = _ns_name(namespace, template_joint.parent)
        child = _ns_name(namespace, template_joint.child)

        out_joints[new_joint_name] = replace(
            template_joint,
            name=new_joint_name,
            parent=parent,
            child=child,
        )


def _instantiate_frames(
    asm_bodies: List[str],
    frame_templates: Dict[str, Frame],
    namespace: str,
    out_frames: Dict[str, Frame],
) -> None:
    asm_body_set = set(asm_bodies)
    for frame_name, template_frame in frame_templates.items():
        if template_frame.attached_to not in asm_body_set:
            continue
        new_frame_name = _ns_name(namespace, frame_name)
        if new_frame_name in out_frames:
            raise ValueError(f"Duplicate instantiated frame name {new_frame_name!r}")

        attached_to = _ns_name(namespace, template_frame.attached_to)
        out_frames[new_frame_name] = replace(
            template_frame,
            name=new_frame_name,
            attached_to=attached_to,
        )


def _instantiate_assembly(
    inst: Instance,
    asm: Assembly,
    body_templates: Dict[str, Body],
    joint_templates: Dict[str, Joint],
    frame_templates: Dict[str, Frame],
    out_bodies: Dict[str, Body],
    out_joints: Dict[str, Joint],
    out_frames: Dict[str, Frame],
) -> CompiledInstance:
    namespace = inst.namespace or inst.name
    root_body_namespaced = _ns_name(namespace, asm.root)

    _instantiate_bodies(asm.bodies, body_templates, namespace, out_bodies, asm.name)
    _instantiate_joints(asm.joints, joint_templates, namespace, out_joints, asm.name)
    _instantiate_frames(asm.bodies, frame_templates, namespace, out_frames)

    return CompiledInstance(
        name=inst.name,
        namespace=namespace,
        root_body=root_body_namespaced,
        pose=inst.pose,
    )


def compile_v0(doc: DocumentV0) -> CompiledModel:
    """
    Compile a v0 input document into a flattened canonical model.
    """
    body_templates = _build_body_templates(doc.model.bodies)
    joint_templates = _build_joint_templates(doc.model.joints)
    frame_templates = _build_frame_templates(doc.model.frames)
    assemblies = _build_assemblies(doc.assemblies)
    instances_in = _build_instances(doc.instances)

    if not instances_in:
        return _compile_implicit(body_templates, joint_templates, frame_templates)

    out_bodies: Dict[str, Body] = {}
    out_joints: Dict[str, Joint] = {}
    out_frames: Dict[str, Frame] = {}
    out_instances: Dict[str, CompiledInstance] = {}

    for inst in instances_in.values():
        if inst.assembly not in assemblies:
            raise ValueError(
                f"Instance {inst.name!r} references unknown assembly {inst.assembly!r}"
            )
        asm = assemblies[inst.assembly]
        out_instances[inst.name] = _instantiate_assembly(
            inst,
            asm,
            body_templates,
            joint_templates,
            frame_templates,
            out_bodies,
            out_joints,
            out_frames,
        )

    return CompiledModel(
        bodies=out_bodies,
        joints=out_joints,
        frames=out_frames,
        instances=out_instances,
    )


def _compile_implicit(
    bodies: Dict[str, Body],
    joints: Dict[str, Joint],
    frames: Dict[str, Frame],
) -> CompiledModel:
    # No namespace prefix, just flatten as-is.
    out_bodies = dict(bodies)
    out_joints = dict(joints)
    out_frames = dict(frames)

    # Single implicit instance metadata
    # root not known here without graph; exporter can call graph().roots()
    return CompiledModel(
        bodies=out_bodies,
        joints=out_joints,
        frames=out_frames,
        instances={},
    )


# --------------------------
# Conversions from input types
# --------------------------


def _geom_from_input(g) -> Geometry:
    # input Geometry is pydantic model with list vectors
    return Geometry(
        type=g.type,
        size=tuple(g.size) if g.size else None,
        radius=g.radius,
        length=g.length,
        uri=g.uri,
        scale=tuple(g.scale) if getattr(g, "scale", None) else None,
    )


def _joint_pose_from_input(p) -> JointPose:
    return JointPose(
        xyz=tuple(p.xyz) if p.xyz else None,
        rpy=tuple(p.rpy) if p.rpy else None,
    )


def _frame_pose_from_input(p) -> FramePose:
    return FramePose(
        xyz=tuple(p.xyz) if p.xyz else None,
        rpy=tuple(p.rpy) if p.rpy else None,
    )


def _instance_pose_from_input(p) -> InstancePose:
    return InstancePose(
        xyz=tuple(p.xyz) if p.xyz else None,
        rpy=tuple(p.rpy) if p.rpy else None,
    )


def _limits_from_input(limits: Optional[InputJointLimits]) -> Optional[JointLimits]:
    if limits is None:
        return None
    return JointLimits(lower=limits.lower, upper=limits.upper)
