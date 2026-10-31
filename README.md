# ZMK Keyboard for Cornix

ZMK board definitions and shields for the Cornix split ergonomic keyboard.

[Documentation: English / 简体中文](http://gh.bhee.online/zmk-keyboard-cornix/) ·
[简体中文 README](./README_zh.md) ·
[日本語 README (AI-generated)](./README_jp.md)

**Current board release:** [`v3.0.0`](https://github.com/hitsmaxft/zmk-keyboard-cornix/releases/tag/v3.0.0)

**ZMK baseline:** pinned commit `4dd95d7840eb3d5a3f59bb29fbf1ab054715ef85` (Zephyr 4.1 compatible)

![Cornix with dongle](images/cornix_with_dongle.png)

## What is included

- `cornix_left//zmk` — left half for a standard split build
- `cornix_right//zmk` — right peripheral half
- `cornix_ph_left//zmk` — left peripheral half for a dongle build
- `cornix_dongle_adapter` — USB dongle interface for the ESB central
- `cornix_dongle_eyelash` — optional display hardware overlay
- `cornix_indicator` — production-ready RGB battery and connection indicators

Cornix uses a compact 3×6 column-staggered layout with three thumb keys per
half. The hardware supports USB-C, Bluetooth-capable controllers, Kailh Choc V2
hot-swap sockets, and 10°, 18°, or 25° tenting. This branch's firmware uses ESB only.

## Zephyr 4.1 requirements

Always use qualified ZMK board names such as `nice_nano//zmk`. The unqualified
`nice_nano` target may select `CONFIG_SETTINGS_NONE=y`, disabling persistent
settings. Use `nice_nano//zmk` for the dongle and reset builds.

For every nice!nano dongle or reset build, verify the final `.config` contains:

```text
CONFIG_NVS=y
CONFIG_SETTINGS_NVS=y
```

It must not contain `CONFIG_SETTINGS_NONE=y`.

## Build targets

This branch intentionally builds **ESB-only firmware**. The GitHub Actions workflow builds the three targets in `build-esb.yaml`; the standard BLE build matrix is disabled. BLE-specific profile actions have been removed from the keymaps, and Bluetooth is disabled in the dongle and split firmware.

## ESB split transport

This branch uses `config/west.yml` to pin the ZMK baseline, ESB module, and
coupled NCS/nrfxlib dependencies to exact revisions. The workflow uses only
`build-esb.yaml`. Bluetooth is disabled, so the unsupported BLE-security
combination in the experimental SDK fork is not part of these firmware builds.

The module README documents testing on nRF52840 only. The target firmware
artifacts are:

- `cornix_dongle_esb_nosd`: flash to the nice!nano USB dongle with the screen.
- `cornix_left_esb`: flash to the left half (`cornix_ph_left` peripheral target).
- `cornix_right_esb`: flash to the right half (`cornix_right` peripheral target).

The USB dongle is the ESB central, while the two halves use ESB peripheral
firmware with IDs 0 and 1. Bluetooth is disabled in all three ESB images. Keep
the addresses in `boards/jzf/cornix/cornix_esb.dtsi` identical across all three
devices; change them if operating multiple Cornix ESB sets nearby.

### ESB radio timing and event reliability

The upstream SDK fork hardcoded the TDMA round-robin slot count to
`CONFIG_ESB_PIPE_COUNT` (8), even when this keyboard has only two active
peripherals. The physical pipe count must remain 8 because the protocol uses
pipe 7 for peripheral-to-central traffic. A small local patch instead sets the
number of scheduled slots from `CONFIG_ZMK_SPLIT_BLE_CENTRAL_PERIPHERALS`
(2). The custom ESB workflow applies this patch only to the pinned SDK checkout.

The ESB targets use 2 kHz polling and individual key-position events,
rather than full matrix snapshots. This avoids reconstructing several changes
in position order when multiple keys change between snapshots and reduces each
key event's payload. The radio stack is still experimental: verify latency,
press/release behavior, simultaneous typing across both halves, and reconnection
on the actual keyboard; this configuration is not a guarantee of a particular
end-to-end latency.

All ESB targets enable `CONFIG_ZMK_BATTERY_REPORTING` so the peripheral
battery symbol required by the ESB module is linked. The ESB central disables
only the BLE-specific battery polling/proxy options, whose storage logic assumes
BLE/Wired split transports. The peripheral's battery event code is not disabled
by this setting.

The ESB build workflow also applies small defensive fixes to the pinned module:
it stops initialization when `esb_initialize()` fails, propagates all errors
from `esb_tx_start()` (rather than checking only `-ENOMEM`), and returns a
defined result from the non-ring-buffer RX path. These patches are checked
against the pinned sources before each build.

## RGB indicators

Version 3.0.0 makes the optional `cornix_indicator` shield production-ready.
It uses `zmk-rgbled-widget` to show battery and split-connection state.

The shield sets `CONFIG_RGBLED_WIDGET_EXT_POWER_TIMEOUT_MS=1000`. When no
animation or static indicator remains active, the WS2812 power rail is turned
off after 1000 ms to reduce idle consumption. LEDs that remain illuminated
still consume power. RGB is opt-in and is not enabled in the default v3.0.0
release artifacts.

## Flashing and recovery

1. Flash the matching ESB UF2 files to the dongle and both keyboard
   halves. Do not mix standard BLE images with ESB images.
2. Power-cycle or reset both halves and the dongle, then connect the dongle to
   the host. Bluetooth bond clearing is not required by this ESB-only build.

Cornix has used the no-SoftDevice flash layout since v2.3. For older firmware,
stock RMK interoperability, or a board that no longer enters UF2 mode, follow
the [bootloader recovery guide](./bootloader/README.md). Do not mix firmware
roles or flash layouts without resetting the affected devices.

## Documentation and support

- [English installation guide](http://gh.bhee.online/zmk-keyboard-cornix/en/)
- [中文安装指南](http://gh.bhee.online/zmk-keyboard-cornix/zh/)
- [ZMK documentation](https://zmk.dev/docs/)
- [Issue tracker](https://github.com/hitsmaxft/zmk-keyboard-cornix/issues)
- [RMK firmware project](https://rmk.rs/)
