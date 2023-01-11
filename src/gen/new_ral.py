#!/usr/bin/python3
########################################################################################################################
# Copyright 2021-2023 Datum Technology Corporation
# All rights reserved.
########################################################################################################################


########################################################################################################################
# IMPORTS
########################################################################################################################
#import gen.ral_typedefs
#import gen.ral_templates
import re
import csv
import jinja2
import tarfile
from jinja2 import Template
from enum import Enum
import os
import sys
from datetime import date
from mio import common
from mio import cfg


########################################################################################################################
# GLOBALS
########################################################################################################################
dbg = False
out_path = ""
default_license = "All rights reserved"
ip_name = ""
name_of_copyright_owner = ""
license = ""
csv_filepath = ""
gen_block_offset = ""
default_gen_block_offset = "0000_0000"
parameters = {}
num_files = 0


########################################################################################################################
# FUNCTIONS
########################################################################################################################
def gen_block():
    common.fatal("Not yet implemented")


def prompt_user_values():
    global out_path
    global csv_filepath
    global ip_name
    global license
    global default_license
    global name_of_copyright_owner
    global parameters
    global gen_block_offset
    global default_gen_block_offset
    
    default_copyright_owner = cfg.org_full_name
    default_vendor          = cfg.org_name
    
    common.info("Moore.io Template Generator: UVM Register Model (v1p0)")
    common.info("******************************************************")
    common.info("The answers to the following questionnaire will be used to generate the code for your new UVM Register Model")
    common.info("")
    
    if out_path == "":
        out_path = common.prompt("Please enter the destination path for this new UVM Register Model (default: '.'):\n").strip()
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
    
    ip_name = common.prompt("Please enter the name of the UVM Environment to which this Model belongs (ex: 'ctrl'); this name will be used for all types (ex: 'uvme_ctrl_reg_block_c'):\n").lower().strip()
    if ip_name == "":
        common.fatal("ERROR: UVM Environment name cannot be empty.  Exiting.")
    
    csv_filepath = common.prompt("Please enter the path of the input .csv file:\n").lower().strip()
    if csv_filepath == "":
        common.fatal("ERROR: Input .csv file path cannot be empty.  Exiting.")
    
    gen_block_offset = common.prompt("Please enter the base address (default: 0000_0000):\n").lower().strip()
    if gen_block_offset == "":
        gen_block_offset = default_gen_block_offset
    
    parameters = {
        "ip_name"                 : ip_name,
        "year"                    : date.today().year,
        "name_of_copyright_owner" : name_of_copyright_owner,
        "license"                 : license,
        "vendor"                  : name_of_vendor
    }


def print_end_message():
    global out_path
    global num_files
    common.info(str(num_files) + " files successfully generated into " + out_path)


########################################################################################################################
# ENTRY POINT
########################################################################################################################
def main():
    prompt_user_values()
    gen_block()
    print_end_message()
