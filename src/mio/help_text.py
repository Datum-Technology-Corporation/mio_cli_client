# Copyright 2021-2022 Datum Technology Corporation
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
########################################################################################################################


version = "1.0.4"
version_text = f"Moore.io CLI Client v{version}"




main_help_text = f"""
                                 Moore.io (`mio`) Command Line Interface (CLI) - v{version}
                                      User Manual: https://mio-cli.readthedocs.io/
              https://mooreio.com - Copyright 2021-2022 Datum Technology Corporation - https://datumtc.ca
Usage:
  mio [--version] [--help]
  mio [--wd WD] [--dbg] CMD [OPTIONS]

Options:
  -v, --version
    Prints the mio version and exits.
  
  -h, --help
    Prints the overall synopsis and a list of the most commonly used commands and exits.
    
  -C WD, --wd WD
    Run as if mio was started in WD (Working Directory) instead of the Present Working Directory `pwd`.
   
  --dbg
    Enables debugging outputs from mio.

Full Command List (`mio help CMD` for help on a specific command):
   Help and Shell/Editor Integration
      doctor         Runs a set of checks to ensure mio installation has what it needs to operate properly
      help           Prints documentation for mio commands
   
   Project and Code Management
      init           Starts project creation dialog
      new            Creates new source code via the mio template engine
   
   IP and Credentials Management
      install        Install all IP dependencies from IP Marketplace
      login          Start session with IP Marketplace
      package        Create a compressed (and potentially encrypted) archive of an IP
      publish        Publish IP to IP Marketplace (must have mio admin account)
   
   EDA Automation
      !              Repeat last command
      regr           Runs regression against an IP
      sim            Performs necessary steps to simulate an IP with any simulator
      
   Manage Results and other EDA Tool Outputs
      clean          Manages outputs from tools (other than job results)
      cov            Manages coverage data from EDA tools
      dox            HDL source code documentation generation via Doxygen
      results        Manages results from EDA tools
"""




repeat_help_text = """Moore.io Repeat (!) Command
   Repeats last command ran by mio.  Currently only supports the `sim` command.
   
Usage:
   mio ! CMD [OPTIONS]
   
Options:
   -b, --bwrap  Does not run command, only creates shell script to re-create the command without mio and creates a
                tarball of the project outside the project root directory.  Currently only supports `sim` command.
   
Examples:
   mio sim uvmt_example -t rand_stim -s 1 ; mio ! sim -b  # Run a simulation for `uvmt_example` and create a tarball
                                                          # that can be run by anyone using only bash."""




sim_help_text = """Moore.io Sim(ulation) Command
   Performs necessary steps to run simulation of an IP.  Only supports Digital Logic Simulation for the time being.
   
   While the controls for individual steps (FuseSoC processing, compilation, elaboration and simulation) are exposed, it
   is recommended to let `mio sim` manage this process as much as possible.  In the event of corrupt simulator
   artifacts, see `mio clean`.  Combining any of the step-control arguments (-F, -C, -E, -S) with missing steps can
   result in unpredictable behavior and is not recommended (ex: `-FS` is illegal).
   
   Two types of arguments (--args) can be passed: compilation (+define+NAME[=VALUE]) and simulation (+NAME[=VALUE]).
   
   For running multiple tests in parallel, see `mio regr`.
   
Usage:
   mio sim IP [OPTIONS] [--args ARG ...]
   
Options:
   -t TEST     , --test      TEST       Specify the UVM test to be run.
   -s SEED     , --seed      SEED       Positive Integer. Specify randomization seed  If none is provided, a random one will be picked.
   -v VERBOSITY, --verbosity VERBOSITY  Specifies UVM logging verbosity: none, low, medium, high, debug. [default: medium]
   -e ERRORS   , --errors    ERRORS     Specifies the number of errors at which compilation/elaboration/simulation is terminated.  [default: 10]
   -a APP      , --app       APP        Specifies simulator application to use: viv, mdc, vcs, xcl, qst, riv. [default: viv]
                                        WARNING: Only Vivado is currently supported. VCS and Metrics will be added in the
                                                 near future (2022/08/23).
   -w          , --waves                Enable wave capture to disk.
   -c          , --cov                  Enable code & functional coverage capture.
   -g          , --gui                  Invokes simulator in graphical or 'GUI' mode.
   
   -S   Simulate  target IP.
   -E   Elaborate target IP.
   -C   Compile   target IP.
   -F   Invoke FuseSoC to prepare core(s) for compilation.
   
Examples:
   mio sim uvmt_my_ip -t smoke -s 1 -w -c             # Compile, elaborate and simulate test 'uvmt_my_ip_smoke_test_c'
                                                      # for IP 'uvmt_my_ip' with seed '1' and waves & coverage capture enabled.
   mio sim uvmt_my_ip -t smoke -s 1 --args +NPKTS=10  # Compile, elaborate and simulate test 'uvmt_my_ip_smoke_test_c'
                                                      # for IP 'uvmt_my_ip' with seed '1' and a simulation argument.
   mio sim uvmt_my_ip -S -t smoke -s 42 -v high -g    # Only simulates test 'uvmt_my_ip_smoke_test_c' for IP 'uvmt_my_ip'
                                                      # with seed '42' and UVM_HIGH verbosity using the simulator in GUI mode.
   mio sim uvmt_my_ip -C                              # Only compile 'uvmt_my_ip'.
   mio sim uvmt_my_ip -E                              # Only elaborate 'uvmt_my_ip'.
   mio sim uvmt_my_ip -CE                             # Compile and elaborate 'uvmt_my_ip'."""




