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
- `cornix_dongle_adapter` — central dongle matrix and Bluetooth role
- `cornix_dongle_eyelash` — optional display hardware overlay
- `cornix_indicator` — production-ready RGB battery and connection indicators

Cornix uses a compact 3×6 column-staggered layout with three thumb keys per
half. The hardware supports USB-C, Bluetooth, Kailh Choc V2 hot-swap sockets,
and 10°, 18°, or 25° tenting.

## Zephyr 4.1 requirements

Always use qualified ZMK board names such as `nice_nano//zmk`. The unqualified
`nice_nano` target may select `CONFIG_SETTINGS_NONE=y`, discard the Bluetooth
identity after reboot, and break existing split bonds.

For every nice!nano dongle or reset build, verify the final `.config` contains:

```text
CONFIG_NVS=y
CONFIG_SETTINGS_NVS=y
```

It must not contain `CONFIG_SETTINGS_NONE=y`.

## Build targets

The standard firmware matrix uses `config/west.yml` and `build.yaml`. It does
not load the experimental NCS/ESB SDK fork, so the BLE security libraries are
not built through the incompatible NCS 3.1/Zephyr 4.1 combination.

## Standard split

```yaml
include:
  - board: cornix_left//zmk
    artifact-name: cornix_left

  - board: cornix_right//zmk
    artifact-name: cornix_right

  - board: cornix_right//zmk
    shield: settings_reset
    artifact-name: cornix_reset
```

## Dongle integration

```yaml
include:
  - board: nice_nano//zmk
    shield: cornix_dongle_adapter cornix_dongle_eyelash dongle_display
    snippet: studio-rpc-usb-uart
    artifact-name: cornix_dongle

  - board: cornix_ph_left//zmk
    artifact-name: cornix_left_for_dongle

  - board: cornix_right//zmk
    artifact-name: cornix_right

  - board: nice_nano//zmk
    shield: settings_reset
    artifact-name: dongle_reset
```

Use `cornix_dongle_eyelash` only when the dongle board does not already expose
`zephyr,display`. The `dongle_display` module supplies the display widgets.

## Experimental ESB split transport

The experimental ESB firmware has a separate manifest, `config-esb/west.yml`,
and build matrix, `build-esb.yaml`. This is intentional: the TDMA/FHSS radio
stack uses a custom NCS fork whose BLE security configuration does not compile
reliably with Zephyr 4.1. The standard BLE builds no longer inherit that fork.
The ESB module and its SDK dependencies are pinned to exact commits.

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

The ESB targets use the 2 kHz polling option and whole-key-state snapshots.
The snapshots let the central reconstruct key transitions from the peripheral's
complete position state, which is intended to reduce stuck keys if an event is
lost. The radio stack is still experimental: these settings should be verified
on the actual keyboard for latency, press/release behavior, key ordering, and
reconnection rather than treated as a guarantee of a particular end-to-end
latency.

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

1. Flash the matching settings-reset UF2 to every role whose bonds must be
   cleared.
2. Flash the left, right, and optional dongle UF2 files to their matching
   devices.
3. Reset both halves together and then reconnect the host.

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
