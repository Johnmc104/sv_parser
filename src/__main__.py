"""
CLI entry point for rtl_scan.

Usage:
    python -m src <directory> [options]

Examples:
    python -m src ./rtl                          # full scan, terminal output
    python -m src ./rtl -m hierarchy             # hierarchy only
    python -m src ./rtl -t top_chip -o result.json   # JSON file output
    python -m src ./rtl --mode filelist --top soc_top
    python -m src ./rtl -D SYNTHESIS -D USE_PLL  # with defines
    python -m src ./rtl -I ./inc -I ./common     # with include dirs
"""

import argparse
import json
import os
import sys

# Allow running as `python -m src` or as a PyInstaller binary
if getattr(sys, 'frozen', False):
    # Running as compiled binary — PyInstaller sets sys.frozen
    _project_root = os.path.dirname(sys.executable)
else:
    _project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.rtl_scan import rtl_scan
from src.formatter import format_result, set_color


def _parse_define(s):
    # type: (str) -> tuple
    """Parse a define string like 'NAME' or 'NAME=VALUE'."""
    if "=" in s:
        k, v = s.split("=", 1)
        return (k.strip(), v.strip())
    return (s.strip(), "")


def build_parser():
    # type: () -> argparse.ArgumentParser
    p = argparse.ArgumentParser(
        prog="rtl_scan",
        description="Scan Verilog/SV RTL directory — structure, hierarchy, ports, filelist",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
modes:
  modules    Module declarations only
  hierarchy  Modules + dependency tree
  ports      Modules + port classification
  filelist   Full analysis + compilation filelist  
  full       All of the above (default)

examples:
  %(prog)s ./rtl
  %(prog)s ./rtl -m hierarchy -t top_chip
  %(prog)s ./rtl -o result.json
  %(prog)s ./rtl -D SYNTHESIS -D USE_PLL=1 -I ./inc
""",
    )

    p.add_argument("directory",
                    help="RTL source directory to scan")
    p.add_argument("-t", "--top",
                    default="", metavar="MODULE",
                    help="top module name (auto-detect if omitted)")
    p.add_argument("-m", "--mode",
                    default="full",
                    choices=["modules", "hierarchy", "ports", "filelist", "full"],
                    help="analysis mode (default: full)")
    p.add_argument("-o", "--output",
                    default="", metavar="FILE",
                    help="write JSON result to file (default: terminal display)")
    p.add_argument("-j", "--json",
                    action="store_true",
                    help="force JSON output to stdout (instead of formatted)")
    p.add_argument("-b", "--base-dir",
                    default="", metavar="DIR",
                    help="base directory for relative paths in filelist")
    p.add_argument("-D", "--define",
                    action="append", default=[], metavar="NAME[=VAL]",
                    help="add preprocessor define (repeatable)")
    p.add_argument("-I", "--incdir",
                    action="append", default=[], metavar="DIR",
                    help="add include search directory (repeatable)")
    p.add_argument("--no-color",
                    action="store_true",
                    help="disable colored terminal output")
    return p


def main(argv=None):
    # type: (list) -> int
    p = build_parser()
    args = p.parse_args(argv)

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
        directory=args.directory,
        top_module=args.top,
        base_dir=args.base_dir,
        mode=args.mode,
        defines=defines if defines else None,
        include_dirs=args.incdir if args.incdir else None,
    )

    # Output
    if args.output:
        # Write JSON to file
        json_str = json.dumps(result, indent=2, ensure_ascii=False)
        with open(args.output, "w") as f:
            f.write(json_str)
            f.write("\n")
        print("Written to %s (%d bytes)" % (args.output, len(json_str)))
        return 0

    if args.json:
        # JSON to stdout
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    # Terminal formatted output
    print(format_result(result, mode=args.mode))

    # Exit code: 1 if errors
    if "error" in result or result.get("parse_errors"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
