#!/usr/bin/python3
########################################################################################################################
# Copyright 2021-2023 Datum Technology Corporation
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
from mio import cfg
from mio import common


########################################################################################################################
# GLOBALS
########################################################################################################################
dbg = True
args = {}
relative_path_to_template = "sets"
out_path = ""
default_license = "All rights reserved."
name_of_copyright_owner = ""
name = ""
name_normal_case = ""
answers_file = None
parameters = {}
default_copyright_owner = ""
default_vendor          = ""


########################################################################################################################
# MAIN
########################################################################################################################
def pick_out_path():
    global args
    global out_path
    global default_copyright_owner
    if (args['-o']):
        out_path = args['-o']
        print("Code will be output to " + out_path)
    if (args['-c']):
        default_copyright_owner = args['<copyright_owner>']
        print("Default copyright owner is " + default_copyright_owner)
        


def get_next_answer(question):
    #global args
    #global answers_file
    #if args['-f']:
    #    return answers_file.readline()
    #else:
    #    return input(question)
    return common.prompt(question)


def gen_component():
    global out_path
    global parameters
    parameters = {
        "year" : date.today().year
    }
    common.info("Moore.io Template Generator: Component (v1p0)")
    
    if out_path == "":
        out_path = get_next_answer("Please enter the destination path for this new Component (default: '.'):\n").strip()
        if out_path == "":
            out_path = "."
    
    name_of_copyright_owner = common.prompt("Please enter the name of the copyright holder or hit RETURN for the default (default is '" + default_copyright_owner + "'):\n").strip()
    if name_of_copyright_owner == "":
        name_of_copyright_owner = default_copyright_owner
    parameters["name_of_copyright_owner"] = name_of_copyright_owner
    
    name_of_vendor = common.prompt("Please enter a vendor name or hit RETURN for the default (default is '" + default_vendor + "'):\n").strip()
    if name_of_vendor == "":
        name_of_vendor = default_vendor
    parameters["vendor"] = name_of_vendor
    
    license = get_next_answer("Please enter a usage license or hit RETURN for the default (default is '" + default_license + "'):\n").strip()
    if license == "":
        license = default_license
    parameters["license"] = license
    
    name = get_next_answer("Please enter the name for this Component (ex: 'my_comp'):\n").lower().strip()
    if name == "":
        common.fatal("ERROR: name cannot be empty.  Exiting.")
    else:
        parameters["name"] = name
        parameters["name_uppercase"] = name.upper()
    
    pkg_name = get_next_answer("Please enter the package name for this Component (ex: 'uvma_apb'):\n").lower().strip()
    if name == "":
        common.fatal("ERROR: name cannot be empty.  Exiting.")
    else:
        parameters["pkg_name"] = pkg_name
        parameters["pkg_name_uppercase"] = pkg_name.upper()
    
    base_class = get_next_answer("Please enter the base class type for this Component (default: 'uvm_component'):\n").lower().strip()
    if base_class == "":
        parameters["base_class"] = "uvm_component"
    else:
        parameters["base_class"] = base_class
    
    #process_file("Component", parameters, files['component']['in'], files['component']['out'])


def gen_object():
    global out_path
    global parameters
    parameters = {
        "year" : date.today().year
    }
    common.info("Moore.io Template Generator: Object (v1p0)")
    
    if out_path == "":
        out_path = get_next_answer("Please enter the destination path for this new Object (default: '.'):\n").strip()
        if out_path == "":
            out_path = "."
    
    name_of_copyright_owner = common.prompt("Please enter the name of the copyright holder or hit RETURN for the default (default is '" + default_copyright_owner + "'):\n").strip()
    if name_of_copyright_owner == "":
        name_of_copyright_owner = default_copyright_owner
    parameters["name_of_copyright_owner"] = name_of_copyright_owner
    
    name_of_vendor = common.prompt("Please enter a vendor name or hit RETURN for the default (default is '" + default_vendor + "'):\n").strip()
    if name_of_vendor == "":
        name_of_vendor = default_vendor
    parameters["vendor"] = name_of_vendor
    
    license = get_next_answer("Please enter a usage license or hit RETURN for the default (default is '" + default_license + "'):\n").strip()
    if license == "":
        license = default_license
    parameters["license"] = license
    
    name = get_next_answer("Please enter the name for this Object (ex: 'my_obj'):\n").lower().strip()
    if name == "":
        common.fatal("ERROR: name cannot be empty.  Exiting.")
    else:
        parameters["name"] = name
        parameters["name_uppercase"] = name.upper()
    
    pkg_name = get_next_answer("Please enter the package name for this Object (ex: 'uvma_apb'):\n").lower().strip()
    if name == "":
        common.fatal("ERROR: name cannot be empty.  Exiting.")
    else:
        parameters["pkg_name"] = pkg_name
        parameters["pkg_name_uppercase"] = pkg_name.upper()
    
    base_class = get_next_answer("Please enter the base class type for this Object (default: 'uvm_object'):\n").lower().strip()
    if base_class == "":
        parameters["base_class"] = "uvm_object"
    else:
        parameters["base_class"] = base_class
    
    #process_file("Object", parameters, files['object']['in'], files['object']['out'])


