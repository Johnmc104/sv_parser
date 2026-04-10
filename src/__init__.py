
"""
sv_parser — Verilog/SystemVerilog RTL structure analysis toolkit.

Modules:
  data_model      Dataclass-based design data structures
  preprocessor    `define / `ifdef / `include text preprocessor
  verilog_parser  ANTLR-based parser producing data_model objects
  rtl_scan        Top-level scanning API (directory → JSON)
"""

from .data_model import (
    PortDirection, PortInfo, ParameterInfo, ConnectionInfo,
    InstanceInfo, WireInfo, ModuleInfo,
)
from .preprocessor import Preprocessor, PreprocessorError
from .verilog_parser import VerilogFileParser
from .rtl_scan import rtl_scan
