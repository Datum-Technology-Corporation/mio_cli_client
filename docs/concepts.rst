Concepts
========


Project
-------

A Project is a collection of IPs and the directories where simulation, linting, synthesis and other EDA task results are
stored.  A Project Descriptor file (``mio.toml``) in the root directory defines metadata specific for the Project.


Sample Descriptor
*****************
::

  [project]
  name        = "my_chip"
  full-name   = "My Chip"
  description = "My big, beautiful chip"



Directory Structure
*******************
Moore.io stores its internal files under ``$PROJECT_ROOT_DIR/.mio/``.  These files are to be considered read-only and should
not be modified.  Any changes can lead to unpredictable behavior.  It is highly recommended to add this directory to
your ``.gitignore``.

IPs are by default stored under ``rtl`` and ``dv``.  These names are arbitrary and there is no obligation to store a
particular type of IP in one or the other.

Each EDA task has its own directory, for results and reports:

- Logic/Analog/Mixed-Signal Simulation - ``sim`` by default
- Linting - ``lint`` by default
- Synthesis - ``syn`` by default
- Design for test - ``dft`` by default
- Formal verification - ``fml`` by default
- Place and route - ``pnr`` by default
- Physical layout - ``lay`` by default

MIO downloads and stores IP code in the Project (``$PROJECT_ROOT_DIR/.mio/vendors``) for `local` IP installations and
under ``~/.mio/vendors`` for `global` installations to store oft-used libraries in a more central location.


IP
--
An IP is a described collection of source code, directories, and associated documentation files.  This descriptor is
captured using YAML and has a standard structure, regardless of its content.

Sample Descriptors
******************

DV
--

The following is an IP descriptor for an IP called 'Datapath Sub-System Test Bench'::

  ip:
    name     : uvmt_dp_ss
    vendor   : acme
    version  : 1.1.2
    full-name: Datapath Sub-System Test Bench
    type     : dv
    sub-type : uvm_tb
  
  dependencies:
    "@accellera/uvm"  :  "1.2"
    "@datum/uvml"     : "~1.0"
    "@datum/uvml_logs": "~1.0"
    "@datum/uvma_axil": "~1.0"
    "@acme/uvme_dp_ss": "~1.0"
  
  structure:
    scripts-path : "bin"
    docs-path    : "docs"
    examples-path: "examples"
    src-path     : "src"
  
  hdl-src:
    directories        : [".", "tb", "tests"]
    top-files          : ["uvmt_dp_ss_pkg.sv"]
    top-constructs     : ["uvmt_dp_ss_tb", "uvml.uvml_sim_summary", "dp_ss.glbl"]
    so-libs            : ["wht_model"]
    tests-path         : "tests"
    tests-name-template: "uvmt_dp_ss_{{ name }}_test_c"

  dut:
    name: "@big-chip/dp_ss"

Design
------

The following is an IP descriptor for a Vivado Project called 'Datapath Sub-System'::

  ip:
     name     : dp_ss
     vendor   : big-chip
     version  : 2.1.4
     full-name: Datapath Sub-System
     type     : rtl
     sub-type : vivado
  
  structure:
     src-path: "xsim"
  
  hdl-src:
     directories: [".", "srcs"]
  
  viv-project:
    name: "dp_ss"
    libs: ["xil_defaultlib", "unisims_ver", "unimacro_ver", "secureip", "xpm"]
    vlog: "vlog.prj"
    vhdl: "vhdl.prj"


Structure
*********

The standard structure is defined below:

- ``ip`` - Catalog information

  - ``name`` - `String` - (Short) Name
  - ``vendor`` - `String` - (Short) Name of the Organization/User owning this IP.
  - ``version`` - `String` - Semver version tag
  - ``full-name`` - `String` - Descriptive name
  - ``type`` - `Enum` - IP Type [``DV``, ``RTL``]
  - ``sub-type`` -  `Enum`
  
    - For RTL [``FLIST``, ``VIVADO``]
    - For DV [``UVM_AGENT``, ``UVM_ENV``, ``UVM_TB``, ``UVM_LIB``, ``UVM_VKIT``, ``UVM_OTHER``, ``VMM``, ``OVM``, ``OTHER``].


- ``dependencies`` - `List` - IP dependencies.  Can include both local (project) and external (from Moore.io IP catalog).

  - ``"@<Vendor>/<IP Name>" : "<Version>"`` - Where ``<IP Name>`` is the (short) name of an IP and ``<Version>`` is the required version of that IP specified via semver.

