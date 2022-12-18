Commands
========

All commands can be prepended by ``--dbg`` to enable mio's debug printout.  If you encounter an issue, re-run the
command with debug enabled and attach the printout to your ticket when you
`file a bug <https://github.com/Datum-Technology-Corporation/mio_client/issues>`_.


Credentials Management
----------------------

login
*****

Description
^^^^^^^^^^^
Authenticates session with the Moore.io IP Marketplace (https://mooreio.com).

Usage
^^^^^
``mio login [OPTIONS]``

Options
^^^^^^^
===============  =========
``-u USERNAME``  ``--username USERNAME``  Specifies Moore.io username (must be combined with ``-p``)
``-p PASSWORD``  ``--password PASSWORD``  Specifies Moore.io password (must be combined with ``-u``)
===============  =========

Examples
^^^^^^^^
=====================================  ========
``mio login``                          Asks credentials only if expired (or never entered)
``mio login -u jenkins -p )Kq3)fkqm``  Specify credentials inline
=====================================  ========



Documentation
-------------

dox
***

Description
^^^^^^^^^^^
Generates reference documentation from IP HDL source code using Doxygen.

Usage
^^^^^
``mio dox IP [OPTIONS]``

Options
^^^^^^^
None for the time being.

Examples
^^^^^^^^
=================  ===============
``mio dox my_ip``  Generates HTML documentation for IP ``my_ip``
=================  ===============


help
****

Description
^^^^^^^^^^^
Displays documentation for a specific mio command.

Usage
^^^^^
``mio help CMD``

Options
^^^^^^^
None

Examples
^^^^^^^^
================  =====
``mio help sim``  Prints documentation for the ``sim`` command.
================  =====



EDA
---

regr
****

Description
^^^^^^^^^^^
Runs a regression (set of tests) against a specific IP.  Regressions are described in Test Suite files (``[<target>.]ts.yml``).

Usage
^^^^^
``mio regr IP [TARGET.]REGRESSION [OPTIONS]``

Options
^^^^^^^
======  =============  =============================================
``-d``  ``--dry-run``  Compiles, elaborates, but only prints the tests mio would normally run (does not actually run them).
======  =============  =============================================

Examples
^^^^^^^^
========================================  =====================
``mio regr uvmt_my_ip sanity``            Run sanity regression for IP ``uvm_my_ip``, from test suite ``ts.yml``
``mio regr uvmt_my_ip apb_xc.sanity``     Run sanity regression for IP ``uvm_my_ip``, from test suite ``apb_xc.ts.yml``
``mio regr uvmt_my_ip axi_xc.sanity -d``  Dry-run sanity regression for IP ``uvm_my_ip``, from test suite ``axi_xc.ts.yml``
========================================  =====================



repeat
******

Description
^^^^^^^^^^^
Repeats last command ran by mio.  Currently only supports Bubble-Wrap (--bwrap) usage for sending bug report tarballs to EDA vendors.  Currently only supported for `sim` command.

Usage
^^^^^
``mio ! CMD [OPTIONS]``

Options
^^^^^^^
================  =========================  ===========================
``-b``            ``--bwrap``                Does not run command, only creates shell script to re-create the command without mio and creates a tarball of the project in the project root directory.  Currently only supports `sim` command.
================  =========================  ===========================

Examples
^^^^^^^^
==========================================================  =============
``mio sim uvmt_example -t rand_stim -s 1 ; mio ! sim -b``   Run a simulation for `uvmt_example` and create a tarball that can be run by anyone using only bash.
==========================================================  =============


sim
***

Description
^^^^^^^^^^^
Performs necessary steps to run simulation of an IP.  Only supports Digital Logic Simulation for the time being.

While the controls for individual steps (FuseSoC processing, compilation, elaboration and simulation) are exposed, it
is recommended to let ``mio sim`` manage this process as much as possible.  In the event of corrupt simulator
artifacts, see ``mio clean``.  Combining any of the step-control arguments (``-F``, ``-C``, ``-E``, ``-S``) with missing steps can
result in unpredictable behavior and is not recommended (ex: ``-FS`` is illegal).

