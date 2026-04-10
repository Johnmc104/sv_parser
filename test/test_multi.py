"""Comprehensive test: Preprocessor + Multi-module + Instances + Classification"""
import sys
sys.path.insert(0, '.')

from src.verilog_parser import VerilogFileParser
from src.preprocessor import Preprocessor

print("=" * 60)
print("TEST 2: Preprocessor + Multi-module with instances")
print("=" * 60)

rtl = """`define DATA_W 8
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

pp = Preprocessor()
pp.add_define("SYNTHESIS")

parser = VerilogFileParser(preprocessor=pp)
mods = parser.parse_text(rtl, "test_multi.v")

mod_map = {m.name: m for m in mods}
print("Modules found:", [m.name for m in mods])
assert len(mods) == 3, "Expected 3 modules, got %d" % len(mods)

# --- sub_fifo ---
fifo = mod_map["sub_fifo"]
print("\n[sub_fifo]")
print("  params:", [(p.name, p.value) for p in fifo.parameters])
assert len(fifo.parameters) == 2
assert fifo.parameters[1].value == "8", "DATA_W macro not expanded: got %s" % fifo.parameters[1].value
print("  ports (%d):" % len(fifo.ports))
for p in fifo.ports:
    print("    %s %s w=%d %s" % (p.direction.value, p.name, p.width, p.range_spec))
assert len(fifo.ports) == 8

wire_names = [w.name for w in fifo.wires]
print("  wires:", wire_names)
print("  sub_fifo OK")

# --- sub_arbiter ---
arb = mod_map["sub_arbiter"]
print("\n[sub_arbiter]")
cls = arb.classify_ports()
print("  dft:", cls["dft"])
print("  irq:", cls["interrupts"])
assert "scan_en" in cls["dft"], "scan_en not classified as DFT"
assert "irq_out" in cls["interrupts"], "irq_out not classified as interrupt"
print("  sub_arbiter OK")

# --- top_chip ---
top = mod_map["top_chip"]
print("\n[top_chip]")
print("  ports: %d (%din/%dout/%dio)" % (
    len(top.ports), len(top.input_ports), len(top.output_ports), len(top.inout_ports)))
print("  instances: %d" % len(top.instances))

for inst in top.instances:
    print("  inst: %s (%s)" % (inst.instance_name, inst.module_type))
    print("    params:", inst.parameters)
    print("    conns:", [(c.port_name, c.signal_expr) for c in inst.connections])

assert len(top.instances) == 2
assert top.instances[0].instance_name == "u_fifo"
assert top.instances[0].module_type == "sub_fifo"
assert top.instances[0].parameters == {"DEPTH": "FIFO_DEPTH", "WIDTH": "8"}
assert len(top.instances[0].connections) == 8
assert top.instances[1].instance_name == "u_arb"
assert top.instances[1].module_type == "sub_arbiter"

# Port classification
cls = top.classify_ports()
print("\n  Port classification:")
print("    clocks:", [c["port"] for c in cls["clocks"]])
print("    resets:", [r["port"] for r in cls["resets"]])
print("    dft:", cls["dft"])
print("    irq:", cls["interrupts"])
assert any(c["port"] == "sys_clk" for c in cls["clocks"])
assert any(c["port"] == "tck" for c in cls["clocks"])
assert any(r["port"] == "sys_rst_n" for r in cls["resets"])

# Hierarchy check
assert top.instantiated_modules == {"sub_fifo", "sub_arbiter"}
print("  top_chip OK")

if parser.errors:
    print("\nParser errors:", parser.errors)

print("\n" + "=" * 60)
print("ALL TESTS PASSED")
print("=" * 60)
