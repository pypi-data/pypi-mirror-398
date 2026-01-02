# 🐛 gdbrunner

A simple CLI tool that starts a GDB server and automatically attaches GDB to debug embedded targets.

## ✨ Features

- 🔌 **Multiple backends** - Supports J-Link and ST-Link debug probes
- 🔍 **Auto-discovery** - Automatically finds STM32CubeProgrammer installation
- 🧹 **Clean lifecycle** - Starts the server, attaches GDB, and cleans up when done
- ⚙️ **Configurable** - JSON-based backend configuration for easy customization

## 📦 Installation

```bash
pip install gdbrunner
```

## 🚀 Usage

```bash
gdbrunner <backend> [options] elf
```

### Backends

- `jlink` - J-Link GDB server
- `stlink` - ST-Link GDB server

### Examples

```bash
# 🔧 Start J-Link and attach GDB
gdbrunner jlink --device STM32H743VI firmware.elf

# 🔧 Start ST-Link and attach GDB (auto-discovers CubeProgrammer path)
gdbrunner stlink firmware.elf

# 👀 Dry run - print server command without running
gdbrunner jlink --device STM32H743VI --dryrun firmware.elf

# 📺 Show server output for debugging connection issues
gdbrunner stlink --show-output firmware.elf
```

Run `gdbrunner --help` for all options.

## 📄 License

MIT
