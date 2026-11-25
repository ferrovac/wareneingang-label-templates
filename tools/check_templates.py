#!/usr/bin/env python3
"""Check every label template in this repository (run by CI on each push).

    pip install jinja2 && python tools/check_templates.py

Per *.svg: valid XML, <svg width/height> in mm, a <metadata id="label"> element whose
data-roll matches one side, well-formed data-inputs, valid Jinja, only known
placeholders, and still a valid SVG after filling in example values.
"""

import pathlib
import re
import sys
import xml.etree.ElementTree as ET

from jinja2 import Environment, StrictUndefined, meta
from jinja2.exceptions import TemplateError

# Keep in sync with the app (wareneingang/labels/context.py, VARIABLES) and README.md.
KNOWN = {"part_no", "part_code", "title", "group", "po", "pos", "aid", "aids", "uhv", "rev",
         "material", "supplier", "foreign_code", "quantity", "date", "user"}
EXAMPLE = {k: "X & <Y>" for k in KNOWN} | {"uhv": False, "quantity": 1}
ROOT = pathlib.Path(__file__).resolve().parents[1]


def mm(value):
    m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*mm\s*", value or "")
    return float(m.group(1)) if m else None


def check(path: pathlib.Path) -> list[str]:
    errors = []
    source = path.read_text(encoding="utf-8")
    try:
        root = ET.fromstring(source)
    except ET.ParseError as e:
        return [f"no valid XML: {e}"]
    if not root.tag.endswith("svg"):
        return ["root element is not <svg>"]
    w, h = mm(root.get("width")), mm(root.get("height"))
    if w is None or h is None:
        errors.append("width/height must be given in mm, e.g. width=\"80mm\"")
    md = next((el for el in root.iter() if el.tag.endswith("metadata") and el.get("id") == "label"), None)
    inputs = set()
    if md is None:
        errors.append('missing <metadata id="label" data-name=… data-roll=…/>')
    else:
        if not md.get("data-name"):
            errors.append("data-name is empty")
        try:
            roll = float(md.get("data-roll", ""))
            if w is not None and h is not None and roll not in (w, h):
                errors.append(f"data-roll {roll:g} mm matches neither width {w:g} nor height {h:g}")
        except ValueError:
            errors.append("data-roll missing or not a number (roll width in mm)")
        for part in filter(None, (md.get("data-inputs") or "").split(";")):
            var = part.split(":", 1)[0].strip()
            if ":" not in part or not re.fullmatch(r"[a-z_][a-z0-9_]*", var):
                errors.append(f"data-inputs entry {part!r} must be variable:Label")
            elif var in KNOWN:
                errors.append(f"data-inputs variable {var!r} shadows a built-in placeholder")
            else:
                inputs.add(var)
    env = Environment(autoescape=True, undefined=StrictUndefined)
    try:
        used = meta.find_undeclared_variables(env.parse(source))
    except TemplateError as e:
        return errors + [f"Jinja syntax error: {e}"]
    unknown = sorted(used - KNOWN - inputs)
    if unknown:
        errors.append(f"unknown placeholder(s): {', '.join(unknown)}")
    else:
        filled = env.from_string(source).render(**EXAMPLE, **{k: "" for k in inputs})
        try:
            ET.fromstring(filled)
        except ET.ParseError as e:
            errors.append(f"not valid SVG after filling in values: {e}")
    return errors


def main() -> int:
    files = sorted(ROOT.glob("*.svg"))
    if not files:
        print("no templates found")
        return 1
    failed = 0
    for f in files:
        errors = check(f)
        print(f"{'OK  ' if not errors else 'FAIL'} {f.name}")
        for e in errors:
            print(f"     - {e}")
        failed += bool(errors)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
