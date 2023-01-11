// Copyright 2021-2023 Datum Technology Corporation
// SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


`ifndef __HELLO_WORLD_TEST_SV__
`define __HELLO_WORLD_TEST_SV__


/**
 * Prints 'Hello, World' during run_phase().
 */
class hello_world_test_c extends uvm_test;

   `uvm_component_utils(hello_world_test_c)

   function new(string name="hello_world_test", uvm_component parent=null);
      super.new(name, parent);
   endfunction

   virtual task run_phase(uvm_phase phase);
      phase.raise_objection(this);
      #(1_000 * 1ns);
      `uvm_info("TEST", "Hello, World!", UVM_NONE)
      #(1_000 * 1ns);
      phase.drop_objection(this);
   endtask

endclass : hello_world_test_c


`endif // __HELLO_WORLD_TEST_SV__
