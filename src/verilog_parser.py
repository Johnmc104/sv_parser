"""
ANTLR-based Verilog parser that produces data_model objects.

Pipeline:  source text  →  Preprocessor  →  ANTLR Lexer/Parser  →  AST Visitors  →  ModuleInfo list

Supports Verilog-2005 (VerilogParser) grammars.
"""

import os
from typing import List, Optional

from antlr4 import CommonTokenStream, InputStream

from verilog.VerilogLexer import VerilogLexer
from verilog.VerilogParser import VerilogParser  # noqa: E501
from verilog.VerilogParserVisitor import VerilogParserVisitor

# Shorthand for typed rule context list accessors (avoids Pylance issues
# with ANTLR's overloaded methods that return Union[List[T], T]).
_ModItemCtx = VerilogParser.Module_itemContext
_PortDeclCtx = VerilogParser.Port_declarationContext

from .data_model import ModuleInfo
from .extractors import (
    extract_instances,
    extract_localparams,
    extract_param_assignments,
    extract_parameters,
    extract_ports_from_declaration,
    extract_wires_from_net_decl,
    extract_wires_from_reg_decl,
)
from .preprocessor import Preprocessor


# ---------------------------------------------------------------------------
# AST Visitor — thin orchestrator delegating to extractors
# ---------------------------------------------------------------------------

class _ModuleCollector(VerilogParserVisitor):
    """Single-pass visitor that collects all module information."""

    def __init__(self, file_path=""):
        # type: (str) -> None
        self.modules = []  # type: List[ModuleInfo]
        self._file_path = file_path
        self._current = None  # type: Optional[ModuleInfo]

    def visitModule_declaration(self, ctx):
        ident = ctx.module_identifier()
        if ident is None:
            return self.visitChildren(ctx)

        mod = ModuleInfo(
            name=ident.getText(),
            file_path=self._file_path,
            line_number=ctx.start.line if ctx.start else 0,
        )
        self._current = mod

        # parameters from module_parameter_port_list
        param_list = ctx.module_parameter_port_list()
        if param_list:
            mod.parameters.extend(extract_parameters(param_list))

        # ports from list_of_port_declarations (ANSI style)
        port_list = ctx.list_of_port_declarations()
        if port_list:
            for pd in port_list.getTypedRuleContexts(_PortDeclCtx):
                mod.ports.extend(extract_ports_from_declaration(pd))

        # visit module body for instances, non-ANSI ports, wires
        for item in ctx.getTypedRuleContexts(_ModItemCtx):
            self.visit(item)

        self.modules.append(mod)
        self._current = None
        return None

    def visitModule_item(self, ctx):
        mod = self._current
        if mod is None:
            return self.visitChildren(ctx)

        pd = ctx.port_declaration()
        if pd:
            mod.ports.extend(extract_ports_from_declaration(pd))
            return None

        param_decl = ctx.parameter_declaration()
        if param_decl:
            mod.parameters.extend(
                extract_param_assignments(param_decl, "parameter"))
            return None

        return self.visitChildren(ctx)

    def visitModule_or_generate_item(self, ctx):
        mod = self._current
        if mod is None:
            return self.visitChildren(ctx)

        lp = ctx.local_parameter_declaration()
        if lp:
            mod.parameters.extend(extract_localparams(lp))
            return None

        mi = ctx.module_instantiation()
        if mi:
            mod.instances.extend(extract_instances(mi))
            return None

        mgid = ctx.module_or_generate_item_declaration()
        if mgid:
            nd = mgid.net_declaration()
            if nd:
                mod.wires.extend(extract_wires_from_net_decl(nd))
                return None
            rd = mgid.reg_declaration()
            if rd:
                mod.wires.extend(extract_wires_from_reg_decl(rd))
                return None

        return self.visitChildren(ctx)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class VerilogFileParser:
    """
    Parse one or more Verilog files into ModuleInfo objects.

    Integrates preprocessor + ANTLR parsing in a single pipeline.
    """

    def __init__(self, preprocessor=None):
        # type: (Optional[Preprocessor]) -> None
        self.preprocessor = preprocessor or Preprocessor()
        self.errors = []  # type: List[str]

    def parse_file(self, filepath):
        # type: (str) -> List[ModuleInfo]
        """Parse a single Verilog file.  Returns list of modules found."""
        filepath = os.path.abspath(filepath)
        try:
            text = self.preprocessor.process_file(filepath)
        except Exception as e:
            self.errors.append("Preprocess error: %s: %s" % (filepath, e))
            with open(filepath, "r", errors="replace") as f:
                text = f.read()

        return self._parse_text(text, filepath)

    def parse_text(self, text, filename="<string>"):
        # type: (str, str) -> List[ModuleInfo]
        """Parse a Verilog text string."""
        try:
            text = self.preprocessor.process_text(text, filename)
        except Exception as e:
            self.errors.append("Preprocess error: %s: %s" % (filename, e))

        return self._parse_text(text, filename)

    def parse_files(self, filepaths):
        # type: (List[str]) -> List[ModuleInfo]
        """Parse multiple files. Returns all modules found."""
        all_modules = []  # type: List[ModuleInfo]
        for fp in filepaths:
            all_modules.extend(self.parse_file(fp))
        return all_modules

    def _parse_text(self, text, filename):
        # type: (str, str) -> List[ModuleInfo]
        """Run ANTLR lexer + parser + visitor."""
        try:
            lexer = VerilogLexer(InputStream(text))
            stream = CommonTokenStream(lexer)
            parser = VerilogParser(stream)
            parser.removeErrorListeners()

            tree = parser.source_text()

            visitor = _ModuleCollector(file_path=filename)
            visitor.visit(tree)

            return visitor.modules
        except Exception as e:
            self.errors.append("Parse error: %s: %s" % (filename, e))
            return []
