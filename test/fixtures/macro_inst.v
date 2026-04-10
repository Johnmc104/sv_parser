// Test fixture: module with macro-containing instantiations
// Simulates DW_apb_ssi pattern where macros are used in port connections

`define DATA_WIDTH 32
`define ADDR_SLICE_LHS 11
`define ADDR_SLICE_RHS 2

module sub_biu (
    input        clk,
    input        rst_n,
    input  [31:0] wdata,
    output [31:0] rdata
);
endmodule

module sub_regfile (
    input        clk,
    input        rst_n,
    input  [7:0] addr,
    output [31:0] data_out
);
endmodule

module sub_txrx (
    input        clk,
    input        rst_n,
    input  [7:0] fifo_depth
);
endmodule

module top_with_macros (
    input         PCLK,
    input         PRESETn,
    input  [31:0] PWDATA,
    output [31:0] PRDATA,
    output        ssi_txd
);

wire [31:0] w_rdata;
wire [31:0] w_wdata;

// Instantiation with macros in port connections (like DW_apb_ssi)
sub_biu U_biu (
    .clk   (PCLK),
    .rst_n (PRESETn),
    .wdata (PWDATA[`DATA_WIDTH-1:0]),
    .rdata (w_rdata)
);

sub_regfile U_regfile (
    .clk      (PCLK),
    .rst_n    (PRESETn),
    .addr     (PWDATA[`ADDR_SLICE_LHS:`ADDR_SLICE_RHS]),
    .data_out (PRDATA)
);

// Undefined macro (simulates missing include)
sub_txrx U_txrx (
    .clk        (PCLK),
    .rst_n      (PRESETn),
    .fifo_depth (`UNDEFINED_FIFO_DEPTH)
);

endmodule
