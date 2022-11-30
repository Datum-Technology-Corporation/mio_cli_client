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
uvm_gen_dir = re.sub("new_block.py", "", os.path.realpath(__file__)) + ".."
relative_path_to_template = uvm_gen_dir + "/templates/sets/"
out_path = ""
default_license = "All rights reserved."
name_of_copyright_owner = ""
name = ""
name_normal_case = ""


########################################################################################################################
# TEMPLATE DATA
########################################################################################################################
agent_cp_parameters = { }
agent_dp_in_parameters = { }
agent_dp_out_parameters = { }
env_tb_parameters = { }


########################################################################################################################
# MAIN
########################################################################################################################
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
    global name_normal_case
    global name_of_copyright_owner
    global default_copyright_owner
    global agent_cp_parameters
    global agent_dp_in_parameters
    global agent_dp_out_parameters
    global env_tb_parameters
    
    default_copyright_owner = cfg.org_full_name
    default_vendor          = cfg.org_name

    common.info("Moore.io Template Generator: RTL Block UVM DV Combo (v1p0)")
    common.info("**********************************************************")
    common.info("The answers to the following questionnaire will be used to generate the code for your new UVM Block-Level Env+TB")
    common.info("")
    
    if out_path == "":
        out_path = common.prompt("Please enter the destination path (default: '.'):\n").strip()
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
    
    name = common.prompt("Please enter the name for this block (ex: 'abc'); this name will be used for all UVM types (ex: 'uvme_abc_env_c'):\n").lower().strip()
    if name == "":
        sys.exit("ERROR: package name cannot be empty.  Exiting.")
    
    name_normal_case = common.prompt("Please enter the (descriptive) name for this block (ex: 'Advanced Bus Control'):\n").strip()
    if name_normal_case == "":
        sys.exit("ERROR: descriptive name cannot be empty.  Exiting.")
    
    agent_cp_parameters = {
        "name"                    : name + "_cp",
        "name_uppercase"          : name.upper() + "_CP",
        "name_normal_case"        : name_normal_case + " Block Control Plane",
        "name_of_copyright_owner" : name_of_copyright_owner,
        "license"                 : license,
        "year"                    : date.today().year,
        "vendor"                  : name_of_vendor
    }
    
    agent_dp_in_parameters = {
        "name"                    : name + "_dpi",
        "name_uppercase"          : name.upper() + "_DPI",
        "name_normal_case"        : name_normal_case + " Block Data Plane Input",
        "name_of_copyright_owner" : name_of_copyright_owner,
        "license"                 : license,
        "year"                    : date.today().year,
        "vendor"                  : name_of_vendor
    }
    
    agent_dp_out_parameters = {
        "name"                    : name + "_dpo",
        "name_uppercase"          : name.upper() + "_DPO",
        "name_normal_case"        : name_normal_case + " Block Data Plane Output",
        "name_of_copyright_owner" : name_of_copyright_owner,
        "license"                 : license,
        "year"                    : date.today().year,
        "vendor"                  : name_of_vendor
    }
    
    env_tb_parameters = {
        "name"                    : name,
        "name_uppercase"          : name.upper(),
        "name_normal_case"        : name_normal_case,
        "name_of_copyright_owner" : name_of_copyright_owner,
        "license"                 : license,
        "year"                    : date.today().year,
        "vendor"                  : name_of_vendor
    }


def gen_block():
    common.fatal("Not yet implemented")


def print_end_message():
    global out_path
    global name
    global parameters
    
    common.banner("IPs successfully generated:")
    common.info("  * " + out_path + "/uvma_" + name + "_cp")
    common.info("  * " + out_path + "/uvma_" + name + "_dpi")
    common.info("  * " + out_path + "/uvma_" + name + "_dpo")
    common.info("  * " + out_path + "/uvme_" + name)
    common.info("  * " + out_path + "/uvmt_" + name)


########################################################################################################################
# ENTRY POINT
########################################################################################################################
def main():
    #pick_out_path()
    prompt_user_values()
    gen_block()
    print_end_message()
