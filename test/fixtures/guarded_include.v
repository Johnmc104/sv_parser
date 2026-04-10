// Regression test: include inside ifdef guard + Verilog-95 ports + macro widths
// Simulates DW_apb_ssi pattern where include files with guards define macros
`include "guarded_defs.vh"

module guarded_top
  (
   clk
  ,rst_n
  ,data_in
  ,data_out
  );

  input                          clk;
  input                          rst_n;
  input  [`MY_DATA_WIDTH-1:0]    data_in;
  output [`MY_DATA_WIDTH-1:0]    data_out;

  wire [`MY_ADDR_WIDTH-1:0] addr;

  guarded_sub U_sub (
    .clk      (clk),
    .rst_n    (rst_n),
    .addr     (addr),
    .data_in  (data_in),
    .data_out (data_out)
  );

endmodule

module guarded_sub (
  input        clk,
  input        rst_n,
  input  [7:0] addr,
  input  [31:0] data_in,
  output [31:0] data_out
);
endmodule
