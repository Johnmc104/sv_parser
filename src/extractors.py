"""
ANTLR AST extraction functions for Verilog constructs.

Standalone functions that take ANTLR parse tree contexts and return
data_model objects.  Used by the module visitor.
"""

from typing import Dict, List

from .ast_utils import range_width
from .data_model import (
    ConnectionInfo,
    InstanceInfo,
    ParameterInfo,
    PortInfo,
    WireInfo,
)
from .port_classify import PortDirection


# ---------------------------------------------------------------------------
# Parameter extraction
# ---------------------------------------------------------------------------

def extract_parameters(param_list_ctx):
    # type: (...) -> List[ParameterInfo]
    """Extract parameters from module_parameter_port_list."""
    params = []  # type: List[ParameterInfo]
    for param_decl in (param_list_ctx.parameter_declaration() or []):
        params.extend(extract_param_assignments(param_decl, "parameter"))
    return params


def extract_param_assignments(ctx, ptype="parameter"):
    # type: (...) -> List[ParameterInfo]
    """Extract parameter assignments from a parameter_declaration."""
    params = []  # type: List[ParameterInfo]
    assign_list = ctx.list_of_param_assignments()
    if assign_list is None:
        return params
    for pa in (assign_list.param_assignment() or []):
        pid = pa.parameter_identifier()
        if pid is None:
            continue
        val_ctx = pa.constant_mintypmax_expression()
        params.append(ParameterInfo(
            name=pid.getText(),
            value=val_ctx.getText() if val_ctx else "",
            param_type=ptype,
        ))
    return params


def extract_localparams(ctx):
    # type: (...) -> List[ParameterInfo]
    """Extract localparams from local_parameter_declaration."""
    params = []  # type: List[ParameterInfo]
    assign_list = ctx.list_of_param_assignments()
    if assign_list is None:
        return params
    for pa in (assign_list.param_assignment() or []):
        pid = pa.parameter_identifier()
        if pid is None:
            continue
        val_ctx = pa.constant_mintypmax_expression()
        params.append(ParameterInfo(
            name=pid.getText(),
            value=val_ctx.getText() if val_ctx else "",
            param_type="localparam",
        ))
    return params


# ---------------------------------------------------------------------------
# Port extraction
# ---------------------------------------------------------------------------

def extract_ports_from_declaration(pd_ctx):
    # type: (...) -> List[PortInfo]
    """Extract ports from a port_declaration context."""
    inout = pd_ctx.inout_declaration()
    inp = pd_ctx.input_declaration()
    outp = pd_ctx.output_declaration()

    if inout:
        return extract_input_inout_ports(inout, PortDirection.INOUT)
    elif inp:
        return extract_input_inout_ports(inp, PortDirection.INPUT)
    elif outp:
        return extract_output_ports(outp)
    return []


def extract_input_inout_ports(decl_ctx, direction):
    # type: (...) -> List[PortInfo]
    """Extract ports from input_declaration or inout_declaration."""
    net_type = decl_ctx.net_type().getText() if decl_ctx.net_type() else ""
    signed = "signed" if any(
        c.getText() == "signed" for c in decl_ctx.getChildren()
    ) else ""

    range_ctx = decl_ctx.range_()
    width, range_spec = range_width(range_ctx)

    type_str = " ".join(filter(None, [net_type, signed])).strip()

    ports = []  # type: List[PortInfo]
    id_list = decl_ctx.list_of_port_identifiers()
    if id_list:
        for pid in (id_list.port_identifier() or []):
            ports.append(PortInfo(
                name=pid.getText(),
                direction=direction,
                width=width,
                range_spec=range_spec,
                net_type=type_str,
            ))
    return ports


