#!/usr/bin/env python3
"""Apply checked, minimal edits to the pinned experimental ESB radio stack.

The edits are idempotent because a CI cache can contain previously transformed
sources. Each edit either recognises the completed change or requires exactly
one original source fragment.
"""
from pathlib import Path
import re
import sys


def replace_regex_once(path: Path, pattern: str, replacement, label: str, already_pattern=None) -> None:
    source = path.read_text(encoding="utf-8")
    if already_pattern is not None:
        already = re.compile(already_pattern, re.MULTILINE)
        already_matches = list(already.finditer(source))
        if len(already_matches) == 1:
            print(f"Already applied: {label}")
            return
        if len(already_matches) > 1:
            raise SystemExit(f"{path}: found {len(already_matches)} copies of the completed {label} fix.")

    regex = re.compile(pattern, re.MULTILINE)
    matches = list(regex.finditer(source))
    if len(matches) != 1:
        raise SystemExit(
            f"{path}: expected exactly one {label} source fragment; found {len(matches)}. "
            "Check the pinned SDK/module revision before changing this script."
        )
    updated = regex.sub(replacement, source, count=1)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(updated)
    print(f"Applied: {label}")


def replace_scoped_central_pipe_count(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    prefix = r"static\s+void\s+central_setup\s*\(\s*void\s*\)\s*\{"
    fixed = re.compile(
        rf"(?s){prefix}.*?^[ \t]*ctx\.pipes\s*=\s*CONFIG_ZMK_SPLIT_BLE_CENTRAL_PERIPHERALS;",
        re.MULTILINE,
    )
    if len(list(fixed.finditer(source))) == 1:
        print("Already applied: two-peripheral TDMA slot scheduling")
        return

    pattern = re.compile(
        rf"(?s)({prefix}.*?)(^[ \t]*)ctx\.pipes\s*=\s*[^;]+;",
        re.MULTILINE,
    )
    matches = list(pattern.finditer(source))
    if len(matches) != 1:
        candidates = [
            line.strip() for line in source.splitlines()
            if "ctx.pipes" in line or "ESB_PIPE_COUNT" in line
        ]
        raise SystemExit(
            f"{path}: expected one ctx.pipes assignment inside central_setup(); "
            f"found {len(matches)}. Candidate lines: {candidates[:8]!r}"
        )

    match = matches[0]
    indent = match.group(2)
    replacement = (
        f"{match.group(1)}{indent}/* Keep physical pipe 7 for uplink traffic; schedule only active halves. */\n"
        f"{indent}ctx.pipes = CONFIG_ZMK_SPLIT_BLE_CENTRAL_PERIPHERALS;"
    )
    updated = source[:match.start()] + replacement + source[match.end():]
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(updated)
    print("Applied: two-peripheral TDMA slot scheduling")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(
            "Usage: apply_esb_stack_fixes.py <sdk-nrf/subsys/esb/esb.c> "
            "<zmk-split-esb/src/split/esb/app_esb.c>"
        )

    sdk_path = Path(sys.argv[1])
    module_path = Path(sys.argv[2])

    replace_scoped_central_pipe_count(sdk_path)
    replace_regex_once(
        module_path,
        r"^([ \t]*)esb_initialize\(\);[ \t]*$",
        lambda m: (
            f"{m.group(1)}ret = esb_initialize();\n"
            f"{m.group(1)}if (ret != 0) {{\n"
            f'{m.group(1)}    LOG_ERR("ESB initialization failed (ret %d)", ret);\n'
            f"{m.group(1)}    return ret;\n"
            f"{m.group(1)}}}"
        ),
        "ESB initialization error propagation",
        already_pattern=r"^[ \t]*ret\s*=\s*esb_initialize\(\);\n[ \t]*if\s*\(\s*ret\s*!=\s*0\s*\)\s*\{\n[ \t]*LOG_ERR\(\"ESB initialization failed \(ret %d\)\",\s*ret\);\n[ \t]*return\s+ret;\n[ \t]*\}",
    )
    replace_regex_once(
        module_path,
        r"^([ \t]*)if\s*\(\s*esb_tx_start\(pipe,\s*data_size\s*\+\s*2\)\s*==\s*-ENOMEM\s*\)\s*\{\n[ \t]*return\s+-ENOMEM;\n[ \t]*\}",
        lambda m: (
            f"{m.group(1)}int ret = esb_tx_start(pipe, data_size + 2);\n"
            f"{m.group(1)}if (ret < 0) {{\n"
            f"{m.group(1)}    return ret;\n"
            f"{m.group(1)}}}"
        ),
        "ESB transmit error propagation",
        already_pattern=r"^[ \t]*int\s+ret\s*=\s*esb_tx_start\(pipe,\s*data_size\s*\+\s*2\);\n[ \t]*if\s*\(\s*ret\s*<\s*0\s*\)\s*\{\n[ \t]*return\s+ret;\n[ \t]*\}",
    )
    replace_regex_once(
        module_path,
        r"^([ \t]*)esb_ctx->rx_handler\(source,\s*payload\.data,\s*payload\.length\);[ \t]*\n([ \t]*)\}",
        lambda m: (
            f"{m.group(1)}esb_ctx->rx_handler(source, payload.data, payload.length);\n"
            f"{m.group(1)}return 0;\n"
            f"{m.group(2)}}}"
        ),
        "defined return from direct-RX handler",
        already_pattern=r"^[ \t]*esb_ctx->rx_handler\(source,\s*payload\.data,\s*payload\.length\);[ \t]*\n[ \t]*return\s+0;[ \t]*\n[ \t]*\}",
    )


if __name__ == "__main__":
    main()
