#!/usr/bin/python3
########################################################################################################################
# Copyright 2022 Datum Technology Corporation
# All rights reserved.
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
uvm_gen_dir = re.sub("new_ss.py", "", os.path.realpath(__file__)) + ".."
relative_path_to_template = uvm_gen_dir + "/templates/sets/"
out_path = ""
default_license = "All rights reserved."
name_of_copyright_owner = ""
name = ""
name_normal_case = ""
clk_agent_name = ""
clk_agent_type = ""
ral_agent_name = ""
ral_agent_type = ""
reset_agent_name = ""
reset_agent_type = ""


########################################################################################################################
# TEMPLATE DATA
########################################################################################################################
parameters = {
    "name"                    : "",
    "name_uppercase"          : "",
    "name_normal_case"        : "",
    "name_of_copyright_owner" : "",
}


########################################################################################################################
# MAIN
########################################################################################################################
def pick_out_path():
    global out_path
    global default_copyright_owner
    if len(sys.argv) > 1:
        out_path = sys.argv[1]
        common.info("Code will be output to " + out_path)
    if len(sys.argv) > 2:
        default_copyright_owner = sys.argv[2].replace('"', "")
        common.info("Default copyright owner is " + default_copyright_owner)


def prompt_user_values():
    global out_path
    global name
    global name_normal_case
    global clk_agent_name
    global clk_agent_type
    global ral_agent_name
    global ral_agent_type
    global reset_agent_name
    global reset_agent_type
    global name_of_copyright_owner
    global default_copyright_owner
    global parameters
    
    default_copyright_owner = cfg.org_full_name
    default_vendor          = cfg.org_name
    
    common.info("Moore.io Template Generator: UVM Environment - Sub-System (SS) (v1p0)")
    common.info("*********************************************************************")
    common.info("The answers to the following questionnaire will be used to generate the code for your new UVM Environment")
    common.info("")
    
    if out_path == "":
        out_path = common.prompt("Please enter the destination path for this new agent (default: '.'):\n").strip()
        if out_path == "":
            out_path = "."
    
    parameters = {
        "name"          : name,
        "name_uppercase": name.upper(),
        "year"          : date.today().year
    }
    
    name_of_copyright_owner = common.prompt("Please enter the name of the copyright holder or hit RETURN for the default (default is '" + default_copyright_owner + "'):\n").strip()
    if name_of_copyright_owner == "":
        name_of_copyright_owner = default_copyright_owner
    parameters["name_of_copyright_owner"] = name_of_copyright_owner
    
    name_of_vendor = common.prompt("Please enter a vendor name or hit RETURN for the default (default is '" + default_vendor + "'):\n").strip()
    if name_of_vendor == "":
        name_of_vendor = default_vendor
    parameters["vendor"] = name_of_vendor
    
    license = common.prompt("Please enter a usage license or hit RETURN for the default (default is '" + default_license + "'):\n").strip()
    if license == "":
        license = default_license
    parameters["license"] = license
    
    name = common.prompt("Please enter the package name for this Environment (ex: 'dp'); this name will be used for all Environment types (ex: 'uvme_dp_env_c'):\n").lower().strip()
    if name == "":
        sys.exit("ERROR: package name cannot be empty.  Exiting.")
    else:
        parameters["name"] = name
        parameters["name_uppercase"] = name.upper()
    
    name_normal_case = common.prompt("Please enter the (descriptive) name for this Environment (ex: 'Data Plane'):\n").strip()
    if name_normal_case == "":
        sys.exit("ERROR: descriptive name cannot be empty.  Exiting.")
    else:
        parameters["name_normal_case"] = name_normal_case
    
    clk_agent_name = common.prompt("Please enter the name of the Clock Agent (default: 'sys_clk'):\n").strip()
    if clk_agent_name == "":
        parameters["clk_agent_name"] = "sys_clk"
        parameters["clk_agent_name_uppercase"] = "SYS_CLK"
    else:
        parameters["clk_agent_name"] = clk_agent_name
        parameters["clk_agent_name_uppercase"] = clk_agent_name.upper()
    
    reset_agent_name = common.prompt("Please enter the name of the Reset Agent (default: 'sys_reset'):\n").strip()
    if reset_agent_name == "":
        parameters["reset_agent_name"] = "sys_reset"
        parameters["reset_agent_name_uppercase"] = "SYS_RESET"
    else:
        parameters["reset_agent_name"] = reset_agent_name
        parameters["reset_agent_name_uppercase"] = reset_agent_name.upper()
    
    ral_agent_type = common.prompt("Please enter the type for the RAL Agent (default: 'axil'):\n").strip()
    if ral_agent_type == "":
        parameters["ral_agent_type"] = "axil"
        parameters["ral_agent_type_uppercase"] = "AXIL"
    else:
        parameters["ral_agent_type"          ] = ral_agent_type
        parameters["ral_agent_type_uppercase"] = ral_agent_type.upper()
    
    ral_agent_name = common.prompt("Please enter the name of the RAL Agent (default: 'axil'):\n").strip()
    if ral_agent_name == "":
        parameters["ral_agent_name"] = "axil"
        parameters["ral_agent_name_uppercase"] = "AXIL"
    else:
        parameters["ral_agent_name"] = ral_agent_name
        parameters["ral_agent_name_uppercase"] = ral_agent_name.upper()


def gen_ss():
    common.fatal("Not yet implemented.")


def print_end_message():
    global out_path
    global name
    global parameters
    
    common.banner("IPs successfully generated")
    common.info("  * " + out_path + "/uvme_" + name)
    common.info("  * " + out_path + "/uvmt_" + name)


########################################################################################################################
# ENTRY POINT
########################################################################################################################
def main():
    #pick_out_path()
    prompt_user_values()
    gen_ss()
    print_end_message()
