#!/usr/bin/env python3
"""
Build the Bruce Light (CYD-2432S028 JS-Lite) image and drop it for the web flasher.

USAGE
-----
Run it from anywhere inside the repository (e.g. from a GitHub Codespace on Ubuntu):

    python3 firmware/build_light_image.py           # from the repo root: setup + build + drop
    cd firmware && python3 build_light_image.py     # same thing, from inside firmware/
    python3 firmware/build_light_image.py --commit  # also git add + commit the drop-in
    python3 firmware/build_light_image.py --commit --push   # then push the commit to origin
    python3 firmware/build_light_image.py --dry-run # only print what it would do
    python3 firmware/build_light_image.py --clean-penv  # delete ~/.platformio/penv first
                                                       # (retry with a clean penv — see below)

WHAT IT DOES
------------
1. Locates the repository root (the directory holding firmware/platformio.ini).
2. Creates .venv (if missing) and installs PlatformIO + uv.
   - uv is required by the pioarduino platform-espressif32 penv setup; installing
     it here means the penv can reuse the same venv's uv (avoids the
     "uv installation via pip failed" fallback path).
3. Pre-flights the environment: python >= 3.10, pip, git, network to PyPI.
4. Smoke-tests the platform's penv setup IN A SCRATCH DIR with visible uv output
   (mirrors builder/penv_setup.py: uv venv -> external uv or pip fallback installs
   uv -> the dependency install). The platform hides its uv output behind --quiet,
   so this is the fastest way to see the REAL error if the Codespace fails here.
   The smoke test fails fast with the visible error if the platform's own step would.
5. Runs `pio run -e CYD-2432S028-JSLITE` inside firmware/ (full log: .tmp/pio-build.log).
6. On failure prints the tail of the log plus specific remediation hints.
7. Verifies the merged image firmware/Bruce-CYD-2432S028-JSLITE.bin exists.
8. Copies it to docs/firmware/Bruce-CYD-2432S028-JSLITE.bin — the file the web
   flasher serves — and prints size/SHA-256.
   Nothing is committed or pushed unless you pass --commit.

KNOWN FAILURE MODES (see .tmp/pio-build.log for the exact error)
----------------------------------------------------------------
- "Failed to install Python dependencies into penv" — the pioarduino platform's
  penv setup could not install its python deps (usually network or a stale penv).
  Fix: verify PyPI/github.com reachability from your Codespace, then rerun with
  --clean-penv to rebuild the ~/.platformio/penv virtual environment from scratch.
- SSL/certificate errors on github.com release-asset downloads — the sandbox
  that created this script blocks those downloads; a Codespace is the
  supported build environment for this image.
"""

import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
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


def venv_python(venv):
    for candidate in (
        venv / "bin" / "python",
        venv / "Scripts" / "python.exe",
        venv / "bin" / "python3",
    ):
        if candidate.exists():
            return candidate
    return None


def pip_ok(python):
    """Check that the venv's python can import pip."""
    try:
        return subprocess.run(
            [str(python), "-m", "pip", "--version"],
            capture_output=True, text=True, timeout=60,
        ).returncode == 0
    except Exception:
        return False


def network_ok():
    """Rough check for PyPI reachability (warns only — does not block)."""
    try:
        import urllib.request
        urllib.request.urlopen("https://pypi.org/simple/", timeout=10)
        return True
    except Exception:
        return False


def preflight(venv, python):
    print("\n[preflight] Environment check")
    problems = []
    ver = sys.version_info
    print(f"  interpreter: {ver.major}.{ver.minor}.{ver.micro} ({sys.executable})")
    if ver < (3, 10):
        problems.append(f"Python >= 3.10 required (platform-espressif32 needs it), found {ver.major}.{ver.minor}")

    if not pip_ok(python):
        problems.append("venv python has no pip — install python3-venv (e.g. sudo apt-get install python3-venv)")

    import shutil as _sh
    if not _sh.which("git"):
        problems.append("git not found on PATH")

    if network_ok():
        print("  network: pypi.org reachable")
    else:
        print("  network: WARNING — pypi.org is NOT reachable (build will likely fail)")

    if problems:
        print("  PREFLIGHT PROBLEMS:")
        for p in problems:
            print(f"   ! {p}")
        print("  (continuing anyway — the build may still succeed)")


def dump_log_tail(log_path, lines=200):
    print(f"\n----- tail of {log_path} (last {lines} lines) -----", file=sys.stderr)
    try:
        tail = subprocess.run(
            ["tail", "-n", str(lines), str(log_path)],
            capture_output=True, text=True, timeout=30,
        )
        sys.stderr.write(tail.stdout)
    except Exception as e:
        sys.stderr.write(f"(could not print log tail: {e})\n")

    print("\n----- likely underlying causes in the log -----", file=sys.stderr)
    try:
        out = subprocess.run(["grep", "-iE", "error|failed|warn|certificate|SSL|uv ", str(log_path)],
                             capture_output=True, text=True, timeout=30).stdout
        for line in out.splitlines()[-40:]:
            print(f"  {line}", file=sys.stderr)
    except Exception:
        pass


