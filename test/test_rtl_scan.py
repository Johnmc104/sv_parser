"""Test rtl_scan with a real multi-file directory."""
import os
import shutil

import pytest

from src.rtl_scan import rtl_scan

TMPDIR = "/tmp/test_rtl_scan"


@pytest.fixture(autouse=True)
def setup_tmpdir():
    """Create and clean up temp RTL directory for each test."""
    if os.path.exists(TMPDIR):
        shutil.rmtree(TMPDIR)
    os.makedirs(TMPDIR)

    # File 1: sub modules
    with open(os.path.join(TMPDIR, "sub_modules.v"), "w") as f:
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
    with open(os.path.join(TMPDIR, "top.v"), "w") as f:
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
    with open(os.path.join(TMPDIR, "soc_top_tb.v"), "w") as f:
        f.write("""
module soc_top_tb;
  reg clk; initial clk = 0; always #5 clk = ~clk;
endmodule
""")

    yield

    shutil.rmtree(TMPDIR, ignore_errors=True)


def _scan(**kwargs):
    defaults = {"directory": TMPDIR, "mode": "full", "defines": {"USE_PLL": ""}}
    defaults.update(kwargs)
    return rtl_scan(**defaults)


def test_modules_found():
    result = _scan()
    mod_names = [m["name"] for m in result["modules"]]
    assert "soc_top" in mod_names
    assert "clk_div" in mod_names
    assert "uart_tx" in mod_names
    assert "pll_wrapper" in mod_names


def test_testbench_excluded():
    result = _scan()
    mod_names = [m["name"] for m in result["modules"]]
    assert "soc_top_tb" not in mod_names


def test_top_detection():
    result = _scan()
    assert result["top"] == "soc_top"


def test_hierarchy():
    result = _scan()
    hierarchy = result["hierarchy"]
    assert "soc_top" in hierarchy
    h = hierarchy["soc_top"]
    inst_modules = [i["module"] for i in h["instances"]]
    assert "clk_div" in inst_modules
    assert "uart_tx" in inst_modules


def test_filelist_order():
    result = _scan()
    fl = result["filelist_info"]
    assert fl["order"] == "bottom-up"
    files = fl["filelist"]
    basenames = [os.path.basename(f) for f in files if not f.startswith("+incdir+")]
    if "sub_modules.v" in basenames and "top.v" in basenames:
        assert basenames.index("sub_modules.v") < basenames.index("top.v")


def test_port_classification():
    result = _scan()
    cls = result.get("port_classification", {})
    assert any(c["port"] == "sys_clk" for c in cls["clocks"])
    assert any(r["port"] == "sys_rst_n" for r in cls["resets"])
    assert "scan_mode" in cls["dft"]


def test_no_unresolved():
    result = _scan()
    assert result["unresolved"] == []


def test_excluded_contains_tb():
    result = _scan()
    excluded = result["filelist_info"].get("excluded", [])
    assert any("soc_top_tb" in e for e in excluded)


def test_single_file_mode():
    """Test scanning a single file."""
    fpath = os.path.join(TMPDIR, "sub_modules.v")
    result = rtl_scan(file=fpath, mode="modules")
    mod_names = [m["name"] for m in result["modules"]]
    assert "clk_div" in mod_names
    assert "uart_tx" in mod_names


def test_inst_mode():
    """Test inst mode on a single file."""
    fpath = os.path.join(TMPDIR, "sub_modules.v")
    result = rtl_scan(file=fpath, mode="inst", top_module="uart_tx")
    assert "module" in result
    assert result["top"] == "uart_tx"
