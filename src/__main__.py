"""
CLI entry point for rtl_scan.

Usage:
    python -m src <input> [options]

Input can be:
    - A single .v / .sv file
    - A directory (scanned recursively)
    - A filelist via -f option (one file path per line)

Examples:
    python -m src ./rtl                          # full scan on directory
    python -m src top.v -m inst                  # instantiation template
    python -m src top.v -m io                    # port I/O table
    python -m src ./rtl -m hierarchy             # hierarchy only
    python -m src -f filelist.f -t top_chip      # scan from filelist
    python -m src ./rtl -t top_chip -o result.json
    python -m src ./rtl -D SYNTHESIS -I ./inc
"""

import argparse
import json
import os
import sys

# Allow running as `python -m src` or as a PyInstaller binary
if getattr(sys, 'frozen', False):
    _project_root = os.path.dirname(sys.executable)
else:
    _project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.rtl_scan import rtl_scan
from src.formatter import format_result, set_color
from src.log import setup_logging


_ALL_MODES = ["modules", "hierarchy", "ports", "filelist", "full", "inst", "io"]


def _parse_define(s):
    # type: (str) -> tuple
    """Parse a define string like 'NAME' or 'NAME=VALUE'."""
    if "=" in s:
        k, v = s.split("=", 1)
        return (k.strip(), v.strip())
    return (s.strip(), "")


def _read_filelist(path):
    # type: (str) -> list
    """Read a filelist file. One path per line, ignoring comments and blanks."""
    files = []
    base = os.path.dirname(os.path.abspath(path))
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("//") or line.startswith("#"):
                continue
            # Skip +incdir+ / +define+ directives (not file paths)
            if line.startswith("+"):
                continue
            # Resolve relative paths w.r.t. filelist location
            if not os.path.isabs(line):
                line = os.path.join(base, line)
            files.append(os.path.normpath(line))
    return files


def build_parser():
    # type: () -> argparse.ArgumentParser
    p = argparse.ArgumentParser(
        prog="rtl_scan",
        description="Verilog/SV RTL structure analysis — modules, hierarchy, ports, inst, io",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
modes:
  modules    Module declarations only
  hierarchy  Modules + dependency tree
  ports      Modules + port classification
  filelist   Full analysis + compilation filelist
  full       All of the above (default)
  inst       Generate instantiation template (single-file friendly)
  io         Generate port I/O table (single-file friendly)

input:
  Positional argument can be a file (.v/.sv) or a directory.
  Use -f to specify a filelist (one path per line).

examples:
  %(prog)s ./rtl
  %(prog)s top.v -m inst
  %(prog)s top.v -m io
  %(prog)s -f files.f -m hierarchy -t top_chip
  %(prog)s ./rtl -o result.json
  %(prog)s ./rtl -D SYNTHESIS -D USE_PLL=1 -I ./inc
""",
    )

    p.add_argument("input", nargs="?", default="",
                    help="RTL file (.v/.sv) or directory to scan")
    p.add_argument("-f", "--filelist",
                    default="", metavar="FILE",
                    help="read file paths from filelist (one per line)")
    p.add_argument("-t", "--top",
                    default="", metavar="MODULE",
                    help="top module name (auto-detect if omitted)")
    p.add_argument("-m", "--mode",
                    default="full", choices=_ALL_MODES,
                    help="analysis mode (default: full)")
    p.add_argument("-o", "--output",
                    default="", metavar="FILE",
                    help="write JSON result to file")
    p.add_argument("-j", "--json",
                    action="store_true",
                    help="JSON output to stdout")
    p.add_argument("-b", "--base-dir",
                    default="", metavar="DIR",
                    help="base directory for relative paths in filelist output")
    p.add_argument("-D", "--define",
                    action="append", default=[], metavar="NAME[=VAL]",
                    help="preprocessor define (repeatable)")
    p.add_argument("-I", "--incdir",
                    action="append", default=[], metavar="DIR",
                    help="include search directory (repeatable)")
    p.add_argument("--no-color",
                    action="store_true",
                    help="disable colored terminal output")
    p.add_argument("-v", "--verbose",
                    action="count", default=0,
                    help="increase verbosity (-v info, -vv debug)")
    p.add_argument("-q", "--quiet",
                    action="store_true",
                    help="suppress log output (errors only)")
    return p


def main(argv=None):
    # type: (list) -> int
    p = build_parser()
    args = p.parse_args(argv)

    # Logging
    setup_logging(verbose=args.verbose, quiet=args.quiet)

    # --- Resolve input ---
    file_arg = ""
    files_arg = None  # type: list
    dir_arg = ""

    if args.filelist:
        # -f filelist mode
        flist_path = os.path.abspath(args.filelist)
        if not os.path.isfile(flist_path):
            sys.stderr.write("Error: filelist not found: %s\n" % args.filelist)
            return 1
        files_arg = _read_filelist(flist_path)
        if not files_arg:
            sys.stderr.write("Error: no files in filelist: %s\n" % args.filelist)
            return 1
    elif args.input:
        input_path = os.path.abspath(args.input)
        if os.path.isfile(input_path):
            file_arg = input_path
        elif os.path.isdir(input_path):
            dir_arg = input_path
        else:
            sys.stderr.write("Error: input not found: %s\n" % args.input)
            return 1
    else:
        p.print_help()
        return 1

    # Parse defines
    defines = {}
    for d in args.define:
        k, v = _parse_define(d)
        defines[k] = v

    # Color control
    is_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
    if args.no_color or args.json or args.output or not is_tty:
        set_color(False)
    else:
        set_color(True)

    # Run scan
    result = rtl_scan(
        directory=dir_arg,
        file=file_arg,
        files=files_arg,
        top_module=args.top,
        base_dir=args.base_dir,
        mode=args.mode,
        defines=defines if defines else None,
        include_dirs=args.incdir if args.incdir else None,
    )

    # Output
    if args.output:
        # Remove non-serializable internal keys
        out = {k: v for k, v in result.items() if not k.startswith("_")}
        json_str = json.dumps(out, indent=2, ensure_ascii=False)
        try:
            with open(args.output, "w") as f:
                f.write(json_str)
                f.write("\n")
        except IOError as e:
            sys.stderr.write("Error writing output: %s\n" % e)
            return 1
        print("Written to %s (%d bytes)" % (args.output, len(json_str)))
        return 0

    if args.json:
        out = {k: v for k, v in result.items() if not k.startswith("_")}
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0

    # Terminal formatted output
    print(format_result(result, mode=args.mode))

    # Exit code: 1 if errors
    if "error" in result or result.get("parse_errors"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