- ``structure`` - Paths for directory structure.

  - ``scripts-path`` - `String` - Location of scripts and misc. files.
  - ``docs-path`` - `String` - Location of documents for Doxygen to use when generating its reference documentation contents. Articles can be added by adding markdown (.md) files in this directory.
  - ``examples-path`` - `String` - Location of sample code for users and can be incorporated into Doxygen documentation.
  - ``src-path`` - `String` - Location of IP source code.

- ``hdl-src`` - Describes Hardware Description Language source code structure and data for compilation and simulation.

  - ``directories`` - `List` - Paths where source code is located, relative to ``src-path``. "``.``" equates the source directory root.
  - ``top-files`` - `List` - Path to top HDL source file(s) for compilation.
  - ``top-constructs`` - `List` - Name of top-level HDL module(s) for elaboration.  For module(s) outside the specified IP, the format is ``<ip name>.<module name>``.
  - ``so-libs`` - `List` - Name of DPI libraries to be loaded.  These must be located in the ``scripts-path`` directory of the IP.  Filename convention is ``<name>.<simulator>.so`` where ``simulator`` is one of ``viv``, ``vcs``, ``mtr``, ``qst``, ``xcl``, ``riv``.
  - ``tests-path`` - `String` - Path to tests source code files.  `Test Bench IPs only.`
  - ``tests-name-template`` - `String` - `Jinja <https://palletsprojects.com/p/jinja/>`_ template with single argument: ``name`` describing the test naming convention for this IP.  `Test Bench IPs only.`
  - ``flist`` - `Dictionary` - Optional.  Specifies which filelist to use when compiling in each simulator.  Using this feature is discouraged, as ``mio`` assembles filelists on the fly before executing jobs.

    - ``<Simulator> : "<Filelist Path>"`` - Where ``<Simulator>`` is [``mtr``, ``riv``, ``qst``, ``vcs``, ``viv``, ``xcl``] and ``<Filelist Path>`` is the path to the filelist from the root of the source directory.

- ``dut`` - For Test Bench (DV) IPs, the section describes the Device Under Test.

  - ``ip-type`` - `Enum` - If DUT is not an IP, specify its type here [``fsoc``]
  - ``name`` - `String` - IP (Short) Name or FuseSoC Core (short) name.
  - ``full-name`` - `String` - FuseSoC Core fully specified name. `FuseSoC DUTs only.`
  - ``target`` - `String` - FuseSoC Core target to be used. `FuseSoC DUTs only.`

- ``viv-project`` - For Vivado Project IP.

  - ``name`` - `Enum` - Name (aka 'lib') of Vivado project.
  - ``libs`` - `List` - List of Vivado libraries needed by Vivado project.
  - ``vlog`` - `String` - Path to (System)Verilog Vivado project file.
  - ``vhdl`` - `String` - Path to VHDL Vivado project file.



IP Marketplace
--------------
The Moore.io IP Marketplace hosts the IP catalog and its source code.  Developers interact with the marketplace primarily
via ``mio login``, ``mio install`` and ``mio publish`` as well as the IP documentation provided online.

License Types
*************
- Free & Open Source (FOS) - Free to list.  Source code and documentation stored on the Marketplace.
- Commercial - IPs that use the Moore.io IP Licensing System to charge end-user for IP.  Encrypted source code and
  documentation are stored on the Marketplace.
- Private - List encrypted repository information for organizations' IP, visible only to internal users.  This allows
  `mio` to resolve dependencies outside the Marketplace catalog.  No Source code is stored on the Marketplace.
  Free for organizations under 10 users.  `Not yet implemented`.




Configuration Space
-------------------
As mentioned in the high-level description, the Configuration space is loaded from multiple ``mio.toml`` files which are
merged into a final configuration space. This information is then used in all further MIO operations.  The full
Configuration Space is detailed in its own section.




Test Suite
----------
Moore.io's regression system flips the script on the usual regression bash scripts of old.  Instead, Test Suite
descriptors (``ts.yml`` for default (single) target IPs, ``<target>.ts.yml`` for multiple target IPs) describe several
regressions at once, with an inside-out approach of Test Sets and Test Groups.  Test Suites must be stored under
``tests-path``, as defined in the IP Descriptor.

