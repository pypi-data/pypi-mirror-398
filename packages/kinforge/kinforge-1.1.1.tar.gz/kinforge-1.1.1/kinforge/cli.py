# PYTHON_ARGCOMPLETE_OK
import argparse
import json
import logging
import sys
from logging import getLogger
from pathlib import Path

try:
    import argcomplete
except ImportError:
    argcomplete = None

from kinforge.compiler.compiler_v0 import compile_v0
from kinforge.compiler.compiler_v1 import compile_v1
from kinforge.errors import KinforgeError
from kinforge.exporters.sdf import export_sdf
from kinforge.exporters.urdf import export_urdf
from kinforge.parser.loader import load_document

logger = getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="kinforge")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="Build model from JSON")
    b.add_argument("input", help="Input JSON file")
    b.add_argument("--out", required=True, help="Output file (.sdf or .urdf)")
    b.add_argument("--format", choices=["sdf", "urdf"], default=None)

    comp = sub.add_parser("completion", help="Show shell completion setup instructions")
    comp.add_argument(
        "--shell",
        choices=["bash", "zsh"],
        default=None,
        help="Shell type (auto-detected if not specified)",
    )

    if argcomplete:
        argcomplete.autocomplete(p)

    args = p.parse_args(argv)

    try:
        doc = load_document(args.input)

        if getattr(doc, "version", None) == "1.0":
            logger.info("Compiling v1 document")
            compiled = compile_v1(doc)  # type: ignore[arg-type]
        else:
            logger.info("Compiling v0 document")
            compiled = compile_v0(doc)  # type: ignore[arg-type]

        out = Path(args.out)
        fmt = args.format or out.suffix.lstrip(".").lower()
        if fmt == "sdf":
            export_sdf(compiled, str(out))
            logger.debug("sdf exported")
        elif fmt == "urdf":
            export_urdf(compiled, str(out), robot_name=out.stem)
            logger.debug("URDF exported")
        else:
            raise KinforgeError(f"Unknown output format {fmt!r}")

        # v1: emit initial joint state sidecar, if present
        if compiled.instances:
            for inst in compiled.instances.values():
                if inst.initial_joints:
                    sidecar = out.with_suffix(f".{inst.name}.joint_states.json")
                    sidecar.write_text(json.dumps(inst.initial_joints, indent=2))

        logger.info(f"✔ Wrote {out}")
        return 0

    except KinforgeError as e:
        logger.error(f"❌ {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
