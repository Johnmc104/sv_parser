"""
Terminal-friendly formatters for RTL scan results.

Renders analysis results as human-readable tables and trees
for terminal output, complementing the JSON output mode.
"""

import os
from typing import Any, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .data_model import ModuleInfo, PortInfo


# ---------------------------------------------------------------------------
# ANSI color helpers (auto-disabled if not a tty)
# ---------------------------------------------------------------------------

_USE_COLOR = True


def set_color(enabled):
    # type: (bool) -> None
    global _USE_COLOR
    _USE_COLOR = enabled


def _c(code, text):
    # type: (str, str) -> str
    if _USE_COLOR:
        return "\033[%sm%s\033[0m" % (code, text)
    return text


def _bold(text):    return _c("1", text)
def _green(text):   return _c("32", text)
def _yellow(text):  return _c("33", text)
def _cyan(text):    return _c("36", text)
def _red(text):     return _c("31", text)
def _dim(text):     return _c("2", text)


# ---------------------------------------------------------------------------
# Table helper
# ---------------------------------------------------------------------------

def _table(headers, rows, indent=0):
    # type: (List[str], List[List[str]], int) -> str
    """Simple aligned table formatter."""
    if not rows:
        return ""
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(cell))

    pad = " " * indent
    lines = []

    # header
    hdr = pad + "  ".join(
        h.ljust(col_widths[i]) for i, h in enumerate(headers))
    lines.append(_bold(hdr))
    lines.append(pad + "  ".join("-" * w for w in col_widths))

    # rows
    for row in rows:
        cells = []
        for i, cell in enumerate(row):
            w = col_widths[i] if i < len(col_widths) else 0
            cells.append(cell.ljust(w))
        lines.append(pad + "  ".join(cells))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section formatters
# ---------------------------------------------------------------------------

def format_modules_summary(result):
    # type: (Dict[str, Any]) -> str
    """Format module list as a compact table."""
    modules = result.get("modules", [])
    if not modules:
        return _yellow("No modules found.")

    lines = [_bold("Modules (%d)" % len(modules)), ""]

    rows = []
    for m in modules:
        name = m["name"]
        ports = m.get("ports", {})
        n_in = len(ports.get("inputs", []))
        n_out = len(ports.get("outputs", []))
        n_io = len(ports.get("inouts", []))
        n_param = len(m.get("parameters", []))
        port_str = "%dI/%dO" % (n_in, n_out)
        if n_io:
            port_str += "/%dIO" % n_io
        fpath = m.get("file", "")
        if fpath:
            fpath = os.path.basename(fpath)
        rows.append([name, port_str, "%dp" % n_param, fpath])

    lines.append(_table(["Module", "Ports", "Params", "File"], rows, indent=2))
    return "\n".join(lines)


def format_hierarchy(result):
    # type: (Dict[str, Any]) -> str
    """Format hierarchy as an indented tree."""
    top = result.get("top", "")
    hierarchy = result.get("hierarchy", {})
    if not top or not hierarchy:
        return ""

    lines = [_bold("Hierarchy (top: %s)" % _cyan(top)), ""]

    def _tree(node, prefix="  ", is_last=True):
        # type: (Dict[str, Any], str, bool) -> None
        instances = node.get("instances", [])
        for i, inst in enumerate(instances):
            last = (i == len(instances) - 1)
            connector = "└── " if last else "├── "
            child_prefix = "    " if last else "│   "

            inst_name = inst.get("instance", "?")
            mod_name = inst.get("module", "?")
            label = "%s (%s)" % (_green(inst_name), _cyan(mod_name))
            lines.append(prefix + connector + label)

            # Recurse into child if hierarchy data exists
            child_node = node.get(mod_name)
            if child_node and isinstance(child_node, dict):
                _tree(child_node, prefix + child_prefix, last)

    root_node = hierarchy.get(top, {})
    lines.append("  " + _cyan(top))
    _tree(root_node, "  ")

    unresolved = result.get("unresolved", [])
    if unresolved:
        lines.append("")
        lines.append("  " + _yellow("Unresolved: %s" % ", ".join(unresolved)))

    return "\n".join(lines)


