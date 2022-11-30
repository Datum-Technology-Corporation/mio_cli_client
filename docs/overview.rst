Overview
============

Purpose of Moore.io Client
--------------------------

Executive Summary
*****************
Moore.io (MIO) is a Hardware Development Toolchain and IP catalog used by Design/Verification  engineers and their
organizations to create and share IP for RTL and Design Verification (DV).  Although the current emphasis is on
front-end  development, the long-term goal is to support the entire FPGA/ASIC engineering process and to generally
support open-source hardware development.

MIO consists of three distinct components:

- the Command Line Interface (CLI) toolchain
- the IP Marketplace
- the UVM Template System

The MIO CLI orchestrates disparate free and/or open source tools into a single, complete,
straightforward and integrated toolchain for hardware engineers.  The CLI consists of a succinct and powerful command
set which developers use via a terminal on their operating system (Windows/Linux/OSX).

The MIO Marketplace hosts commercial and Free & Open-Source (FOS) hardware IPs, their documentation, as well as proof of work that the IP has
been thoroughly tested.

The UVM Template System is a collection of 17 interlocking code generators that quickly create any UVM construct
desired with the highest level of code quality, documentation and adherence to cutting-edge industry practices, such as
`Advanced UVM <https://www.linkedin.com/pulse/advanced-uvm-brian-hunter/>`_.


Engineering Perspective
***********************

MIO solves six technical problems:

- Automated root problem analysis in constrained-random UVM testing
- Generation of quality new UVM constructs
- Management of Hardware Description Language (HDL) IP and dependencies
- Lack of quality FOS fundamental UVM libraries (`scoreboards <https://www.mooreio.com/catalog/1155>`_, `logging <https://www.mooreio.com/catalog/1153>`_, `clocking agent <https://www.mooreio.com/catalog/1156>`_, etc.)
- Automation of and interfacing with free & commercial EDA tools
- Management and analysis of simulation results


Management Perspective
**********************

MIO addresses six common concerns:

- Reducing DV budget while improving verification process and results
- Reducing the "time to first bug found" to days, from weeks or months
- Enabling IP re-use across teams and projects
- Multiplying IP value with industrial-grade UVM verification
- Accelerating coverage progress
- Generating quality IP documentation for clients/users


Availability
************
The CLI toolchain and UVM templates are open to all.  Moore.io is currently in an invitation-only Beta for the
commercial libraries on the IP marketplace.


What does it cost?
******************
The CLI client itself is FOS, as are some of the IPs found on the Moore.io IP Marketplace.  This includes the Moore.io
Core Collection.

- Publishing FOS IP is free.
- Publishing commercial IP is a paid service.
- Private IP catalog support is a paid service (cloud or self-hosted) - `Not yet available`




High-Level System Description
-----------------------------

The Moore.io Client
*******************
The MIO CLI Client is written in Python3 and is available for Windows, Linux and Mac OS. It uses descriptor files that
define Project, IP, Configuration and Regressions.  These drive EDA tool automation and can be edited via text editor as
they all use industry standard formats (YAML, TOML).

The MIO CLI Client provides a universal frontend (aka Makefile) and automation for the majority of EDA tools, free and
commercial.  It also installs and manages IPs from the MIO IP Marketplace, runs regressions, generates reference
documentation from code, and performs operations on simulation results as well as functional and code coverage.

This enables the automation of the following tasks with a single, simple CLI command:

- Logic Simulation
- UVM code generation (any constructs, from test benches to tests)
- Linting
- RTL Assembly with `FuseSoC <http://fusesoc.net/>`_
- Synthesis - `Coming soon`
- Place and Route - `Coming soon`
- Static Timing Analysis - `Coming soon`
- Formal Verification - `Coming soon`


Projects
********
A Moore.io Project is identified by its ``mio.toml`` descriptor, which also doubles as configuration repository.  Its
location, by definition, is the Project Root Directory (``$PROJECT_ROOT_DIR``).  Projects contain IPs and directories
for the results of jobs run on these IPs, as well as the reports derived from results data.


IP
**
A Moore.io IP is a set of source code files and directories described by an IP Descriptor (``ip.yml``).  Its location, 
by definition, is the IP Root Directory.  This descriptor contains all required information for job automation and
listing on the Moore.io IP Marketplace.


Configuration
*************
The MIO Client behavior is controlled by the Configuration Space which is loaded from two sources: disk and CLI.  On disk,
TOML files (``mio.toml``) are used.  Via command line, the ``-c=<name>=<value>`` or ``--config=<name>=<value>`` argument
is used (`coming soon`).

A full listing of options can be found in Configuration Space section.


Regressions
***********
Regressions are captured by the Moore.io Test Suite (``[<target>.]ts.yml``), a simple but powerful descriptor that turns
the usual solution inside-out by defining regressions by features rather than tests.


UVM Template System
*******************
The IEEE Standard for 80% of all work in chip engineering has been a wonderful unifying force for the industry.  But it is incomplete and requires a lot of code and expertise to get projects off the ground.  The Moore.io UVM Template System solves these problems and provides a complete solution that is compatible with the free Xilinx Vivado simulator.  The templates emphasize IP re-use from the Moore.io IP Marketplace, meaning you spend no time on infrastructure and all your time on your business logic.

