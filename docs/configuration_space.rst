Configuration Space
===================

``mio`` behavior is controlled by the configuration space, which is obtained from multiple sources, in decreasing precedence:

- Command line parameters - ``-c <name>=<value>`` or ``--config=<name>=<value>`` - `Coming soon`
- Project configuration file - ``$PROJECT_ROOT_DIR/mio.toml``
- User configuration file - ``~/.mio/mio.toml``
- Built-in defaults - ``$MIO_HOME/data/mio.toml``

Environment Variables
---------------------
``mio`` needs certain environment variables to be set and will set some of its own.  The former are required for proper operation while the latter are to be used by the user in integration and extension.

Input
*****
- ``$VERIBLE_HOME`` - Path to Verible installation directory.
- ``$METRICS_HOME`` - Path to Metrics simulator installation directory.
- ``$QUESTA_HOME`` - Path to Siemens Questa simulator installation directory.
- ``$RIVIERA_HOME`` - Path to Aldec Riviera PRO simulator installation directory.
- ``$VCS_HOME`` - Path to Synopsys VCS simulator installation directory.
- ``$VIVADO_HOME`` - Path to Xilinx Vivado installation directory (``bin`` should be found under this directory).
- ``$XCELIUM_HOME`` - Path to Cadence XCelium simulator installion directory.

Output
******
- ``${{ name.upper() }}_SRC_PATH`` - Path to IP ``name`` 's source directory on disk.  Custom filelists must use this as their base directory.


ip
--

global-paths
************

- Required: Yes
- Type: ``String[]``
- Default: ``[]``

`mio` searches these absolute paths for IP descriptors.


paths
*****

- Required: Yes
- Type: ``String[]``
- Default: ``["dv","rtl"]``

`mio` searches these relative (to the project root) paths for IP descriptors.  The names used are irrelevant to the IP
types contained therein.  Ex: DV IPs could be stored under ``rtl`` and vice-versa with no impact on functionality.


encryption
----------

metrics-key-path
***************

- Required: Yes
- Type: ``String``
- Default: ``null``
- Example: ``/tools/mtr.key``

Absolute path to location of Metrics Cloud Simulator encryption key file.  This must be set in order to encrypt IP using vivado.
See https://support.metrics.ca/hc/en-us/articles/360061975092-User-Guide-DSim-IEEE-1735-Encryption-In-Verilog for more information.


vivado-key-path
***************

- Required: Yes
- Type: ``String``
- Default: ``null``
- Example: ``/tools/viv.key``

Absolute path to location of Xilinx Vivado encryption key file.  This must be set in order to encrypt IP using vivado.
See https://www.xilinx.com/products/intellectual-property/ip-encryption.html for more information.


lint
----

root-path
*********

- Required: Yes
- Type: ``String``
- Default: ``lint``

Project-relative path to directory where HDL linting results and reports are stored.


org
---

name
****

- Required: Yes
- Type: ``String``
- Default: ``Null``
- Example: ``Acme``

Short name for the Organization (i.e. vendor name).



full-name
*********

- Required: Yes
- Type: ``String``
- Default: ``null``
- Example: ``Acme Corporation``

Full legal name for the Organization.




project
-------

name
****

- Required: Yes
- Type: ``String``
- Default: ``null``
- Example: ``chip_123``

Short name for the current project.  Cannot contain spaces.



full-name
*********

- Required: Yes
- Type: ``String``
- Default: ``null``
- Example: ``Chip 123``

Descriptive name for the current project.


description
***********

- Required: No
- Type: ``String``
- Default: ``null``
- Example: ``Chip for 123 clients``

Descriptive text for the current project.



simulation
----------

default-simulator
*****************

- Required: Yes
- Type: ``String``
- Default: ``viv``

Simulator used when invoking the ``sim`` command without specifying ``-a APP`` ``--app APP``.


root-path
*********

- Required: Yes
- Type: ``String``
- Default: ``sim``

Project-relative path to directory where HDL simulations results and reports are stored.


regressions-dir
***************

- Required: Yes
- Type: ``String``
- Default: ``regressions``

Name of directory where regressions results are stored.  This directory is always created directly under root-path.


results-dir
***********

- Required: Yes
- Type: ``String``
- Default: ``results``

Name of directory where immediate results are stored.  This directory is always created directly under root-path.


test-result-path-template
*************************

- Required: Yes
- Type: ``String``
- Default: ``{{ ip_name }}_{{ test_name }}_{{ seed }}{% if args_present %}_{% for arg in args %}{{ arg }}{% endfor %}{% endif %}``

`Jinja <https://palletsprojects.com/p/jinja/>`_ template used to generate the directory names for IP simulation test results.


timescale
*********

- Required: Yes
- Type: ``String``
- Default: ``1ns/1ps``

Simulation timescale specified to the simulator via command line.


uvm-version
***********

- Required: Yes
- Type: ``String``
- Default: ``1.2``

Specifies the version of UVM to be used during simulation.





synthesis
---------

root-path
*********

- Required: Yes
- Type: ``String``
- Default: ``syn``

Project-relative path to directory where logic synthesis results and reports are stored.