def format_ports(result):
    # type: (Dict[str, Any]) -> str
    """Format port classification as grouped tables."""
    cls = result.get("port_classification")
    if not cls:
        return ""

    lines = [_bold("Port Classification"), ""]

    # Clocks
    clocks = cls.get("clocks", [])
    if clocks:
        rows = [[c["port"], c.get("direction", "")] for c in clocks]
        lines.append("  " + _cyan("Clocks (%d)" % len(clocks)))
        lines.append(_table(["Port", "Dir"], rows, indent=4))
        lines.append("")

    # Resets
    resets = cls.get("resets", [])
    if resets:
        rows = [[r["port"], r.get("direction", ""), r.get("active", "")] for r in resets]
        lines.append("  " + _cyan("Resets (%d)" % len(resets)))
        lines.append(_table(["Port", "Dir", "Active"], rows, indent=4))
        lines.append("")

    # DFT
    dft = cls.get("dft", [])
    if dft:
        lines.append("  " + _cyan("DFT (%d)" % len(dft)))
        lines.append("    " + ", ".join(dft))
        lines.append("")

    # Interrupts
    irqs = cls.get("interrupts", [])
    if irqs:
        lines.append("  " + _cyan("Interrupts (%d)" % len(irqs)))
        lines.append("    " + ", ".join(irqs))
        lines.append("")

    # Data
    data_in = cls.get("data_inputs", [])
    data_out = cls.get("data_outputs", [])
    if data_in or data_out:
        lines.append("  " + _cyan("Data"))
        if data_in:
            lines.append("    inputs:  " + ", ".join(data_in))
        if data_out:
            lines.append("    outputs: " + ", ".join(data_out))
        lines.append("")

    return "\n".join(lines)


def format_filelist(result):
    # type: (Dict[str, Any]) -> str
    """Format filelist info."""
    fl = result.get("filelist_info")
    if not fl:
        return ""

    files = fl.get("filelist", [])
    excluded = fl.get("excluded", [])
    unresolved = fl.get("unresolved", [])

    lines = [_bold("Filelist (bottom-up)"), ""]
    for f in files:
        if f.startswith("+incdir+"):
            lines.append("  " + _dim(f))
        else:
            lines.append("  " + f)

    if excluded:
        lines.append("")
        lines.append("  " + _yellow("Excluded (%d):" % len(excluded)))
        for e in excluded:
            lines.append("    " + _dim(e))

    if unresolved:
        lines.append("")
        lines.append("  " + _red("Unresolved: %s" % ", ".join(unresolved)))

    return "\n".join(lines)


def format_errors(result):
    # type: (Dict[str, Any]) -> str
    """Format parse errors."""
    errors = result.get("parse_errors", [])
    if not errors:
        return ""
    lines = [_red("Parse Errors (%d)" % len(errors))]
    for e in errors:
        lines.append("  " + _red(e))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Instantiation template (inst mode)
# ---------------------------------------------------------------------------