Two types of arguments (``--args``) can be passed: compilation (``+define+NAME[=VALUE]``) and simulation (``+NAME[=VALUE]``).

For running multiple tests in parallel, see ``mio regr``.

Usage
^^^^^
``mio sim IP [OPTIONS] [--args ARG ...]``

Options
^^^^^^^
================  =========================  ===========================
``-t TEST``       ``--test TEST``            Specify the UVM test to be run.
``-s SEED``       ``--seed SEED``            Positive Integer. Specify randomization seed  If none is provided, a random one will be picked.
``-v VERBOSITY``  ``--verbosity VERBOSITY``  Specifies UVM logging verbosity: ``none``, ``low``, ``medium``, ``high``, ``debug``. [default: ``medium``]
``-e ERRORS``     ``--errors    ERRORS``     Specifies the number of errors at which compilation/elaboration/simulation is terminated.  [default: ``10``]
``-w``            ``--waves``                Enable wave capture to disk.
``-c``            ``--cov``                  Enable code & functional coverage capture.
``-g``            ``--gui``                  Invokes simulator in graphical or 'GUI' mode.
``-a APP``        ``--app APP``              Specifies simulator application to use: ``viv``, ``mtr``, ``vcs``, ``xcl``, ``qst``, ``riv``. [default: ``viv``]
================  =========================  ===========================


Examples
^^^^^^^^
=====================================================  =============
``mio sim uvmt_my_ip -t smoke -s 1 -w -c``             Compile, elaborate and simulate test ``uvmt_my_ip_smoke_test_c`` for IP ``uvmt_my_ip`` with seed ``1`` and waves & coverage capture enabled.
``mio sim uvmt_my_ip -t smoke -s 1 --args +NPKTS=10``  Compile, elaborate and simulate test ``uvmt_my_ip_smoke_test_c`` for IP ``uvmt_my_ip`` with seed ``1`` and a simulation argument.
``mio sim uvmt_my_ip -S -t smoke -s 42 -v high -g``    Only simulates test ``uvmt_my_ip_smoke_test_c`` for IP ``uvmt_my_ip`` with seed ``42`` and ``UVM_HIGH`` verbosity using the simulator in GUI mode.
``mio sim uvmt_my_ip -C``                              Only compile ``uvmt_my_ip``.
``mio sim uvmt_my_ip -E``                              Only elaborate ``uvmt_my_ip``.
``mio sim uvmt_my_ip -CE``                             Compile and elaborate ``uvmt_my_ip``.
=====================================================  =============


Generators
----------

init
****

Description
^^^^^^^^^^^
Creates a new Project skeleton if not already within a Project.  If so, a new IP skeleton is created.
This is the recommended method for importing code to the Moore.io ecosystem.

Usage
^^^^^
``mio init [OPTIONS]``

Options
^^^^^^^
None for the time being.

Examples
^^^^^^^^
=========================  ===========
``mio init``               Create a new empty Project/IP in this location.
``mio -C ~/my_proj init``  Create a new empty Project at a specific location.
=========================  ===========


new
***

Description
^^^^^^^^^^^
Invokes the Datum UVM Code Template system.  If no generator name is specified, the user is prompted to select from a
list of what is currently available: 17 Templates, from advanced agents to tests.

Usage
^^^^^
``mio new [OPTIONS]``

Options
^^^^^^^
===============  =======================  ====
``-t TEMPLATE``  ``--template TEMPLATE``  Name of template to use: ``basic_agent``, ``parallel_agent``, ``serial_agent``, ``block_tb``, ``ss_tb``, ``lib``, ``ral``, ``comp``, ``obj``, ``reg_adapter``, ``reg_block``, ``reg``, ``seq_lib``, ``seq``, ``test``, ``vseq_lib``, ``vseq``.
===============  =======================  ====