Sample Descriptor
*****************
::

  test-suite:
    info:
       name: Data Sub-System Test Suite for APB interconnect
       ip: uvmt_data_ss
    target:
       cmp-args : ["+define+XC=APB"]
       elab-args: []
       sim-args : []
    settings:
       waves: [sanity, bugs]
       cov  : [nightly, weekly]
       verbosity:
          sanity : high
          nightly: medium
          weekly : low
          bugs   : debug
       max-duration:
          sanity :  1
          nightly:  5
          weekly : 12
          bugs   :  1
       max-jobs:
          sanity :  5
          nightly: 10
          weekly : 20
          bugs   :  1
  
  functional:
     datapath:
        rand_traffic:
           sanity : [1]
           nightly: 10
           weekly :
              seeds: 50
              args : ["+NUM_PKTS=500"]
           weekly :
              seeds: 50
              args : ["+NUM_PKTS=1000"]
           bugs: [5456984234547]
     registers:
        reg_hw_reset:
           sanity: [1]
           nightly: 1
           weekly: 1
           bugs: []
        reg_bit_bash:
           sanity: [1]
           nightly: 1
           weekly: 1
           bugs: []
  
  error:
     datapath:
        rand_err_traffic:
           sanity : [1]
           nightly: 10
           weekly :
              seeds: 5
              args : ["+MIN_PKT_SZ=64","+MAX_PKT_SZ=127"]
           weekly :
              seeds: 10
              args : ["+MIN_PKT_SZ=128","+MAX_PKT_SZ=255"]
           weekly :
              seeds: 30
              args : ["+MIN_PKT_SZ=256","+MAX_PKT_SZ=511"]
           weekly :
              seeds: 55
              args : ["+MIN_PKT_SZ=512","+MAX_PKT_SZ=2048"]
           bugs: [
              8438499331868,
              7945216883479,
              2496127794534,
              9652178425414,
              3486521841268
           ]

  

Structure
*********
All test suites have 2 sections.  The metadata and the regression definitions.  ``mio`` does not currently interface with
scheduling engines such as GRID or LSF, but plans to in the near future.

The ``max-duration`` feature allows ``mio`` to prematurely end regressions via a hard time limit.  Simulations processes
are simply killed off.  The regression report will list these as ``FAILED - ABORTED``.


Metadata
^^^^^^^^
This section of the test suite contains the information necessary to run the regressions.

- ``test-suite`` - Test Suite Metadata
  
  - ``info`` - General Information
    
    - ``name`` - `String` - Descriptive name.  Ex: "Data Sub-System Test Suite for APB interconnect"
    - ``ip`` - `String` - Owner IP.  Ex: "uvmt_data_ss"
    
  - ``target`` - Target Specifications
    
    - ``cmp-args`` - `String[]` - Compilation arguments.  Ex: ``["+define+XC=APB"]``
    - ``elab-args`` - `String[]` - Elaboration arguments.  Ex: ``["-L apb_lib"]``
    - ``sim-args`` - `String[]` - Simulation arguments.  Ex: ``["+NUM_PKTS=100"]``
  
  - ``settings`` - Regression Parameters
    
    - ``waves`` - `String[]` - List of regressions for which wave capture is enabled.  Ex: ``[sanity, bugs]``
    - ``cov`` - `String[]` - List of regressions for which coverage sampling is enabled.  Ex: ``[nightly, weekly]``
    - ``verbosity`` - `String[String]` - Dictionary mapping each regression with a UVM logging verbosity level.  Ex: ``{sanity:high, nightly:medium}``
    - ``max-duration`` - `Integer[String]` - Dictionary mapping each regression with a timeout (specified in hours).  Ex: ``{sanity:1, nightly:5}``
    - ``max-jobs`` - `Integer[String]` - Dictionary mapping each regression with a limit on concurrent simulations.  Ex: ``{sanity:5, nightly:10}``

Regressions Definition
^^^^^^^^^^^^^^^^^^^^^^
This section of the test suite defines the contents of the regressions.

- Test Set - Ex: ``functional`` - Top-level elements; encapsulate test groups.
  
  - Test Group - Ex: ``registers`` - Used to sort tests into features.
    
    - Test - Ex: ``reg_bit_bash`` - The name of the test used must match what would be entered on the command line.
      
      - Regression Entry - `String` - Regression name.  Ex: ``sanity``
        
        - Without arguments
          
          - `Integer` - Specifies the amount of random seeds to run.  Ex: ``100``
          - `OR`
          - `Integer[]` - Specifies a list of seeds to be run.  Ex: ``[1,42,73]``
        
        - With arguments
          
          - `seeds` - `Integer` or `Integer[]` - Former specifies the amount of random seeds to run; latter specifies a list of seeds to be run.  Ex: ``100`` or ``[1,42]``
          - `args` - `String []` - List of arguments to be passed.  Ex: ``["+ASYNC_RESET","+NUM_PKTS=100"]``

