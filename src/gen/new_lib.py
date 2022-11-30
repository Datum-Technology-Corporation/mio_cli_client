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
uvm_gen_dir = re.sub("new_lib.py", "", os.path.realpath(__file__)) + ".."
relative_path_to_template = uvm_gen_dir + "/templates/sets/"
out_path = ""
default_license = "All rights reserved."
name_of_copyright_owner = ""
name = ""
name_normal_case = ""


########################################################################################################################
# TEMPLATE DATA
########################################################################################################################
parameters = { }


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
    global reset_agent_type
    global name_of_copyright_owner
    global default_copyright_owner
    global parameters
    
    default_copyright_owner = cfg.org_full_name
    default_vendor          = cfg.org_name
    
    common.info("Moore.io Template Generator: UVM Library (v1p1)")
    common.info("***********************************************")
    common.info("The answers to the following questionnaire will be used to generate the code for your new UVM Library")
    common.info("")
    
    if out_path == "":
        out_path = common.prompt("Please enter the destination path for this new Library (default: '.'):\n").strip()
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
    
    name = common.prompt("Please enter the name of this new Library (ex: 'math'); this name will be used for all Library types (ex: 'uvml_math_c'):\n").lower().strip()
    if name == "":
        sys.exit("ERROR: package name cannot be empty.  Exiting.")
    
    name_normal_case = common.prompt("Please enter the (descriptive) name for this new Library (ex: 'Mathematical Objects'):\n").strip()
    if name_normal_case == "":
        sys.exit("ERROR: descriptive name cannot be empty.  Exiting.")
    
    parameters = {
        "name_normal_case"        : name_normal_case,
        "name"                    : name,
        "name_uppercase"          : name.upper(),
        "year"                    : date.today().year,
        "name_of_copyright_owner" : name_of_copyright_owner,
        "license"                 : license,
        "vendor"                  : name_of_vendor
    }


def gen_lib():
    common.fatal("Not yet implemented.")


def print_end_message():
    global out_path
    global name
    global parameters
    
    common.banner("IPs successfully generated:")
    common.info("  * " + out_path + "/uvml_" + name)
    common.info("  * " + out_path + "/uvme_" + name + "_st")
    common.info("  * " + out_path + "/uvmt_" + name + "_st")


########################################################################################################################
# ENTRY POINT
########################################################################################################################
def main():
    #pick_out_path()
    prompt_user_values()
    gen_lib()
    print_end_message()
