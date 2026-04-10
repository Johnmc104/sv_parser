"""
rtl_scan — Top-level RTL structural analysis API.

Scans a directory of Verilog files and produces:
  - Module declarations with ports and parameters
  - Hierarchy / dependency graph
  - Port classification (clock, reset, DFT, data, interrupt)
  - Ordered filelist for compilation

Usage::

    from src.rtl_scan import rtl_scan
    result = rtl_scan("/path/to/rtl", top_module="top", mode="full")
"""

import json
import os
from typing import Any, Dict, List, Optional, Set

from .data_model import ModuleInfo
from .preprocessor import Preprocessor
from .verilog_parser import VerilogFileParser


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

_RTL_EXTENSIONS = {".v", ".sv", ".vh", ".svh"}

# Patterns that suggest a file is a testbench, not synthesizable RTL
_TB_PATTERNS = {"_tb", "testbench", "tb_", "test_", "_test"}


def discover_rtl_files(
    directory: str,
    exclude_tb: bool = True,
) -> List[str]:
    """Recursively find Verilog/SV files in *directory*.

    If *exclude_tb* is True, files whose base name contains typical
    testbench patterns are excluded.
    """
    rtl_files: List[str] = []
    for root, _dirs, files in os.walk(directory):
        for f in sorted(files):
            ext = os.path.splitext(f)[1].lower()
            if ext not in _RTL_EXTENSIONS:
                continue
            if exclude_tb:
                lower = f.lower()
                if any(p in lower for p in _TB_PATTERNS):
                    continue
            rtl_files.append(os.path.join(root, f))
    return rtl_files


# ---------------------------------------------------------------------------
# Hierarchy analysis
# ---------------------------------------------------------------------------

def _find_top_modules(modules: Dict[str, ModuleInfo]) -> List[str]:
    """Find modules that are never instantiated by any other module."""
    instantiated: Set[str] = set()
    for mod in modules.values():
        instantiated.update(mod.instantiated_modules)

    tops = [name for name in modules if name not in instantiated]
    return tops


