"""SDF export functionality for Kinforge models."""

import logging
from pathlib import Path
from typing import Optional, cast
from xml.etree.ElementTree import Element, ElementTree, SubElement  # nosec B405

from kinforge.compiler.compiled import CompiledInstance, CompiledModel
from kinforge.errors import ExportError
from kinforge.model.body import Body, Geometry
from kinforge.model.frame import Frame
from kinforge.model.joint import Joint
from kinforge.utils.names import is_base_link, ns_join, validate_sdf_name
from kinforge.utils.ordering import sorted_items, stable_sort
from kinforge.utils.transforms import rpy_str, xyz_str

logger = logging.getLogger(__name__)

# Constants for configurable defaults
DEFAULT_FRAME_MASS = 0.001
DEFAULT_WORLD_NAME = "generated"

# ============================================================
# Public API
# ============================================================


def export_sdf(
    model: CompiledModel,
    out_path: str,
    world_name: Optional[str] = None,
) -> None:
    """
    Export a compiled model to SDF format.

    Args:
        model: The compiled model to export
        out_path: Path where the SDF file will be written
        world_name: Name for the world element (only used for multi-instance models).
                   Defaults to "generated".

    Raises:
        ExportError: If the model is invalid or export fails
    """
    # Validate output path
    out_path_obj = Path(out_path)
    if out_path_obj.exists() and not out_path_obj.is_file():
        raise ExportError(f"Output path exists but is not a file: {out_path}")

    # Ensure parent directory exists
    out_path_obj.parent.mkdir(parents=True, exist_ok=True)

    # Validate model
    _validate_model(model)

    instances = list(model.instances.values())
    if not instances:
        raise ExportError("CompiledModel has no instances to export")

    sdf = Element("sdf", version="1.8")

    if len(instances) == 1:
        _export_instance_model(sdf, model, instances[0])
    else:
        # Use provided world name or default
        final_world_name = world_name if world_name is not None else DEFAULT_WORLD_NAME
        validate_sdf_name(final_world_name, "world name")
        world = SubElement(sdf, "world", name=final_world_name)

        # Sort instances by name for deterministic output
        sorted_instances = stable_sort(
            instances, key=lambda i: cast(CompiledInstance, i).name
        )
        for inst in sorted_instances:
            _export_instance_model(world, model, cast(CompiledInstance, inst))

    # Write with error handling
    try:
        ElementTree(sdf).write(out_path, encoding="utf-8", xml_declaration=True)
    except OSError as e:
        raise ExportError(f"Failed to write SDF to {out_path}: {e}") from e


# ============================================================
# Validation
# ============================================================


def _validate_model(model: CompiledModel) -> None:  # noqa: C901
    """Validate model before export."""
    if not model.bodies:
        raise ExportError("CompiledModel has no bodies")

    if not model.instances:
        raise ExportError("CompiledModel has no instances")

    # Validate instance names
    for inst_name, inst in model.instances.items():
        validate_sdf_name(inst_name, "instance name")
        if inst.namespace is not None and inst.namespace != "":
            validate_sdf_name(inst.namespace, f"namespace for instance {inst_name!r}")

    # Validate body names
    for body_name, body in model.bodies.items():
        validate_sdf_name(body_name, "body name")
        # Validate body itself
        try:
            body.validate()
        except ValueError as e:
            raise ExportError(f"Invalid body {body_name!r}: {e}") from e

    # Validate joint names and structure
    for joint_name, joint in model.joints.items():
        validate_sdf_name(joint_name, "joint name")
        try:
            joint.validate()
        except ValueError as e:
            raise ExportError(f"Invalid joint {joint_name!r}: {e}") from e

    # Validate frame names
    for frame_name, _frame in model.frames.items():
        validate_sdf_name(frame_name, "frame name")


# ============================================================
# Instance → <model>
# ============================================================


def _export_instance_model(
    parent: Element,
    model: CompiledModel,
    inst: CompiledInstance,
) -> None:
    sdf_model = SubElement(parent, "model", name=inst.name)
    SubElement(sdf_model, "static").text = "false"

    if inst.pose:
        SubElement(sdf_model, "pose").text = (
            f"{xyz_str(inst.pose.xyz)} {rpy_str(inst.pose.rpy)}"
        )
    else:
        SubElement(sdf_model, "pose").text = "0 0 0 0 0 0"

    # ----------------
    # Links (bodies)
    # ----------------
    for body_name, body in sorted_items(dict(model.bodies)):
        link_name = ns_join(inst.namespace, body_name)
        _emit_link(sdf_model, link_name, cast(Body, body))

    # ----------------
    # Frames (as fixed links)
    # ----------------
    _emit_frames_as_links(sdf_model, model, inst)

    # ----------------
    # Joints
    # ----------------
    for joint_name, joint in sorted_items(dict(model.joints)):
        _emit_joint(
            sdf_model,
            ns_join(inst.namespace, joint_name),
            cast(Joint, joint),
            inst,
        )


# ============================================================
# Links / Joints
# ============================================================


def _emit_link(sdf_model: Element, name: str, body: Body) -> None:
    """Emit a link element for a body."""
    link = SubElement(sdf_model, "link", name=name)
    _emit_inertial(link, body)

    # Check if this is a base link (affects geometry positioning)
    is_base = is_base_link(name)

    if body.visual:
        visual = SubElement(link, "visual", name="visual")
        _emit_geometry_block(visual, body.visual, body_name=name, is_base=is_base)

    if body.collision:
        collision = SubElement(link, "collision", name="collision")
        _emit_geometry_block(collision, body.collision, body_name=name, is_base=is_base)