def gen_reg_block():
    global out_path
    global parameters
    parameters = {
        "year" : date.today().year
    }
    common.info("Moore.io Template Generator: Register Block (v1p0)")
    
    if out_path == "":
        out_path = get_next_answer("Please enter the destination path for this new Register Block (default: '.'):\n").strip()
        if out_path == "":
            out_path = "."
    
    name_of_copyright_owner = common.prompt("Please enter the name of the copyright holder or hit RETURN for the default (default is '" + default_copyright_owner + "'):\n").strip()
    if name_of_copyright_owner == "":
        name_of_copyright_owner = default_copyright_owner
    parameters["name_of_copyright_owner"] = name_of_copyright_owner
    
    name_of_vendor = common.prompt("Please enter a vendor name or hit RETURN for the default (default is '" + default_vendor + "'):\n").strip()
    if name_of_vendor == "":
        name_of_vendor = default_vendor
    parameters["vendor"] = name_of_vendor
    
    license = get_next_answer("Please enter a usage license or hit RETURN for the default (default is '" + default_license + "'):\n").strip()
    if license == "":
        license = default_license
    parameters["license"] = license
    
    name = get_next_answer("Please enter the name for this Register Block (ex: 'top'):\n").lower().strip()
    if name == "":
        common.fatal("ERROR: name cannot be empty.  Exiting.")
    else:
        parameters["name"] = name
        parameters["name_uppercase"] = name.upper()
    
    pkg_name = get_next_answer("Please enter the package name for this Register Block (ex: 'uvme_my_ss'):\n").lower().strip()
    if name == "":
        common.fatal("ERROR: name cannot be empty.  Exiting.")
    else:
        parameters["pkg_name"] = pkg_name
        parameters["pkg_name_uppercase"] = pkg_name.upper()
    
    base_class = get_next_answer("Please enter the base class type for this Register Block (default: 'uvm_reg_block'):\n").lower().strip()
    if base_class == "":
        parameters["base_class"] = "uvm_reg_block"
    else:
        parameters["base_class"] = base_class
    
    #process_file("Register Block", parameters, files['reg_block']['in'], files['reg_block']['out'])


def gen_reg():
    global out_path
    global parameters
    parameters = {
        "year" : date.today().year
    }
    common.info("Moore.io Template Generator: Register (v1p0)")
    
    if out_path == "":
        out_path = get_next_answer("Please enter the destination path for this new Register (default: '.'):\n").strip()
        if out_path == "":
            out_path = "."
    
    name_of_copyright_owner = common.prompt("Please enter the name of the copyright holder or hit RETURN for the default (default is '" + default_copyright_owner + "'):\n").strip()
    if name_of_copyright_owner == "":
        name_of_copyright_owner = default_copyright_owner
    parameters["name_of_copyright_owner"] = name_of_copyright_owner
    
    name_of_vendor = common.prompt("Please enter a vendor name or hit RETURN for the default (default is '" + default_vendor + "'):\n").strip()
    if name_of_vendor == "":
        name_of_vendor = default_vendor
    parameters["vendor"] = name_of_vendor
    
    license = get_next_answer("Please enter a usage license or hit RETURN for the default (default is '" + default_license + "'):\n").strip()
    if license == "":
        license = default_license
    parameters["license"] = license
    
    name = get_next_answer("Please enter the name for this Register (ex: 'status'):\n").lower().strip()
    if name == "":
        common.fatal("ERROR: name cannot be empty.  Exiting.")
    else:
        parameters["name"] = name
        parameters["name_uppercase"] = name.upper()
    
    pkg_name = get_next_answer("Please enter the package name for this Register (ex: 'uvme_my_ss'):\n").lower().strip()
    if name == "":
        common.fatal("ERROR: name cannot be empty.  Exiting.")
    else:
        parameters["pkg_name"] = pkg_name
        parameters["pkg_name_uppercase"] = pkg_name.upper()
    
    base_class = get_next_answer("Please enter the base class type for this Register (default: 'uvm_reg'):\n").lower().strip()
    if base_class == "":
        parameters["base_class"] = "uvm_reg"
    else:
        parameters["base_class"] = base_class
    
    #process_file("Register", parameters, files['reg']['in'], files['reg']['out'])


