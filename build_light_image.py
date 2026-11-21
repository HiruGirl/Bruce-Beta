#!/usr/bin/env python3
"""
Build the Bruce Light (CYD-2432S028 JS-Lite) image and drop it for the web flasher.

USAGE
-----
Run this from anywhere (e.g. from a GitHub Codespace on Ubuntu):

    python3 build_light_image.py                    # setup + build + drop (local)
    python3 build_light_image.py --commit           # also git add + commit the drop-in
    python3 build_light_image.py --commit --push    # then push the commit to origin
    python3 build_light_image.py --dry-run          # only print what it would do

WHAT IT DOES
------------
1. Locates the repository root (the directory holding firmware/platformio.ini).
2. Creates .venv (if missing) and installs PlatformIO (idempotent).
3. Runs `pio run -e CYD-2432S028-JSLITE` inside firmware/ (log: .tmp/pio-build.log).
4. Verifies the merged image `firmware/Bruce-CYD-2432S028-JSLITE.bin` exists.
5. Copies it to `docs/firmware/Bruce-CYD-2432S028-JSLITE.bin` — the file the web
   flasher serves — and prints size/SHA-256.
6. Prints the next steps. Nothing is committed or pushed unless you pass --commit.

NOTE
----
The firmware/ image is a gitignored build artifact. The docs/firmware/ copy is
the committed, published site artifact: the web flasher fetches it from
https://hirugirl.github.io/Bruce-Beta/ and flashes it to the CYD at address 0x0.
"""

import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
FIRMWARE_DIR_REL = "firmware"
PIO_ENV = "CYD-2432S028-JSLITE"
BIN_NAME = "Bruce-CYD-2432S028-JSLITE.bin"


def find_repo_root():
    for candidate in [SCRIPT_DIR, *SCRIPT_DIR.parents]:
        if (candidate / "firmware" / "platformio.ini").is_file():
            return candidate
    fail(f"cannot find the repository root (firmware/platformio.ini) starting at {SCRIPT_DIR}")


def fail(msg):
    print(f"\nERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def run(cmd, cwd=None, **kwargs):
    print(f"\n$ {' '.join(str(c) for c in cmd)}")
    return subprocess.run([str(c) for c in cmd], cwd=cwd, check=False, **kwargs)


def hash_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(
        description="Build the Bruce Light (CYD-2432S028 JS-Lite) firmware image.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--commit", action="store_true",
                        help="git add + commit the docs/firmware/ drop-in")
    parser.add_argument("--push", action="store_true",
                        help="push the commit (requires --commit)")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the steps and exit")
    args = parser.parse_args()
    if args.push and not args.commit:
        fail("--push requires --commit")

    root = find_repo_root()
    firmware_dir = root / "firmware"
    bin_path = firmware_dir / BIN_NAME
    docs_bin_dir = root / "docs" / "firmware"
    docs_bin = docs_bin_dir / BIN_NAME

    print(f"Repository: {root}")
    if args.dry_run:
        print("\n[dry-run] would do:")
        print("  1. create .venv (if missing) + pip install platformio")
        print(f"  2. pio run -e {PIO_ENV}    (cwd={firmware_dir})")
        print(f"  3. verify {bin_path} exists")
        print(f"  4. copy to {docs_bin}")
        print(f"  5. print size/SHA-256")
        if args.commit:
            print(f"  + git add docs/firmware/{BIN_NAME} && git commit")
            if args.push:
                print("  + git push origin HEAD")
        return

    # 1. venv + platformio
    venv = root / ".venv"
    if not (venv / "pyvenv.cfg").is_file():
        print("\n[1/5] Creating .venv")
        r = run([sys.executable, "-m", "venv", venv], cwd=root)
        if r.returncode != 0:
            fail("venv creation failed — is python3-venv installed?")

    python = next((p for p in (venv / "bin" / "python", venv / "Scripts" / "python.exe",
                              venv / "bin" / "python3") if p.exists()), None)
    if python is None:
        fail(f"venv python not found in {venv}")

    print("\n[1/5] Installing PlatformIO")
    r = run([python, "-m", "pip", "install", "--upgrade", "platformio"])
    if r.returncode != 0:
        fail("pip install platformio failed")

    pio = next((p for p in (venv / "bin" / "pio", venv / "Scripts" / "pio.exe") if p.exists()), None)
    pio_cmd = [str(pio)] if pio else [str(python), "-m", "platformio"]

    # 2. Build
    log_dir = root / ".tmp"
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / "pio-build.log"
    print(f"\n[2/5] Building {PIO_ENV} (log: {log_path})")
    with open(log_path, "w") as log:
        r = subprocess.run(
            [*pio_cmd, "run", "-e", PIO_ENV],
            cwd=firmware_dir,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if r.returncode != 0:
        print("\nBuild FAILED — tail of log:", file=sys.stderr)
        tail = subprocess.run(["tail", "-100", str(log_path)], capture_output=True, text=True)
        print(tail.stdout, file=sys.stderr)
        print(f"Full log: {log_path}", file=sys.stderr)
        fail("pio build failed — see log above")

    print(f"  full log saved to {log_path}")

    # 3. Verify
    print("\n[3/5] Verifying merged image")
    if not bin_path.is_file():
        fail(f"expected {bin_path} not found after a successful build")
    size = bin_path.stat().st_size
    print(f"  {bin_path}: {size} bytes")
    if size < 100_000:
        print("  WARNING: image is unexpectedly small")

    # 4. Drop into docs/firmware/
    print("\n[4/5] Dropping into docs/firmware/")
    docs_bin_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(bin_path, docs_bin)
    digest = hash_file(docs_bin)
    print(f"  {docs_bin}: {docs_bin.stat().st_size} bytes")
    print(f"  sha256={digest}")

    # 5. Report
    print("\n[5/5] Build complete")
    print("\nNext steps:")
    print("  1. Commit the published drop-in:")
    print("       git add docs/firmware/Bruce-CYD-2432S028-JSLITE.bin")
    print("       git commit -m \"Add CYD-2432S028 JSLITE image\"")
    print("       git push origin <branch>   # Pages redeploys from docs/")
    print("  2. Flash the CYD with web flasher:")
    print("       https://hirugirl.github.io/Bruce-Beta/  (Web Serial in Chrome/Edge)")
    print("\nNote: firmware/Bruce-CYD-2432S028-JSLITE.bin is a gitignored build")
    print("artifact — the docs/firmware/ copy is the committed, published one.")

    if args.commit:
        print("\nCommitting docs/firmware/ drop-in ...")
        r = run(["git", "add", f"docs/firmware/{BIN_NAME}"], cwd=root)
        if r.returncode != 0:
            fail("git add failed")
        r = run(["git", "commit", "-m", f"Add CYD-2432S028 JSLITE image (sha256={digest[:12]})"], cwd=root)
        if r.returncode != 0:
            fail("git commit failed")
        if args.push:
            r = run(["git", "push", "origin", "HEAD"], cwd=root)
            if r.returncode != 0:
                fail("git push failed")


if __name__ == "__main__":
    main()