def remediation(log_path):
    print("\nRemediation hints (see the full log for the exact error):", file=sys.stderr)
    print("  1. If the log shows 'uv' errors or certificate/SSL errors:", file=sys.stderr)
    print("       - confirm pypi.org and github.com are reachable from your Codespace", file=sys.stderr)
    print("         (curl -v https://pypi.org/simple/  /  curl -I https://github.com)", file=sys.stderr)
    print("       - rerun with: python3 firmware/build_light_image.py --clean-penv", file=sys.stderr)
    print("  2. If the log shows 'No module named pip':", file=sys.stderr)
    print("       - the system python lacks venv/pip: sudo apt-get install -y python3-venv", file=sys.stderr)
    print("  3. A STALE or BROKEN ~/.platformio/penv (e.g. from an earlier failed run or", file=sys.stderr)
    print("     a newer/older Python) can cause this too — --clean-penv removes it and", file=sys.stderr)
    print("     recreates it from scratch.", file=sys.stderr)
    print("  4. The URL-pinned platform download (github.com release assets) is blocked in", file=sys.stderr)
    print("     the build sandbox; builds must happen in a Codespace.", file=sys.stderr)


PENVSMOKE_DEPS = [
    "pioarduino>=6.1.19",
    "littlefs-python>=0.16.0",
    "fatfs-ng>=0.1.14",
    "pyyaml>=6.0.2",
    "rich-click>=1.8.6",
    "zopfli>=0.2.2",
    "intelhex>=2.3.0",
    "rich>=14.0.0",
    "cryptography>=45.0.3",
    "certifi>=2025.8.3",
    "ecdsa>=0.19.1",
    "bitstring>=4.3.1",
    "reedsolo>=1.5.3,<1.8",
    "esp-idf-size>=2.0.0",
    "esp-coredump>=1.14.0",
    "pyelftools>=0.32",
]


