# Copyright 2021-2023 Datum Technology Corporation
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
########################################################################################################################


import jinja2
from jinja2 import Template
from mio import common
from mio import cfg
from mio import user
import re
import os
from datetime import date


uvm_gen_dir               = re.sub("init.py", "", os.path.realpath(__file__)) + ".."
relative_path_to_template = uvm_gen_dir + "/templates/"
project_toml_file_path    = relative_path_to_template + "mio.toml"
dv_ip_file_path           = relative_path_to_template + "dv_ip.yml"
rtl_ip_file_path          = relative_path_to_template + "rtl_ip.yml"
vivado_ip_file_path       = relative_path_to_template + "vivado_ip.yml"
ts_yml_file_path          = relative_path_to_template + "ts.yml.j2"


def new_project(wd):
    common.dbg(f"Using {wd} as working directory")
    common.banner("Welcome to the Moore.io Project Initializer v1.0")
    project_name = ""
    project_full_name = ""
    copyright_owner = ""
    while project_name == "":
        project_name = common.prompt("Please enter the project name (ex: 'example_chip'):").strip().lower()
    while project_full_name == "":
        project_full_name = common.prompt("Please enter the full project name (ex: 'Example Chip'):").strip()
    copyright_owner = user.org_full_name
    try:
        fin = open(project_toml_file_path, "rt")
        data = fin.read()
        template = Template(data)
        data = template.render(name=project_name, full_name=project_full_name, year=date.today().year, name_of_copyright_owner=copyright_owner)
        fout_path = wd + "/mio.toml"
        fout = open(fout_path, "w+")
        common.dbg(f"Writing to {fout_path}")
        fout.write(data)
        fout.close()
        common.create_dir (wd + "/dft"  )
        common.create_dir (wd + "/docs" )
        common.create_dir (wd + "/dv"   )
        common.create_dir (wd + "/lint" )
        common.create_dir (wd + "/rtl"  )
        common.create_dir (wd + "/sim"  )
        common.create_dir (wd + "/syn"  )
        common.create_dir (wd + "/tools")
        
        common.copy_file(relative_path_to_template + "/project_gitignore", wd + "/.gitignore")
        common.copy_file(relative_path_to_template + "/sim_gitignore"    , wd + "/sim/.gitignore")
    except Exception as e:
        common.fatal("Failed to create project structure: " + str(e))
    common.info("Project created successfully.")


def new_ip(wd):
    common.dbg(f"Using {wd} as working directory")
    common.info("Welcome to the Moore.io IP Initializer v1.0")
    common.info("  The following IP types are available:")
    common.info("  [0] - RTL IP")
    common.info("  [1] - Vivado Project IP")
    common.info("  [2] - DV  IP")
    ip_type = -1
    while ip_type != 0 and ip_type != 1 and ip_type != 2:
        ip_type = common.prompt("Please select the type of IP:").strip().lower()
        ip_type = int(ip_type)
    ip_name = ""
    ip_full_name = ""
    copyright_owner = ""
    while ip_name == "":
        ip_name = common.prompt("Please enter the IP name (ex: 'example_ip'):").strip().lower()
    while ip_full_name == "":
        ip_full_name = common.prompt("Please enter the full IP name (ex: 'Example IP'):").strip()
    
    # TODO Improvement: Ask the user for these
    bin_dir  = "bin"
    docs_dir = "docs"
    ex_dir   = "examples"
    src_dir  = "src"
    
    if ip_type == 2:
        create_ip_dirs(wd, bin_dir, docs_dir, ex_dir, src_dir)
        data = new_dv_ip(wd, ip_name, ip_full_name, bin_dir, docs_dir, ex_dir, src_dir)
        try:
            fout_path = wd + "/ip.yml"
            fout = open(fout_path, "w+")
            common.dbg(f"Writing to {fout_path}")
            fout.write(data[0])
            fout.close()
            fout_path = wd + "/" + src_dir + "/ts.yml"
            fout = open(fout_path, "w+")
            common.dbg(f"Writing to {fout_path}")
            fout.write(data[1])
            fout.close()
        except Exception as e:
            common.fatal("Failed to create IP structure: " + str(e))
    else:
        if ip_type == 0:
            create_ip_dirs(wd, bin_dir, docs_dir, ex_dir, src_dir)
            data = new_rtl_ip(wd, ip_name, ip_full_name, bin_dir, docs_dir, ex_dir, src_dir)
        elif ip_type == 1:
            src_dir  = "xsim"
            data = new_viv_ip(wd, ip_name, ip_full_name, bin_dir, docs_dir, ex_dir, src_dir)
        try:
            fout_path = wd + "/ip.yml"
            fout = open(fout_path, "w+")
            common.dbg(f"Writing to {fout_path}")
            fout.write(data)
            fout.close()
        except Exception as e:
            common.fatal("Failed to create IP structure: " + str(e))
    common.info(f"IP {ip_name} initialized successfully.")


