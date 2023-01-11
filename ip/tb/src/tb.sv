// Copyright 2021-2023 Datum Technology Corporation
// SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


`ifndef __TB_SV__
`define __TB_SV__


timeunit       1ns;
timeprecision  1ps;


import uvm_pkg::*;
`include "uvm_macros.svh"
`include "hello_world_test.sv"


/**
 * Test bench top.
 */
module tb;

   logic  clk, reset_n;
   top    dut(.*);

   initial begin
      clk = 0;
      forever begin
         #(10ns);
         clk = !clk;
      end
   end

   initial begin
      reset_n = 0;
      #(100ns);
      reset_n = 1;
   end

   initial begin
      uvm_top.run_test();
   end

endmodule: tb


`endif // __TB_SV__
