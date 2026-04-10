"""
ANTLR-based Verilog parser that produces data_model objects.

Pipeline:  source text  →  Preprocessor  →  ANTLR Lexer/Parser  →  AST Visitors  →  ModuleInfo list

Supports both Verilog-2005 (VerilogParser) grammars.
"""

import os
import re
from typing import Dict, List, Optional, Tuple

from antlr4 import CommonTokenStream, InputStream

from verilog.VerilogLexer import VerilogLexer
from verilog.VerilogParser import VerilogParser
from verilog.VerilogParserVisitor import VerilogParserVisitor

from .data_model import (
    ConnectionInfo,
    InstanceInfo,
    ModuleInfo,
    ParameterInfo,
    PortDirection,
    PortInfo,
    WireInfo,
)
from .preprocessor import Preprocessor


# ---------------------------------------------------------------------------
# Helper: evaluate simple range expressions
# ---------------------------------------------------------------------------

def _try_eval_range(expr_text: str) -> Optional[int]:
    """Try to evaluate a constant range expression to an integer.

    Handles: plain numbers, PARAM-1 style, simple arithmetic.
    Returns None if evaluation fails (parameterized width kept as text).
    """
    text = expr_text.strip()
    if not text:
        return None
    # Pure number
    if text.isdigit():
        return int(text)
    # Simple arithmetic with only digits and +-*/
    safe = re.sub(r"[0-9+\-*/() ]", "", text)
    if not safe:
        try:
            return int(eval(text))  # safe: only digits and arithmetic ops
        except Exception:
            pass
    return None


def _range_width(range_ctx) -> Tuple[int, str]:
    """Extract width and range_spec from a range_ context.

    Returns (width, range_text).
    """
    if range_ctx is None:
        return 1, ""

    range_text = range_ctx.getText()  # e.g. "[31:0]" or "[IOADDR_WIDTH-1:0]"
    msb_ctx = range_ctx.msb_constant_expression()
    lsb_ctx = range_ctx.lsb_constant_expression()

    if msb_ctx is None or lsb_ctx is None:
        return 1, range_text

    msb_val = _try_eval_range(msb_ctx.getText())
    lsb_val = _try_eval_range(lsb_ctx.getText())

    if msb_val is not None and lsb_val is not None:
        width = abs(msb_val - lsb_val) + 1
    else:
        width = 0  # parameterized — can't compute statically

    return width, range_text


# ---------------------------------------------------------------------------
# AST Visitor — extracts modules, ports, parameters, instances, wires
# ---------------------------------------------------------------------------

