#!/usr/bin/env python3
"""Compare a Vial keymap's vial.json customKeycodes with the firmware enum.

Vial maps customKeycodes[i] to (QK_KB_0 | USER00 | USER_START) + i, purely by
position. A missing or extra JSON entry still builds but mislabels every
following key in the Vial GUI.

Usage:
    python3 audit_custom_keycodes.py <vial.json> <header-with-enum> [-D NAME ...]

-D NAME marks a preprocessor symbol as defined (for example -D KC_BLUETOOTH_ENABLE)
so simple #ifdef/#if defined()/#else blocks inside the enum are resolved.
Unresolvable #if expressions are reported and treated as false.
"""
import argparse
import json
import re
import sys

BASES = ("QK_KB_0", "USER00", "USER_START", "SAFE_RANGE")


def find_enum_body(text):
    for m in re.finditer(r"enum\s*\w*\s*\{", text):
        end = text.find("};", m.end())
        body = text[m.end():end]
        if any(re.search(r"=\s*" + b + r"\b", body) for b in BASES):
            return body
    return None


def eval_cond(expr, defined, warnings):
    expr = expr.strip()
    terms = re.findall(r"(!?)\s*defined\s*\(\s*(\w+)\s*\)", expr)
    if terms and re.fullmatch(r"[\s!()&|\w]*", expr):
        py = re.sub(r"(!?)\s*defined\s*\(\s*(\w+)\s*\)",
                    lambda m: ("not " if m.group(1) else "") + str(m.group(2) in defined), expr)
        py = py.replace("&&", " and ").replace("||", " or ")
        # eval is safe here: only boolean literals, and/or/not and parentheses may remain
        if set(re.findall(r"\w+", py)) <= {"True", "False", "and", "or", "not"}:
            try:
                return bool(eval(py, {"__builtins__": {}}, {}))
            except SyntaxError:
                pass
    warnings.append("unresolved #if " + expr + " (treated as false)")
    return False


def enum_members(body, defined):
    """Return enum members in declaration order, tracking explicit '= X' values."""
    stack, members, warnings = [], [], []
    for raw in body.splitlines():
        line = raw.split("//")[0].strip()
        if not line:
            continue
        if line.startswith("#"):
            d = line[1:].strip()
            if d.startswith("ifdef"):
                stack.append(d.split()[1] in defined)
            elif d.startswith("ifndef"):
                stack.append(d.split()[1] not in defined)
            elif d.startswith("if"):
                stack.append(eval_cond(d[2:], defined, warnings))
            elif d.startswith("else"):
                stack[-1] = not stack[-1]
            elif d.startswith("endif"):
                stack.pop()
            continue
        if not all(stack):
            continue
        for part in line.split(","):
            part = part.strip()
            if part:
                name, _, value = (p.strip() for p in part.partition("="))
                members.append((name, value))
    return members, warnings


def resolve_positions(members):
    """Map member -> offset from the base, following '= OTHER + 1' aliases."""
    pos, nxt, out = {}, 0, []
    for name, value in members:
        if value:
            if value in BASES:
                nxt = 0
            elif value in pos:
                nxt = pos[value]
            elif re.fullmatch(r"(\w+)\s*\+\s*(\d+)", value):
                ref, add = re.fullmatch(r"(\w+)\s*\+\s*(\d+)", value).groups()
                nxt = pos.get(ref, -999) + int(add)
            else:  # e.g. KC_NO: not a slot
                pos[name] = None
                continue
        pos[name] = nxt
        if not name.startswith("__") and name != "NEW_SAFE_RANGE":
            out.append((nxt, name))
        nxt += 1
    return sorted(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vial_json")
    ap.add_argument("header")
    ap.add_argument("-D", action="append", default=[], dest="defines")
    args = ap.parse_args()

    labels = [c.get("shortName") or c.get("name") for c in
              json.load(open(args.vial_json)).get("customKeycodes", [])]
    body = find_enum_body(open(args.header).read())
    if body is None:
        sys.exit("no enum starting at " + "/".join(BASES) + " found in " + args.header)
    members, warnings = enum_members(body, set(args.defines))
    slots = resolve_positions(members)

    width = max(len(slots), len(labels))
    by_pos = {p: n for p, n in slots}
    print(f"{'idx':>3}  {'firmware enum':<28} vial.json shortName")
    for i in range(width):
        print(f"{i:>3}  {by_pos.get(i, '-'):<28} {labels[i] if i < len(labels) else '-'}")
    for w in warnings:
        print("warning:", w)
    print(f"\nenum slots: {len(slots)}  vial.json entries: {len(labels)}")
    if len(slots) != len(labels):
        print("MISMATCH: counts differ, labels after the first gap are shifted")
        sys.exit(1)
    print("counts match; check the names line up")


if __name__ == "__main__":
    main()