regr_help_text = """Moore.io Regr(ession) Command
   Runs a set of tests against a specific IP.  Regressions are described in Test Suite files (`[<target>.]ts.yml`).
   
Usage:
   mio regr IP [TARGET.]REGRESSION [OPTIONS]
   
Options:
   -d, --dry-run  Compiles, elaborates, but only prints the tests mio would normally run (does not actually run them).
   
Examples:
   mio regr uvmt_my_ip sanity            # Run sanity regression for IP 'uvm_my_ip', from test suite 'ts.yml'
   mio regr uvmt_my_ip apb_xc.sanity     # Run sanity regression for IP 'uvm_my_ip', from test suite 'apb_xc.ts.yml'
   mio regr uvmt_my_ip axi_xc.sanity -d  # Dry-run sanity regression for IP 'uvm_my_ip', from test suite 'axi_xc.ts.yml'"""




clean_help_text = """Moore.io Clean Command
   Deletes output artifacts from EDA tools.  Only simulation is currently supported.
   
Usage:
   mio clean IP [OPTIONS]
   
Options:
   -d, --deep  Also clean compiled IP dependencies.
   
Examples:
   mio clean uvmt_my_ip     # Delete compilation, elaboration and simulation binaries for IP 'uvmt_my_ip'
   mio clean uvmt_my_ip -d  # Delete compilation, elaboration and simulation binaries for IP 'uvmt_my_ip' and its dependencies"""




dox_help_text = """Moore.io Dox(ygen) Invokation Command
   Generates reference documentation from IP HDL source code.
   
Usage:
   mio dox IP [OPTIONS]
   
Options:
   
Examples:
   mio dox my_ip  # Generates HTML documentation for IP 'my_ip'"""




init_help_text = """Moore.io Init(ialization) Command
   Creates a new Project skeleton if not already within a Project.  If so, a new IP skeleton is created.
   This is the recommended method for importing code to the Moore.io ecosystem.
   
Usage:
   mio init [OPTIONS]

Options:
   
Examples:
   mio              init  # Create a new empty Project/IP in this location.
   mio -C ~/my_proj init  # Create a new empty Project at a specific location."""




install_help_text = """Moore.io IP Install Command
   Installs an IP and any IPs that it depends on from the Moore.io IP Marketplace (https://mooreio.com).  IPs can be
   installed either locally (PROJECT_ROOT/.mio/vendors) or globally (~/.mio/vendors).
   
Usage:
   mio install IP [OPTIONS]
   
Options:
   -g         , --global             # Installs IP dependencies for all user projects
   -u USERNAME, --username USERNAME  # Specifies Moore.io username (must be combined with -p)
   -p PASSWORD, --password PASSWORD  # Specifies Moore.io password (must be combined with -u)
   
Examples:
   mio install uvmt_my_ip                          # Install IP dependencies for 'uvmt_my_ip' locally.
   mio install uvmt_another_ip                     # Install IP dependencies for 'uvmt_another_ip' globally.
   mio install uvmt_my_ip -u jenkins -p )Kq3)fkqm  # Specify credentials for Jenkins job."""




