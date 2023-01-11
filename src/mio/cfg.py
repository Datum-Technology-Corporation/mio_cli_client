# Copyright 2021-2023 Datum Technology Corporation
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
########################################################################################################################


from mio import clean
from mio import cov
from mio import dox
from mio import results
from mio import sim
from mio import common

import jinja2
import os
import sys
import re
import pathlib
import toml

cli_args = None
dbg             = True
sim_debug       = False
sim_gui         = False
sim_waves       = False
sim_cov         = False
glb_args = {}
glb_cfg  = {}

#version_str = 'Moore.io Client Command Line Interface 1.2.0'
mio_client_dir    = re.sub("cfg.py", "", os.path.realpath(__file__))
mio_data_src_dir  = str(pathlib.Path(os.path.join(mio_client_dir, "../data")).resolve())
mio_template_dir  = str(pathlib.Path(os.path.join(mio_client_dir, "../templates")).resolve())
vivado_home       = os.getenv("MIO_VIVADO_HOME" , '/tools/vivado/2022.1/Vivado/2022.1/bin/')
metrics_home      = os.getenv("MIO_METRICS_HOME", '/tools/metrics/')
vcs_home          = os.getenv("MIO_VCS_HOME"    , '/tools/vcs/'    )
xcelium_home      = os.getenv("MIO_XCELIUM_HOME", '/tools/xcelium/')
questa_home       = os.getenv("MIO_QUESTA_HOME" , '/tools/questa/' )
riviera_home      = os.getenv("MIO_RIVIERA_HOME", '/tools/riviera/')
uvm_dpi_so        = "uvm_dpi"
user_dir          = os.path.expanduser("~")
mio_user_dir      = user_dir + "/.mio"
user_global_ips_path = mio_user_dir + "/vendors"
global_ips_path = ""
org_name      = ""
org_full_name = ""
default_simulator = common.simulators_enum.VIVADO
uvm_version = ""

pwd                   = ""
temp_path             = ""
project_dir           = ""
project_name          = ""
sim_dir               = ""
sim_results_dir       = ""
regr_results_dir      = ""
mio_data_dir          = ""
fsoc_dir              = ""
sim_output_dir        = ""
dependencies_path     = ""
ip_cache_file_path    = ""
fsoc_cache_file_path  = ""
job_history_file_path = ""
commands_file_path    = ""
user_file_path        = mio_user_dir + "/user.yml"
builtin_ip_path       = ""
user_mio_file         = mio_user_dir + "/mio.toml"

sim_timescale   = ""
regression_name = ""
test_suite_name = ""
test_results_path_template = ""
encryption_key_path_vivado = ""
encryption_key_path_metrics = ""

templateLoader = jinja2.FileSystemLoader(searchpath=mio_template_dir)
templateEnv    = jinja2.Environment(loader=templateLoader)

fresh_fsoc_cache = False
fresh_ip_cache = False

ip_paths = []
job_history = {}
configuration = {}
ip_local_cache = {}
ip_external_cache = {}
fsoc_cache = None
target_ip = None
target_ip_name = ""
target_ip_is_local = False

project_toml_file_path = "./mio.toml"



def set_pwd(wd):
    global pwd
    pwd = str(wd.resolve())




def set_project_dir(path):
    global project_dir 
    global mio_data_dir
    global temp_path
    global fsoc_dir
    global sim_output_dir
    global dependencies_path
    global builtin_ip_path
    global ip_cache_file_path
    global fsoc_cache_file_path
    global job_history_file_path
    global commands_file_path
    project_dir           = path
    mio_data_dir          = project_dir + "/.mio"
    temp_path             = mio_data_dir + '/temp'
    fsoc_dir              = mio_data_dir + "/fsoc"
    sim_output_dir        = mio_data_dir + "/sim"
    dependencies_path     = mio_data_dir + "/vendors"
    builtin_ip_path       = mio_data_src_dir + "/ip"
    commands_file_path    = mio_data_dir + "/commands.yml"
    fsoc_cache_file_path  = mio_data_dir + "/fsoc_cache.yml"
    ip_cache_file_path    = mio_data_dir + "/ip_cache.yml"
    job_history_file_path = mio_data_dir + "/job_history.yml"




