"""
rtl_scan — Top-level RTL structural analysis API.

Scans a directory of Verilog files and produces:
  - Module declarations with ports and parameters
  - Hierarchy / dependency graph
  - Port classification (clock, reset, DFT, data, interrupt)
  - Ordered filelist for compilation

Usage::

    from src.rtl_scan import rtl_scan, rtl_scan_json
    result_dict = rtl_scan("/path/to/rtl", top_module="top", mode="full")
    result_json = rtl_scan_json("/path/to/rtl", mode="full")
"""

import json
import os
from typing import Any, Dict, List, Optional

from .data_model import ModuleInfo
from .file_discovery import discover_rtl_files
from .hierarchy import (
    build_hierarchy,
    find_top_modules,
    find_unresolved,
    generate_filelist,
)
from .preprocessor import Preprocessor
from .verilog_parser import VerilogFileParser


# ---------------------------------------------------------------------------
# Main API
# ---------------------------------------------------------------------------

def rtl_scan(
    directory,
    top_module="",
    base_dir="",
    mode="full",
    defines=None,
    include_dirs=None,
):
    # type: (str, str, str, str, Optional[Dict[str, str]], Optional[List[str]]) -> Dict[str, Any]
    """Scan an RTL directory and return structured analysis dict.

    Args:
        directory:    RTL source directory path
        top_module:   Top module name (empty → auto-detect)
        base_dir:     Base directory for relative paths in filelist
        mode:         Analysis mode —
                      "modules"   : module declarations only
                      "hierarchy" : modules + dependency graph
                      "ports"     : modules + port classification
                      "filelist"  : full analysis + filelist
                      "full"      : all of the above (default)
        defines:      Extra `define macros {NAME: VALUE}
        include_dirs: Extra +incdir+ search paths

    Returns:
        Dict with analysis results.
    """
    directory = os.path.abspath(directory)
    if not os.path.isdir(directory):
        return {"error": "Directory not found: %s" % directory}

    # --- setup preprocessor ---
    pp = Preprocessor()
    if defines:
        pp.add_defines(defines)
    if include_dirs:
        pp.add_include_dirs(include_dirs)
    pp.add_include_dir(directory)

    # --- discover & parse ---
    files = discover_rtl_files(directory)
    if not files:
        return {"error": "No RTL files found", "directory": directory}

    parser = VerilogFileParser(preprocessor=pp)
    all_modules = parser.parse_files(files)

    # Build module dict (last definition wins for duplicates)
    modules = {}  # type: Dict[str, ModuleInfo]
    for mod in all_modules:
        modules[mod.name] = mod

    # --- detect top module ---
    top = _resolve_top(modules, top_module)

    # --- build result based on mode ---
    result = _build_result(modules, top, mode, directory, base_dir)

    if parser.errors:
        result["parse_errors"] = parser.errors

    return result


def rtl_scan_json(
    directory,
    top_module="",
    base_dir="",
    mode="full",
    defines=None,
    include_dirs=None,
):
    # type: (str, str, str, str, Optional[Dict[str, str]], Optional[List[str]]) -> str
    """Same as rtl_scan() but returns a JSON string."""
    result = rtl_scan(
        directory,
        top_module=top_module,
        base_dir=base_dir,
        mode=mode,
        defines=defines,
        include_dirs=include_dirs,
    )
    return json.dumps(result, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_top(modules, top_module):
    # type: (Dict[str, ModuleInfo], str) -> str
    """Resolve or auto-detect the top module."""
    if top_module:
        return top_module

    tops = find_top_modules(modules)
    if len(tops) == 1:
        return tops[0]
    if tops:
        return max(
            tops,
            key=lambda n: len(modules[n].instances) if n in modules else 0)
    return list(modules.keys())[0] if modules else ""


def _build_result(modules, top, mode, directory, base_dir):
    # type: (Dict[str, ModuleInfo], str, str, str, str) -> Dict[str, Any]
    """Build the result dict based on mode."""
    result = {}  # type: Dict[str, Any]

    # Always include modules
    result["modules"] = [mod.to_dict() for mod in modules.values()]

    if mode in ("hierarchy", "filelist", "full"):
        hierarchy = {}  # type: Dict[str, Any]
        if top:
            hierarchy = build_hierarchy(top, modules)
        result["top"] = top
        result["hierarchy"] = {top: hierarchy} if top else {}
        result["unresolved"] = find_unresolved(modules)

    if mode in ("ports", "full"):
        if top and top in modules:
            result["port_classification"] = modules[top].classify_ports()

    if mode in ("filelist", "full"):
        if top:
            result["filelist_info"] = generate_filelist(
                modules, top,
                base_dir=base_dir or directory,
                rtl_dir=directory,
            )

    return result
