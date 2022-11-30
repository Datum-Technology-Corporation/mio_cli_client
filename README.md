[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Documentation Status](https://readthedocs.org/projects/mio-cli/badge/?version=latest)](https://mio-cli.readthedocs.io/en/latest/?badge=latest)

# [Moore.io](https://www.mooreio.com/) [Command Line Interface Client](https://datum-technology-corporation.github.io/mio_cli_client/)


## About

|  | From the [User Manual](https://mio-cli.readthedocs.io/en/latest/)'s [Executive Summary](https://mio-cli.readthedocs.io/en/latest/overview.html#executive-summary) |
|-|-|
| [![Moore.io Logo](https://github.com/Datum-Technology-Corporation/mio_cli_client/blob/gh-pages/assets/img/logo.png?raw=true)](https://mio-cli.readthedocs.io/en/latest/index.html) | The Moore.io Command Line Interface (CLI) Client orchestrates disparate free and/or open source tools into a single, complete, straightforward and integrated toolchain for hardware engineers.  The CLI consists of a succinct and powerful command set which developers use via a terminal on their operating system (Windows/Linux/OSX). |



## Installation
`mio` can be installed directly from [`pip3`](https://pip.pypa.io/en/stable/), but it is recommended to use [`pipx`](https://pypa.github.io/pipx/):

````
pipx install mio-cli
````

`pipx` can be installed via:

````
python3 -m pip install --user pipx
python3 -m pipx ensurepath
````



## [Developer Guide](https://datum-technology-corporation.github.io/mio_cli_client/dev_guide.html)

## [Demo Project](https://github.com/Datum-Technology-Corporation/mio_demo)




## Usage
````
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
      help           Documentation for all mio commands
   
   Project and Code Management
      init           Starts project creation dialog
      new            Creates new source code via the mio template engine
   
   IP and Credentials Management
      install        Install all IP dependencies from IP Marketplace
      login          Start session with IP Marketplace
      package        Create a compressed archive of an IP
      publish        Publish IP to IP Marketplace
   
   EDA Automation
      sim            Performs necessary steps to simulate an IP with any simulator
      regr           Run regression against an IP
      
   Manage Results and other EDA Tool Outputs
      clean          Manages outputs from tools (other than job results)
      dox            HDL source code documentation generation via Doxygen
      cov            Manages coverage data from EDA tools
      results        Manages results from EDA tools
````
