# This file is part of the OpenMV project.
#
# Copyright (C) 2025 OpenMV, LLC.
# This work is licensed under the MIT license, see the file LICENSE for details.

"""Command-line interface for gdbrunner."""

import argparse
import glob
import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path


def load_backends():
    """Load backends from JSON config."""
    config_path = Path(__file__).parent / "backends.json"
    with open(config_path) as f:
        return json.load(f)


def search_path(patterns):
    """Search glob patterns and return first match."""
    for pattern in patterns:
        expanded = os.path.expanduser(pattern)
        matches = sorted(glob.glob(expanded), reverse=True)
        if matches:
            return matches[0]
    return None


def add_arguments(parser, config):
    """Add arguments from JSON config to parser."""
    def parse_bool(value):
        if value.lower() in ("true", "1", "yes"):
            return True
        if value.lower() in ("false", "0", "no"):
            return False
        raise argparse.ArgumentTypeError(f"Invalid boolean: {value}")

    for arg in config["arguments"]:
        flag = arg["flag"]
        kwargs = {}

        if "help" in arg:
            kwargs["help"] = arg["help"]
        if "default" in arg:
            kwargs["default"] = arg["default"]
        elif arg.get("auto"):
            path = search_path(config.get("paths", []))
            if path:
                kwargs["default"] = path
        if arg.get("required") and "default" not in kwargs:
            kwargs["required"] = True

        arg_type = arg.get("type")
        if arg_type == "int":
            kwargs["type"] = int
        elif arg_type == "bool":
            kwargs["type"] = parse_bool

        parser.add_argument(flag, **kwargs)


def build_command(config, args):
    """Build server command from config and parsed args."""
    cmd = [config["command"]]

    # Add fixed args
    if "fixed_args" in config:
        cmd.extend(config["fixed_args"])

    # Add arguments based on parsed values
    for arg in config["arguments"]:
        flag = arg["flag"]
        dest = flag[2:].replace("-", "_")
        value = getattr(args, dest, None)

        if value is None:
            continue

        arg_type = arg.get("type")
        if arg_type == "bool":
            if value:
                cmd.append(arg["cmd"])
        else:
            cmd.extend([arg["cmd"], str(value)])

    return cmd


def wait_for_port(port, timeout=3.0):
    """Wait for a port to become available."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("localhost", port), timeout=0.5):
                return True
        except (ConnectionRefusedError, socket.timeout, OSError):
            time.sleep(0.1)
    return False


def run_debug_session(args, server_cmd):
    """Start GDB server, run GDB, and clean up."""
    # Start GDB server in background
    server_proc = subprocess.Popen(
        server_cmd,
        stdout=None if args.show_output else subprocess.DEVNULL,
        stderr=None if args.show_output else subprocess.DEVNULL,
        start_new_session=True,
    )

    def cleanup(signum=None, frame=None):
        server_proc.terminate()
        try:
            server_proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            server_proc.kill()
        if signum is not None:
            sys.exit(128 + signum)

    signal.signal(signal.SIGTERM, cleanup)

    # Wait for server to be ready
    if not wait_for_port(args.port):
        print("GDB server failed to start", file=sys.stderr)
        cleanup()
        sys.exit(1)

    # Build GDB command
    gdb_cmd = [
        f"{args.toolchain}gdb",
        "-iex", "set confirm off",
        "-ex", f"target remote localhost:{args.port}",
    ]

    # Add gdbinit from current directory if it exists (overrides ~/.gdbinit)
    gdbinit = os.path.join(os.getcwd(), ".gdbinit")
    if os.path.exists(gdbinit):
        gdb_cmd.extend(["-ix", gdbinit])

    gdb_cmd.append(args.elf)

    # Run GDB (ignore SIGINT so Ctrl+C goes to GDB, not us)
    old_sigint = signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        result = subprocess.run(gdb_cmd)
        cleanup()
        sys.exit(result.returncode)
    except FileNotFoundError:
        print(f"GDB not found: {args.toolchain}gdb", file=sys.stderr)
        cleanup()
        sys.exit(1)
    finally:
        signal.signal(signal.SIGINT, old_sigint)


def main():
    backends = load_backends()

    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("Usage: gdbrunner <backend> [options] elf\n")
        print("Common options:\n")
        print("  --toolchain PREFIX  Toolchain prefix (default: arm-none-eabi-)")
        print("  --dryrun            Print command without running")
        print("  --show-output       Show server output")
        print("  elf                 ELF file to debug")

        for name in sorted(backends.keys()):
            config = backends[name]
            print(f"\n{name} options:\n")
            for arg in config["arguments"]:
                flag = arg["flag"]
                help_text = arg.get("help", "")
                print(f"  {flag:22} {help_text}")

        sys.exit(0 if sys.argv[1:] in (["-h"], ["--help"]) else 1)

    backend = sys.argv[1].lower()
    if backend not in backends:
        print(f"Unknown backend: {backend}", file=sys.stderr)
        print(f"Available backends: {', '.join(sorted(backends.keys()))}", file=sys.stderr)
        sys.exit(1)

    config = backends[backend]
    parser = argparse.ArgumentParser(
        prog=f"gdbrunner {backend}",
        description=f"Start {backend} GDB server and attach GDB"
    )
    parser.add_argument(
        "--toolchain", default="arm-none-eabi-",
        help="Toolchain prefix (default: arm-none-eabi-)"
    )
    parser.add_argument(
        "--dryrun", action="store_true",
        help="Print command without running"
    )
    parser.add_argument(
        "--show-output", action="store_true",
        help="Show server output"
    )
    add_arguments(parser, config)
    parser.add_argument("elf", help="ELF file to debug")

    args = parser.parse_args(sys.argv[2:])
    server_cmd = build_command(config, args)

    if args.dryrun:
        print(" ".join(server_cmd))
    else:
        run_debug_session(args, server_cmd)


if __name__ == "__main__":
    main()
