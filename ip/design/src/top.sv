// Copyright 2022 Datum Technology Corporation
// SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


`ifndef __TOP_SV__
`define __TOP_SV__


/**
 * Empty synchronous digital design.
 */
module top(input clk, reset_n);

   always @(posedge clk) begin
      if (reset_n === 0) begin
         // Reset variables ...
      end
      else if (reset_n === 1) begin
         // Do stuff ...
      end
   end

endmodule : top


`endif // __TOP_SV__