class _ModuleCollector(VerilogParserVisitor):
    """Single-pass visitor that collects all module information."""

    def __init__(self, file_path: str = ""):
        self.modules: List[ModuleInfo] = []
        self._file_path = file_path
        self._current: Optional[ModuleInfo] = None

    # --- module scope ---

    def visitModule_declaration(self, ctx: VerilogParser.Module_declarationContext):
        ident = ctx.module_identifier()
        if ident is None:
            return self.visitChildren(ctx)

        name = ident.getText()
        line = ctx.start.line if ctx.start else 0

        mod = ModuleInfo(
            name=name,
            file_path=self._file_path,
            line_number=line,
        )
        self._current = mod

        # parameters from module_parameter_port_list
        param_list = ctx.module_parameter_port_list()
        if param_list:
            self._collect_parameters(param_list)

        # ports from list_of_port_declarations
        port_list = ctx.list_of_port_declarations()
        if port_list:
            self._collect_ports_from_list(port_list)

        # visit module body for instances, port decls in body, wires
        for item in (ctx.module_item() or []):
            self.visit(item)

        self.modules.append(mod)
        self._current = None
        # Don't call visitChildren — we already walked items above
        return None

    # --- parameter collection ---

    def _collect_parameters(self, param_list_ctx):
        """Collect parameters from module_parameter_port_list."""
        for param_decl in (param_list_ctx.parameter_declaration() or []):
            self._add_parameter(param_decl, "parameter")

    def _add_parameter(self, ctx, ptype: str = "parameter"):
        if self._current is None:
            return
        # parameter_declaration has list_of_param_assignments
        assign_list = ctx.list_of_param_assignments()
        if assign_list is None:
            return
        for pa in (assign_list.param_assignment() or []):
            pid = pa.parameter_identifier()
            if pid is None:
                continue
            name = pid.getText()
            val_ctx = pa.constant_mintypmax_expression()
            value = val_ctx.getText() if val_ctx else ""
            self._current.parameters.append(
                ParameterInfo(name=name, value=value, param_type=ptype)
            )

    # --- port collection from ANSI list ---

    def _collect_ports_from_list(self, list_ctx):
        """Collect ports from list_of_port_declarations (ANSI style)."""
        for pd in (list_ctx.port_declaration() or []):
            self._visit_port_declaration(pd)

    def _visit_port_declaration(self, pd_ctx):
        if self._current is None:
            return

        inout = pd_ctx.inout_declaration()
        inp = pd_ctx.input_declaration()
        outp = pd_ctx.output_declaration()

        if inout:
            self._extract_ports(inout, PortDirection.INOUT)
        elif inp:
            self._extract_ports(inp, PortDirection.INPUT)
        elif outp:
            self._extract_ports_output(outp)

    def _extract_ports(self, decl_ctx, direction: PortDirection):
        """Extract ports from inout_declaration or input_declaration."""
        # Grammar: 'input' net_type? 'signed'? range_? list_of_port_identifiers
        net_type = decl_ctx.net_type().getText() if decl_ctx.net_type() else ""
        signed = "signed" if any(c.getText() == "signed" for c in decl_ctx.getChildren()) else ""

        range_ctx = decl_ctx.range_()
        width, range_spec = _range_width(range_ctx)

        type_str = " ".join(filter(None, [net_type, signed])).strip()

        id_list = decl_ctx.list_of_port_identifiers()
        if id_list:
            for pid in (id_list.port_identifier() or []):
                self._current.ports.append(PortInfo(
                    name=pid.getText(),
                    direction=direction,
                    width=width,
                    range_spec=range_spec,
                    net_type=type_str,
                ))

    def _extract_ports_output(self, decl_ctx):
        """Extract ports from output_declaration (more complex due to 'reg')."""
        direction = PortDirection.OUTPUT

        range_ctx = decl_ctx.range_()
        width, range_spec = _range_width(range_ctx)

        # Determine net type from AST children (not text matching)
        net_type_parts = []
        if decl_ctx.net_type():
            net_type_parts.append(decl_ctx.net_type().getText())
        # 'reg' appears as a terminal child in the second alternative:
        #   'output' 'reg' 'signed'? range_? list_of_variable_port_identifiers
        if any(c.getText() == "reg" for c in decl_ctx.getChildren()):
            net_type_parts.append("reg")
        if any(c.getText() == "signed" for c in decl_ctx.getChildren()):
            net_type_parts.append("signed")
        if decl_ctx.output_variable_type():
            net_type_parts.append(decl_ctx.output_variable_type().getText())

        type_str = " ".join(net_type_parts).strip()

        # list_of_port_identifiers or list_of_variable_port_identifiers
        id_list = decl_ctx.list_of_port_identifiers()
        if id_list:
            for pid in (id_list.port_identifier() or []):
                self._current.ports.append(PortInfo(
                    name=pid.getText(),
                    direction=direction,
                    width=width,
                    range_spec=range_spec,
                    net_type=type_str,
                ))

        var_list = decl_ctx.list_of_variable_port_identifiers()
        if var_list:
            for vpid in (var_list.var_port_id() or []):
                pid = vpid.port_identifier()
                if pid:
                    self._current.ports.append(PortInfo(
                        name=pid.getText(),
                        direction=direction,
                        width=width,
                        range_spec=range_spec,
                        net_type=type_str,
                    ))

    # --- body items ---

    def visitModule_item(self, ctx):
        """Visit module body items for ports, instances, wires, params."""
        if self._current is None:
            return self.visitChildren(ctx)

        # port_declaration in body (non-ANSI style)
        pd = ctx.port_declaration()
        if pd:
            self._visit_port_declaration(pd)
            return None

        # parameter_declaration in body
        param_decl = ctx.parameter_declaration()
        if param_decl:
            self._add_parameter(param_decl, "parameter")
            return None

        # Recurse into module_or_generate_item via children
        return self.visitChildren(ctx)

    def visitModule_or_generate_item(self, ctx):
        if self._current is None:
            return self.visitChildren(ctx)

        # local_parameter_declaration
        lp = ctx.local_parameter_declaration()
        if lp:
            self._add_localparam(lp)
            return None

        # module_instantiation
        mi = ctx.module_instantiation()
        if mi:
            self._visit_module_instantiation(mi)
            return None

        # module_or_generate_item_declaration (for net/reg declarations)
        mgid = ctx.module_or_generate_item_declaration()
        if mgid:
            self._visit_item_declaration(mgid)
            return None

        return self.visitChildren(ctx)

    def _add_localparam(self, ctx):
        if self._current is None:
            return
        assign_list = ctx.list_of_param_assignments()
        if assign_list is None:
            return
        for pa in (assign_list.param_assignment() or []):
            pid = pa.parameter_identifier()
            if pid is None:
                continue
            name = pid.getText()
            val_ctx = pa.constant_mintypmax_expression()
            value = val_ctx.getText() if val_ctx else ""
            self._current.parameters.append(
                ParameterInfo(name=name, value=value, param_type="localparam")
            )

    # --- module instantiation ---

    def _visit_module_instantiation(self, ctx):
        """Extract instance info from module_instantiation."""
        if self._current is None:
            return

        mod_id = ctx.module_identifier()
        if mod_id is None:
            return
        module_type = mod_id.getText()

        # parameter overrides
        params: Dict[str, str] = {}
        pva = ctx.parameter_value_assignment()
        if pva:
            lpa = pva.list_of_parameter_assignments()
            if lpa:
                # named parameter assignments
                for npa in (lpa.named_parameter_assignment() or []):
                    pid = npa.parameter_identifier()
                    expr = npa.mintypmax_expression()
                    if pid:
                        params[pid.getText()] = expr.getText() if expr else ""
                # ordered parameter assignments
                for idx, opa in enumerate(lpa.ordered_parameter_assignment() or []):
                    expr = opa.expression()
                    if expr:
                        params[f"#{idx}"] = expr.getText()

        # module_instance entries (usually one, can be multiple)
        for mi in (ctx.module_instance() or []):
            nomi = mi.name_of_module_instance()
            if nomi is None:
                continue
            inst_name = nomi.module_instance_identifier().getText() if nomi.module_instance_identifier() else nomi.getText()

            connections: List[ConnectionInfo] = []
            lpc = mi.list_of_port_connections()
            if lpc:
                # named connections: .port(signal)
                for npc in (lpc.named_port_connection() or []):
                    pid = npc.port_identifier()
                    expr = npc.expression()
                    if pid:
                        connections.append(ConnectionInfo(
                            port_name=pid.getText(),
                            signal_expr=expr.getText() if expr else "",
                        ))
                # ordered connections
                for idx, opc in enumerate(lpc.ordered_port_connection() or []):
                    expr = opc.expression()
                    connections.append(ConnectionInfo(
                        port_name=f"#{idx}",
                        signal_expr=expr.getText() if expr else "",
                    ))

            self._current.instances.append(InstanceInfo(
                instance_name=inst_name,
                module_type=module_type,
                connections=connections,
                parameters=dict(params),
            ))

    # --- wire / reg declarations ---

    def _visit_item_declaration(self, ctx):
        """Extract wire/reg declarations from module_or_generate_item_declaration."""
        if self._current is None:
            return

        nd = ctx.net_declaration()
        if nd:
            self._extract_wires_from_net_decl(nd)
            return

        rd = ctx.reg_declaration()
        if rd:
            self._extract_wires_from_reg_decl(rd)
            return

    def _extract_wires_from_net_decl(self, ctx):
        range_ctx = ctx.range_()
        width, range_spec = _range_width(range_ctx)

        # list_of_net_identifiers
        id_list = ctx.list_of_net_identifiers()
        if id_list:
            for nid in (id_list.net_id() or []):
                net_ident = nid.net_identifier()
                if net_ident:
                    self._current.wires.append(WireInfo(
                        name=net_ident.getText(),
                        width=width,
                        range_spec=range_spec,
                    ))

        # list_of_net_decl_assignments
        assign_list = ctx.list_of_net_decl_assignments()
        if assign_list:
            for nda in (assign_list.net_decl_assignment() or []):
                net_ident = nda.net_identifier()
                if net_ident:
                    self._current.wires.append(WireInfo(
                        name=net_ident.getText(),
                        width=width,
                        range_spec=range_spec,
                    ))

    def _extract_wires_from_reg_decl(self, ctx):
        range_ctx = ctx.range_()
        width, range_spec = _range_width(range_ctx)

        var_list = ctx.list_of_variable_identifiers()
        if var_list:
            for vt in (var_list.variable_type() or []):
                vid = vt.variable_identifier()
                if vid:
                    self._current.wires.append(WireInfo(
                        name=vid.getText(),
                        width=width,
                        range_spec=range_spec,
                    ))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class VerilogFileParser:
    """
    Parse one or more Verilog files into ModuleInfo objects.

    Integrates preprocessor + ANTLR parsing in a single pipeline.
    """

    def __init__(self, preprocessor: Optional[Preprocessor] = None):
        self.preprocessor = preprocessor or Preprocessor()
        self.errors: List[str] = []

    def parse_file(self, filepath: str) -> List[ModuleInfo]:
        """Parse a single Verilog file.  Returns list of modules found."""
        filepath = os.path.abspath(filepath)
        try:
            text = self.preprocessor.process_file(filepath)
        except Exception as e:
            self.errors.append(f"Preprocess error: {filepath}: {e}")
            # Fallback: read raw file
            with open(filepath, "r", errors="replace") as f:
                text = f.read()

        return self._parse_text(text, filepath)

    def parse_text(self, text: str, filename: str = "<string>") -> List[ModuleInfo]:
        """Parse a Verilog text string."""
        try:
            text = self.preprocessor.process_text(text, filename)
        except Exception as e:
            self.errors.append(f"Preprocess error: {filename}: {e}")

        return self._parse_text(text, filename)

    def parse_files(self, filepaths: List[str]) -> List[ModuleInfo]:
        """Parse multiple files. Returns all modules found."""
        all_modules: List[ModuleInfo] = []
        for fp in filepaths:
            all_modules.extend(self.parse_file(fp))
        return all_modules

    def _parse_text(self, text: str, filename: str) -> List[ModuleInfo]:
        """Run ANTLR lexer + parser + visitor."""
        try:
            lexer = VerilogLexer(InputStream(text))
            stream = CommonTokenStream(lexer)
            parser = VerilogParser(stream)

            # Suppress ANTLR error output; collect errors instead
            parser.removeErrorListeners()

            tree = parser.source_text()

            visitor = _ModuleCollector(file_path=filename)
            visitor.visit(tree)

            return visitor.modules
        except Exception as e:
            self.errors.append(f"Parse error: {filename}: {e}")
            return []
