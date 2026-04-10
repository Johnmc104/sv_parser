"""
RTL hierarchy and dependency analysis.

Provides:
  - Top module detection
  - Hierarchy tree construction
  - Unresolved module detection
  - Topological sort for compilation order
  - Filelist generation
"""

import os
from typing import Any, Dict, List, Optional, Set

from .data_model import ModuleInfo
from .file_discovery import discover_rtl_files


def find_top_modules(modules):
    # type: (Dict[str, ModuleInfo]) -> List[str]
    """Find modules that are never instantiated by any other module."""
    instantiated = set()  # type: Set[str]
    for mod in modules.values():
        instantiated.update(mod.instantiated_modules)
    return [name for name in modules if name not in instantiated]


def build_hierarchy(top, modules, visited=None):
    # type: (str, Dict[str, ModuleInfo], Optional[Set[str]]) -> Dict[str, Any]
    """Build a hierarchy dict rooted at *top*."""
    if visited is None:
        visited = set()

    if top in visited:
        return {"circular_ref": top}
    visited = visited | {top}

    mod = modules.get(top)
    if mod is None:
        return {}

    node = {
        "file": mod.file_path,
        "instances": [],
    }  # type: Dict[str, Any]

    for inst in mod.instances:
        node["instances"].append({
            "module": inst.module_type,
            "instance": inst.instance_name,
        })

    for inst in mod.instances:
        child = inst.module_type
        if child in modules and child not in visited:
            node[child] = build_hierarchy(child, modules, visited)

    return node


def find_unresolved(modules):
    # type: (Dict[str, ModuleInfo]) -> List[str]
    """Find module types that are instantiated but not defined."""
    all_instantiated = set()  # type: Set[str]
    for mod in modules.values():
        all_instantiated.update(mod.instantiated_modules)
    return sorted(all_instantiated - set(modules.keys()))


def topo_sort(modules, top):
    # type: (Dict[str, ModuleInfo], str) -> List[str]
    """Topological sort (bottom-up: leaves first)."""
    order = []  # type: List[str]
    visited = set()  # type: Set[str]

    def dfs(name):
        # type: (str) -> None
        if name in visited or name not in modules:
            return
        visited.add(name)
        for child in modules[name].instantiated_modules:
            dfs(child)
        order.append(name)

    dfs(top)
    return order


def generate_filelist(modules, top, base_dir="", rtl_dir=""):
    # type: (Dict[str, ModuleInfo], str, str, str) -> Dict[str, Any]
    """Generate ordered filelist for compilation."""
    sorted_names = topo_sort(modules, top)
    unresolved = find_unresolved(modules)

    filelist = []       # type: List[str]
    seen_files = set()  # type: Set[str]
    inc_dirs = set()    # type: Set[str]

    for name in sorted_names:
        mod = modules.get(name)
        if mod is None or not mod.file_path:
            continue

        fpath = mod.file_path
        if fpath in seen_files:
            continue
        seen_files.add(fpath)

        fdir = os.path.dirname(fpath)
        if fdir:
            inc_dirs.add(fdir)

        if base_dir:
            try:
                fpath = os.path.relpath(fpath, base_dir)
            except ValueError:
                pass
        filelist.append(fpath)

    incdir_entries = []  # type: List[str]
    for d in sorted(inc_dirs):
        if base_dir:
            try:
                d = os.path.relpath(d, base_dir)
            except ValueError:
                pass
        incdir_entries.append("+incdir+%s" % d)

    excluded = []  # type: List[str]
    if rtl_dir:
        all_files = set(
            os.path.abspath(f)
            for f in discover_rtl_files(rtl_dir, exclude_tb=False)
        )
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
