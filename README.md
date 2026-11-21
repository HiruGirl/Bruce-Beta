# Bruce-Beta — Light (JS-Lite) for CYD-2432S028

A trimmed variant of [Bruce](https://github.com/BruceDevices/firmware) for the
classic **CYD-2432S028** (2.8" Cheap Yellow Display, SPI touch, 240x320, classic 4 MB),
built around **WiFi + BLE + JS Interpreter + Clock/Others** — with every non-kept
attack/tooling surface hidden.

## What's different from upstream

| Kept | Hidden/dropped |
| --- | --- |
| WiFi (AP + station) | RF/SubGHz, NRF24, IR, RFID, GPS, LoRa, FM, Ethernet, SDR, packet sniffers, DoS/evil-twin attack menus |
| BLE | BadUSB menu, microphone, iButton, HID submenus, SSH/Telnet/SOCKS4/Sniff/Scan/NetCut/Responder/Netcut (split list above) |
| JS Interpreter (mquickjs) | Launcher-only metadata (`LAUNCHER_*`) |
| Settings | Filesharing via ESP-NOW |
| Clock (startup app) | file-sharing |
| Others (QR codes, Megalodon) | WiFi Pass Recovery, WiFite, BLE Suite |

The light build keeps the interpreter fully functional — it is just not the
"official" story: the interpreter natives (BadUSB, audio, BLE Spam) compile like
upstream, but the user-facing menus, start-up apps and config switches for those
features are removed. Use an unsupported-feature build to inspect them.

## Building

```bash
git clone https://github.com/HiruGirl/Bruce-Beta.git
cd Bruce-Beta
python3 -m venv .venv
.venv/bin/pip install platformio
cd firmware
../.venv/bin/pio run -e CYD-2432S028-JSLITE
```

The merged image (`Bruce-CYD-2432S028-JSLITE.bin`) is produced in `firmware/`.
Flash it at address `0x0` (bootloader + partitions + app). Keep the raw args you
used — do **not** flash without the partition table unless you also flash that.

> Node: this env needs the pioarduino platform-espressif32 (55.03.39), the
> framework-arduinoespressif32-libs, and mquickjs 0.0.6. The Linux/macOS/Windows
> build needs host `gcc` (with `-m32` support is not required by the generator —
> it runs native and emits headers).

## Web flasher

`docs/` contains a single-page web flasher (esptool-js + Web Serial) that works from
a GitHub Pages deployment of this repository. To serve it:

1. Enable Pages in **Settings → Pages**, source = **branch `main` → folder `/docs`**,
2. (after merging) open the site, plug your CYD in, flash.

See `docs/README.md` for the full workflow.

## License

See `firmware/LICENSE` and `firmware/THIRD_PARTY.md`.
