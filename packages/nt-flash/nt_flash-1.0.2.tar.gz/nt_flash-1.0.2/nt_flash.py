#!/usr/bin/env python3
"""
nt_flash - Disting NT Firmware Flash Tool

A wrapper around NXP SPSDK for flashing firmware to the
Expert Sleepers Disting NT Eurorack module.

Usage:
    nt_flash <manufacturing_package.zip>
    nt_flash --url <firmware_url>
"""

import argparse
import json
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

VERSION = "1.0.2"

# USB Device IDs
SDP_VID = 0x1FC9
SDP_PID = 0x0135
MBOOT_VID = 0x15A2
MBOOT_PID = 0x0073

# Memory addresses (from official NXP scripts)
FLASHLOADER_ADDR = 0x20001C00
FLEXSPI_OPTION_ADDR = 0x2000
FLEXSPI_BASE_ADDR = 0x60000000
FIRMWARE_WRITE_ADDR = 0x60001000

# FlexSPI configuration options
FLEXSPI_NOR_OPTION = 0xC0000008
FCB_OPTION = 0xF000000F


def progress(message: str, percent: Optional[int] = None):
    """Print progress message."""
    if percent is not None:
        print(f"{message} {percent}%")
    else:
        print(message)
    sys.stdout.flush()


def run_sdphost(*args, timeout: int = 30) -> bool:
    """Run sdphost command."""
    cmd = ["sdphost", "-u", f"0x{SDP_VID:04X},0x{SDP_PID:04X}", "--"] + list(args)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except FileNotFoundError:
        print("ERROR: sdphost not found. Install SPSDK: pip install spsdk", file=sys.stderr)
        sys.exit(1)


def run_blhost(*args, timeout: int = 30) -> bool:
    """Run blhost command."""
    cmd = ["blhost", "-t", str(timeout * 1000), "-u", f"0x{MBOOT_VID:04X},0x{MBOOT_PID:04X}", "--"] + list(args)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except FileNotFoundError:
        print("ERROR: blhost not found. Install SPSDK: pip install spsdk", file=sys.stderr)
        sys.exit(1)


def wait_for_sdp_device(timeout: int = 30) -> bool:
    """Wait for device in SDP bootloader mode."""
    progress("WAITING_BOOTLOADER")
    start = time.time()
    while time.time() - start < timeout:
        if run_sdphost("error-status", timeout=5):
            progress("DEVICE_DETECTED sdp")
            return True
        time.sleep(0.5)
    return False


def wait_for_mboot_device(timeout: int = 15) -> bool:
    """Wait for device in flashloader (MBoot) mode."""
    start = time.time()
    while time.time() - start < timeout:
        if run_blhost("get-property", "1", "0", timeout=5):
            progress("DEVICE_DETECTED mboot")
            return True
        time.sleep(0.5)
    return False


def extract_package(zip_path: Path, extract_dir: Path) -> tuple[Path, Path, str]:
    """Extract flashloader, firmware, and version from package."""
    progress("EXTRACTING")

    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_dir)
        names = zf.namelist()

        # Find manifest
        manifest_name = next((n for n in names if n.endswith('MANIFEST.json')), None)
        if not manifest_name:
            raise ValueError("MANIFEST.json not found in package")

        manifest_path = extract_dir / manifest_name
        with open(manifest_path) as f:
            manifest = json.load(f)
        version = manifest.get('version', manifest.get('firmware_version', 'unknown'))

        # Find flashloader
        flashloader_path = None
        for name in names:
            if 'flashloader' in name.lower() and name.endswith('.bin'):
                flashloader_path = extract_dir / name
                break
        if not flashloader_path or not flashloader_path.exists():
            raise ValueError("Flashloader binary not found in package")

        # Find firmware
        firmware_path = None
        app_firmware = manifest.get('app_firmware', '')
        if app_firmware:
            for name in names:
                if name.endswith(Path(app_firmware).name):
                    firmware_path = extract_dir / name
                    break
        if not firmware_path:
            for name in names:
                if 'disting' in name.lower() and name.endswith('.bin'):
                    firmware_path = extract_dir / name
                    break
        if not firmware_path or not firmware_path.exists():
            raise ValueError("Firmware binary not found in package")

    progress(f"PACKAGE_INFO {version}")
    print(f"[DEBUG] Flashloader: {flashloader_path}", file=sys.stderr)
    print(f"[DEBUG] Firmware: {firmware_path} ({firmware_path.stat().st_size} bytes)", file=sys.stderr)

    return flashloader_path, firmware_path, version