def _build_hierarchy(
    top: str,
    modules: Dict[str, ModuleInfo],
    visited: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """Build a hierarchy dict rooted at *top*."""
    if visited is None:
        visited = set()

    if top in visited:
        return {"circular_ref": top}
    visited = visited | {top}

    mod = modules.get(top)
    if mod is None:
        return {}

    node: Dict[str, Any] = {
        "file": mod.file_path,
        "instances": [],
    }
    for inst in mod.instances:
        node["instances"].append({
            "module": inst.module_type,
            "instance": inst.instance_name,
        })

    # Recurse into children
    for inst in mod.instances:
        child = inst.module_type
        if child in modules and child not in visited:
            node[child] = _build_hierarchy(child, modules, visited)

    return node


def _find_unresolved(modules: Dict[str, ModuleInfo]) -> List[str]:
    """Find module types that are instantiated but not defined."""
    all_instantiated: Set[str] = set()
    for mod in modules.values():
        all_instantiated.update(mod.instantiated_modules)
    return sorted(all_instantiated - set(modules.keys()))


# ---------------------------------------------------------------------------
# Filelist generation (topological sort, bottom-up)
# ---------------------------------------------------------------------------

def _topo_sort(modules: Dict[str, ModuleInfo], top: str) -> List[str]:
    """Topological sort of module dependencies starting from *top*.

    Returns module names in bottom-up order (leaves first).
    """
    order: List[str] = []
    visited: Set[str] = set()

    def dfs(name: str):
        if name in visited or name not in modules:
            return
        visited.add(name)
        for child in modules[name].instantiated_modules:
            dfs(child)
        order.append(name)

    dfs(top)
    return order


def _generate_filelist(
    modules: Dict[str, ModuleInfo],
    top: str,
    base_dir: str = "",
    rtl_dir: str = "",
) -> Dict[str, Any]:
    """Generate ordered filelist for compilation."""
    sorted_names = _topo_sort(modules, top)
    unresolved = _find_unresolved(modules)

    filelist: List[str] = []
    seen_files: Set[str] = set()

    # Collect include directories
    inc_dirs: Set[str] = set()

    for name in sorted_names:
        mod = modules.get(name)
        if mod is None or not mod.file_path:
            continue

        fpath = mod.file_path
        if fpath in seen_files:
            continue
        seen_files.add(fpath)

        # Collect directory for +incdir+
        fdir = os.path.dirname(fpath)
        if fdir:
            inc_dirs.add(fdir)

        # Make path relative to base_dir if given
        if base_dir:
            try:
                fpath = os.path.relpath(fpath, base_dir)
            except ValueError:
                pass

        filelist.append(fpath)

    # Build incdir entries
    incdir_entries: List[str] = []
    for d in sorted(inc_dirs):
        if base_dir:
            try:
                d = os.path.relpath(d, base_dir)
            except ValueError:
                pass
        incdir_entries.append(f"+incdir+{d}")

    # Identify excluded files (files in rtl_dir not in the filelist)
    excluded: List[str] = []
    if rtl_dir:
        all_files = set(os.path.abspath(f) for f in discover_rtl_files(rtl_dir, exclude_tb=False))
        used_files = set(os.path.abspath(f) for f in seen_files)
        for ef in sorted(all_files - used_files):
            if base_dir:
                try:
                    ef = os.path.relpath(ef, base_dir)
                except ValueError:
                    pass
            excluded.append(ef)

    return {
        "filelist": incdir_entries + filelist,
        "order": "bottom-up",
        "excluded": excluded,
        "unresolved": unresolved,
    }


# ---------------------------------------------------------------------------
# Main API
# ---------------------------------------------------------------------------

def rtl_scan(
    directory: str,
    top_module: str = "",
    base_dir: str = "",
    mode: str = "full",
    defines: Optional[Dict[str, str]] = None,
    include_dirs: Optional[List[str]] = None,
) -> str:
    """Scan an RTL directory and return structured JSON analysis.

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
        JSON string with analysis results.
    """
    directory = os.path.abspath(directory)
    if not os.path.isdir(directory):
        return json.dumps({"error": f"Directory not found: {directory}"}, indent=2)

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
        return json.dumps({"error": "No RTL files found", "directory": directory}, indent=2)

    parser = VerilogFileParser(preprocessor=pp)
    all_modules = parser.parse_files(files)

    # Build module dict (last definition wins for duplicates)
    modules: Dict[str, ModuleInfo] = {}
    for mod in all_modules:
        modules[mod.name] = mod

    # --- detect top module ---
    if top_module:
        top = top_module
    else:
        tops = _find_top_modules(modules)
        if len(tops) == 1:
            top = tops[0]
        elif tops:
            # Heuristic: pick the one with most instances
            top = max(tops, key=lambda n: len(modules[n].instances) if n in modules else 0)
        else:
            top = list(modules.keys())[0] if modules else ""

    # --- build result based on mode ---
    result: Dict[str, Any] = {}

    # Always include modules
    result["modules"] = [mod.to_dict() for mod in modules.values()]

    if mode in ("hierarchy", "filelist", "full"):
        hierarchy: Dict[str, Any] = {}
        if top:
            hierarchy = _build_hierarchy(top, modules)
        result["top"] = top
        result["hierarchy"] = {top: hierarchy} if top else {}
        result["unresolved"] = _find_unresolved(modules)

    if mode in ("ports", "full"):
        if top and top in modules:
            result["port_classification"] = modules[top].classify_ports()

    if mode in ("filelist", "full"):
        if top:
            result["filelist_info"] = _generate_filelist(
                modules, top,
                base_dir=base_dir or directory,
                rtl_dir=directory,
            )

    if parser.errors:
        result["parse_errors"] = parser.errors

    return json.dumps(result, indent=2, ensure_ascii=False)
