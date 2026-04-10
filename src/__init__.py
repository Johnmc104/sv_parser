"""
sv_parser — Verilog/SystemVerilog RTL structure analysis toolkit.

Modules:
  port_classify   Port direction/category enums and classification
  data_model      Dataclass-based design data structures
  preprocessor    `define / `ifdef / `include text preprocessor
  ast_utils       ANTLR range evaluation helpers
  extractors      ANTLR AST extraction functions
  verilog_parser  ANTLR-based parser producing data_model objects
  file_discovery  RTL file discovery utilities
  hierarchy       Hierarchy and dependency analysis
  rtl_scan        Top-level scanning API (file/dir/filelist → dict/JSON)
  formatter       Terminal-friendly output formatters
"""

from .port_classify import PortDirection, PortCategory, classify_port
from .data_model import (
    PortInfo, ParameterInfo, ConnectionInfo,
    InstanceInfo, WireInfo, ModuleInfo,
)
from .preprocessor import Preprocessor, PreprocessorError
from .verilog_parser import VerilogFileParser
from .rtl_scan import rtl_scan, rtl_scan_json
from .formatter import format_result, format_inst, format_io