def new_dv_ip(wd, name, full_name, bin_dir, docs_dir, ex_dir, src_dir):
    copyright_owner = user.org_full_name
    vendor = user.org_name.lower()
    has_dut = False
    top_file = ""
    top_construct = ""
    dut_name = ""
    fsoc = False
    fsoc_dut_full_name = ""
    fsoc_dut_target = ""
    
    while top_file == "":
        top_file = common.prompt(f"Please enter the top file name (ex: '{name}_pkg.sv'):").strip()
    
    is_tb = ""
    while is_tb not in ["yes", "y", "no", "n"]:
        is_tb = common.prompt("Is this a Test Bench? (y/n)").strip().lower()
    if (is_tb == "y") or (is_tb == "yes"):
        has_dut = True
    
    dut_fsoc  = ""
    if has_dut:
        while dut_fsoc not in ["yes", "y", "no", "n"]:
            dut_fsoc = common.prompt("Is the DUT a FuseSoC Core? (y/n)").strip().lower()
        if (dut_fsoc == "y") or (dut_fsoc == "yes"):
            fsoc = True
            while dut_name == "":
                dut_name = common.prompt("Please enter the DUT FuseSoC Core name (ex: 'core-v-mcu'):").strip().lower()
            while fsoc_dut_full_name == "":
                fsoc_dut_full_name = common.prompt("Please enter the DUT FuseSoC Core fully defined name (ex: 'openhwgroup.org:systems:core-v-mcu'):").strip().lower()
            while fsoc_dut_target == "":
                fsoc_dut_target = common.prompt("Please enter the DUT FuseSoC Core target name (ex: 'xsim'):").strip().lower()
        else:
            while dut_name == "":
                dut_name = common.prompt("Please enter the DUT IP name (ex: '@acme/example'):").strip().lower()
        while top_construct == "":
            top_construct = common.prompt(f"Please enter the Test Bench's top module name (ex: '{name}_tb'):").strip()
    
    template_args = {
        "simulator"               : common.get_simulator_short_name(cfg.default_simulator),
        "bin_dir"                 : bin_dir           ,
        "docs_dir"                : docs_dir          ,
        "ex_dir"                  : ex_dir            ,
        "src_dir"                 : src_dir           ,
        "name"                    : name              ,
        "vendor"                  : vendor            ,
        "full_name"               : full_name         ,
        "has_dut"                 : has_dut           ,
        "top_file"                : top_file          ,
        "top_construct"           : top_construct     ,
        "dut_name"                : dut_name          ,
        "fsoc"                    : fsoc              ,
        "fsoc_dut_full_name"      : fsoc_dut_full_name,
        "fsoc_dut_target"         : fsoc_dut_target   ,
        "year"                    : date.today().year ,
        "name_of_copyright_owner" : copyright_owner
        }
    try:
        fin = open(dv_ip_file_path, "r")
        data = fin.read()
        template = Template(data)
        ip_yml = template.render(template_args)
        fin = open(ts_yml_file_path, "r")
        data = fin.read()
        template = Template(data)
        ts_yml = template.render(template_args)
    except Exception as e:
        common.fatal(f"Failed to create ip.yml at {wd}: {e}")
    return [ip_yml, ts_yml]


def new_rtl_ip(wd, name, full_name, bin_dir, docs_dir, ex_dir, src_dir):
    copyright_owner = user.org_full_name
    vendor = user.org_name.lower()
    
    top_file = ""
    while top_file == "":
        top_file = common.prompt("Please enter the top file name (ex: 'top.sv'):").strip()
    
    template_args = {
        "simulator"               : common.get_simulator_short_name(cfg.default_simulator),
        "bin_dir"                 : bin_dir          ,
        "docs_dir"                : docs_dir         ,
        "ex_dir"                  : ex_dir           ,
        "src_dir"                 : src_dir          ,
        "name"                    : name             ,
        "vendor"                  : vendor           ,
        "full_name"               : full_name        ,
        "top_file"                : top_file         ,
        "year"                    : date.today().year,
        "name_of_copyright_owner" : copyright_owner
        }
    try:
        fin = open(rtl_ip_file_path, "r")
        data = fin.read()
        template = Template(data)
    except Exception as e:
        common.fatal(f"Failed to create ip.yml at {wd}: {e}")
    return template.render(template_args)


def new_viv_ip(wd, name, full_name, bin_dir, docs_dir, ex_dir, src_dir):
    copyright_owner = user.org_full_name
    vendor = user.org_name.lower()
    
    lib_name = ""
    while lib_name != "":
        lib_name = common.prompt("Please enter the Vivado Library Name:").strip()
    
    template_args = {
        "bin_dir"                 : bin_dir          ,
        "docs_dir"                : docs_dir         ,
        "ex_dir"                  : ex_dir           ,
        "src_dir"                 : src_dir          ,
        "name"                    : name             ,
        "vendor"                  : vendor           ,
        "full_name"               : full_name        ,
        "lib_name"                : lib_name         ,
        "year"                    : date.today().year,
        "name_of_copyright_owner" : copyright_owner
        }
    try:
        fin = open(vivado_ip_file_path, "r")
        data = fin.read()
        template = Template(data)
    except Exception as e:
        common.fatal(f"Failed to create ip.yml at {wd}: {e}")
    return template.render(template_args)


def create_ip_dirs(wd, bin_dir, docs_dir, ex_dir, src_dir):
    common.create_dir(wd + f"/{bin_dir}" )
    common.create_dir(wd + f"/{docs_dir}")
    common.create_dir(wd + f"/{ex_dir}"  )
    common.create_dir(wd + f"/{src_dir}" )