def format_inst(result):
    # type: (Dict[str, Any]) -> str
    """Generate Verilog instantiation template from parse result.

    Replicates vtool_inst.py behavior: produces a `.port(w_signal)` style
    template with wire declarations.
    """
    from .data_model import ModuleInfo
    mod = result.get("_module_info")  # type: ModuleInfo
    if mod is None:
        return _red("No module info for inst generation")

    name = mod.name
    ports = mod.ports

    if not ports:
        return _yellow("Module '%s' has no ports." % name)

    # Build signal names: replace i_/o_ prefix with w_
    def _wire_name(p):
        # type: (PortInfo) -> str
        n = p.name
        if n.startswith("i_"):
            return "w_" + n[2:]
        if n.startswith("o_"):
            return "w_" + n[2:]
        return n

    wire_names = [_wire_name(p) for p in ports]
    max_port = max(len(p.name) for p in ports)
    max_wire = max(len(w) for w in wire_names)

    # Wire declarations
    wire_lines = []
    for p, wn in zip(ports, wire_names):
        if not wn.startswith("w_"):
            continue
        if p.width > 1:
            wire_lines.append("wire [%d:0] %s;" % (p.width - 1, wn))
        else:
            wire_lines.append("wire %s;" % wn)

    # Instance template
    inst_lines = []
    params = [p for p in mod.parameters if p.param_type == "parameter"]
    if params:
        max_param = max(len(p.name) for p in params)
        max_val = max(len(p.value) for p in params) if any(p.value for p in params) else 1
        inst_lines.append("%s #(" % name)
        for i, par in enumerate(params):
            comma = "," if i < len(params) - 1 else ""
            val = par.value if par.value else ""
            inst_lines.append(
                "  .%-*s (%-*s )%s" % (
                    max_param, par.name,
                    max_val, val,
                    comma,
                )
            )
        inst_lines.append(") inst_%s (" % name)
    else:
        inst_lines.append("%s inst_%s(" % (name, name))
    for i, (p, wn) in enumerate(zip(ports, wire_names)):
        comma = "," if i < len(ports) - 1 else ""
        # Comment with port info
        comment = p.direction.value
        if p.range_spec:
            comment += " " + p.range_spec
        inst_lines.append(
            "  .%-*s (%-*s )%s // %s" % (
                max_port, p.name,
                max_wire, wn,
                comma, comment,
            )
        )
    inst_lines.append(");")

    sections = []
    if wire_lines:
        sections.append("\n".join(wire_lines))
    sections.append("\n".join(inst_lines))
    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Port I/O table (io mode)
# ---------------------------------------------------------------------------

def format_io(result):
    # type: (Dict[str, Any]) -> str
    """Generate port I/O table from parse result.

    Terminal table with Name, Width, Dir, Category columns.
    Groups are separated by blank lines when direction changes.
    """
    from .data_model import ModuleInfo
    mod = result.get("_module_info")  # type: ModuleInfo
    if mod is None:
        return _red("No module info for io table")

    ports = mod.ports
    if not ports:
        return _yellow("Module '%s' has no ports." % mod.name)

    lines = [_bold("Port I/O Table: %s (%d ports)" % (_cyan(mod.name), len(ports))), ""]

    # Build rows with direction grouping
    rows = []
    last_dir = None
    for p in ports:
        dir_str = p.direction.value
        if last_dir is not None and dir_str != last_dir:
            rows.append(["", "", "", ""])  # blank separator
        last_dir = dir_str

        dir_short = {"input": "I", "output": "O", "inout": "IO"}.get(dir_str, dir_str)
        width_str = str(p.width)
        cat = p.category.value
        rows.append([p.name, width_str, dir_short, cat])

    lines.append(_table(["Name", "Width", "Dir", "Category"], rows, indent=2))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Full terminal report
# ---------------------------------------------------------------------------

def format_result(result, mode="full"):
    # type: (Dict[str, Any], str) -> str
    """Format the full analysis result for terminal display.

    Respects *mode* to show only relevant sections.
    """
    sections = []

    # Error in result?
    if "error" in result:
        return _red("Error: %s" % result["error"])

    # Single-module modes
    if mode == "inst":
        return format_inst(result)
    if mode == "io":
        return format_io(result)

    sections.append(format_modules_summary(result))

    if mode in ("hierarchy", "filelist", "full"):
        h = format_hierarchy(result)
        if h:
            sections.append(h)

    if mode in ("ports", "full"):
        p = format_ports(result)
        if p:
            sections.append(p)

    if mode in ("filelist", "full"):
        f = format_filelist(result)
        if f:
            sections.append(f)

    errs = format_errors(result)
    if errs:
        sections.append(errs)

    return "\n\n".join(s for s in sections if s)
