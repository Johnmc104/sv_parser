"""
Dataclass-based design data structures for RTL analysis.

Provides: PortInfo, ParameterInfo, ConnectionInfo, InstanceInfo,
           WireInfo, ModuleInfo  (and helper enums / functions).
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PortDirection(Enum):
    INPUT = "input"
    OUTPUT = "output"
    INOUT = "inout"


class PortCategory(Enum):
    """Port classification for SDC / constraint generation."""
    CLOCK = "clock"
    RESET = "reset"
    DFT = "dft"
    INTERRUPT = "interrupt"
    DATA = "data"


# ---------------------------------------------------------------------------
# Port classification helpers
# ---------------------------------------------------------------------------

_CLK_RE = re.compile(
    r'(^|_)(clk|clock|pclk|hclk|aclk|fclk|tck|sclk|mclk|gclk|rclk)($|_|\d)',
    re.IGNORECASE,
)
_RST_RE = re.compile(
    r'(^|_)(rst|reset|presetn|hresetn|aresetn)($|_|n\b)',
    re.IGNORECASE,
)
_DFT_RE = re.compile(
    r'(^|_)(scan|dft|jtag|tms|tdi|tdo|trst|bist|mbist)($|_)',
    re.IGNORECASE,
)
_IRQ_RE = re.compile(
    r'(^|_)(intr|irq|interrupt)($|_)|int_req',
    re.IGNORECASE,
)


def classify_port(name: str) -> PortCategory:
    """Classify a port by naming convention."""
    if _CLK_RE.search(name):
        return PortCategory.CLOCK
    if _RST_RE.search(name):
        return PortCategory.RESET
    if _DFT_RE.search(name):
        return PortCategory.DFT
    if _IRQ_RE.search(name):
        return PortCategory.INTERRUPT
    return PortCategory.DATA


def detect_reset_active_low(name: str) -> bool:
    """True if the reset signal is active-low (ends with _n / n)."""
    return bool(re.search(r'(_n|resetn|rstn)$', name, re.IGNORECASE))


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class PortInfo:
    name: str
    direction: PortDirection
    width: int = 1
    range_spec: str = ""      # original range text, e.g. "[31:0]"
    net_type: str = ""        # wire / reg / logic / signed …
    comment: str = ""

    @property
    def category(self) -> PortCategory:
        return classify_port(self.name)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "name": self.name,
            "direction": self.direction.value,
            "width": self.width,
        }
        if self.range_spec:
            d["range"] = self.range_spec
        if self.net_type:
            d["type"] = self.net_type
        return d


@dataclass
class ParameterInfo:
    name: str
    value: str = ""
    param_type: str = "parameter"   # parameter | localparam

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "value": self.value, "type": self.param_type}


@dataclass
class ConnectionInfo:
    port_name: str
    signal_expr: str = ""     # expression text connected to port

    def to_dict(self) -> Dict[str, Any]:
        return {"port": self.port_name, "signal": self.signal_expr}


@dataclass
class InstanceInfo:
    instance_name: str
    module_type: str
    connections: List[ConnectionInfo] = field(default_factory=list)
    parameters: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "instance": self.instance_name,
            "module": self.module_type,
        }
        if self.parameters:
            d["parameters"] = self.parameters
        if self.connections:
            d["connections"] = [c.to_dict() for c in self.connections]
        return d


@dataclass
class WireInfo:
    name: str
    width: int = 1
    range_spec: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"name": self.name, "width": self.width}
        if self.range_spec:
            d["range"] = self.range_spec
        return d


@dataclass
class ModuleInfo:
    """Complete information about one Verilog/SystemVerilog module."""
    name: str
    file_path: str = ""
    line_number: int = 0
    ports: List[PortInfo] = field(default_factory=list)
    parameters: List[ParameterInfo] = field(default_factory=list)
    instances: List[InstanceInfo] = field(default_factory=list)
    wires: List[WireInfo] = field(default_factory=list)

    # --- derived helpers ---

    @property
    def port_names(self) -> List[str]:
        return [p.name for p in self.ports]

    @property
    def input_ports(self) -> List[PortInfo]:
        return [p for p in self.ports if p.direction == PortDirection.INPUT]

    @property
    def output_ports(self) -> List[PortInfo]:
        return [p for p in self.ports if p.direction == PortDirection.OUTPUT]

    @property
    def inout_ports(self) -> List[PortInfo]:
        return [p for p in self.ports if p.direction == PortDirection.INOUT]

    @property
    def instantiated_modules(self) -> Set[str]:
        return {inst.module_type for inst in self.instances}

    def classify_ports(self) -> Dict[str, Any]:
        """Classify ports by naming convention."""
        clocks = []
        resets = []
        dft: List[str] = []
        interrupts: List[str] = []
        data_inputs: List[str] = []
        data_outputs: List[str] = []

        for p in self.ports:
            cat = p.category
            if cat == PortCategory.CLOCK:
                clocks.append({
                    "port": p.name,
                    "direction": p.direction.value,
                })
            elif cat == PortCategory.RESET:
                resets.append({
                    "port": p.name,
                    "direction": p.direction.value,
                    "active": "low" if detect_reset_active_low(p.name) else "high",
                })
            elif cat == PortCategory.DFT:
                dft.append(p.name)
            elif cat == PortCategory.INTERRUPT:
                interrupts.append(p.name)
            else:
                if p.direction == PortDirection.INPUT:
                    data_inputs.append(p.name)
                elif p.direction == PortDirection.OUTPUT:
                    data_outputs.append(p.name)
                else:
                    data_inputs.append(p.name)

        return {
            "clocks": clocks,
            "resets": resets,
            "dft": dft,
            "interrupts": interrupts,
            "data_inputs": data_inputs,
            "data_outputs": data_outputs,
        }

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "name": self.name,
            "file": self.file_path,
            "line": self.line_number,
            "type": "module",
            "parameters": [p.name for p in self.parameters],
            "ports": {
                "inputs": [p.name for p in self.input_ports],
                "outputs": [p.name for p in self.output_ports],
                "inouts": [p.name for p in self.inout_ports],
            },
        }
        return d

    def to_full_dict(self) -> Dict[str, Any]:
        """Full serialization including instances and wires."""
        d = self.to_dict()
        d["ports_detail"] = [p.to_dict() for p in self.ports]
        d["parameters_detail"] = [p.to_dict() for p in self.parameters]
        d["instances"] = [i.to_dict() for i in self.instances]
        if self.wires:
            d["wires"] = [w.to_dict() for w in self.wires]
        return d
