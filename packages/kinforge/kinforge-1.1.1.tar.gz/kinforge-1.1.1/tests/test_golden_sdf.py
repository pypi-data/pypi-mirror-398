from pathlib import Path
from typing import cast

import defusedxml
from defusedxml.ElementTree import fromstring, tostring

defusedxml.defuse_stdlib()  # type: ignore[no-untyped-call] # nosec B404

from kinforge.compiler.compiler_v0 import compile_v0  # noqa: E402
from kinforge.compiler.compiler_v1 import compile_v1  # noqa: E402
from kinforge.exporters.sdf import export_sdf  # noqa: E402
from kinforge.parser.loader import load_document  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def _canon(xml_text: str) -> bytes:
    el = fromstring(xml_text.encode("utf-8"))
    return tostring(el)


def _run_and_compare(json_name: str, golden_name: str, tmp_path: Path):
    src = ROOT / "examples" / json_name
    golden = ROOT / "tests" / "golden" / golden_name
    out = tmp_path / golden_name

    doc = load_document(src)

    # Determine version and compile accordingly
    if getattr(doc, "version", None) == "1.0":
        compiled = compile_v1(doc)  # type: ignore[arg-type]
    else:
        compiled = compile_v0(doc)  # type: ignore[arg-type]

    export_sdf(compiled, str(out))

    got = _canon(out.read_text())
    expected = _canon(golden.read_text())
    assert got == expected  # nosec B101


def test_golden_simple_arm(tmp_path):
    _run_and_compare(
        "simple_arm.json",
        "simple_arm.sdf",
        tmp_path,
    )


def test_golden_kuka_like_arm(tmp_path):
    _run_and_compare(
        "industrial_arm.json",
        "industrial_arm.sdf",
        tmp_path,
    )


def test_golden_warehouse_world(tmp_path):
    """Test multi-model export with warehouse world example."""
    _run_and_compare(
        "warehouse_world.json",
        "warehouse_world.sdf",
        tmp_path,
    )
