# nt_flash

A command-line tool for flashing firmware to the Expert Sleepers Disting NT Eurorack module.

## Installation

```bash
pip install nt-flash
```

This installs the `nt_flash` command and all dependencies (including NXP SPSDK).

### Requirements

- Python 3.9 or later
- USB access to the Disting NT in bootloader mode

## Usage

```bash
# Flash from a local package
nt_flash manufacturing_package.zip

# Flash from a URL
nt_flash --url https://example.com/firmware.zip

# Show help
nt_flash --help
```

## Options

| Option | Description |
|--------|-------------|
| `-u, --url URL` | Download package from URL |
| `-t, --timeout SECS` | Device detection timeout (default: 60) |
| `-v, --verbose` | Enable verbose output |
| `--version` | Show version |
| `-h, --help` | Show help |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Invalid arguments |
| 2 | Package error (invalid or missing files) |
| 3 | Download failed |
| 4 | Device not found (timeout) |
| 5 | Flash error |

## Progress Output

The tool outputs structured progress messages for integration with other tools:

```
EXTRACTING
PACKAGE_INFO 1.2.3
WAITING_BOOTLOADER
DEVICE_DETECTED sdp
UPLOADING_FLASHLOADER 100%
DEVICE_DETECTED mboot
CONFIGURING_MEMORY
ERASING 100%
WRITING 100%
RESETTING
COMPLETE
```

## Firmware Package Format

The tool expects a ZIP file (manufacturing_package.zip) containing:

- `MANIFEST.json` - Package metadata
- `*flashloader*.bin` - NXP flashloader binary
- `disting_NT.bin` - Disting NT firmware binary

## How It Works

1. Extracts flashloader and firmware from the package
2. Waits for device in SDP bootloader mode (USB 0x1FC9:0x0135)
3. Uploads flashloader to RAM and executes it
4. Waits for flashloader to enumerate (USB 0x15A2:0x0073)
5. Configures FlexSPI NOR memory
6. Erases flash region
7. Writes firmware at offset 0x1000
8. Resets device to boot new firmware

This is a wrapper around [NXP SPSDK](https://github.com/nxp-mcuxpresso/spsdk) CLI tools (`blhost` and `sdphost`), using separate subprocess calls for each operation to ensure clean USB state.

## Why Subprocess?

The SPSDK Python API has USB HID buffer state issues when multiple operations share the same connection. Using subprocess calls to the CLI tools (which each run in a fresh process) ensures reliable operation. See [SPSDK issue discussion](https://github.com/nxp-mcuxpresso/spsdk/issues) for details.

## License

MIT License
