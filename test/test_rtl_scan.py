"""Test rtl_scan with a real multi-file directory."""
import sys, os, json, shutil
sys.path.insert(0, '.')

from src.rtl_scan import rtl_scan

print("=" * 60)
print("TEST 3: rtl_scan directory scan + hierarchy + filelist")
print("=" * 60)

# Create temp RTL directory
tmpdir = "/tmp/test_rtl_scan"
if os.path.exists(tmpdir):
    shutil.rmtree(tmpdir)
os.makedirs(tmpdir)

# File 1: sub modules
with open(os.path.join(tmpdir, "sub_modules.v"), "w") as f:
    f.write("""
module clk_div #(parameter DIV = 2)(
  input  clk_in,
  input  rst_n,
  output reg clk_out
);
  reg [7:0] cnt;
  always @(posedge clk_in or negedge rst_n)
    if (!rst_n) begin cnt <= 0; clk_out <= 0; end
    else if (cnt == DIV/2 - 1) begin cnt <= 0; clk_out <= ~clk_out; end
    else cnt <= cnt + 1;
endmodule

module uart_tx (
  input        clk,
  input        rst_n,
  input  [7:0] tx_data,
  input        tx_valid,
  output       tx_serial,
  output       tx_busy
);
  wire baud_tick;
endmodule
""")

# File 2: top with `define and `ifdef
with open(os.path.join(tmpdir, "top.v"), "w") as f:
    f.write("""`define BAUD_DIV 868

`ifdef USE_PLL
module pll_wrapper(input clk_in, output clk_out);
endmodule
`endif

module soc_top (
  input        sys_clk,
  input        sys_rst_n,
  input        scan_mode,
  input  [7:0] uart_din,
  input        uart_wr,
  output       uart_txd,
  output       uart_busy_irq
);

  wire slow_clk;

  clk_div #(.DIV(`BAUD_DIV)) u_clk_div (
    .clk_in  (sys_clk),
    .rst_n   (sys_rst_n),
    .clk_out (slow_clk)
  );

  uart_tx u_uart (
    .clk       (slow_clk),
    .rst_n     (sys_rst_n),
    .tx_data   (uart_din),
    .tx_valid  (uart_wr),
    .tx_serial (uart_txd),
    .tx_busy   (uart_busy_irq)
  );

endmodule
""")

# File 3: testbench (should be excluded)
with open(os.path.join(tmpdir, "soc_top_tb.v"), "w") as f:
    f.write("""
module soc_top_tb;
  reg clk; initial clk = 0; always #5 clk = ~clk;
endmodule
""")

# Run rtl_scan (returns dict directly)
result = rtl_scan(
    tmpdir,
    mode="full",
    defines={"USE_PLL": ""},
)

print("\n--- JSON result (condensed) ---")
print("Modules:", [m["name"] for m in result["modules"]])
print("Top:", result.get("top"))
print("Hierarchy keys:", list(result.get("hierarchy", {}).keys()))
print("Unresolved:", result.get("unresolved"))
print("Filelist:", result.get("filelist_info", {}).get("filelist"))
print("Excluded:", result.get("filelist_info", {}).get("excluded"))

# Assertions
mod_names = [m["name"] for m in result["modules"]]
assert "soc_top" in mod_names
assert "clk_div" in mod_names
assert "uart_tx" in mod_names
assert "pll_wrapper" in mod_names, "ifdef USE_PLL should include pll_wrapper"
assert "soc_top_tb" not in mod_names, "Testbench should be excluded"

assert result["top"] == "soc_top", "Top should be soc_top, got %s" % result["top"]

hierarchy = result["hierarchy"]
assert "soc_top" in hierarchy
h = hierarchy["soc_top"]
inst_modules = [i["module"] for i in h["instances"]]
assert "clk_div" in inst_modules
assert "uart_tx" in inst_modules

# Filelist should be bottom-up: sub_modules first, then top
fl = result["filelist_info"]
assert fl["order"] == "bottom-up"
files = fl["filelist"]
file_basenames = [os.path.basename(f) for f in files if not f.startswith("+incdir+")]
print("File order:", file_basenames)
# clk_div and uart_tx should come before soc_top
if "sub_modules.v" in file_basenames and "top.v" in file_basenames:
    assert file_basenames.index("sub_modules.v") < file_basenames.index("top.v"), \
        "Bottom-up order: sub_modules.v should come before top.v"

# Port classification
cls = result.get("port_classification", {})
print("\nPort classification:")
print("  clocks:", [c["port"] for c in cls.get("clocks", [])])
print("  resets:", [r["port"] for r in cls.get("resets", [])])
print("  dft:", cls.get("dft", []))
print("  irq:", cls.get("interrupts", []))
assert any(c["port"] == "sys_clk" for c in cls["clocks"])
assert any(r["port"] == "sys_rst_n" for r in cls["resets"])
assert "scan_mode" in cls["dft"]

# Excluded should contain the tb file
excluded = fl.get("excluded", [])
print("Excluded:", excluded)

# Unresolved should be empty (all modules defined)
assert result["unresolved"] == [], "Should have no unresolved, got %s" % result["unresolved"]

# pll_wrapper is defined but not instantiated — it's another top candidate
# but soc_top should still be chosen as top (more instances)

# Cleanup
shutil.rmtree(tmpdir)

print("\n" + "=" * 60)
print("ALL TESTS PASSED")
print("=" * 60)
