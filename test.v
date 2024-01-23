//-----------------------------------------------------------------------------
// The confidential and proprietary information contained in this file may
// only be used by a person authorised under and to the extent permitted
// by a subsisting licensing agreement from ARM Limited.
//
//            (C) COPYRIGHT 2012-2013 ARM Limited.
//                ALL RIGHTS RESERVED
//
// This entire notice must be reproduced on all copies of this file
// and copies of this file may only be made by a person if such person is
// permitted to do so under the terms of a subsisting license agreement
// from ARM Limited.
//
//      SVN Information
//
//      Checked In          : $Date: 2013-01-10 15:38:18 +0000 (Thu, 10 Jan 2013) $
//
//      Revision            : $Revision: 233272 $
//
//      Release Information : Cortex-M System Design Kit-r1p0-00rel0
//
//-----------------------------------------------------------------------------
//-----------------------------------------------------------------------------
// Abstract : Simple IOP GPIO
//-----------------------------------------------------------------------------
//-------------------------------------
// Programmer's model
// -------------------------------
// 0x000 RW    Data
// 0x004 RW    Data Output latch
// 0x010 RW    Output Enable Set
// 0x014 RW    Output Enable Clear
// 0x018 RW    Alternate Function Set
// 0x01C RW    Alternate Function Clear
// 0x020 RW    Interrupt Enable Set
// 0x024 RW    Interrupt Enable Clear
// 0x028 RW    Interrupt Type Set
// 0x02C RW    Interrupt Type Clear
// 0x030 RW    Interrupt Polarity Set
// 0x034 RW    Interrupt Polarity Clear
// 0x038 R     Interrupt Status
//       W     Interrupt Status Clear
// 0x400 - 0x7FC : Byte 0 masked access
// 0x800 - 0xBFC : Byte 1 masked access
//-------------------------------------
module cmsdk_iop_gpio
  #(// Parameter to define valid bit pattern for Alternate functions
    // If an I/O pin does not have alternate function its function mask
    // can be set to 0 to reduce gate count.
    //
    // By default every bit can have alternate function
    parameter ALTERNATE_FUNC_MASK    = 16'hFFFF,
  
    // Default alternate function settings
    parameter ALTERNATE_FUNC_DEFAULT = 16'h0000,
  
    // By default use little endian
    parameter BE                     = 0,
    parameter IOADDR_WIDTH           = 12,
    parameter GPIO_WIDTH = 16
  )
  
  // --------------------------------------------------------------------------
  // Port Definitions
  // --------------------------------------------------------------------------
  (// Inputs
    input          FCLK,      // Free-running clock
    input          HCLK,      // System clock
    input          HRESETn,   // System reset
    input  signed        i_IOSEL,     // Decode for peripheral
    input  wire [IOADDR_WIDTH-1:0] i_IOADDR,    // I/O transfer address
    input  wire        i_IOWRITE,   // I/O transfer direction
    input  wire [1:0]  i_IOSIZE,    // I/O transfer size
    input  wire        i_IOTRANS,   // I/O transaction
    input  wire [31:0] i_IOWDATA,   // I/O write data bus
  
    input  wire [3:0]  ECOREVNUM, // Engineering-change-order revision bits
  
    input  wire [GPIO_WIDTH-1:0] PORTIN,    // GPIO Interface input
  
    // Outputs
    output wire [31:0] o_IORDATA,   // I/0 read data bus
  
    output wire [15:0] PORTOUT,   // GPIO output
    output wire [15:0] PORTEN,    // GPIO output enable
    output wire [15:0] PORTFUNC,  // Alternate function control
  
    output wire [15:0] GPIOINT,   // Interrupt output for each pin
    output wire o_COMBINT); // Combined interrupt
  
  // The GPIO width by default is 16-bit, but is coded in a way that it is
  // easy to customise the width.
  localparam PortWidth                 = 16;
  // Local parameter for IDs, IO PORT GPIO has part number of 820
  localparam ARM_CMSDK_IOP_GPIO_PID0   = {32'h00000020}; // 0xFE0 : PID 0 IOP GPIO part number[7:0]
  localparam ARM_CMSDK_IOP_GPIO_PID1   = {32'h000000B8}; // 0xFE4 : PID 1 [7:4] jep106_id_3_0. [3:0] part number [11:8]
  localparam ARM_CMSDK_IOP_GPIO_PID2   = {32'h0000001B}; // 0xFE8 : PID 2 [7:4] revision, [3] jedec_used. [2:0] jep106_id_6_4
  localparam ARM_CMSDK_IOP_GPIO_PID3   = {32'h00000000}; // 0xFEC : PID 3
  localparam ARM_CMSDK_IOP_GPIO_PID4   = {32'h00000004}; // 0xFD0 : PID 4
  localparam ARM_CMSDK_IOP_GPIO_PID5   = {32'h00000000}; // 0xFD4 : PID 5
  localparam ARM_CMSDK_IOP_GPIO_PID6   = {32'h00000000}; // 0xFD8 : PID 6
  localparam ARM_CMSDK_IOP_GPIO_PID7   = {32'h00000000}; // 0xFDC : PID 7
  localparam ARM_CMSDK_IOP_GPIO_CID0   = {32'h0000000D}; // 0xFF0 : CID 0
  localparam ARM_CMSDK_IOP_GPIO_CID1   = {32'h000000F0}; // 0xFF4 : CID 1 PrimeCell class
  localparam ARM_CMSDK_IOP_GPIO_CID2   = {32'h00000005}; // 0xFF8 : CID 2
  localparam ARM_CMSDK_IOP_GPIO_CID3   = {32'h000000B1}; // 0xFFC : CID 3
  //    Note : Customer changing the design should modify
  //          - jep106 value (www.jedec.org)
  //          - part number (customer define)
  //          - Optional revision and modification number (e.g. rXpY)
  
  // --------------------------------------------------------------------------
  // Internal wires
  // --------------------------------------------------------------------------
  
  reg [31:0] read_mux;
  reg [31:0] read_mux_le;
  
  // Signals for Control registers
  wire [31:0] reg_datain32;
  wire [PortWidth-1:0] reg_datain;
  wire [PortWidth-1:0] reg_dout;
  wire [PortWidth-1:0] reg_douten;
  wire [PortWidth-1:0] reg_altfunc;
  wire [PortWidth-1:0] reg_inten; // Interrupt enable
  wire [PortWidth-1:0] reg_inttype; // Interrupt edge(1)/level(0)
  wire [PortWidth-1:0] reg_intpol; // Interrupt active level
  wire [PortWidth-1:0] reg_intstat; // interrupt status
  
  // interrupt signals
  wire [PortWidth-1:0] new_raw_int;
  
  wire bigendian;
  reg [31:0] IOWDATALE; // Little endian version of IOWDATA
  
  // Detect a valid write to this slave
  wire write_trans                     = IOSEL & IOWRITE & IOTRANS;
  
  wire [1:0] iop_byte_strobe;
  
  assign bigendian                     = (BE!=0) ? 1'b1 : 1'b0;
  
  // Generate byte strobes to allow the GPIO registers to handle different transfer sizes
  assign iop_byte_strobe[0]            = (IOSIZE[1] | ((IOADDR[1]==1'b0) & IOSIZE[0]) | (IOADDR[1:0]==2'b00)) & IOSEL;
  assign iop_byte_strobe[1]            = (IOSIZE[1] | ((IOADDR[1]==1'b0) & IOSIZE[0]) | (IOADDR[1:0]==2'b01)) & IOSEL;
  
  // Read operation
  always @(IOADDR or reg_datain32 or reg_dout or reg_douten or
      reg_altfunc or reg_inten or reg_inttype or reg_intpol or
      reg_intstat or ECOREVNUM) begin
    case (IOADDR[11:10])
      2'b00: begin
        if (IOADDR[9:6]==4'h0)
          case (IOADDR[5:2])
            4'h0 : read_mux_le      = reg_datain32;
            4'h1 : read_mux_le      = {{32-PortWidth{1'b0}}, reg_dout};
            4'h2, 4'h3: read_mux_le = {32{1'b0}};
            4'h4, 4'h5: read_mux_le = {{32-PortWidth{1'b0}}, reg_douten };
            4'h6, 4'h7: read_mux_le = {{32-PortWidth{1'b0}}, reg_altfunc};
            4'h8, 4'h9: read_mux_le = {{32-PortWidth{1'b0}}, reg_inten };
            4'hA, 4'hB: read_mux_le = {{32-PortWidth{1'b0}}, reg_inttype};
            4'hC, 4'hD: read_mux_le = {{32-PortWidth{1'b0}}, reg_intpol };
            4'hE : read_mux_le      = {{32-PortWidth{1'b0}}, reg_intstat};
            4'hF : read_mux_le      = {32{1'b0}};
            default: read_mux_le    = {32{1'bx}}; // X-propagation if address is X
          endcase
        else
          read_mux_le = {32{1'b0}};
      end
      2'b01: begin
        // lower byte mask read
        read_mux_le = {{24{1'b0}}, (reg_datain32[7:0] & IOADDR[9:2])};
      end
      2'b10: begin
        // upper byte mask read
        read_mux_le = {{16{1'b0}}, (reg_datain32[15:8] & IOADDR[9:2]), {8{1'b0}}};
      end
      2'b11: begin
        if (IOADDR[9:6]==4'hF) // Peripheral IDs and Component IDs.
          case (IOADDR[5:2]) // IOP GPIO has part number of 820
            4'h0, 4'h1,
            4'h2, 4'h3: read_mux_le = {32{1'b0}}; // 0xFC0-0xFCC : not used
            4'h4 : read_mux_le      = ARM_CMSDK_IOP_GPIO_PID4; // 0xFD0 : PID 4
            4'h5 : read_mux_le      = ARM_CMSDK_IOP_GPIO_PID5; // 0xFD4 : PID 5
            4'h6 : read_mux_le      = ARM_CMSDK_IOP_GPIO_PID6; // 0xFD8 : PID 6
            4'h7 : read_mux_le      = ARM_CMSDK_IOP_GPIO_PID7; // 0xFDC : PID 7
            4'h8 : read_mux_le      = ARM_CMSDK_IOP_GPIO_PID0; // 0xFE0 : PID 0 AHB GPIO part number[7:0]
            4'h9 : read_mux_le      = ARM_CMSDK_IOP_GPIO_PID1;
            // 0xFE0 : PID 1 [7:4] jep106_id_3_0. [3:0] part number [11:8]
            4'hA : read_mux_le      = ARM_CMSDK_IOP_GPIO_PID2;
            // 0xFE0 : PID 2 [7:4] revision, [3] jedec_used. [2:0] jep106_id_6_4
            4'hB : read_mux_le      = {ARM_CMSDK_IOP_GPIO_PID3[31:8],ECOREVNUM[3:0], 4'h0};
            // 0xFE0  PID 3 [7:4] ECO revision, [3:0] modification number
            4'hC : read_mux_le      = ARM_CMSDK_IOP_GPIO_CID0; // 0xFF0 : CID 0
            4'hD : read_mux_le      = ARM_CMSDK_IOP_GPIO_CID1; // 0xFF4 : CID 1 PrimeCell class
            4'hE : read_mux_le      = ARM_CMSDK_IOP_GPIO_CID2; // 0xFF8 : CID 2
            4'hF : read_mux_le      = ARM_CMSDK_IOP_GPIO_CID3; // 0xFFC : CID 3
            default: read_mux_le    = {32{1'bx}}; // X-propagation if address is X
          endcase
        // Note : Customer changing the design should modify
        // - jep106 value (www.jedec.org)
        // - part number (customer define)
        // - Optional revision and modification number (e.g. rXpY)
        else
          read_mux_le = {32{1'b0}};
      end
      default: begin
        read_mux_le = {32{1'bx}}; // X-propagation if address is X
      end
    endcase
  end
  
  // endian conversion
  always @(bigendian or IOSIZE or read_mux_le or IOWDATA) begin
    if ((bigendian)&(IOSIZE==2'b10)) begin
      read_mux  = {read_mux_le[ 7: 0],read_mux_le[15: 8],
            read_mux_le[23:16],read_mux_le[31:24]};
      IOWDATALE = {IOWDATA[ 7: 0],IOWDATA[15: 8],IOWDATA[23:16],IOWDATA[ 31:24]};
    end
    else if ((bigendian)&(IOSIZE==2'b01)) begin
      read_mux  = {read_mux_le[23:16],read_mux_le[31:24],
            read_mux_le[ 7: 0],read_mux_le[15: 8]};
      IOWDATALE = {IOWDATA[23:16],IOWDATA[ 31:24],IOWDATA[ 7: 0],IOWDATA[15: 8]};
    end
    else begin
      read_mux  = read_mux_le;
      IOWDATALE = IOWDATA;
    end
  end
  
  // ----------------------------------------------------------
  // Synchronize input with double stage flip-flops
  // ----------------------------------------------------------
  // Signals for input double flop-flop synchroniser
  reg [PortWidth-1:0] reg_in_sync1;
  reg [PortWidth-1:0] reg_in_sync2;
  
  always @(posedge FCLK or negedge HRESETn) begin
    if (~HRESETn) begin
      reg_in_sync1 <= {PortWidth{1'b0}};
      reg_in_sync2 <= {PortWidth{1'b0}};
    end
    else begin
      reg_in_sync1 <= PORTIN;
      reg_in_sync2 <= reg_in_sync1;
    end
  end
  
  assign reg_datain                    = reg_in_sync2;
  // format to 32-bit for data read
  assign reg_datain32                  = {{32-PortWidth{1'b0}},reg_datain};
  
  // ----------------------------------------------------------
  // Data Output register
  // ----------------------------------------------------------
  wire [32:0] current_dout_padded;
  wire [PortWidth-1:0] nxt_dout_padded;
  reg [PortWidth-1:0] reg_dout_padded;
  wire reg_dout_normal_write0;
  wire reg_dout_normal_write1;
  wire reg_dout_masked_write0;
  wire reg_dout_masked_write1;
  
  assign reg_dout_normal_write0        = write_trans &
    ((IOADDR[11:2] == 10'h000)|(IOADDR[11:2] == 10'h001)) & iop_byte_strobe[0];
  assign reg_dout_normal_write1        = write_trans &
    ((IOADDR[11:2] == 10'h000)|(IOADDR[11:2] == 10'h001)) & iop_byte_strobe[1];
  assign reg_dout_masked_write0        = write_trans &
    (IOADDR[11:10] == 2'b01) & iop_byte_strobe[0];
  assign reg_dout_masked_write1        = write_trans &
    (IOADDR[11:10] == 2'b10) & iop_byte_strobe[1];
  
  // padding to 33-bit for easier coding
  assign current_dout_padded           = {{(33-PortWidth){1'b0}},reg_dout};
  
  // byte #0
  assign nxt_dout_padded[7:0]          = // simple write
    (reg_dout_normal_write0) ? IOWDATALE[7:0] :
    // write lower byte with bit mask
    ((IOWDATALE[7:0] & IOADDR[9:2])|(current_dout_padded[7:0] & (~(IOADDR[9:2]))));
  
  // byte #0 registering stage
  always @(posedge HCLK or negedge HRESETn) begin
    if (~HRESETn)
      reg_dout_padded[7:0] <= 8'h00;
    else if (reg_dout_normal_write0 | reg_dout_masked_write0)
      reg_dout_padded[7:0] <= nxt_dout_padded[7:0];
  end
  
  // byte #1
  assign nxt_dout_padded[15:8]         = // simple write
    (reg_dout_normal_write1) ? IOWDATALE[15:8] :
    // write higher byte with bit mask
    ((IOWDATALE[15:8] & IOADDR[9:2])|(current_dout_padded[15:8] & (~(IOADDR[9:2]))));
  
  // byte #1 registering stage
  always @(posedge HCLK or negedge HRESETn) begin
    if (~HRESETn)
      reg_dout_padded[15:8] <= 8'h00;
    else if (reg_dout_normal_write1 | reg_dout_masked_write1)
      reg_dout_padded[15:8] <= nxt_dout_padded[15:8];
  end
  
  assign reg_dout[PortWidth-1:0]       = reg_dout_padded[PortWidth-1:0];
  
  
  // ----------------------------------------------------------
  // Output enable register
  // ----------------------------------------------------------
  
  reg [PortWidth-1:0] reg_douten_padded;
  integer loop1; // loop variable for register
  wire [PortWidth-1:0] reg_doutenclr;
  wire [PortWidth-1:0] reg_doutenset;
  
  
  assign reg_doutenset[7:0]            = ((write_trans == 1'b1) & (IOADDR[11:2] == 10'h004)
      & (iop_byte_strobe[0] == 1'b1)) ? IOWDATALE[7:0] : {8{1'b0}};
  
  assign reg_doutenset[15:8]           = ((write_trans == 1'b1) & (IOADDR[11:2] == 10'h004)
      & (iop_byte_strobe[1] == 1'b1)) ? IOWDATALE[15:8] : {8{1'b0}};
  
  assign reg_doutenclr[7:0]            = ((write_trans == 1'b1) & (IOADDR[11:2] == 10'h005)
      & (iop_byte_strobe[0] == 1'b1)) ? IOWDATALE[7:0] : {8{1'b0}};
  
  assign reg_doutenclr[15:8]           = ((write_trans == 1'b1) & (IOADDR[11:2] == 10'h005)
      & (iop_byte_strobe[1] == 1'b1)) ? IOWDATALE[15:8] : {8{1'b0}};
  
  
  // registering stage
  always @(posedge HCLK or negedge HRESETn) begin
    if (~HRESETn)
      reg_douten_padded <= {PortWidth{1'b0}};
    else
      for (loop1 = 0; loop1 < PortWidth; loop1 = loop1 + 1) begin
        if (reg_doutenset[loop1] | reg_doutenclr[loop1])
          reg_douten_padded[loop1] <= reg_doutenset[loop1];
      end
  end
  
  assign reg_douten[PortWidth-1:0]     = reg_douten_padded[PortWidth-1:0];
  
  
  // ----------------------------------------------------------
  // Alternate function register
  // ----------------------------------------------------------
  
  
  reg [PortWidth-1:0] reg_altfunc_padded;
  integer loop2; // loop variable for register
  wire [PortWidth-1:0] reg_altfuncset;
  wire [PortWidth-1:0] reg_altfuncclr;
  
  assign reg_altfuncset[7:0]           = ((write_trans == 1'b1) & (IOADDR[11:2] == 10'h006)
      & (iop_byte_strobe[0] == 1'b1)) ? IOWDATALE[7:0] : {8{1'b0}};
  
  assign reg_altfuncset[15:8]          = ((write_trans == 1'b1) & (IOADDR[11:2] == 10'h006)
      & (iop_byte_strobe[1] == 1'b1)) ? IOWDATALE[15:8] : {8{1'b0}};
  
  assign reg_altfuncclr[7:0]           = ((write_trans == 1'b1) & (IOADDR[11:2] == 10'h007)
      & (iop_byte_strobe[0] == 1'b1)) ? IOWDATALE[7:0] : {8{1'b0}};
  
  assign reg_altfuncclr[15:8]          = ((write_trans == 1'b1) & (IOADDR[11:2] == 10'h007)
      & (iop_byte_strobe[1] == 1'b1)) ? IOWDATALE[15:8] : {8{1'b0}};
  
  
  // registering stage
  always @(posedge HCLK or negedge HRESETn) begin
    if (~HRESETn)
      reg_altfunc_padded <= ALTERNATE_FUNC_DEFAULT;
    else
      for(loop2 = 0; loop2 < PortWidth; loop2 = loop2 + 1) begin
        if (reg_altfuncset[loop2] | reg_altfuncclr[loop2])
          reg_altfunc_padded[loop2] <= reg_altfuncset[loop2];
      end
  end
  
  assign reg_altfunc[PortWidth-1:0]    = reg_altfunc_padded[PortWidth-1:0] & ALTERNATE_FUNC_MASK;
  
  
  // ----------------------------------------------------------
  // Interrupt enable register
  // ----------------------------------------------------------
  
  reg [PortWidth-1:0] reg_inten_padded;
  integer loop3; // loop variable for register
  wire [PortWidth-1:0] reg_intenset;
  wire [PortWidth-1:0] reg_intenclr;
  
  assign reg_intenset[7:0]             = ((write_trans == 1'b1) & (IOADDR[11:2] == 10'h008)
      & (iop_byte_strobe[0] == 1'b1)) ? IOWDATALE[7:0] : {8{1'b0}};
  
  assign reg_intenset[15:8]            = ((write_trans == 1'b1) & (IOADDR[11:2] == 10'h008)
      & (iop_byte_strobe[1] == 1'b1)) ? IOWDATALE[15:8] : {8{1'b0}};
  
  assign reg_intenclr[7:0]             = ((write_trans == 1'b1) & (IOADDR[11:2] == 10'h009)
      & (iop_byte_strobe[0] == 1'b1)) ? IOWDATALE[7:0] : {8{1'b0}};
  
  assign reg_intenclr[15:8]            = ((write_trans == 1'b1) & (IOADDR[11:2] == 10'h009)
      & (iop_byte_strobe[1] == 1'b1)) ? IOWDATALE[15:8] : {8{1'b0}};
  
  
  // registering stage
  always @(posedge HCLK or negedge HRESETn) begin
    if (~HRESETn)
      reg_inten_padded <= {PortWidth{1'b0}};
    else
      for(loop3 = 0; loop3 < PortWidth; loop3 = loop3 + 1) begin
        if (reg_intenclr[loop3] | reg_intenset[loop3])
          reg_inten_padded[loop3] <= reg_intenset[loop3];
      end
  end
  
  assign reg_inten[PortWidth-1:0]      = reg_inten_padded[PortWidth-1:0];
  
  
  // ----------------------------------------------------------
  // Interrupt Type register
  // ----------------------------------------------------------
  
  reg [PortWidth-1:0] reg_inttype_padded;
  integer loop4; // loop variable for register
  wire [PortWidth-1:0] reg_inttypeset;
  wire [PortWidth-1:0] reg_inttypeclr;
  
  assign reg_inttypeset[7:0]           = ((write_trans == 1'b1) & (IOADDR[11:2] == 10'h00A)
      & (iop_byte_strobe[0] == 1'b1)) ? IOWDATALE[7:0] : {8{1'b0}};
  
  assign reg_inttypeset[15:8]          = ((write_trans == 1'b1) & (IOADDR[11:2] == 10'h00A)
      & (iop_byte_strobe[1] == 1'b1)) ? IOWDATALE[15:8] : {8{1'b0}};
  
  assign reg_inttypeclr[7:0]           = ((write_trans == 1'b1) & (IOADDR[11:2] == 10'h00B)
      & (iop_byte_strobe[0] == 1'b1)) ? IOWDATALE[7:0] : {8{1'b0}};
  
  assign reg_inttypeclr[15:8]          = ((write_trans == 1'b1) & (IOADDR[11:2] == 10'h00B)
      & (iop_byte_strobe[1] == 1'b1)) ? IOWDATALE[15:8] : {8{1'b0}};
  
  
  // registering stage
  always @(posedge HCLK or negedge HRESETn) begin
    if (~HRESETn)
      reg_inttype_padded <= {PortWidth{1'b0}};
    else
      for(loop4 = 0; loop4 < PortWidth; loop4 = loop4 + 1) begin
        if (reg_inttypeset[loop4] | reg_inttypeclr[loop4])
          reg_inttype_padded[loop4] <= reg_inttypeset[loop4];
      end
  end
  
  assign reg_inttype[PortWidth-1:0]    = reg_inttype_padded[PortWidth-1:0];
  
  
  // ----------------------------------------------------------
  // Interrupt Polarity register
  // ----------------------------------------------------------
  
  
  reg [PortWidth-1:0] reg_intpol_padded;
  integer loop5; // loop variable for register
  wire [PortWidth-1:0] reg_intpolset;
  wire [PortWidth-1:0] reg_intpolclr;
  
  assign reg_intpolset[7:0]            = ((write_trans == 1'b1) & (IOADDR[11:2] == 10'h00C)
      & (iop_byte_strobe[0] == 1'b1)) ? IOWDATALE[7:0] : {8{1'b0}};
  
  assign reg_intpolset[15:8]           = ((write_trans == 1'b1) & (IOADDR[11:2] == 10'h00C)
      & (iop_byte_strobe[1] == 1'b1)) ? IOWDATALE[15:8] : {8{1'b0}};
  
  assign reg_intpolclr[7:0]            = ((write_trans == 1'b1) & (IOADDR[11:2] == 10'h00D)
      & (iop_byte_strobe[0] == 1'b1)) ? IOWDATALE[7:0] : {8{1'b0}};
  
  assign reg_intpolclr[15:8]           = ((write_trans == 1'b1) & (IOADDR[11:2] == 10'h00D)
      & (iop_byte_strobe[1] == 1'b1)) ? IOWDATALE[15:8] : {8{1'b0}};
  
  // registering stage
  always @(posedge HCLK or negedge HRESETn) begin
    if (~HRESETn)
      reg_intpol_padded <= {PortWidth{1'b0}};
    else
      for(loop5 = 0; loop5 < PortWidth; loop5 = loop5 + 1) begin
        if (reg_intpolset[loop5] | reg_intpolclr[loop5])
          reg_intpol_padded[loop5] <= reg_intpolset[loop5];
      end
  end
  
  assign reg_intpol[PortWidth-1:0]     = reg_intpol_padded[PortWidth-1:0];
  
  
  // ----------------------------------------------------------
  // Interrupt status/clear register
  // ----------------------------------------------------------
  
  reg [PortWidth-1:0] reg_intstat_padded;
  integer loop6; // loop variable for register
  wire [PortWidth-1:0] reg_intclr_padded;
  wire reg_intclr_normal_write0;
  wire reg_intclr_normal_write1;
  
  wire [PortWidth-1:0] new_masked_int;
  
  assign reg_intclr_normal_write0      = write_trans &
    (IOADDR[11:2] == 10'h00E) & iop_byte_strobe[0];
  assign reg_intclr_normal_write1      = write_trans &
    (IOADDR[11:2] == 10'h00E) & iop_byte_strobe[1];
  
  assign reg_intclr_padded[ 7:0]       = {8{reg_intclr_normal_write0}} & IOWDATALE[ 7:0];
  assign reg_intclr_padded[15:8]       = {8{reg_intclr_normal_write1}} & IOWDATALE[15:8];
  
  assign new_masked_int[PortWidth-1:0] = new_raw_int[PortWidth-1:0] & reg_inten[PortWidth-1:0];
  
  // registering stage
  always @(posedge FCLK or negedge HRESETn) begin
    if (~HRESETn)
      reg_intstat_padded <= {PortWidth{1'b0}};
    else
      for (loop6=0;loop6<PortWidth;loop6=loop6+1) begin
        if (new_masked_int[loop6] | reg_intclr_padded[loop6])
          reg_intstat_padded[loop6] <= new_masked_int[loop6];
      end
  end
  
  assign reg_intstat[PortWidth-1:0]    = reg_intstat_padded[PortWidth-1:0];
  
  // ----------------------------------------------------------
  // Interrupt generation
  // ----------------------------------------------------------
  // reg_datain is the synchronized input
  
  reg [PortWidth-1:0] reg_last_datain; // last state of synchronized input
  wire [PortWidth-1:0] high_level_int;
  wire [PortWidth-1:0] low_level_int;
  wire [PortWidth-1:0] rise_edge_int;
  wire [PortWidth-1:0] fall_edge_int;
  
  // Last input state for edge detection
  always @(posedge FCLK or negedge HRESETn) begin
    if (~HRESETn)
      reg_last_datain <= {PortWidth{1'b0}};
    else if (|reg_inttype)
      reg_last_datain <= reg_datain;
  end
  
  assign high_level_int                = reg_datain & reg_intpol & (~reg_inttype);
  assign low_level_int                 = (~reg_datain) & (~reg_intpol) & (~reg_inttype);
  assign rise_edge_int                 = reg_datain & (~reg_last_datain) & reg_intpol & reg_inttype;
  assign fall_edge_int                 = (~reg_datain) & reg_last_datain & (~reg_intpol) & reg_inttype;
  assign new_raw_int                   = high_level_int | low_level_int | rise_edge_int | fall_edge_int;
  
  // ----------------------------------------------------------
  // Output to external
  // ----------------------------------------------------------
  assign PORTOUT                       = reg_dout;
  assign PORTEN                        = reg_douten;
  assign PORTFUNC                      = reg_altfunc;
  
  assign IORDATA                       = read_mux;
  
  // Connect interrupt signal to top level
  assign GPIOINT                       = reg_intstat;
  assign COMBINT                       = (|reg_intstat);
 
  endmodule
  