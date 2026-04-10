"""Comprehensive test: Preprocessor + Multi-module + Instances + Classification."""
from src.verilog_parser import VerilogFileParser
from src.preprocessor import Preprocessor

RTL_SOURCE = """\
`define DATA_W 8
`define ADDR_W 4

`ifdef SYNTHESIS
  `define TECH_CELL sky130
`else
  `define TECH_CELL generic
`endif

module sub_fifo #(
  parameter DEPTH = 16,
  parameter WIDTH = `DATA_W
)(
  input              clk,
  input              rst_n,
  input  [WIDTH-1:0] din,
  input              wr_en,
  input              rd_en,
  output [WIDTH-1:0] dout,
  output             full,
  output             empty
);
  reg [`ADDR_W-1:0] wr_ptr, rd_ptr;
  wire [`ADDR_W:0] count;
endmodule

module sub_arbiter (
  input        clk,
  input        scan_en,
  input  [3:0] req,
  output [3:0] gnt,
  output       irq_out
);
  wire scan_chain;
endmodule

module top_chip #(
  parameter FIFO_DEPTH = 32
)(
  input              sys_clk,
  input              sys_rst_n,
  input              tck,
  input              tms,
  input              tdi,
  output             tdo,
  input  [7:0]       data_in,
  output [7:0]       data_out,
  inout  [3:0]       gpio,
  output             chip_irq
);
  wire [7:0] fifo_dout;
  wire fifo_full, fifo_empty;
  wire [3:0] arb_gnt;

  sub_fifo #(
    .DEPTH(FIFO_DEPTH),
    .WIDTH(8)
  ) u_fifo (
    .clk    (sys_clk),
    .rst_n  (sys_rst_n),
    .din    (data_in),
    .wr_en  (1'b1),
    .rd_en  (~fifo_empty),
    .dout   (fifo_dout),
    .full   (fifo_full),
    .empty  (fifo_empty)
  );

  sub_arbiter u_arb (
    .clk     (sys_clk),
    .scan_en (1'b0),
    .req     (gpio),
    .gnt     (arb_gnt),
    .irq_out (chip_irq)
  );

  assign data_out = fifo_dout;
endmodule
"""


def _parse_multi():
    pp = Preprocessor()
    pp.add_define("SYNTHESIS")
    parser = VerilogFileParser(preprocessor=pp)
    return parser.parse_text(RTL_SOURCE, "test_multi.v")


def test_module_count():
    mods = _parse_multi()
    assert len(mods) == 3
    names = [m.name for m in mods]
    assert "sub_fifo" in names
    assert "sub_arbiter" in names
    assert "top_chip" in names


def test_sub_fifo():
    mods = _parse_multi()
    fifo = {m.name: m for m in mods}["sub_fifo"]
    assert len(fifo.parameters) == 2
    # DATA_W macro should be expanded to 8
    assert fifo.parameters[1].value == "8"
    assert len(fifo.ports) == 8
    wire_names = [w.name for w in fifo.wires]
    assert "wr_ptr" in wire_names
    assert "rd_ptr" in wire_names


def test_sub_arbiter_classification():
    mods = _parse_multi()
    arb = {m.name: m for m in mods}["sub_arbiter"]
    cls = arb.classify_ports()
    assert "scan_en" in cls["dft"]
    assert "irq_out" in cls["interrupts"]


def test_top_chip_ports():
    mods = _parse_multi()
    top = {m.name: m for m in mods}["top_chip"]
    assert len(top.ports) == 10
    assert len(top.input_ports) == 6
    assert len(top.output_ports) == 3
    assert len(top.inout_ports) == 1


def test_top_chip_instances():
    mods = _parse_multi()
    top = {m.name: m for m in mods}["top_chip"]
    assert len(top.instances) == 2

    u_fifo = top.instances[0]
    assert u_fifo.instance_name == "u_fifo"
    assert u_fifo.module_type == "sub_fifo"
    assert u_fifo.parameters == {"DEPTH": "FIFO_DEPTH", "WIDTH": "8"}
    assert len(u_fifo.connections) == 8

    u_arb = top.instances[1]
    assert u_arb.instance_name == "u_arb"
    assert u_arb.module_type == "sub_arbiter"


def test_top_chip_classification():
    mods = _parse_multi()
    top = {m.name: m for m in mods}["top_chip"]
    cls = top.classify_ports()
    assert any(c["port"] == "sys_clk" for c in cls["clocks"])
    assert any(c["port"] == "tck" for c in cls["clocks"])
    assert any(r["port"] == "sys_rst_n" for r in cls["resets"])


def test_top_chip_hierarchy():
    mods = _parse_multi()
    top = {m.name: m for m in mods}["top_chip"]
    assert top.instantiated_modules == {"sub_fifo", "sub_arbiter"}
