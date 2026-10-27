#!/usr/bin/env python3
"""Apply checked, minimal edits to the pinned experimental ESB radio stack.

Each transformation uses a whitespace-tolerant expression and requires exactly
one match. If the checkout changes unexpectedly, abort rather than silently
applying a partial or potentially incorrect fix.
"""
from pathlib import Path
import re
import sys


def replace_regex_once(path: Path, pattern: str, replacement, label: str) -> None:
    source = path.read_text(encoding="utf-8")
    regex = re.compile(pattern, re.MULTILINE)
    matches = list(regex.finditer(source))
    if len(matches) != 1:
        details = ""
        if path.name == "esb.c":
            candidates = [
                line.strip() for line in source.splitlines()
                if "ctx.pipes" in line or "ESB_PIPE_COUNT" in line
            ]
            details = f" Candidate lines: {candidates[:8]!r}"
        raise SystemExit(
            f"{path}: expected exactly one {label} source fragment; "
            f"found {len(matches)}.{details} "
            "Check the pinned SDK/module revision before changing this script."
        )
    updated = regex.sub(replacement, source, count=1)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(updated)
    print(f"Applied: {label}")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(
            "Usage: apply_esb_stack_fixes.py <sdk-nrf/subsys/esb/esb.c> "
            "<zmk-split-esb/src/split/esb/app_esb.c>"
        )

    sdk_path = Path(sys.argv[1])
    module_path = Path(sys.argv[2])

    replace_regex_once(
        sdk_path,
        r"^([ \t]*)ctx\.pipes[ \t]*=[ \t]*ESB_PIPE_COUNT;[ \t]*$",
        lambda m: (
            f"{m.group(1)}/* Keep physical pipe 7 for uplink traffic; schedule only active halves. */\n"
            f"{m.group(1)}ctx.pipes = CONFIG_ZMK_SPLIT_BLE_CENTRAL_PERIPHERALS;"
        ),
        "two-peripheral TDMA slot scheduling",
    )
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
    )


if __name__ == "__main__":
    main()
