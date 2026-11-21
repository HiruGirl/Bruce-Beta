// ══════════════════════════════════════════════════════════════════════════════
// Bruce Light — CYD-2432S028 web flasher configuration
//
// Where to find the Light (JS-Lite) firmware image:
//   Build it from this repo (env CYD-2432S028-JSLITE) — see docs/README.md —
//   then either:
//     (a) drop the produced .bin into docs/firmware/ and keep this URL as-is
//         (same-origin → no CORS, fully offline-capable), or
//     (b) set the URL to any HTTPS-hosted .bin (e.g. a GitHub release asset).
//
// The .bin is the merged esptool image (bootloader + partitions + app) and is
// flashed at address 0x0 with eraseAll=true, which overwrites the whole chip.
// ══════════════════════════════════════════════════════════════════════════════
export const FIRMWARE_URL = "firmware/Bruce-CYD-2432S028-JSLITE.bin";
export const FIRMWARE_NAME = "Bruce Light (CYD-2432S028 JS-Lite)";
export const FIRMWARE_ADDRESS = 0x0; // merged image: bootloader + partition table + app
export const FLASH_MODE = "dio";
export const FLASH_FREQ = "80m";
export const FLASH_SIZE = "4MB"; // 4MB CYD-2432S028

// Set to true to erase the chip before flashing (recommended).
export const ERASE_ALL = true;

// Set to true to compress the payload before flashing (usually faster flashing).
export const COMPRESS = true;
