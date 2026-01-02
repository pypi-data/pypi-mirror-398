# gdbrunner

GDB runner - start debug servers and attach GDB.

## Installation

```bash
pip install gdbrunner
```

## Usage

```bash
gdbrunner <backend> [options] elf
```

### Backends

- `jlink` - J-Link GDB server
- `stlink` - ST-Link GDB server

### Examples

```bash
# Start J-Link and attach GDB
gdbrunner jlink --device STM32H743VI firmware.elf

# Start ST-Link and attach GDB
gdbrunner stlink --cube-prog /path/to/cubeprog firmware.elf

# Dry run - print server command without running
gdbrunner jlink --device STM32H743VI --dryrun firmware.elf
```

Run `gdbrunner --help` for all options.

## License

MIT
