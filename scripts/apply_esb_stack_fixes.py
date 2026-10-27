#!/usr/bin/env python3
"""Apply checked, minimal edits to the pinned experimental ESB radio stack.

Each transformation requires its exact upstream fragment to occur exactly
once. If the checkout changes unexpectedly, abort rather than silently applying
a partial or potentially incorrect fix.
"""
from pathlib import Path
import sys


def replace_once(path: Path, before: str, after: str, label: str) -> None:
    source = path.read_text(encoding="utf-8")
    count = source.count(before)
    if count != 1:
        raise SystemExit(
            f"{path}: expected exactly one {label} source fragment; found {count}. "
            "Check the pinned SDK/module revision before changing this script."
        )
    updated = source.replace(before, after, 1)
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

    replace_once(
        sdk_path,
        "\tctx.pipes = ESB_PIPE_COUNT;",
        "\t/* Keep physical pipe 7 for uplink traffic; schedule only active halves. */\n"
        "\tctx.pipes = CONFIG_ZMK_SPLIT_BLE_CENTRAL_PERIPHERALS;",
        "two-peripheral TDMA slot scheduling",
    )
    replace_once(
        module_path,
        "    esb_initialize();",
        "    ret = esb_initialize();\n"
        "    if (ret != 0) {\n"
        '        LOG_ERR("ESB initialization failed (ret %d)", ret);\n'
        "        return ret;\n"
        "    }",
        "ESB initialization error propagation",
    )
    replace_once(
        module_path,
        "    if (esb_tx_start(pipe, data_size + 2) == -ENOMEM) {\n"
        "        return -ENOMEM;\n"
        "    }",
        "    int ret = esb_tx_start(pipe, data_size + 2);\n"
        "    if (ret < 0) {\n"
        "        return ret;\n"
        "    }",
        "ESB transmit error propagation",
    )
    replace_once(
        module_path,
        "    esb_ctx->rx_handler(source, payload.data, payload.length);\n}",
        "    esb_ctx->rx_handler(source, payload.data, payload.length);\n"
        "    return 0;\n}",
        "defined return from direct-RX handler",
    )


if __name__ == "__main__":
    main()