Examples
^^^^^^^^
=======================  =======
``mio new``              Invoke the template menu
``mio new -t block_tb``  Create new UVM Block-level UVM Environment+TB along with Control Plane and Data Plane Agents
=======================  =======


IP Management
-------------

install
*******

Description
^^^^^^^^^^^
Installs an IP and any IPs that it depends on from the Moore.io IP Marketplace (https://mooreio.com).  IPs can be
installed either locally (``$PROJECT_ROOT/.mio/vendors``) or globally (``~/.mio/vendors``).

Usage
^^^^^
``mio install IP [OPTIONS]``

Options
^^^^^^^
===============  =======================  ==============
``-g``           ``--global``             Installs IP dependencies for all user projects
``-u USERNAME``  ``--username USERNAME``  Specifies Moore.io username (must be combined with ``-p``)
``-p PASSWORD``  ``--password PASSWORD``  Specifies Moore.io password (must be combined with ``-u``)
===============  =======================  ==============

Examples
^^^^^^^^
==================================================  ================
``mio install uvmt_my_ip``                          Install IP dependencies for ``uvmt_my_ip`` locally.
``mio install uvmt_another_ip``                     Install IP dependencies for ``uvmt_another_ip`` globally.
``mio install uvmt_my_ip -u jenkins -p )Kq3)fkqm``  Specify credentials for Jenkins job.
==================================================  ================


package
*******

Description
^^^^^^^^^^^
Command for encrypting/compressing entire IP on local disk.  To enable IP encryption, add an ``encrypted`` entry to the
``hdl-src`` section of your descriptor (ip.yml).  Moore.io will only attempt to encrypt using the simulators listed
under ``simulators-supported`` of the ``ip`` section.

Vivado requires a key for encryption; please ensure that you have specified your key location either in the project
or user Configuration file (mio.toml).  https://mooreio-client.readthedocs.io/en/latest/configuration.html#encryption
for more on the subject.

Usage
^^^^^
``mio package IP DEST [OPTIONS]``

Options
^^^^^^^
======  ============  ======
``-n``  ``--no-tgz``  Do not create compressed tarball
======  ============  ======

Examples
^^^^^^^^
==================================  ======
``mio package uvma_my_ip ~``        Create compressed archive of IP ``uvma_my_ip`` under user's home directory.
``mio package uvma_my_ip ~/ip -n``  Process IP ``uvma_my_ip`` but do not create compressed archive.
==================================  ======


Results Management
------------------

clean
*****

Description
^^^^^^^^^^^
Deletes output artifacts from EDA tools.  Only simulation is currently supported.

Usage
^^^^^
``mio clean IP [OPTIONS]``

Options
^^^^^^^
======  ==========  ================
``-d``  ``--deep``  Also clean compiled IP dependencies.
======  ==========  ================

Examples
^^^^^^^^
===========================  ==============================
``mio clean uvmt_my_ip``     Delete compilation, elaboration and simulation binaries for IP ``uvmt_my_ip``
``mio clean uvmt_my_ip -d``  Delete compilation, elaboration and simulation binaries for IP ``uvmt_my_ip`` and its dependencies
===========================  ==============================



cov
***

Description
^^^^^^^^^^^
Merges code and functional coverage data into a single database from which report(s) are generated.  These reports
are output into the simulation directory.

Usage
^^^^^
``mio cov IP [OPTIONS]``

Options
^^^^^^^
None for the time being.

Examples
^^^^^^^^
=================  ======
``mio cov my_ip``  Merge coverage data for ``my_ip`` and generate a report.
=================  ======


results
*******


Description
^^^^^^^^^^^
Parses Simulaton results for a target IP and generates both HTML and Jenkins-compatible XML reports.  These reports
are output into the simulation directory.

Usage
^^^^^
``mio results IP REPORT_NAME [OPTIONS]``

Options
^^^^^^^
None for the time being.

Examples
^^^^^^^^
=================================  =====
``mio results my_ip sim_results``  Parse simulation results for ``my_ip`` and generate reports under ``sim_results`` filenames.
=================================  =====
