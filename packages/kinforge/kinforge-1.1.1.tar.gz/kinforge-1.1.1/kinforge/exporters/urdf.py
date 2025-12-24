from typing import cast
from xml.etree.ElementTree import Element, ElementTree, SubElement  # nosec B405

from kinforge.compiler.compiled import CompiledModel
from kinforge.model.body import Body, Geometry
from kinforge.model.frame import Frame
from kinforge.model.joint import Joint
from kinforge.utils.ordering import sorted_items
from kinforge.utils.transforms import rpy_str, xyz_str


def _emit_link(robot: Element, name: str, body: Body) -> None:
    link = SubElement(robot, "link", name=name)

    if body.mass is not None:
        inertial = SubElement(link, "inertial")
        SubElement(inertial, "mass", value=str(body.mass))

    if body.visual:
        vis = SubElement(link, "visual")
        geom = SubElement(vis, "geometry")
        _emit_urdf_geometry(geom, body.visual)

    if body.collision:
        col = SubElement(link, "collision")
        geom = SubElement(col, "geometry")
        _emit_urdf_geometry(geom, body.collision)


def _emit_joint(robot: Element, name: str, joint: Joint) -> None:
    j = SubElement(robot, "joint", name=name, type=joint.type)
    SubElement(j, "parent", link=joint.parent)
    SubElement(j, "child", link=joint.child)

    if joint.origin:
        SubElement(
            j,
            "origin",
            xyz=xyz_str(joint.origin.xyz),
            rpy=rpy_str(joint.origin.rpy),
        )

    if joint.axis:
        SubElement(j, "axis", xyz=xyz_str(joint.axis))

    if joint.limits and joint.type in ("revolute", "prismatic"):
        attrs = {}
        if joint.limits.lower is not None:
            attrs["lower"] = str(joint.limits.lower)
        if joint.limits.upper is not None:
            attrs["upper"] = str(joint.limits.upper)
        attrs.setdefault("effort", "1.0")
        attrs.setdefault("velocity", "1.0")
        SubElement(j, "limit", **attrs)


def _emit_frame(robot: Element, fname: str, fr: Frame) -> None:
    SubElement(robot, "link", name=fname)
    j = SubElement(robot, "joint", name=f"{fname}__fixed", type="fixed")
    SubElement(j, "parent", link=fr.attached_to)
    SubElement(j, "child", link=fname)
    if fr.pose:
        SubElement(j, "origin", xyz=xyz_str(fr.pose.xyz), rpy=rpy_str(fr.pose.rpy))


def export_urdf(model: CompiledModel, out_path: str, robot_name: str = "robot") -> None:
    robot = Element("robot", name=robot_name)

    for name, body in sorted_items(dict(model.bodies)):
        _emit_link(robot, name, cast(Body, body))

    for name, joint in sorted_items(dict(model.joints)):
        _emit_joint(robot, name, cast(Joint, joint))

    for fname, fr in sorted_items(dict(model.frames)):
        _emit_frame(robot, fname, cast(Frame, fr))

    ElementTree(robot).write(out_path, encoding="utf-8", xml_declaration=True)


def _emit_urdf_geometry(parent: Element, geom: Geometry):
    if geom.type == "box":
        SubElement(parent, "box", size=xyz_str(geom.size))
    elif geom.type == "sphere":
        SubElement(parent, "sphere", radius=str(geom.radius))
    elif geom.type == "cylinder":
        SubElement(parent, "cylinder", radius=str(geom.radius), length=str(geom.length))
    elif geom.type == "mesh":
        if geom.uri is None:
            raise ValueError("Mesh geometry requires uri")
        attrs: dict[str, str] = {"filename": geom.uri}
        if geom.scale:
            attrs["scale"] = xyz_str(geom.scale)
        SubElement(parent, "mesh", attrib=attrs)
    else:
        raise ValueError(f"Unsupported geometry type: {geom.type}")
