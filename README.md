# ZMK Keyboard for Cornix

ZMK board definitions and shields for the Cornix split ergonomic keyboard.

[Documentation: English / 简体中文](http://gh.bhee.online/zmk-keyboard-cornix/) ·
[简体中文 README](./README_zh.md) ·
[日本語 README (AI-generated)](./README_jp.md)

**Current board release:** [`v3.0.0`](https://github.com/hitsmaxft/zmk-keyboard-cornix/releases/tag/v3.0.0)

**ZMK baseline:** `main` with Zephyr 4.1

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

Standard split:

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

Dongle integration:

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

An optional experimental build is available using
[zmk-feature-split-esb](https://github.com/kumbung01/zmk-feature-split-esb).
The module README currently documents testing on nRF52840 only. The Cornix
configuration uses the accompanying
[`sdk-nrf` TDMA/FHSS branch](https://github.com/kumbung01/sdk-nrf/tree/v3.1-branch-tdma-fhss)
and `nrfxlib` `v3.1-branch`, pinned in `config/west.yml`.

The firmware artifacts are:

- `cornix_dongle_esb_nosd`: flash to the nice!nano USB dongle with the screen.
- `cornix_left_esb`: flash to the left half (`cornix_ph_left` peripheral target).
- `cornix_right_esb`: flash to the right half (`cornix_right` peripheral target).

The USB dongle is the ESB central, while the two keyboard halves use ESB
peripheral firmware with IDs 0 and 1. Bluetooth is disabled on these ESB builds.
The standard BLE dongle build keeps the adapter's default BLE settings; the ESB central shield disables Bluetooth for the ESB target. All three ESB
devices must use matching values from `boards/jzf/cornix/cornix_esb.dtsi`;
change those addresses if operating multiple separate Cornix ESB sets nearby.

Treat these firmware images as experimental until the build succeeds and the
three devices are tested together. In particular, verify split key events,
battery reporting, display operation, USB HID output and reconnection after
power cycling on the actual hardware.

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