def _emit_joint(
    sdf_model: Element,
    name: str,
    joint: Joint,
    inst: CompiledInstance,
) -> None:
    """Emit a joint element."""
    j = SubElement(sdf_model, "joint", name=name, type=joint.type)

    SubElement(j, "parent").text = ns_join(inst.namespace, joint.parent)
    SubElement(j, "child").text = ns_join(inst.namespace, joint.child)

    if joint.origin:
        SubElement(j, "pose").text = (
            f"{xyz_str(joint.origin.xyz)} {rpy_str(joint.origin.rpy)}"
        )

    if joint.axis:
        axis = SubElement(j, "axis")
        SubElement(axis, "xyz").text = xyz_str(joint.axis)

        if joint.limits:
            # Only export limits if at least one bound is set
            if joint.limits.lower is not None or joint.limits.upper is not None:
                lim = SubElement(axis, "limit")
                if joint.limits.lower is not None:
                    SubElement(lim, "lower").text = str(joint.limits.lower)
                if joint.limits.upper is not None:
                    SubElement(lim, "upper").text = str(joint.limits.upper)


# ============================================================
# Frames as fixed links
# ============================================================


def _emit_frames_as_links(
    sdf_model: Element,
    model: CompiledModel,
    inst: CompiledInstance,
) -> None:
    """Emit frames as zero-mass links with fixed joints."""
    for frame_name, frame in sorted_items(dict(model.frames)):
        fname = ns_join(inst.namespace, frame_name)

        # Create a zero-mass link for the frame
        link = SubElement(sdf_model, "link", name=fname)
        inertial = SubElement(link, "inertial")
        SubElement(inertial, "mass").text = str(DEFAULT_FRAME_MASS)

        # Create a fixed joint to attach the frame
        # Use unique separator to avoid collision with user names
        j = SubElement(
            sdf_model,
            "joint",
            name=f"{fname}::frame_fixed",
            type="fixed",
        )
        SubElement(j, "parent").text = ns_join(
            inst.namespace, cast(Frame, frame).attached_to
        )
        SubElement(j, "child").text = fname

        frame = cast(Frame, frame)
        if frame.pose is not None:
            SubElement(j, "pose").text = (
                f"{xyz_str(frame.pose.xyz)} {rpy_str(frame.pose.rpy)}"
            )


# ============================================================
# Inertial
# ============================================================


def _emit_inertial(link: Element, body: Body) -> None:
    """Emit inertial properties for a link."""
    inertial = SubElement(link, "inertial")

    if body.mass is not None:
        mass = body.mass
    else:
        # Default mass - log a warning
        mass = 1.0
        logger.warning(
            f"Body {body.name!r} has no mass specified, defaulting to {mass} kg"
        )

    SubElement(inertial, "mass").text = str(mass)


# ============================================================
# Geometry
# ============================================================


def _emit_geometry_block(
    parent: Element,
    geom: Geometry,
    *,
    body_name: str,
    is_base: bool,
) -> None:
    """Emit geometry block with pose and geometry element."""
    # Validate geometry before exporting
    try:
        geom.validate()
    except ValueError as e:
        raise ExportError(f"Invalid geometry for body {body_name!r}: {e}") from e

    pose = _geometry_pose(geom, is_base=is_base)
    if pose:
        SubElement(parent, "pose").text = pose

    geometry = SubElement(parent, "geometry")
    _emit_geometry(geometry, geom, body_name=body_name)


def _geometry_pose(geom: Geometry, *, is_base: bool) -> Optional[str]:
    """
    Calculate geometry pose offset for SDF export.

    Some geometries need centering adjustments based on type and position.
    """
    if geom.type == "cylinder":
        # Cylinders need to be shifted by half their length
        if geom.length is not None:
            return f"0 0 {geom.length / 2} 0 0 0"
        return None

    if geom.type == "box" and is_base:
        # Base boxes need to be shifted by half their height
        if geom.size is not None:
            return f"0 0 {geom.size[2] / 2} 0 0 0"
        return None

    return None


def _emit_geometry(geometry_el: Element, geom: Geometry, *, body_name: str) -> None:
    """Emit the actual geometry element based on type."""
    if geom.type == "box":
        if geom.size is None:
            raise ExportError(f"Box geometry for body {body_name!r} missing size")
        box = SubElement(geometry_el, "box")
        SubElement(box, "size").text = xyz_str(geom.size)

    elif geom.type == "cylinder":
        if geom.radius is None or geom.length is None:
            raise ExportError(
                f"Cylinder geometry for body {body_name!r} missing radius or length"
            )
        cyl = SubElement(geometry_el, "cylinder")
        SubElement(cyl, "radius").text = str(geom.radius)
        SubElement(cyl, "length").text = str(geom.length)

    elif geom.type == "sphere":
        if geom.radius is None:
            raise ExportError(f"Sphere geometry for body {body_name!r} missing radius")
        sph = SubElement(geometry_el, "sphere")
        SubElement(sph, "radius").text = str(geom.radius)

    elif geom.type == "mesh":
        if not geom.uri:
            raise ExportError(f"Mesh geometry for body {body_name!r} missing URI")
        mesh = SubElement(geometry_el, "mesh")
        SubElement(mesh, "uri").text = geom.uri
        if geom.scale:
            SubElement(mesh, "scale").text = xyz_str(geom.scale)

    else:
        raise ExportError(
            f"Unsupported geometry type {geom.type!r} for body {body_name!r}"
        )
