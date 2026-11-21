import { ESPLoader, Transport } from "./assets/bundle.js";
import {
  FIRMWARE_URL, FIRMWARE_NAME, FIRMWARE_ADDRESS,
  FLASH_MODE, FLASH_FREQ, FLASH_SIZE, ERASE_ALL, COMPRESS,
} from "./assets/config.js";

const statusBox = document.getElementById("status");
const progress = document.getElementById("progress");
const fill = document.getElementById("progressFill");
const connectBtn = document.getElementById("connect");
const flashBtn = document.getElementById("flash");
const log = document.getElementById("log");

let port = null;
let loader = null;
let firmwareBlob = null;

function setStatus(text, cls = "") {
  statusBox.textContent = text;
  statusBox.className = "status " + cls;
}
function logLine(text) {
  const line = document.createElement("div");
  line.className = "line";
  line.textContent = text;
  log.appendChild(line);
  log.scrollTop = log.scrollHeight;
}
function setProgress(written, total) {
  const pct = total > 0 ? Math.round((written / total) * 100) : 0;
  fill.style.width = pct + "%";
  progress.querySelector("span").textContent =
    total > 0 ? `${pct}%  (${Math.round(written / 1024)} KB / ${Math.round(total / 1024)} KB)` : "";
}
function fail(err) {
  console.error(err);
  setStatus("Error: " + (err && err.message ? err.message : String(err)), "error");
  logLine("ERROR: " + (err && err.message ? err.message : String(err)));
  connectBtn.disabled = false;
  flashBtn.disabled = true;
}

const terminal = {
  writeLine: (s) => logLine(s),
  clean: () => {},
  write: (s) => logLine(s),
};

async function connect() {
  try {
    if (!("serial" in navigator)) {
      throw new Error("Web Serial is not available in this browser. Use Chrome or Edge on desktop.");
    }
    setStatus("Please plug your CYD-2432S028 in and pick the port…");
    connectBtn.disabled = true;
    port = await navigator.serial.requestPort();
    if (!port) {
      setStatus("No port selected.", "error");
      connectBtn.disabled = false;
      return;
    }
    await port.open({ baudRate: 115200 });
    setStatus("Port open. Loading firmware…", "ok");

    setStatus("Fetching " + FIRMWARE_NAME + "…");
    const resp = await fetch(FIRMWARE_URL);
    if (!resp.ok) {
      throw new Error(`Could not fetch firmware (HTTP ${resp.status}). Did you drop the .bin at ${FIRMWARE_URL}?`);
    }
    firmwareBlob = await resp.arrayBuffer();
    logLine(`Loaded ${Math.round(firmwareBlob.byteLength / 1024)} KB.`);
    setStatus("Firmware loaded. Connecting to the board…", "ok");

    const transport = new Transport(port);
    loader = new ESPLoader({ transport, baudrate: 115200, terminal });
    await loader.main();
    setStatus("Connected to the chip. Ready to flash.", "ok");
    connectBtn.disabled = true;
    flashBtn.disabled = false;
  } catch (err) {
    fail(err);
  }
}

async function flash() {
  try {
    if (!loader || !firmwareBlob) throw new Error("Connect first.");
    setStatus("Flashing… do NOT unplug the device.", "busy");
    flashBtn.disabled = true;
    const total = firmwareBlob.byteLength;
    await loader.writeFlash({
      fileArray: [{ data: new Uint8Array(firmwareBlob), address: FIRMWARE_ADDRESS }],
      flashMode: FLASH_MODE,
      flashFreq: FLASH_FREQ,
      flashSize: FLASH_SIZE,
      eraseAll: ERASE_ALL,
      compress: COMPRESS,
      reportProgress: (_i, written, bytes) => setProgress(written, total || bytes),
    });
    setProgress(total, total);
    setStatus("Flashed! Reset the board — Bruce Light should boot.", "ok");
    logLine("Done.");
  } catch (err) {
    fail(err);
  } finally {
    flashBtn.disabled = false;
  }
}

connectBtn.addEventListener("click", connect);
flashBtn.addEventListener("click", flash);