login_help_text = """Moore.io User Login Command
   Authenticates session with the Moore.io IP Marketplace (https://mooreio.com).
   
Usage:
   mio login [OPTIONS]
   
Options:
   -u USERNAME, --username USERNAME  # Specifies Moore.io username (must be combined with -p)
   -p PASSWORD, --password PASSWORD  # Specifies Moore.io password (must be combined with -u)
   
Examples:
   mio login                          # Asks credentials only if expired (or never entered)
   mio login -u jenkins -p )Kq3)fkqm  # Specify credentials inline"""




publish_help_text = """Moore.io IP Publish Command
   Packages and publishes an IP to the Moore.io IP Marketplace (https://mooreio.com).
   Currently only available to administrator accounts.
   
Usage:
   mio publish IP [OPTIONS]
   
Options:
   -u USERNAME, --username USERNAME  # Specifies Moore.io username (must be combined with -p)
   -p PASSWORD, --password PASSWORD  # Specifies Moore.io password (must be combined with -u)
   -o ORG     , --org      ORG       # Specifies Moore.io IP Marketplace Organization client name.  Commercial IPs only.
   
Examples:
   mio publish uvma_my_ip                               # Publish IP 'uvma_my_ip'.
   mio publish uvma_my_ip -u acme_jenkins -p )Kq3)fkqm  # Specify credentials for Jenkins job.
   mio publish uvma_my_ip -o chip_inc                   # Publish IP 'uvma_my_ip' for client 'chip_inc'."""




package_help_text = """Moore.io IP Package Command
   Command for encrypting/compressing entire IP on local disk.  To enable IP encryption, add an 'encrypted' entry to the
   'hdl-src' section of your descriptor (ip.yml).  Moore.io will only attempt to encrypt using the simulators listed
   under 'simulators-supported' of the 'ip' section.
   
   Vivado requires a key for encryption; please ensure that you have specified your key location either in the project
   or user Configuration file (mio.toml).  https://mooreio-client.readthedocs.io/en/latest/configuration.html#encryption
   for more on the subject.
   
Usage:
   mio package IP DEST [OPTIONS]
   
Options:
   -n, --no-tgz  # Do not create compressed tarball
   
Examples:
   mio package uvma_my_ip ~        # Create compressed archive of IP 'uvma_my_ip' under user's home directory.
   mio package uvma_my_ip ~/ip -n  # Process IP 'uvma_my_ip' but do not create compressed archive."""




new_help_text = """Moore.io New Command
   Invokes the Datum UVM Code Template system.  If no generator name is specified, the user is prompted to select from a
   list of what is currently available: 17 Templates, from advanced agents to tests.
    
Usage:
   mio new [OPTIONS]
   
Options:
   -t TEMPLATE, --template TEMPLATE  Name of template to use: basic_agent, parallel_agent, serial_agent, block_tb, ss_tb,
                                                              lib, ral, comp, obj, reg_adapter, reg_block, reg, seq_lib,
                                                              seq, test, vseq_lib, vseq
Examples:
   mio new              # Invoke the template menu
   mio new -t block_tb  # Create new UVM Block-level UVM Environment+TB along with Control Plane and Data Plane Agents"""




results_help_text = """Moore.io Results Command
   Parses Simulaton results for a target IP and generates both HTML and Jenkins-compatible XML reports.  These reports
   are output into the simulation directory.
   
Usage:
   mio results IP REPORT_NAME [OPTIONS]
   
Options:
   
Examples:
   mio results my_ip sim_results  # Parse simulation results for 'my_ip' and generate reports under 'sim_results' filenames."""




cov_help_text = """Moore.io Cov(erage) Command
   Merges code and functional coverage data into a single database from which report(s) are generated.  These reports
   are output into the simulation directory.  WARNING: Currenly only supports Vivado.
   
Usage:
   mio cov IP [OPTIONS]
   
Options:
   
Examples:
   mio cov my_ip  # Merge coverage data for 'my_ip' and generate a report."""




doctor_help_text = """Moore.io Doctor Command
   Runs a set of checks to ensure mio installation has what it needs to operate properly.
   
Usage:
   mio doctor [OPTIONS]
   
Options:
   
Examples:
   mio doctor"""

