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
uvm_gen_dir = re.sub("new_agent_parallel.py", "", os.path.realpath(__file__)) + ".."
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
# METHODS
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
    channels = []
    dir_1_str = ""
    dir_2_str = ""
    is_duplex = False
    is_be     = False
    
    default_copyright_owner = cfg.org_full_name
    default_vendor          = cfg.org_name
    
    common.info("Moore.io Template Generator: UVM Advanced Parallel Agent - (v1p0)")
    common.info("******************************************************************")
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
    
    name = common.prompt("Please enter the package name for this agent (ex: 'axi'); this name will be used for all agent types (ex: 'uvma_axi_agent_c'):\n").lower().strip()
    if name == "":
        sys.exit("ERROR: package name cannot be empty.  Exiting.")
    
    full_name = common.prompt("Please enter the full name for this agent (ex: 'Advanced eXtensible Interface'):\n").strip()
    if full_name == "":
        sys.exit("ERROR: full name cannot be empty.  Exiting.")
    
    is_mm_str = common.prompt("Is this agent memory mapped?  [N/y]").strip().lower()
    if is_mm_str == "":
        is_mm = False
    else:
        if is_mm_str == "n" or is_mm_str == "no":
            is_mm = False
        elif is_mm_str == "y" or is_mm_str == "yes":
            is_mm = True
        else:
            sys.exit("ERROR: please enter 'y' or 'n'")
    
    if is_mm:
        mode_1 = common.prompt("Please enter the first mode for this new agent (default: 'mstr'):\n").strip().lower()
        if mode_1 == "":
            mode_1 = "mstr"
        mode_2 = common.prompt("Please enter the second mode for this new agent (default: 'slv'):\n").strip().lower()
        if mode_2 == "":
            mode_2 = "slv"
        is_be_str = common.prompt("Does this agent support byte-enabled addressing?  [Y/n]").strip().lower()
        if is_be_str == "":
            is_be = True
        else:
            if is_be_str == "n" or is_be_str == "no":
                is_be = False
            elif is_be_str == "y" or is_be_str == "yes":
                is_be = True
            else:
                sys.exit("ERROR: please enter 'y' or 'n'")
        num_segments_str = common.prompt("How many channels are on the physical interface? (Ex: AXI has 5):\n").strip()
        num_segments = int(num_segments_str)
        if num_segments_str == "" or (num_segments <= 0):
            sys.exit("ERROR: please enter an integer larger than 0")
        if num_segments > 5:
            sys.exit("ERROR: please enter an integer smaller or equal to 5")
        if num_segments > 1:
            for ii in range(num_segments):
                channel_name = common.prompt("Please enter the name for channel #" + str(ii+1) + ":\n").strip().lower()
                if channel_name == "":
                    sys.exit("ERROR: channel name cannot be empty.  Exiting")
                tx_name = common.prompt("Please select which agent mode is the 'tx' for channel '" + channel_name + "': '" + mode_1 + "' or '" + mode_2 + "'\n").strip().lower()
                if tx_name != mode_1 and tx_name != mode_2:
                    sys.exit("ERROR: channel tx must be '" + mode_1 + "' or '" + mode_2 + "'.  Exiting")
                if tx_name == mode_1:
                    rx_name = mode_2
                else:
                    rx_name = mode_1
                channels.append({
                    "tx"   : tx_name,
                    "rx"   : rx_name,
                    "name" : channel_name,
                    "index": ii
                })
        else:
            channels.append({
                "tx"   : mode_1,
                "rx"   : mode_2,
                "name" : "phy",
                "index": 0
            })
    else:
        mode_1 = common.prompt("Please enter the first mode for this new agent (default: 'client'):\n").strip().lower()
        if mode_1 == "":
            mode_1 = "client"
        mode_2 = common.prompt("Please enter the second mode for this new agent (default: 'mac'):\n").strip().lower()
        if mode_2 == "":
            mode_2 = "mac"
        
        is_duplex_str = common.prompt("Is this agent duplex?  [Y/n]").strip().lower()
        if is_duplex_str == "":
            num_segments = 2
            is_duplex = False
        else:
            if is_duplex_str == "n" or is_duplex_str == "no":
                num_segments = 1
                is_duplex = False
            elif is_duplex_str == "y" or is_duplex_str == "yes":
                num_segments = 2
                is_duplex = True
            else:
                common.fatal("ERROR: please enter 'y' or 'n'")
        if is_duplex:
            dir_1_str = common.prompt("Please enter the first direction for this new agent (default: 'tx'):\n").strip().lower()
            if dir_1_str == "":
                dir_1_str = "tx"
            dir_2_str = common.prompt("Please enter the second direction for this new agent (default: 'rx'):\n").strip().lower()
            if dir_2_str == "":
                dir_2_str = "rx"
            channels.append({
                "tx"   : mode_1,
                "rx"   : mode_2,
                "name" : dir_1_str,
                "index": 0
            })
            channels.append({
                "tx"   : mode_2,
                "rx"   : mode_1,
                "name" : dir_2_str,
                "index": 1
            })
        else:
            channels.append({
                "tx"   : mode_1,
                "rx"   : mode_2,
                "name" : "phy",
                "index": 0
            })
    
    mm_agent_files[svg_agent_block_diagrams [num_segments-1]] = "uvma_{{ name }}/docs/agent_block_diagram.svg"
    mm_agent_files[vsdx_agent_block_diagrams[num_segments-1]] = "uvma_{{ name }}/docs/agent_block_diagram.vsdx"
    if is_duplex:
        stream_agent_files[svg_agent_block_diagrams   [-1]] = "uvma_{{ name }}/docs/agent_block_diagram.svg"
        stream_agent_files[vsdx_agent_block_diagrams  [-1]] = "uvma_{{ name }}/docs/agent_block_diagram.vsdx"
        stream_env_files[svg_stream_env_block_diagrams [1]] = "uvme_{{ name }}_st/docs/env_block_diagram.svg"
        stream_env_files[vsdx_stream_env_block_diagrams[1]] = "uvme_{{ name }}_st/docs/env_block_diagram.vsdx"
    else:
        stream_agent_files[svg_agent_block_diagrams    [0]] = "uvma_{{ name }}/docs/agent_block_diagram.svg"
        stream_agent_files[vsdx_agent_block_diagrams   [0]] = "uvma_{{ name }}/docs/agent_block_diagram.vsdx"
        stream_env_files[svg_stream_env_block_diagrams [0]] = "uvme_{{ name }}_st/docs/env_block_diagram.svg"
        stream_env_files[vsdx_stream_env_block_diagrams[0]] = "uvme_{{ name }}_st/docs/env_block_diagram.vsdx"
    
    parameters = {
        "name"                    : name,
        "full_name"               : full_name,
        "name_of_copyright_owner" : name_of_copyright_owner,
        "license"                 : license,
        "year"                    : date.today().year,
        "mm"                      : is_mm,
        "sbe"                     : is_be,
        "mode_1"                  : mode_1,
        "mode_2"                  : mode_2,
        "dir_1"                   : dir_1_str,
        "dir_2"                   : dir_2_str,
        "duplex"                  : is_duplex,
        "segments"                : channels,
        "num_segments"            : num_segments,
        "multisegment"            : (len(channels) > 1),
        "vendor"                  : name_of_vendor
    }
    
    # Flatten some parameters for svg
    sequencer = 0
    driver = 0
    chan_id = 0
    for channel in channels:
        parameters['sqrn' + str(sequencer)] = mode_1 + "_" + channel['name']
        parameters['sqrt' + str(sequencer)] = name + "_" + mode_1 + "_" + channel['name']
        sequencer += 1
        parameters['sqrn' + str(sequencer)] = mode_2 + "_" + channel['name']
        parameters['sqrt' + str(sequencer)] = name + "_" + mode_2 + "_" + channel['name']
        sequencer += 1
        parameters['drvn' + str(driver)] = mode_1 + "_" + channel['name']
        parameters['drvt' + str(driver)] = name + "_" + mode_1 + "_" + channel['name']
        parameters['dmp' + str(driver)] = "drv_" + mode_1 + "_" + channel['name'] + "_mp"
        driver += 1
        parameters['drvn' + str(driver)] = mode_2 + "_" + channel['name']
        parameters['drvt' + str(driver)] = name + "_" + mode_2 + "_" + channel['name']
        parameters['dmp' + str(driver)] = "drv_" + mode_2 + "_" + channel['name'] + "_mp"
        driver += 1
        parameters['mmp' + str(chan_id)] = "mon_" + channel['name'] + "_mp"
        chan_id += 1


def gen_agent():
    common.fatal("Not implemented yet.")


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