def extract_output_ports(decl_ctx):
    # type: (...) -> List[PortInfo]
    """Extract ports from output_declaration."""
    direction = PortDirection.OUTPUT

    range_ctx = decl_ctx.range_()
    width, range_spec = range_width(range_ctx)

    # Determine net type from AST children (not text matching)
    net_type_parts = []
    if decl_ctx.net_type():
        net_type_parts.append(decl_ctx.net_type().getText())
    if any(c.getText() == "reg" for c in decl_ctx.getChildren()):
        net_type_parts.append("reg")
    if any(c.getText() == "signed" for c in decl_ctx.getChildren()):
        net_type_parts.append("signed")
    if decl_ctx.output_variable_type():
        net_type_parts.append(decl_ctx.output_variable_type().getText())

    type_str = " ".join(net_type_parts).strip()

    ports = []  # type: List[PortInfo]

    id_list = decl_ctx.list_of_port_identifiers()
    if id_list:
        for pid in (id_list.port_identifier() or []):
            ports.append(PortInfo(
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
                ports.append(PortInfo(
                    name=pid.getText(),
                    direction=direction,
                    width=width,
                    range_spec=range_spec,
                    net_type=type_str,
                ))
    return ports


# ---------------------------------------------------------------------------
# Instance extraction
# ---------------------------------------------------------------------------

def extract_instances(mi_ctx):
    # type: (...) -> List[InstanceInfo]
    """Extract instances from module_instantiation context."""
    mod_id = mi_ctx.module_identifier()
    if mod_id is None:
        return []
    module_type = mod_id.getText()

    # Parameter overrides
    params = {}  # type: Dict[str, str]
    pva = mi_ctx.parameter_value_assignment()
    if pva:
        lpa = pva.list_of_parameter_assignments()
        if lpa:
            for npa in (lpa.named_parameter_assignment() or []):
                pid = npa.parameter_identifier()
                expr = npa.mintypmax_expression()
                if pid:
                    params[pid.getText()] = expr.getText() if expr else ""
            for idx, opa in enumerate(
                lpa.ordered_parameter_assignment() or []
            ):
                expr = opa.expression()
                if expr:
                    params["#%d" % idx] = expr.getText()

    instances = []  # type: List[InstanceInfo]
    for mi in (mi_ctx.module_instance() or []):
        nomi = mi.name_of_module_instance()
        if nomi is None:
            continue
        inst_id = nomi.module_instance_identifier()
        inst_name = inst_id.getText() if inst_id else nomi.getText()

        connections = _extract_connections(mi)

        instances.append(InstanceInfo(
            instance_name=inst_name,
            module_type=module_type,
            connections=connections,
            parameters=dict(params),
        ))
    return instances


def _extract_connections(mi_ctx):
    # type: (...) -> List[ConnectionInfo]
    """Extract port connections from a module_instance."""
    connections = []  # type: List[ConnectionInfo]
    lpc = mi_ctx.list_of_port_connections()
    if not lpc:
        return connections

    for npc in (lpc.named_port_connection() or []):
        pid = npc.port_identifier()
        expr = npc.expression()
        if pid:
            connections.append(ConnectionInfo(
                port_name=pid.getText(),
                signal_expr=expr.getText() if expr else "",
            ))
    for idx, opc in enumerate(lpc.ordered_port_connection() or []):
        expr = opc.expression()
        connections.append(ConnectionInfo(
            port_name="#%d" % idx,
            signal_expr=expr.getText() if expr else "",
        ))
    return connections


# ---------------------------------------------------------------------------
# Wire / reg extraction
# ---------------------------------------------------------------------------

def extract_wires_from_net_decl(ctx):
    # type: (...) -> List[WireInfo]
    """Extract wire declarations from net_declaration."""
    range_ctx = ctx.range_()
    width, range_spec = range_width(range_ctx)

    wires = []  # type: List[WireInfo]

    id_list = ctx.list_of_net_identifiers()
    if id_list:
        for nid in (id_list.net_id() or []):
            net_ident = nid.net_identifier()
            if net_ident:
                wires.append(WireInfo(
                    name=net_ident.getText(),
                    width=width,
                    range_spec=range_spec,
                ))

    assign_list = ctx.list_of_net_decl_assignments()
    if assign_list:
        for nda in (assign_list.net_decl_assignment() or []):
            net_ident = nda.net_identifier()
            if net_ident:
                wires.append(WireInfo(
                    name=net_ident.getText(),
                    width=width,
                    range_spec=range_spec,
                ))
    return wires


def extract_wires_from_reg_decl(ctx):
    # type: (...) -> List[WireInfo]
    """Extract reg declarations from reg_declaration."""
    range_ctx = ctx.range_()
    width, range_spec = range_width(range_ctx)

    wires = []  # type: List[WireInfo]
    var_list = ctx.list_of_variable_identifiers()
    if var_list:
        for vt in (var_list.variable_type() or []):
            vid = vt.variable_identifier()
            if vid:
                wires.append(WireInfo(
                    name=vid.getText(),
                    width=width,
                    range_spec=range_spec,
                ))
    return wires
