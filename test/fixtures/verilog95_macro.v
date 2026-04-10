// Reproduces DW_apb_ssi pattern: Verilog-95 port list + macro widths
// Include file intentionally missing to simulate real scenario

`include "missing_defines.vh"

module dw_ssi_top
  (
   pclk
  ,presetn
  ,paddr
  ,pwdata
  ,prdata
  ,txd
  ,rxd
  );

  input                           pclk;
  input                           presetn;
  input  [`APB_ADDR_WIDTH-1:0]    paddr;
  input  [`APB_DATA_WIDTH-1:0]    pwdata;
  output [`APB_DATA_WIDTH-1:0]    prdata;
  output [`SSI_SPI_MULTIIO-1:0]   txd;
  input  [`SSI_SPI_MULTIIO-1:0]   rxd;

  wire                            wr_en;
  wire [`SSI_ADDR_SLICE_LHS-2:0]  reg_addr;
  wire [`MAX_APB_DATA_WIDTH-1:0]  ipwdata;

  // Instantiation with macro in port connection
  dw_ssi_biu
   U_biu
    (
     .pclk      (pclk)
    ,.presetn   (presetn)
    ,.paddr     (paddr[`SSI_ADDR_SLICE_LHS-1:0])
    ,.pwdata    (pwdata)
    ,.prdata    (prdata)
    ,.wr_en     (wr_en)
    ,.reg_addr  (reg_addr)
    ,.ipwdata   (ipwdata)
    );

  dw_ssi_regfile
   U_regfile
    (
     .pclk     (pclk)
    ,.presetn  (presetn)
    ,.wr_en    (wr_en)
    ,.reg_addr (reg_addr)
    ,.ipwdata  (ipwdata)
    );

  dw_ssi_shift
   U_shift
    (
     .pclk     (pclk)
    ,.presetn  (presetn)
    ,.txd      (txd)
    ,.rxd      (rxd)
    );

endmodule

module dw_ssi_biu (
  input        pclk,
  input        presetn,
  input  [7:0] paddr,
  input  [31:0] pwdata,
  output [31:0] prdata,
  output       wr_en,
  output [3:0] reg_addr,
  output [31:0] ipwdata
);
endmodule

module dw_ssi_regfile (
  input        pclk,
  input        presetn,
  input        wr_en,
  input  [3:0] reg_addr,
  input  [31:0] ipwdata
);
endmodule

module dw_ssi_shift (
  input        pclk,
  input        presetn,
  output       txd,
  input        rxd
);
endmodule