def flash_firmware(package_path: Path, timeout: int = 60, verbose: bool = False):
    """Main flash operation using subprocess calls to blhost/sdphost."""

    with TemporaryDirectory() as tmpdir:
        extract_dir = Path(tmpdir)

        # Extract package
        flashloader_path, firmware_path, version = extract_package(package_path, extract_dir)
        firmware_size = firmware_path.stat().st_size

        # Wait for SDP device
        if not wait_for_sdp_device(timeout):
            raise TimeoutError(f"SDP device not found within {timeout} seconds. Is device in bootloader mode?")

        # Upload flashloader
        progress("UPLOADING_FLASHLOADER", 0)
        if not run_sdphost("write-file", hex(FLASHLOADER_ADDR), str(flashloader_path)):
            raise RuntimeError("Failed to upload flashloader")
        progress("UPLOADING_FLASHLOADER", 100)

        # Jump to flashloader
        run_sdphost("jump-address", hex(FLASHLOADER_ADDR))

        # Wait for flashloader to initialize
        time.sleep(3)

        # Wait for MBoot device
        if not wait_for_mboot_device(timeout=15):
            raise TimeoutError("Flashloader did not start")

        # Configure FlexSPI memory
        progress("CONFIGURING_MEMORY")
        if not run_blhost("fill-memory", hex(FLEXSPI_OPTION_ADDR), "4", hex(FLEXSPI_NOR_OPTION), "word"):
            raise RuntimeError("Failed to fill memory for FlexSPI config")
        if not run_blhost("configure-memory", "9", hex(FLEXSPI_OPTION_ADDR)):
            raise RuntimeError("Failed to configure FlexSPI memory")

        # Erase flash region
        erase_size = firmware_size + 0x1000
        progress("ERASING", 0)
        if not run_blhost("flash-erase-region", hex(FLEXSPI_BASE_ADDR), str(erase_size), "0", timeout=60):
            raise RuntimeError("Failed to erase flash")
        progress("ERASING", 100)

        # Generate Flash Config Block (FCB)
        if not run_blhost("fill-memory", hex(FLEXSPI_OPTION_ADDR), "4", hex(FCB_OPTION), "word"):
            raise RuntimeError("Failed to fill memory for FCB")
        if not run_blhost("configure-memory", "9", hex(FLEXSPI_OPTION_ADDR)):
            raise RuntimeError("Failed to generate FCB")

        # Write firmware
        progress("WRITING", 0)
        if not run_blhost("write-memory", hex(FIRMWARE_WRITE_ADDR), str(firmware_path), "0", timeout=120):
            raise RuntimeError("Failed to write firmware")
        progress("WRITING", 100)

        # Reset device to boot new firmware
        progress("RESETTING")
        run_blhost("reset")  # May fail if device resets too quickly, that's OK

        progress("COMPLETE")
        print("\nFlash complete. Device is rebooting.", file=sys.stderr)


def download_package(url: str, dest: Path) -> Path:
    """Download package from URL."""
    import urllib.request

    progress("DOWNLOADING", 0)

    def report_progress(block_num, block_size, total_size):
        if total_size > 0:
            percent = min(100, int(block_num * block_size * 100 / total_size))
            progress("DOWNLOADING", percent)

    urllib.request.urlretrieve(url, dest, reporthook=report_progress)
    progress("DOWNLOADING", 100)
    return dest


def main():
    parser = argparse.ArgumentParser(
        description="Flash firmware to Disting NT via USB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit codes:
  0  Success
  1  Invalid arguments
  2  Package error
  3  Download error
  4  Device not found
  5  Flash error
"""
    )
    parser.add_argument("package", nargs="?", help="Path to manufacturing_package.zip")
    parser.add_argument("-u", "--url", help="Download package from URL")
    parser.add_argument("-t", "--timeout", type=int, default=60,
                        help="Device detection timeout in seconds (default: 60)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Verbose output")
    parser.add_argument("--version", action="version", version=f"nt_flash {VERSION}")

    args = parser.parse_args()

    if not args.package and not args.url:
        parser.error("Either package path or --url is required")

    try:
        if args.url:
            with TemporaryDirectory() as tmpdir:
                package_path = Path(tmpdir) / "firmware.zip"
                download_package(args.url, package_path)
                flash_firmware(package_path, args.timeout, verbose=args.verbose)
        else:
            package_path = Path(args.package)
            if not package_path.exists():
                progress(f"ERROR Package not found: {package_path}")
                return 2
            flash_firmware(package_path, args.timeout, verbose=args.verbose)

        return 0

    except zipfile.BadZipFile:
        progress("ERROR Invalid ZIP file")
        return 2
    except ValueError as e:
        progress(f"ERROR {e}")
        return 2
    except TimeoutError as e:
        progress(f"ERROR {e}")
        return 4
    except Exception as e:
        progress(f"ERROR {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 5


if __name__ == "__main__":
    sys.exit(main())
