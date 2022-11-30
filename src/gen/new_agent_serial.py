#!/usr/bin/python3
########################################################################################################################
# Copyright 2022 Datum Technology Corporation
# All rights reserved
########################################################################################################################


########################################################################################################################
# IMPORTS
########################################################################################################################
from datetime import date
import os
import sys
import re
import jinja2
from jinja2 import Template
from mio import common
from mio import new
from mio import cfg
#from vsdx import VisioFile


########################################################################################################################
# GLOBALS
########################################################################################################################
dbg = False
uvm_gen_dir = re.sub("new_agent_serial.py", "", os.path.realpath(__file__)) + ".."
relative_path_to_template = uvm_gen_dir + "/templates/sets/"
out_path = ""
default_license = "All rights reserved."
name_of_copyright_owner = ""
name = ""
full_name = ""


########################################################################################################################
# TEMPLATE DATA
########################################################################################################################
parameters = { }


########################################################################################################################
# MAIN
########################################################################################################################
def combine_dict(d1, d2):
    d3 = {}
    for d in d1:
        d3[d] = d1[d]
    for d in d2:
        d3[d] = d2[d]
    return d3


def pick_out_path():
    global out_path
    global default_copyright_owner
    if len(sys.argv) > 1:
        out_path = sys.argv[1]
        print("Code will be output to " + out_path)
    if len(sys.argv) > 2:
        default_copyright_owner = sys.argv[2].replace('"', "")
        print("Default copyright owner is " + default_copyright_owner)


def prompt_user_values():
    global out_path
    global name
    global full_name
    global name_of_copyright_owner
    global parameters
    
    default_copyright_owner = cfg.org_full_name
    default_vendor          = cfg.org_name
    
    common.info("Moore.io Template Generator: UVM Advanced Serial Agent - (v1p0)")
    common.info("***************************************************************")
    common.info("The answers to the following questionnaire will be used to generate the code for your new UVM Agent")
    common.info("")
    
    if out_path == "":
        out_path = common.prompt("Please enter the destination path for this new agent (default: '.'):\n").strip()
        if out_path == "":
            out_path = "."
    
    name_of_copyright_owner = common.prompt("Please enter the name of the copyright holder or hit RETURN for the default (default is '" + default_copyright_owner + "'):\n").strip()
    if name_of_copyright_owner == "":
        name_of_copyright_owner = default_copyright_owner
    
    name_of_vendor = common.prompt("Please enter a vendor name or hit RETURN for the default (default is '" + default_vendor + "'):\n").strip()
    if name_of_vendor == "":
        name_of_vendor = default_vendor
    
    license = common.prompt("Please enter a usage license or hit RETURN for the default (default is '" + default_license + "'):\n").strip()
    if license == "":
        license = default_license
    
    name = common.prompt("Please enter the package name for this agent (ex: 'spi'); this name will be used for all agent types (ex: 'uvma_spi_agent_c'):\n").lower().strip()
    if name == "":
        sys.exit("ERROR: package name cannot be empty.  Exiting.")
    
    full_name = common.prompt("Please enter the full name for this agent (ex: 'Serial Peripheral Interface'):\n").strip()
    if full_name == "":
        sys.exit("ERROR: full name cannot be empty.  Exiting.")
    
    is_symmetric_str = common.prompt("Is the physical interface symmetric?  [N/y]").strip().lower()
    if is_symmetric_str == "":
        is_symmetric = False
    else:
        if is_symmetric_str == "n" or is_symmetric_str == "no":
            is_symmetric = False
        elif is_symmetric_str == "y" or is_symmetric_str == "yes":
            is_symmetric = True
        else:
            sys.exit("ERROR: please enter 'y' or 'n'")
    
    is_ddr_str = common.prompt("Is the physical interface using DDR clocking?  [N/y]").strip().lower()
    if is_ddr_str == "":
        is_ddr = False
    else:
        if is_ddr_str == "n" or is_ddr_str == "no":
            is_ddr = False
        elif is_ddr_str == "y" or is_ddr_str == "yes":
            is_ddr = True
        else:
            sys.exit("ERROR: please enter 'y' or 'n'")
    
    mode_1 = common.prompt("Please enter the first mode for this new agent (default: 'mstr'):\n").strip()
    if mode_1 == "":
        mode_1 = "mstr"
    
    mode_2 = common.prompt("Please enter the second mode for this new agent (default: 'slv'):\n").strip()
    if mode_2 == "":
        mode_2 = "slv"
    
    tx_str = common.prompt("Please enter the first direction for this new agent (default: 'm2s'):\n").strip()
    if tx_str == "":
        tx_str = "m2s"
    
    rx_str = common.prompt("Please enter the second direction for this new agent (default: 's2m'):\n").strip()
    if rx_str == "":
        rx_str = "s2m"
    
    parameters = {
        "name"                    : name,
        "full_name"               : full_name,
        "name_of_copyright_owner" : name_of_copyright_owner,
        "license"                 : license,
        "year"                    : date.today().year,
        "symmetric"               : is_symmetric,
        "ddr"                     : is_ddr,
        "mode_1"                  : mode_1,
        "mode_2"                  : mode_2,
        "tx"                      : tx_str,
        "rx"                      : rx_str,
        "dmp0"                    : "drv_" + tx_str + "_mp",
        "dmp1"                    : "drv_" + rx_str + "_mp",
        "vendor"                  : name_of_vendor
    }


def gen_agent():
    common.fatal("Not yet implemented")


def print_end_message():
    global out_path
    global name
    global parameters
    
    common.banner("IPs successfully generated:")
    common.info("  * " + out_path + "/uvma_" + name)
    common.info("  * " + out_path + "/uvme_" + name + "_st")
    common.info("  * " + out_path + "/uvmt_" + name + "_st")


########################################################################################################################
# ENTRY POINT
########################################################################################################################
def main():
    #pick_out_path()
    prompt_user_values()
    gen_agent()
    print_end_message()
