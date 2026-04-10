"""
rtl_scan — Top-level RTL structural analysis API.

Supports three input modes:
  - Single file:  rtl_scan(file="top.v")
  - File list:    rtl_scan(files=["a.v", "b.v"])
  - Directory:    rtl_scan(directory="/path/to/rtl")

Produces:
  - Module declarations with ports and parameters
  - Hierarchy / dependency graph
  - Port classification (clock, reset, DFT, data, interrupt)
  - Ordered filelist for compilation
  - Instantiation template (inst mode)
  - Port I/O table (io mode)

Usage::

    from src.rtl_scan import rtl_scan, rtl_scan_json
    result = rtl_scan(directory="/path/to/rtl", mode="full")
    result = rtl_scan(file="top.v", mode="inst")
    result = rtl_scan(files=["a.v", "b.v"], mode="modules")
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
    directory="",
    file="",
    files=None,
    top_module="",
    base_dir="",
    mode="full",
    defines=None,
    include_dirs=None,
):
    # type: (str, str, Optional[List[str]], str, str, str, Optional[Dict[str, str]], Optional[List[str]]) -> Dict[str, Any]
    """Scan RTL source(s) and return structured analysis dict.

    Exactly one of *directory*, *file*, or *files* should be provided.

    Args:
        directory:    RTL source directory to scan recursively
        file:         Single Verilog/SV file to parse
        files:        Explicit list of file paths to parse
        top_module:   Top module name (empty → auto-detect)
        base_dir:     Base directory for relative paths in filelist
        mode:         Analysis mode —
                      "modules"   : module declarations only
                      "hierarchy" : modules + dependency graph
                      "ports"     : modules + port classification
                      "filelist"  : full analysis + filelist
                      "full"      : all of the above (default)
                      "inst"      : instantiation template
                      "io"        : port I/O table
        defines:      Extra `define macros {NAME: VALUE}
        include_dirs: Extra +incdir+ search paths

    Returns:
        Dict with analysis results.
    """
    # --- resolve input files ---
    resolved_files, rtl_dir, err = _resolve_input(directory, file, files)
    if err:
        return {"error": err}

    # --- setup preprocessor ---
    pp = Preprocessor()
    if defines:
        pp.add_defines(defines)
    if include_dirs:
        pp.add_include_dirs(include_dirs)
    if rtl_dir:
        pp.add_include_dir(rtl_dir)

    # --- parse ---
    parser = VerilogFileParser(preprocessor=pp)
    all_modules = parser.parse_files(resolved_files)

    if not all_modules:
        result = {"error": "No modules found"}  # type: Dict[str, Any]
        if parser.errors:
            result["parse_errors"] = parser.errors
        return result

    # Build module dict (last definition wins for duplicates)
    modules = {}  # type: Dict[str, ModuleInfo]
    for mod in all_modules:
        modules[mod.name] = mod

    # --- detect top module ---
    top = _resolve_top(modules, top_module)

    # --- build result based on mode ---
    result = _build_result(modules, top, mode, rtl_dir or "", base_dir)

    if parser.errors:
        result["parse_errors"] = parser.errors

    return result


def rtl_scan_json(
    directory="",
    file="",
    files=None,
    top_module="",
    base_dir="",
    mode="full",
    defines=None,
    include_dirs=None,
):
    # type: (str, str, Optional[List[str]], str, str, str, Optional[Dict[str, str]], Optional[List[str]]) -> str
    """Same as rtl_scan() but returns a JSON string."""
    result = rtl_scan(
        directory=directory,
        file=file,
        files=files,
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

def _resolve_input(directory, file, files):
    # type: (str, str, Optional[List[str]]) -> tuple
    """Resolve input to a list of file paths and an RTL directory.

    Returns:
        (resolved_files, rtl_dir, error_msg)
    """
    if file:
        file = os.path.abspath(file)
        if not os.path.isfile(file):
            return ([], "", "File not found: %s" % file)
        return ([file], os.path.dirname(file), "")

    if files:
        resolved = []
        for f in files:
            f = os.path.abspath(f)
            if not os.path.isfile(f):
                return ([], "", "File not found: %s" % f)
            resolved.append(f)
        if not resolved:
            return ([], "", "No files provided")
        # Use directory of first file as rtl_dir
        return (resolved, os.path.dirname(resolved[0]), "")

    if directory:
        directory = os.path.abspath(directory)
        if not os.path.isdir(directory):
            return ([], "", "Directory not found: %s" % directory)
        found = discover_rtl_files(directory)
        if not found:
            return ([], directory, "No RTL files found in: %s" % directory)
        return (found, directory, "")

    return ([], "", "No input specified (use file, files, or directory)")


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

    # inst / io modes: detailed module info for the target module
    if mode in ("inst", "io"):
        target = modules.get(top) if top else None
        if target is None:
            # Fall back to first module
            target = next(iter(modules.values()))
        result["module"] = target.to_full_dict()
        result["top"] = target.name
        # Include raw ModuleInfo ref for formatter (not serialized)
        result["_module_info"] = target
        return result

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