def load_configuration():
    global configuration
    global project_name
    global sim_dir
    global sim_results_dir
    global regr_results_dir
    global ip_paths
    global test_results_path_template
    global encryption_key_path_vivado
    global encryption_key_path_metrics
    global org_name
    global org_full_name
    global global_ips_path
    global default_simulator
    global uvm_version
    global sim_timescale
    
    project_name      = configuration.get("project", {}).get("name")
    #org_name          = user.user_data['org-name']
    #org_full_name     = user.user_data['org-full-name']
    sim_dir           = os.path.join(project_dir, configuration.get("simulation", {}).get("root-path"))
    sim_results_dir   = os.path.join(sim_dir    , configuration.get("simulation", {}).get("results-dir"))
    regr_results_dir  = os.path.join(sim_dir    , configuration.get("simulation", {}).get("regressions-dir"))
    uvm_version                = configuration.get("simulation", {}).get("uvm-version").strip()
    sim_timescale              = configuration.get("simulation", {}).get("timescale").strip()
    test_results_path_template = configuration.get("simulation", {}).get("test-result-path-template").strip()
    default_simulator_str      = configuration.get("simulation", {}).get("default-simulator").strip()
    
    encryption_key_path_vivado  = configuration.get("encryption", {}).get("vivado-key-path" ).strip().replace("~", user_dir)
    encryption_key_path_metrics = configuration.get("encryption", {}).get("metrics-key-path").strip().replace("~", user_dir)
    
    org_name      = configuration.get("org", {}).get("name").strip()
    org_full_name = configuration.get("org", {}).get("full-name").strip()
    
    global_ips_path = configuration.get("ip", {}).get("global-paths")
    ip_paths        = configuration.get("ip", {}).get("paths")
    
    if not encryption_key_path_vivado == None:
        encryption_key_path_vivado = encryption_key_path_vivado.replace("~", user_dir)
    if not encryption_key_path_metrics == None:
        encryption_key_path_metrics = encryption_key_path_metrics.replace("~", user_dir)
    
    if default_simulator_str == "viv":
        default_simulator = common.simulators_enum.VIVADO
    elif default_simulator_str == "vcs":
        default_simulator = common.simulators_enum.VCS
    elif default_simulator_str == "mdc":
        default_simulator = common.simulators_enum.METRICS
    elif default_simulator_str == "xcl":
        default_simulator = common.simulators_enum.XCELIUM
    elif default_simulator_str == "qst":
        default_simulator = common.simulators_enum.QUESTA
    elif default_simulator_str == "riv":
        default_simulator = common.simulators_enum.RIVIERA
    else:
        common.warning(f"Default simulator selected ('{default_simulator_str}') is invalid.  Using vivado.")
        default_simulator = common.simulators_enum.VIVADO




def find_project_descriptor():
    global project_toml_file_path
    found_file = False
    current_dir = pwd
    while found_file == False:
        if not os.path.exists(current_dir):
            return False
        else:
            project_toml_file_path = os.path.join(current_dir, "mio.toml")
            project_toml_file_path = str(pathlib.Path(project_toml_file_path).resolve())
            if not os.path.exists(project_toml_file_path):
                current_dir = os.path.join(current_dir, "..")
            else:
                found_file = True
                set_project_dir(current_dir)
                common.dbg("Found Moore.io project TOML Configuration file at " + project_toml_file_path)
    return found_file




def load_tree():
    global configuration
    builtin_toml_file_path = os.path.join(mio_data_src_dir, "mio.toml")
    user_toml_file_path    = os.path.join(mio_user_dir    , "mio.toml")
    
    try:
        configuration = toml.load(builtin_toml_file_path)
    except Exception as e:
        common.fatal(f"Failed to parse Built-in Configuration ({builtin_toml_file_path}): {e}", False)
    if os.path.exists(user_toml_file_path):
        try:
            common.merge_dict(configuration, toml.load(user_toml_file_path))
        except Except as e:
            common.fatal(f"Failed to parse User Configuration ({user_toml_file_path}): {e}", False)
        common.dbg("Found Moore.io user TOML Configuration file at " + user_toml_file_path)
    try:
        common.merge_dict(configuration, toml.load(project_toml_file_path))
    except Exception as e:
        common.fatal(f"Failed to parse Project Configuration ({project_toml_file_path}): {e}", False)
    common.dbg("Final configuration:\n" + toml.dumps(configuration))
