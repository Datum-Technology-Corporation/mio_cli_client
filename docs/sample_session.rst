Sample Session
==============

This section outlines a command listing that should enable you to get an overview of the ``mio`` workflow and its
essential features.  This example assumes you are familiar with CLI basics.


Initialize a new Project
-----------------------------

1. Ensure mio is installed and operational.  Displays basic help text.

  ``mio --help``
  
2. Create project directory and move into it.

  ``mkdir my_mio_project``
  
  ``cd my_mio_project``
  
3. Initialize a new project.  Creates directory structure and mio.toml project file.

  ``mio init``
  
  - Enter name for project ex: "my_project"
  - Enter name for copyright holder ex: "my inc."


Create a new UVM Test Bench
---------------------------

1. Invoke the UVM Block Test Bench Generator.  Alternatively, type "mio new" without parameters and then select item "3" from the menu.

  ``mio new -t block_tb``
  
  - Requests for path, copyright holder and usage license will use the default if left blank (enter key).
  - A block name must be supplied when requested. Ex: "my_block".
  - A descriptive name for the block must be supplied. Ex: "My Example Block".
  - This will generate the following IPs, assuming block name was "my_block":
    
    - Control plane agent (``uvma_my_block_cp``)
    - Data plane input agent (``uvma_my_block_dp_in``)
    - Data plane output agent (``uvma_my_block_dp_out``)
    - UVM Environment (``uvme_my_block``)
    - UVM Test Bench (``uvmt_my_block``)
  
  Note: Each IP directory has a README.md with user instructions and its own descriptor (ip.yml) file.
  

2. Install dependencies from the Moore.io IP marketplace.

  ``mio install uvmt_my_block``
  
  - If you do not yet have a moore.io account, visit https://mooreio.com/account/register and create one.
  - Use the same username and password in response to this command's requests as used for your mio account.

3. View documentation

  ``mio dox uvmt_my_block``
  
  - Generates Doxygen HTML documentation from block test bench IP source code. 
  - See command output for viewing in a browser.
  


Run a simulation
----------------

1. Run a test from the block test bench we generated.

  ``mio sim uvmt_my_block -t rand_stim -s 1 -w -c``
  
  - IP: ``uvmt_my_block``
  - Test Name: ``rand_stim``
  - Seed: ``1``
  - Waveform capture: ``Enabled``
  - Coverage sampling: ``Enabled``


2. View simulation results.
  
  All commands for viewing the results of a single test run are printed automatically to the terminal after simulation
  has ended.
  
  Ex:
  ::
  
    ************************************************************************************************************************
      Simulation results
    ************************************************************************************************************************
    
      Main log: emacs /home/user/my_project/sim/results/uvmt_my_block_rand_stim_1/sim.log &
                gvim  /home/user/my_project/sim/results/uvmt_my_block_rand_stim_1/sim.log &
                vim   /home/user/my_project/sim/results/uvmt_my_block_rand_stim_1/sim.log
    
      Transaction logs: pushd /home/user/my_project/sim/results/uvmt_my_block_rand_stim_1/trn_log
      Test result dir : pushd /home/user/my_project/sim/results/uvmt_my_block_rand_stim_1



Run a regression
-------------------

1. Clean up the work area.

  ``mio clean uvmt_my_block -d``
  
  Deletes all compiled HDL code for block test bench, including external dependencies (aka deep clean).  Whenever you
  encounter unexpected elaboration errors, run an ``mio clean`` command on your IP and try again.

2. Run the "sanity" regression.

  ``mio regr uvmt_my_block sanity``
  
  - Runs the block test suite's "sanity" regression. 
  - See command output for generated report locations (similar to simulation results). Ex:
  
  ::
  
    ************************************************************************************************************************
      'sanity' regression PASSED
    ************************************************************************************************************************
      Duration: 0 hour(s), 0 minute(s), 56 second(s)
    
      HTML report      : firefox /home/user/my_project/sim/sanity_2023_01_15_16_20_00.html &
      Jenkins XML      : cat     /home/user/my_project/sim/sanity_2023_01_15_16_20_00.xml  &
      Results directory: pushd   /home/user/my_project/sim/regressions/uvmt_my_block_sanity/2023_01_15_16_20_00