def smoke_test_penv(venv, python, root):
    """
    Replicate the platform's penv setup in a scratch dir — WITHOUT the platform's
    --quiet flags — so that a Codespace failure prints the REAL underlying error.
    Mirrors pioarduino/platform-espressif32's builder/penv_setup.py exactly.
    """
    uv = venv / "bin" / "uv"
    if not uv.exists():
        uv = venv / "Scripts" / "uv.exe"
    if not uv.exists():
        print("\n[2/6] uv not found in .venv — skipping penv smoke test\n")
        return True

    # uv venv --clear --python=<python> <penv>   (platform: setup_pipenv_in_package)
    smoke_dir = root / ".tmp" / "penv-smoke"
    smoke_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(smoke_dir, ignore_errors=True)

    print("\n[2/6] Smoke-testing platform penv setup (visible uv output)")
    print("  mirroring builder/penv_setup.py of the pinned platform ...")
    r = run([str(uv), "venv", "--clear", f"--python={python}", smoke_dir], cwd=root)
    if r.returncode != 0:
        print("  WARNING: uv venv failed — the platform would fail here too", file=sys.stderr)

    penv_py = smoke_dir / "bin" / "python"
    if not penv_py.is_file():
        print("  WARNING: penv python missing — continuing anyway", file=sys.stderr)
        return True

    # Platform: external uv installs uv into the penv (fallback allowed)
    r = run([str(uv), "pip", "install", "uv>=0.1.0", f"--python={penv_py}"], cwd=root)
    if r.returncode != 0:
        print("  (platform behavior: external uv failed — falling back to pip)")
        # Platform: pip fallback installs uv into the penv
        run([str(penv_py), "-m", "ensurepip", "--default-pip"], cwd=root)
        r = run([str(penv_py), "-m", "pip", "install", "uv>=0.1.0", "--no-cache-dir"], cwd=root)
        if r.returncode != 0:
            print("  WARNING: pip fallback failed — the platform would fail here too", file=sys.stderr)

    penv_uv = smoke_dir / "bin" / "uv"
    if not penv_uv.is_file():
        print("  WARNING: penv uv not found — the dep-install gate below would be skipped", file=sys.stderr)
        shutil.rmtree(smoke_dir, ignore_errors=True)
        return True

    # Platform: install the deps via penv uv --quiet --upgrade   (the step that fails)
    print("\n  [2/6] penv dependency install (this is where the platform fails in Codespaces)")
    r = run([str(penv_uv), "pip", "install", f"--python={penv_py}", "--upgrade", *PENVSMOKE_DEPS], cwd=root)
    shutil.rmtree(smoke_dir, ignore_errors=True)
    if r.returncode != 0:
        print("\n  *** penv dependency install FAILED — the real error is printed above ***", file=sys.stderr)
        print("  *** this is the step behind the 'Failed to install Python dependencies into penv' error ***", file=sys.stderr)
        return False

    print("\n  penv smoke test OK")
    return True


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
    parser.add_argument("--clean-penv", action="store_true",
                        help="delete ~/.platformio/penv before building (recreates it from scratch)")
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
        print("  1. create .venv (if missing) + pip install platformio + uv")
        print(f"  2. pio run -e {PIO_ENV}    (cwd={firmware_dir})")
        print(f"  3. verify {bin_path} exists")
        print(f"  4. copy to {docs_bin}")
        print(f"  5. print size/SHA-256")
        if args.commit:
            print(f"  + git add docs/firmware/{BIN_NAME} && git commit")
            if args.push:
                print("  + git push origin HEAD")
        return

    # 1. venv + platformio (+ uv; the platform's penv setup reuses it)
    venv = root / ".venv"
    if not (venv / "pyvenv.cfg").is_file():
        print("\n[1/6] Creating .venv")
        r = run([sys.executable, "-m", "venv", venv], cwd=root)
        if r.returncode != 0:
            fail("venv creation failed — is python3-venv installed? (sudo apt-get install -y python3-venv)")

    python = venv_python(venv)
    if python is None:
        fail(f"venv python not found in {venv}")

    print("\n[1/6] Installing PlatformIO + uv")
    r = run([python, "-m", "pip", "install", "--upgrade", "platformio", "uv"])
    if r.returncode != 0:
        fail("pip install platformio failed")

    pio = venv / "bin" / "pio"
    if not pio.exists():
        pio_modules = [venv / "Scripts" / "platformio"]
        pio = pio_modules[0] if pio_modules[0].exists() else None
    pio_cmd = [str(pio)] if pio else [str(python), "-m", "platformio"]

    print("\n[preflight] Tool versions")
    subprocess.run([*pio_cmd, "--version"], capture_output=False, check=False)
    if (venv / "bin" / "uv").exists():
        subprocess.run([str(venv / "bin" / "uv"), "--version"], capture_output=False, check=False)
    elif (venv / "Scripts" / "uv.exe").exists():
        subprocess.run([str(venv / "Scripts" / "uv.exe"), "--version"], capture_output=False, check=False)
    else:
        print("  WARNING: uv not found in .venv — the platform's penv setup may fall")
        print("  back to 'pip install uv', which is the common source of penv failures.")
        print("  Try: .venv/bin/pip install uv")

    preflight(venv, python)

    # Optional: clear stale platformio penv
    if args.clean_penv:
        penv = Path.home() / ".platformio" / "penv"
        if penv.is_dir():
            print(f"\n[1/6] Removing stale penv at {penv}")
            shutil.rmtree(penv, ignore_errors=True)
        print("      (recreated by the build)")

    # Optional: smoke-test the penv setup with visible uv output
    if not smoke_test_penv(venv, python, root):
        print("\nThe platform will fail at the same step. Fix the environment above, then retry.", file=sys.stderr)
        print("Most likely causes: blocked PyPI/network access, a broken/stale penv, or a broken uv binary.", file=sys.stderr)
        print("Use --clean-penv to recreate the penv from scratch and retry.", file=sys.stderr)
        sys.exit(1)

    # 2. Build
    log_dir = root / ".tmp"
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / "pio-build.log"
    print(f"\n[3/6] Building {PIO_ENV} (log: {log_path})")
    with open(log_path, "w") as log:
        r = subprocess.run(
            [*pio_cmd, "run", "-e", PIO_ENV],
            cwd=firmware_dir,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if r.returncode != 0:
        print("\nBuild FAILED", file=sys.stderr)
        dump_log_tail(log_path, 200)
        remediation(log_path)
        fail("pio build failed — see the log tail above")

    print(f"  full log saved to {log_path}")

    # 3. Verify
    print("\n[4/6] Verifying merged image")
    if not bin_path.is_file():
        fail(f"expected {bin_path} not found after a successful build")
    size = bin_path.stat().st_size
    print(f"  {bin_path}: {size} bytes")
    if size < 100_000:
        print("  WARNING: image is unexpectedly small")

    # 4. Drop into docs/firmware/
    print("\n[5/6] Dropping into docs/firmware/")
    docs_bin_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(bin_path, docs_bin)
    digest = hash_file(docs_bin)
    print(f"  {docs_bin}: {docs_bin.stat().st_size} bytes")
    print(f"  sha256={digest}")

    # 5. Report
    print("\n[6/6] Build complete")
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