def gen_test():
    global out_path
    global parameters
    parameters = {
        "year" : date.today().year
    }
    common.info("Moore.io Template Generator: Test (v1p0)")
    
    if out_path == "":
        out_path = get_next_answer("Please enter the destination path for this new Test (default: '.'):\n").strip()
        if out_path == "":
            out_path = "."
    
    name_of_copyright_owner = common.prompt("Please enter the name of the copyright holder or hit RETURN for the default (default is '" + default_copyright_owner + "'):\n").strip()
    if name_of_copyright_owner == "":
        name_of_copyright_owner = default_copyright_owner
    parameters["name_of_copyright_owner"] = name_of_copyright_owner
    
    name_of_vendor = common.prompt("Please enter a vendor name or hit RETURN for the default (default is '" + default_vendor + "'):\n").strip()
    if name_of_vendor == "":
        name_of_vendor = default_vendor
    parameters["vendor"] = name_of_vendor
    
    license = get_next_answer("Please enter a usage license or hit RETURN for the default (default is '" + default_license + "'):\n").strip()
    if license == "":
        license = default_license
    parameters["license"] = license
    
    name = get_next_answer("Please enter the name for this Test (ex: 'smoke'):\n").lower().strip()
    if name == "":
        common.fatal("ERROR: name cannot be empty.  Exiting.")
    else:
        parameters["name"] = name
        parameters["name_uppercase"] = name.upper()
    
    vseq_name = get_next_answer("Please enter the Virtual Sequence name for this Test (ex: 'basic_access'):\n").lower().strip()
    if name == "":
        common.fatal("ERROR: name cannot be empty.  Exiting.")
    else:
        parameters["vseq_name"] = vseq_name
    
    pkg_name = get_next_answer("Please enter the package name for this Test (ex: 'my_ss'):\n").lower().strip()
    if name == "":
        common.fatal("ERROR: name cannot be empty.  Exiting.")
    else:
        parameters["tb_name"] = pkg_name
        parameters["tb_name_uppercase"] = pkg_name.upper()
    
    base_class = get_next_answer("Please enter the base class type for this Test (ex: 'uvm_test'):\n").lower().strip()
    if base_class == "":
        common.fatal("ERROR: base class type cannot be empty.  Exiting.")
    else:
        parameters["base_class"] = base_class
    
    #process_file("Test", parameters, files['test']['in'], files['test']['out'])


def gen_vseq():
    global out_path
    global parameters
    parameters = {
        "year" : date.today().year
    }
    common.info("Moore.io Template Generator: Virtual Sequence (v1p0)")
    
    if out_path == "":
        out_path = get_next_answer("Please enter the destination path for this new Virtual Sequence (default: '.'):\n").strip()
        if out_path == "":
            out_path = "."
    
    
    name_of_copyright_owner = common.prompt("Please enter the name of the copyright holder or hit RETURN for the default (default is '" + default_copyright_owner + "'):\n").strip()
    if name_of_copyright_owner == "":
        name_of_copyright_owner = default_copyright_owner
    parameters["name_of_copyright_owner"] = name_of_copyright_owner
    
    name_of_vendor = common.prompt("Please enter a vendor name or hit RETURN for the default (default is '" + default_vendor + "'):\n").strip()
    if name_of_vendor == "":
        name_of_vendor = default_vendor
    parameters["vendor"] = name_of_vendor
    
    license = get_next_answer("Please enter a usage license or hit RETURN for the default (default is '" + default_license + "'):\n").strip()
    if license == "":
        license = default_license
    parameters["license"] = license
    
    name = get_next_answer("Please enter the name for this Virtual Sequence (ex: 'basic_access'):\n").lower().strip()
    if name == "":
        common.fatal("ERROR: name cannot be empty.  Exiting.")
    else:
        parameters["name"] = name
        parameters["name_uppercase"] = name.upper()
    
    pkg_name = get_next_answer("Please enter the package name for this Virtual Sequence (ex: 'uvme_my_ss'):\n").lower().strip()
    if name == "":
        common.fatal("ERROR: name cannot be empty.  Exiting.")
    else:
        parameters["pkg_name"] = pkg_name
        parameters["pkg_name_uppercase"] = pkg_name.upper()
    
    base_class = get_next_answer("Please enter the base class type for this Virtual Sequence (ex: 'uvme_my_ss_base_vseq_c'):\n").lower().strip()
    if base_class == "":
        common.fatal("ERROR: base class type cannot be empty.  Exiting.")
    else:
        parameters["base_class"] = base_class
    
    #process_file("Virtual Sequence", parameters, files['vseq']['in'], files['vseq']['out'])



########################################################################################################################
# ENTRY POINT
########################################################################################################################
def main(template_name):
    global out_path
    global parameters
    global default_copyright_owner
    global default_vendor
    #if args['-f']:
    #    answers_file = open(args['-f'], "rt")
    
    #pick_out_path()
    
    default_copyright_owner = cfg.org_full_name
    default_vendor          = cfg.org_name
    
    global relative_path_to_template
    relative_path_to_template = cfg.mio_template_dir + "/sets/singleton/"
    
    common.fatal("Not yet implemented.")
    
    if (template_name == 'component'):
        gen_component()
    
    if (template_name == 'object'):
        gen_object()
    
    if (template_name == 'reg'):
        gen_reg()
    
    if (template_name == 'reg_block'):
        gen_reg_block()
    
    if (template_name == 'test'):
        gen_test()
    
    if (template_name == 'vseq'):
        gen_vseq()

