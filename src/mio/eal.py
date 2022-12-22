# Copyright 2022 Datum Technology Corporation
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
########################################################################################################################

from mio import user
from mio import common
from mio import cache
from mio import cfg
from mio import sim
from jinja2 import Template
from fusesoc import main as fsoc
from tqdm import tqdm
import fusesoc
import atexit
import pathlib
import argparse
import os
import subprocess
import re
import yaml
import glob
from yaml.loader import SafeLoader
from threading import BoundedSemaphore

eda_processes = []
bar = None

vivado_default_compilation_args  = ["--incr", "-sv"]
metrics_default_compilation_args = ["+acc+b", "-suppress MultiBlockWrite:ReadingOutputModport:UndefinedMacro"]
vcs_default_compilation_args     = ["-lca", "-sverilog"]
xcelium_default_compilation_args = []
questa_default_compilation_args  = ["-64", "-incrcomp"]
riviera_default_compilation_args = []

vivado_project_default_vlog_compilation_args = ["--relax"]
vivado_project_default_vhdl_compilation_args = ["--relax"]

vivado_default_gen_image_args  = ["--incr", "-sv", "-relax", "--O0", "-v 0", "-timescale 1ns/1ps", "-dup_entity_as_module"]
metrics_default_gen_image_args = ["+acc+b", "-suppress MultiBlockWrite:ReadingOutputModport:UndefinedMacro:DupModuleDefn"]
vcs_default_gen_image_args     = ["-lca", "-sverilog"]
xcelium_default_gen_image_args = []
questa_default_gen_image_args  = ["-64", "-incrcomp"]
riviera_default_gen_image_args = []

vivado_default_elaboration_args  = ["--incr", "-relax", "--O0", "-v 0", "-dup_entity_as_module"]
metrics_default_elaboration_args = ["+acc+b", "-suppress DupModuleDefn"]
vcs_default_elaboration_args     = []
xcelium_default_elaboration_args = []
questa_default_elaboration_args  = ["-64"]
riviera_default_elaboration_args = []

vivado_default_simulation_args  = ["--stats"]
metrics_default_simulation_args = []
vcs_default_simulation_args     = []
xcelium_default_simulation_args = []
questa_default_simulation_args  = ["-64", "-c"]
riviera_default_simulation_args = []

vivado_cmp_log_error_regexes  = ["ERROR:", "CRITICAL WARNING:"]
metrics_cmp_log_error_regexes = ["=E:", "=F:"]
vcs_cmp_log_error_regexes     = ["Error-"]
xcelium_cmp_log_error_regexes = ["*E "]
questa_cmp_log_error_regexes  = ["\*\* Error:"]
riviera_cmp_log_error_regexes = ["Error:"]

vivado_cmp_log_warning_regexes  = ["WARNING:"]
metrics_cmp_log_warning_regexes = ["=W:"]
vcs_cmp_log_warning_regexes     = ["Warning-"]
xcelium_cmp_log_warning_regexes = ["*W "]
questa_cmp_log_warning_regexes  = ["\*\* Warning:"]
riviera_cmp_log_warning_regexes = ["Warning:"]

vivado_elab_log_error_regexes  = ["ERROR:","Invalid path for DPI library:"]
metrics_elab_log_error_regexes = ["=E:", "=F:"]
vcs_elab_log_error_regexes     = ["Error-"]
xcelium_elab_log_error_regexes = ["*E "]
questa_elab_log_error_regexes  = ["\*\* Error:"]
riviera_elab_log_error_regexes = ["Error:"]

vivado_elab_log_warning_regexes  = ["WARNING:"]
metrics_elab_log_warning_regexes = ["=W:"]
vcs_elab_log_warning_regexes     = ["Warning-"]
xcelium_elab_log_warning_regexes = ["*W "]
questa_elab_log_warning_regexes  = ["\*\* Warning:"]
riviera_elab_log_warning_regexes = ["Warning:"]

vivado_gen_image_log_error_regexes  = ["ERROR:", "CRITICAL WARNING:"]
metrics_gen_image_log_error_regexes = ["=E:", "=F:", "error:"]
vcs_gen_image_log_error_regexes     = ["Error-"]
xcelium_gen_image_log_error_regexes = ["*E "]
questa_gen_image_log_error_regexes  = ["\*\* Error:"]
riviera_gen_image_log_error_regexes = ["Error:"]

vivado_gen_image_log_warning_regexes  = ["WARNING:"]
metrics_gen_image_log_warning_regexes = ["=W:"]
vcs_gen_image_log_warning_regexes     = ["Warning-"]
xcelium_gen_image_log_warning_regexes = ["*W "]
questa_gen_image_log_warning_regexes  = ["\*\* Warning:"]
riviera_gen_image_log_warning_regexes = ["Warning:"]

sem = BoundedSemaphore(1)


def compile_fsoc_core(flist_path, core, sim_job):
    defines = sim_job.cmp_args
    timestamp_start = common.timestamp()
    var_name = "MIO_" + core.sname.replace("-", "_").upper() + "_SRC_PATH"
    os.environ[var_name] = core.dir
    sim_job.bwrap_flists[var_name] = "$PROJECT_ROOT_DIR/" + os.path.relpath(core.dir, cfg.project_dir)
    common.dbg(f"FuseSoC env var '{var_name}'='{core.dir}'")
    vendor = "@fsoc"
    log_file_path = compile_flist(vendor, core.sname, flist_path, [], sim_job, local=True)
    if not sim_job.dry_run:
        timestamp_end = common.timestamp()
        errors = scan_cmp_log_file_for_errors(log_file_path, sim_job)
        if len(errors):
            common.error("Errors during compilation of FuseSoC core '" + core.name + "':")
            for error in errors:
                common.error("  " + error)
            sim.kill_progress_bar()
            common.fatal("Stopping due to compilation.")
        log_cmp_history_fsoc(core, log_file_path, sim_job, timestamp_start, timestamp_end)
    return log_file_path


def gen_ip_image(ip, sim_job, fsoc_core_name, fsoc_core_flist_path):
    ip_str = f"{ip.vendor}/{ip.name}"
    ip_dir = f"{ip.vendor}__{ip.name}"
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    deps_list  = get_dep_list(ip, sim_job)
    flist_path = gen_master_flist(ip, sim_job, deps_list, fsoc_core_name, fsoc_core_flist_path)
    
    for dep in deps_list:
        prep_ip_for_gen_image(dep, sim_job)
    prep_ip_for_gen_image(ip, sim_job)
    
    timestamp_start = common.timestamp()
    log_file_path = gen_image_flist(ip, ip.vendor, ip.name, flist_path, sim_job, ip.is_local)
    if not sim_job.dry_run:
        timestamp_end = common.timestamp()
        errors = scan_gen_image_log_file_for_errors(log_file_path, sim_job)
        if len(errors):
            common.error("Errors during compilation/elaboration of IP '" + ip_str + "':")
            for error in errors:
                common.error("  " + error)
            sim.kill_progress_bar()
            common.fatal("Stopping due to compilation/elaborationn errors. Full log: " + log_file_path)
        log_gen_image_history_ip(ip, log_file_path, sim_job, timestamp_start, timestamp_end)
        ip.is_compiled  [sim_job.simulator] = True
        ip.is_elaborated[sim_job.simulator] = True
    return log_file_path


def prep_ip_for_gen_image(ip, sim_job):
    ip_str = f"{ip.vendor}/{ip.name}"
    ip_dir = f"{ip.vendor}__{ip.name}"
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    if sim_job.bwrap:
        if ip.is_global:
            if ip.is_encrypted:
                common.copy_directory(ip.path + "/" + ip.src_path + "." + sim_str, f"{cfg.temp_path}/{ip_dir}")
            else:
                common.copy_directory(ip.path + "/" + ip.src_path, f"{cfg.temp_path}/{ip_dir}")
            path = "${PROJECT_ROOT_DIR}/.mio/temp/" + ip_dir
        else:
            if ip.is_encrypted:
                path = "${PROJECT_ROOT_DIR}/" + os.path.relpath(ip.path + "/" + ip.src_path + "." + sim_str, cfg.project_dir)
            else:
                path = "${PROJECT_ROOT_DIR}/" + os.path.relpath(ip.path + "/" + ip.src_path, cfg.project_dir)
    elif ip.is_global and (sim_job.simulator == common.simulators_enum.METRICS):
        if ip.is_encrypted:
            common.copy_directory(ip.path + "/" + ip.src_path + "." + sim_str, f"{cfg.temp_path}/{ip_dir}")
            path = ".mio/temp/" + ip_dir
        else:
            common.copy_directory(ip.path + "/" + ip.src_path, f"{cfg.temp_path}/{ip_dir}")
            path = ".mio/temp/" + ip_dir
    else:
        if ip.is_encrypted:
            path = ip.path + "/" + ip.src_path + "." + sim_str
        else:
            path = ip.path + "/" + ip.src_path
    
    flist_env_var_name = 'MIO_' + ip.name.upper() + '_SRC_PATH'
    os.environ[flist_env_var_name] = path
    sim_job.bwrap_flists[flist_env_var_name] = path



def compile_ip(ip, sim_job):
    ip_str = f"{ip.vendor}/{ip.name}"
    ip_dir = f"{ip.vendor}__{ip.name}"
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    flist_path = get_ip_flist_path(ip, sim_job)
    deps_list  = get_dep_list(ip, sim_job)
    if sim_job.bwrap:
        if ip.is_global:
            if ip.is_encrypted:
                common.copy_directory(ip.path + "/" + ip.src_path + "." + sim_str, f"{cfg.temp_path}/{ip_dir}")
            else:
                common.copy_directory(ip.path + "/" + ip.src_path, f"{cfg.temp_path}/{ip_dir}")
            path = "${PROJECT_ROOT_DIR}/.mio/temp/" + ip_dir
        else:
            if ip.is_encrypted:
                path = "${PROJECT_ROOT_DIR}/" + os.path.relpath(ip.path + "/" + ip.src_path + "." + sim_str, cfg.project_dir)
            else:
                path = "${PROJECT_ROOT_DIR}/" + os.path.relpath(ip.path + "/" + ip.src_path, cfg.project_dir)
    elif ip.is_global and (sim_job.simulator == common.simulators_enum.METRICS):
        if ip.is_encrypted:
            common.copy_directory(ip.path + "/" + ip.src_path + "." + sim_str, f"{cfg.temp_path}/{ip_dir}")
            path = ".mio/temp/" + ip_dir
        else:
            common.copy_directory(ip.path + "/" + ip.src_path, f"{cfg.temp_path}/{ip_dir}")
            path = ".mio/temp/" + ip_dir
    else:
        if ip.is_encrypted:
            path = ip.path + "/" + ip.src_path + "." + sim_str
        else:
            path = ip.path + "/" + ip.src_path
    
    if (not sim_job.bwrap) and sim_job.simulator == common.simulators_enum.METRICS:
        set_uvm_version(sim_job)
        flist_path = os.path.relpath(flist_path, cfg.project_dir)
    
    if sim_job.bwrap:
        flist_path = os.path.relpath(flist_path, cfg.project_dir)
    
    flist_env_var_name = 'MIO_' + ip.name.upper() + '_SRC_PATH'
    os.environ[flist_env_var_name] = path
    sim_job.bwrap_flists[flist_env_var_name] = path
    timestamp_start = common.timestamp()
    log_file_path = compile_flist(ip.vendor, ip.name, flist_path, deps_list, sim_job, ip.is_local)
    if not sim_job.dry_run:
        timestamp_end = common.timestamp()
        errors = scan_cmp_log_file_for_errors(log_file_path, sim_job)
        if len(errors):
            common.error("Errors during compilation of IP '" + ip_str + "':")
            for error in errors:
                common.error("  " + error)
            sim.kill_progress_bar()
            common.fatal("Stopping due to compilation errors. Full log: " + log_file_path)
        log_cmp_history_ip(ip, log_file_path, sim_job, timestamp_start, timestamp_end)
        ip.is_compiled[sim_job.simulator] = True
    return log_file_path


def compile_vivado_project(ip, sim_job):
    ip_str = f"{ip.vendor}/{ip.name}"
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    defines = sim_job.cmp_args
    dep_list = get_dep_list(ip, sim_job)
    timestamp_start = common.timestamp()
    log_file_paths = do_compile_vivado_project(ip, dep_list, sim_job)
    if not sim_job.dry_run:
        timestamp_end = common.timestamp()
        errors = scan_cmp_log_file_for_errors(log_file_paths[0], sim_job)
        errors.append(scan_cmp_log_file_for_errors(log_file_paths[1], sim_job))
        if len(errors):
            common.error("Errors during compilation of Vivado Project IP '" + ip_str + "':")
            for error in errors:
                common.error("  " + error)
            sim.kill_progress_bar()
            common.fatal("Stopping due to compilation errors. Logs: " + log_file_paths[0] + " & " + log_file_paths[0])
        log_cmp_history_vivado_project(ip, log_file_paths[0], log_file_paths[1], sim_job, timestamp_start, timestamp_end)
        ip.is_compiled[sim_job.simulator] = True
    return log_file_paths


def elaborate(ip, sim_job):
    ip_str = f"{ip.vendor}/{ip.name}"
    ip_dir_name = f"{ip.vendor}__{ip.name}"
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    defines = sim_job.cmp_args
    if sim_job.is_regression:
        ip_dir_name = f"{ip.vendor}__{ip.name}__{sim_job.regression_name}"
        common.create_dir(cfg.sim_output_dir + "/" + sim_str + "/regr_wd/" + ip_dir_name)
        common.create_dir(cfg.sim_output_dir + "/" + sim_str + "/regr_wd/" + ip_dir_name + "/" + sim_job.regression_timestamp)
        elab_out =        cfg.sim_output_dir + "/" + sim_str + "/regr_wd/" + ip_dir_name + "/" + sim_job.regression_timestamp
    else:
        ip_dir_name = f"{ip.vendor}__{ip.name}"
        elab_out = cfg.sim_output_dir + "/" + sim_str + "/sim_wd"
    common.create_dir(elab_out)
    timestamp_start = common.timestamp()
    log_file_path = do_elaborate(ip, sim_job, elab_out)
    if not sim_job.dry_run:
        timestamp_end = common.timestamp()
        errors = scan_elab_log_file_for_errors(log_file_path, sim_job)
        if len(errors):
            common.error("Errors during elaboration of IP '" + ip_str + "':")
            for error in errors:
                common.error("  " + error)
            sim.kill_progress_bar()
            common.fatal("Stopping due to elaboration errors. Full log: " + log_file_path)
        log_elab_history(ip, log_file_path, sim_job, timestamp_start, timestamp_end)
        ip.is_elaborated[sim_job.simulator] = True
    return elab_out


def simulate(ip, sim_job):
    ip_str = f"{ip.vendor}/{ip.name}"
    ip_dir_name = f"{ip.vendor}__{ip.name}"
    sim_args = sim_job.sim_args
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    global sem
    start = common.timestamp()
    log_sim_start_history(ip, sim_job, start)
    if sim_job.is_regression:
        ip_dir_name = f"{ip.vendor}__{ip.name}__{sim_job.regression_name}"
        sim_out = cfg.sim_output_dir + "/" + sim_str + "/regr_wd/" + ip_dir_name + "/" + sim_job.regression_timestamp
    else:
        ip_dir_name = f"{ip.vendor}__{ip.name}"
        sim_out = cfg.sim_output_dir + "/" + sim_str + "/sim_wd"
    do_simulate(ip, sim_job, sim_out)
    if not sim_job.dry_run:
        sem.acquire()
        log_sim_end_history(ip, sim_job, start, common.timestamp())
        sem.release()


def init_metrics_workspace():
    mdc_path = cfg.project_dir + "/.mdc"
    if not os.path.exists(mdc_path):
        common.info("Initializing Metrics workspace, this will take a few minutes ...")
        launch_eda_bin(cfg.metrics_home + "/mdc", ["initialize"], wd=cfg.project_dir)
        launch_eda_bin(cfg.metrics_home + "/mdc", ["status"], wd=cfg.project_dir, output=True)
        sync_ignore_filepath = f"{mdc_path}/sync_ignore"
        if os.path.exists(sync_ignore_filepath):
            with open(sync_ignore_filepath, "a") as f:
                src_dir_name = cfg.configuration.get("simulation", {}).get("root-path")
                f.writelines([".mio/sim", src_dir_name, "tools", "syn", "dft", "lint", "docs"])
        else:
            common.fatal(f"Failed to initialize Metrics Cloud Simulator workspace")


def gen_image_flist(ip, vendor, name, flist_path, sim_job, local):
    defines = sim_job.cmp_args
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    arg_list = []
    cmp_args_list = convert_compilation_args(sim_job)
    
    ip_dir_name = f"{vendor}__{name}"
    ip_regr_root_path = cfg.sim_output_dir + "/" + sim_str + "/regr_wd/" + ip_dir_name + "__" + sim_job.regression_name + "/"
    if sim_job.is_regression:
        cmp_out = ip_regr_root_path + sim_job.regression_timestamp
    else:
        cmp_out = cfg.sim_output_dir + "/" + sim_str + "/sim_wd"
    
    if sim_job.simulator != common.simulators_enum.METRICS:
        if sim_job.is_regression:
            common.create_dir(ip_regr_root_path)
        common.create_dir(cmp_out)
    
    compilation_log_path = cfg.sim_dir + "/cmp/" + ip_dir_name + "." + sim_str + ".log"
    compilation_command_file = f"{ip_dir_name}.{sim_str}.gen_image.cmd.txt"
    
    if sim_job.simulator == common.simulators_enum.VIVADO:
        # Not yet supported for vivado
        # 1) Finish assembly of prj file
        # 2) Parse user vivado flists OR drop them for vivado entirely
        arg_list.append("-prj " + flist_path)
        arg_list += vivado_default_gen_image_args
        arg_list += cmp_args_list
        arg_list.append("-L uvm")
        arg_list.append(f"-s {ip_dir_name}")
        arg_list.append("--log "  + compilation_log_path)
        write_cmd_to_disk(sim_job, "xelab", arg_list, compilation_command_file)
        sim_job.bwrap_commands += launch_eda_bin(cfg.vivado_home + "/xelab", arg_list, wd=cmp_out, output=cfg.dbg, dry_run=sim_job.dry_run)
        
    elif sim_job.simulator == common.simulators_enum.VCS:
        arg_list += vcs_default_gen_image_args
        arg_list.append(license_macros_file_path);
        arg_list.append("-f " + flist_path)
        arg_list += cmp_args_list
        arg_list += deps_list
        arg_list.append("-l "  + compilation_log_path)
        write_cmd_to_disk(sim_job, "vcs", arg_list, compilation_command_file)
        sim_job.bwrap_commands += launch_eda_bin(cfg.vcs_home + "/vcs", arg_list, wd=cmp_out, output=cfg.dbg, dry_run=sim_job.dry_run)
        
    elif sim_job.simulator == common.simulators_enum.METRICS:
        arg_list += metrics_default_gen_image_args
        arg_list.append("-F " + flist_path)
        mtr_compilation_log_path = ip_dir_name + "." + sim_str + ".log"
        arg_list.append("-l " + mtr_compilation_log_path)
        arg_list.append(f"-timescale {cfg.sim_timescale}")
        
        if ip.vendor == "@global":
            arg_list.append(f"-genimage global__{ip.name}")
        elif ip.vendor == "@fsoc":
            arg_list.append(f"-genimage fsoc__{ip.name}")
        else:
            arg_list.append(f"-genimage {ip.vendor}__{ip.name}")
        
        for construct in ip.hdl_src_top_constructs:
            if "." in construct:
                lib,name = construct.split(".")
                arg_list.append(f"-top {name}")
            else:
                arg_list.append(f"-top {construct}")
        
        arg_list_str = ""
        for arg in arg_list:
            arg_list_str = arg_list_str + f" {arg}"
        if cfg.dbg:
            arg_list = [f"dsim -v -a '{arg_list_str}'"]
        else:
            arg_list = [f"dsim -a '{arg_list_str}'"]
        write_cmd_to_disk(sim_job, "mdc", arg_list, compilation_command_file)
        sim_job.bwrap_commands += launch_eda_bin(cfg.metrics_home + "/mdc", arg_list, wd=cfg.project_dir, output=cfg.dbg, dry_run=sim_job.dry_run)
        launch_eda_bin(cfg.metrics_home + "/mdc", ["download", mtr_compilation_log_path], wd=cfg.project_dir, output=cfg.dbg, dry_run=sim_job.dry_run)
        if not sim_job.dry_run:
            common.move_file(f"{cfg.project_dir}/_downloaded_{mtr_compilation_log_path}", compilation_log_path)
        
    elif sim_job.simulator == common.simulators_enum.XCELIUM:
        arg_list += xcelium_default_gen_image_args
        arg_list.append(license_macros_file_path);
        arg_list.append("-f " + flist_path)
        # TODO Add compilation output argument for nc
        write_cmd_to_disk(sim_job, "xrun", arg_list, compilation_command_file)
        sim_job.bwrap_commands += launch_eda_bin(cfg.nc_home + "/xrun", arg_list, wd=cmp_out, output=cfg.dbg, dry_run=sim_job.dry_run)
        
    elif sim_job.simulator == common.simulators_enum.QUESTA:
        os.environ['MIO_UVM_HOME'] = f"$MIO_QUESTA_HOME/../verilog_src/uvm-{cfg.uvm_version}"
        arg_list += questa_default_gen_image_args
        arg_list.append(license_macros_file_path);
        arg_list.append("-f " + flist_path)
        arg_list += cmp_args_list
        arg_list += deps_list
        arg_list.append(f"-Ldir {cmp_out_dir}")
        arg_list.append("-l "  + compilation_log_path)
        arg_list.append(f"-work {name}")
        write_cmd_to_disk(sim_job, "vlog", arg_list, compilation_command_file)
        sim_job.bwrap_commands += launch_eda_bin(cfg.questa_home + "/vlog", arg_list, wd=cmp_out, output=cfg.dbg)
        
    elif sim_job.simulator == common.simulators_enum.RIVIERA:
        arg_list += riviera_default_gen_image_args
        arg_list.append(license_macros_file_path);
        arg_list.append("-f " + flist_path)
        # TODO Add compilation output argument for riviera
        write_cmd_to_disk(sim_job, "vlog", arg_list, compilation_command_file)
        sim_job.bwrap_commands += launch_eda_bin(cfg.riviera_home + "/vlog", arg_list, wd=cmp_out, output=cfg.dbg, dry_run=sim_job.dry_run)
    
    return compilation_log_path



def compile_flist(vendor, name, flist_path, deps, sim_job, local, licensed=True):
    defines = sim_job.cmp_args
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    arg_list = []
    cmp_args_list = convert_compilation_args(sim_job)
    deps_list     = convert_deps_to_args(deps, sim_job)
    incdir_list   = get_incdir_list(deps, sim_job)
    
    #if licensed:
    #    license_ip = cache.get_ip("datum", "uvml_mio_lic", True)
    #    license_macros_file_path = license_ip.path + "/" + license_ip.src_path + "/uvml_mio_lic_macros.svh"
    license_macros_file_path = ""
    
    ip_dir_name = f"{vendor}__{name}"
    cmp_out_dir = cfg.sim_output_dir + "/" + sim_str + "/cmp_out/"
    cmp_out = cmp_out_dir + ip_dir_name
    sim_out = cfg.sim_output_dir + "/" + sim_str + "/sim_wd"
    
    if sim_job.simulator != common.simulators_enum.METRICS:
        common.create_dir(cmp_out)
        common.create_dir(sim_out)
    
    compilation_log_path = cfg.sim_dir + "/cmp/" + ip_dir_name + "." + sim_str + ".cmp.log"
    compilation_command_file = f"{ip_dir_name}.{sim_str}.cmp.cmd.txt"
    
    if sim_job.simulator == common.simulators_enum.VIVADO:
        arg_list += vivado_default_compilation_args
        arg_list += incdir_list
        arg_list.append(license_macros_file_path);
        arg_list.append("-f " + flist_path)
        arg_list += cmp_args_list
        arg_list.append("-L uvm")
        arg_list.append(f"--uvm_version {cfg.uvm_version}")
        arg_list += deps_list
        arg_list.append(f"--work {name}={cmp_out}")
        arg_list.append("--log "  + compilation_log_path)
        write_cmd_to_disk(sim_job, "xvlog", arg_list, compilation_command_file)
        sim_job.bwrap_commands += launch_eda_bin(cfg.vivado_home + "/xvlog", arg_list, wd=sim_out, output=cfg.dbg, dry_run=sim_job.dry_run)
        
    elif sim_job.simulator == common.simulators_enum.VCS:
        arg_list += vcs_default_compilation_args
        arg_list.append(license_macros_file_path);
        arg_list.append("-f " + flist_path)
        arg_list += cmp_args_list
        arg_list += deps_list
        arg_list.append("-l "  + compilation_log_path)
        write_cmd_to_disk(sim_job, "vcs", arg_list, compilation_command_file)
        sim_job.bwrap_commands += launch_eda_bin(cfg.vcs_home + "/vcs", arg_list, wd=sim_out, output=cfg.dbg, dry_run=sim_job.dry_run)
        
    elif sim_job.simulator == common.simulators_enum.METRICS:
        arg_list += metrics_default_compilation_args
        arg_list += incdir_list
        if vendor == "@global":
            arg_list.append(f"-lib global__{name}")
        elif vendor == "@fsoc":
            arg_list.append(f"-lib fsoc__{name}")
        else:
            arg_list.append(f"-lib {vendor}__{name}")
        #common.copy_file(license_macros_file_path, f"{cfg.temp_path}/uvml_mio_lic_macros.svh")
        #arg_list.append(f".mio/temp/uvml_mio_lic_macros.svh") # HACK compute that path
        arg_list.append("-F " + flist_path)
        mtr_compilation_log_path = ip_dir_name + "." + sim_str + ".cmp.log"
        arg_list.append("-l " + mtr_compilation_log_path)
        arg_list.append(f"-timescale {cfg.sim_timescale}")
        
        arg_list_str = ""
        for arg in arg_list:
            arg_list_str = arg_list_str + f" {arg}"
        if cfg.dbg:
            arg_list = [f"dvlcom -v -a '{arg_list_str}'"]
        else:
            arg_list = [f"dvlcom -a '{arg_list_str}'"]
        #launch_eda_bin(cfg.metrics_home + "/mdc", ["initialize"], wd=cfg.project_dir, output=True) # TODO Add project.yml and store this in there
        write_cmd_to_disk(sim_job, "mdc", arg_list, compilation_command_file)
        sim_job.bwrap_commands += launch_eda_bin(cfg.metrics_home + "/mdc", arg_list, wd=cfg.project_dir, output=cfg.dbg, dry_run=sim_job.dry_run)
        launch_eda_bin(cfg.metrics_home + "/mdc", ["download", mtr_compilation_log_path], wd=cfg.project_dir, output=cfg.dbg, dry_run=sim_job.dry_run)
        if not sim_job.dry_run:
            common.move_file(f"{cfg.project_dir}/_downloaded_{mtr_compilation_log_path}", compilation_log_path)
        
    elif sim_job.simulator == common.simulators_enum.XCELIUM:
        arg_list += xcelium_default_compilation_args
        arg_list.append(license_macros_file_path);
        arg_list.append("-f " + flist_path)
        # TODO Add compilation output argument for nc
        write_cmd_to_disk(sim_job, "xrun", arg_list, compilation_command_file)
        sim_job.bwrap_commands += launch_eda_bin(cfg.nc_home + "/xrun", arg_list, wd=sim_out, output=cfg.dbg, dry_run=sim_job.dry_run)
        
    elif sim_job.simulator == common.simulators_enum.QUESTA:
        os.environ['MIO_UVM_HOME'] = f"$MIO_QUESTA_HOME/../verilog_src/uvm-{cfg.uvm_version}"
        arg_list += questa_default_compilation_args
        arg_list.append(license_macros_file_path);
        arg_list.append("-f " + flist_path)
        arg_list += cmp_args_list
        arg_list += deps_list
        arg_list.append(f"-Ldir {cmp_out_dir}")
        arg_list.append("-l "  + compilation_log_path)
        arg_list.append(f"-work {name}")
        write_cmd_to_disk(sim_job, "vlog", arg_list, compilation_command_file)
        sim_job.bwrap_commands += launch_eda_bin(cfg.questa_home + "/vlog", arg_list, wd=sim_out, output=cfg.dbg)
        
    elif sim_job.simulator == common.simulators_enum.RIVIERA:
        arg_list += riviera_default_compilation_args
        arg_list.append(license_macros_file_path);
        arg_list.append("-f " + flist_path)
        # TODO Add compilation output argument for riviera
        write_cmd_to_disk(sim_job, "vlog", arg_list, compilation_command_file)
        sim_job.bwrap_commands += launch_eda_bin(cfg.riviera_home + "/vlog", arg_list, wd=sim_out, output=cfg.dbg, dry_run=sim_job.dry_run)
    
    return compilation_log_path


def do_compile_vivado_project(ip, deps, sim_job, local):
    ip_str = f"{ip.vendor}/{ip.name}"
    ip_dir_name = f"{ip.vendor}__{ip.name}"
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    cmp_out = cfg.sim_output_dir + "/" + sim_str + "/cmp_out/" + ip_dir_name
    sim_out = cfg.sim_output_dir + "/" + sim_str + "/cmp_wd/" + ip_dir_name
    
    if sim_job.simulator == common.simulators_enum.VIVADO:
        vlog_compilation_log_path = cfg.sim_dir + "/cmp/" + ip_dir_name + ".viv.vlog.cmp.log"
        vhdl_compilation_log_path = cfg.sim_dir + "/cmp/" + ip_dir_name + ".viv.vhdl.cmp.log"
        vlog_arg_list = ["-prj "  + ip.vproj_vlog]
        vlog_arg_list.append("--work " + ip.name + "=" + cmp_out)
        vlog_arg_list += vivado_project_default_vlog_compilation_args
        vlog_arg_list += convert_defines(sim_job)
        vlog_arg_list += convert_compilation_args(sim_job)
        vlog_arg_list += convert_deps_to_args(deps, sim_job)
        vlog_arg_list.append("--log " + vlog_compilation_log_path)
        vhdl_arg_list = ["-prj " + ip.vproj_vhdl]
        vhdl_arg_list.append("--work " + ip.name + "=" + cmp_out)
        vhdl_arg_list += vivado_project_default_vhdl_compilation_args
        vlog_arg_list += convert_defines(sim_job)
        vlog_arg_list += convert_compilation_args(sim_job)
        vlog_arg_list += convert_deps_to_args(deps, sim_job)
        vhdl_arg_list.append("--log " + vhdl_compilation_log_path)
        compilation_command_file = f"{ip_dir_name}.{sim_str}.cmp.xvlog.cmd.txt"
        write_cmd_to_disk(sim_job, "xvlog", arg_list, compilation_command_file)
        sim_job.bwrap_commands += launch_eda_bin(cfg.vivado_home + "/xvlog", vlog_arg_list, wd=sim_out, dry_run=sim_job.dry_run)
        compilation_command_file = f"{ip_dir_name}.{sim_str}.cmp.xvhdl.cmd.txt"
        write_cmd_to_disk(sim_job, "xvhdl", arg_list, compilation_command_file)
        sim_job.bwrap_commands += launch_eda_bin(cfg.vivado_home + "/xvhdl", vhdl_arg_list, wd=sim_out, dry_run=sim_job.dry_run)
    else:
        common.fatal("Vivado Project IP are not yet compatible with simulator '" + sim_str + "'.")
    
    return [vlog_compilation_log_path, vhdl_compilation_log_path]


def do_elaborate(ip, sim_job, wd):
    ip_str = f"{ip.vendor}/{ip.name}"
    ip_dir_name = f"{ip.vendor}__{ip.name}"
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    arg_list = []
    def_list  = convert_defines(sim_job)
    elab_list = convert_elaboration_args(sim_job)
    deps_ip_list = get_dep_list(ip, sim_job)
    deps_list = convert_deps_to_args(deps_ip_list, sim_job)
    so_libs = get_all_so_libs(ip, sim_job)
    elaboration_log_path = cfg.sim_dir + "/elab/" + ip_dir_name + "." + sim_str + ".elab.log"
    cmp_out_dir = cfg.sim_output_dir + "/" + sim_str + "/cmp_out/"
    ip_cmp_path = cmp_out_dir + ip_dir_name
    elaboration_command_file = f"{ip_dir_name}.{sim_str}.elab.cmd.txt"
    
    if sim_job.simulator == common.simulators_enum.VIVADO:
        if ip.has_dut:
            arg_list += dut_elab_to_arg_list(ip, sim_job)
        arg_list += def_list
        arg_list += elab_list
        arg_list += deps_list
        arg_list += vivado_default_elaboration_args
        arg_list.append(f"-timescale {cfg.sim_timescale}")
        arg_list.append("--log "  + elaboration_log_path)
        arg_list.append("-s "     + ip.name)
        arg_list.append("-L "     + ip.name + "=" + ip_cmp_path)
        for construct in ip.hdl_src_top_constructs:
            if "." in construct:
                arg_list.append(construct)
            else:
                arg_list.append(ip.name + "." + construct)
        
        common.create_dir(wd)
        arg_list.append(f"-sv_root {wd}")
        
        for so_lib in so_libs:
            common.copy_file(so_libs[so_lib], f"{wd}/{so_lib}")
            arg_list.append(f"-sv_lib {so_lib}")
        
        write_cmd_to_disk(sim_job, "xelab", arg_list, elaboration_command_file)
        sim_job.bwrap_commands += launch_eda_bin(cfg.vivado_home + "/xelab", arg_list, wd, output=cfg.dbg, dry_run=sim_job.dry_run)
        
    elif sim_job.simulator == common.simulators_enum.VCS:
        arg_list += vcs_default_elaboration_args
        if ip.has_dut:
            arg_list += dut_elab_to_arg_list(ip, sim_job)
        # TODO Add elaboration output argument for vcs
        write_cmd_to_disk(sim_job, "vcs", arg_list, elaboration_command_file)
        sim_job.bwrap_commands += launch_eda_bin(cfg.vcs_home + "/vcs", arg_list, wd, output=cfg.dbg, dry_run=sim_job.dry_run)
        
    elif sim_job.simulator == common.simulators_enum.METRICS:
        arg_list += metrics_default_elaboration_args
        mtr_elaboration_log_path = ip_dir_name + "." + sim_str + ".elab.log"
        arg_list.append(f"-l {mtr_elaboration_log_path}")
        arg_list.append(f"-timescale {cfg.sim_timescale}")
        arg_list += def_list
        arg_list += elab_list
        arg_list += deps_list
        if ip.has_dut:
            arg_list += dut_elab_to_arg_list(ip, sim_job)
        #arg_list.append(f"+incdir+%UVM_HOME%/src")
        #arg_list.append(f"%UVM_HOME%/src/uvm_pkg.sv")
        
        if ip.vendor == "@global":
            arg_list.append(f"-genimage global__{ip.name}")
            arg_list.append(f"-L global__{ip.name}")
        elif ip.vendor == "@fsoc":
            arg_list.append(f"-genimage fsoc__{ip.name}")
            arg_list.append(f"-L fsoc__{ip.name}")
        else:
            arg_list.append(f"-genimage {ip.vendor}__{ip.name}")
            arg_list.append(f"-L {ip.vendor}__{ip.name}")
        
        for construct in ip.hdl_src_top_constructs:
            if "." in construct:
                lib,name = construct.split(".")
                arg_list.append(f"-top {name}")
            else:
                arg_list.append(f"-top {construct}")
        
        arg_list_str = ""
        for arg in arg_list:
            arg_list_str = arg_list_str + f" {arg}"
        if cfg.dbg:
            arg_list = [f"dsim -v -a '{arg_list_str}'"]
        else:
            arg_list = [f"dsim -a '{arg_list_str}'"]
        write_cmd_to_disk(sim_job, "mdc", arg_list, elaboration_command_file)
        sim_job.bwrap_commands += launch_eda_bin(cfg.metrics_home + "/mdc", arg_list, wd=cfg.project_dir, output=cfg.dbg, dry_run=sim_job.dry_run)
        sim_job.bwrap_commands += launch_eda_bin(cfg.metrics_home + "/mdc", ["download", mtr_elaboration_log_path], wd=cfg.project_dir, output=cfg.dbg, dry_run=sim_job.dry_run)
        if not sim_job.dry_run:
            common.move_file(f"{cfg.project_dir}/_downloaded_{mtr_elaboration_log_path}", elaboration_log_path)
        
    elif sim_job.simulator == common.simulators_enum.XCELIUM:
        arg_list += xcelium_default_elaboration_args
        if ip.has_dut:
            arg_list += dut_elab_to_arg_list(ip, sim_job)
        # TODO Add elaboration output argument for nc
        write_cmd_to_disk(sim_job, "xrun", arg_list, elaboration_command_file)
        sim_job.bwrap_commands += launch_eda_bin(cfg.nc_home + "/xrun", arg_list, wd, output=cfg.dbg, dry_run=sim_job.dry_run)
        
    elif sim_job.simulator == common.simulators_enum.QUESTA:
        for construct in ip.hdl_src_top_constructs:
            if "." in construct:
                arg_list.append(construct)
            else:
                arg_list.append(ip.name + "." + construct)
        
        arg_list += questa_default_elaboration_args
        if ip.has_dut:
            arg_list += dut_elab_to_arg_list(ip, sim_job)
        arg_list += def_list
        arg_list += elab_list
        arg_list += deps_list
        arg_list.append(f"-work {ip_dir_name}")
        arg_list.append(f"-o {ip.name}")
        arg_list.append(f"-l {elaboration_log_path}")
        arg_list.append(f"-Ldir {cmp_out_dir}")
        write_cmd_to_disk(sim_job, "vopt", arg_list, elaboration_command_file)
        sim_job.bwrap_commands += launch_eda_bin(cfg.questa_home + "/vopt", arg_list, wd, output=cfg.dbg, dry_run=sim_job.dry_run)
        
    elif sim_job.simulator == common.simulators_enum.RIVIERA:
        arg_list += riviera_default_elaboration_args
        if ip.has_dut:
            arg_list += dut_elab_to_arg_list(ip, sim_job)
        # TODO Add elaboration output argument for riviera
        write_cmd_to_disk(sim_job, "vlog", arg_list, elaboration_command_file)
        sim_job.bwrap_commands += launch_eda_bin(cfg.riviera_home + "/vlog", arg_list, wd, output=cfg.dbg, dry_run=sim_job.dry_run)
    
    return elaboration_log_path


def do_simulate(ip, sim_job, wd):
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    ip_str = f"{ip.vendor}/{ip.name}"
    ip_dir_name = f"{ip.vendor}__{ip.name}"
    global sem
    sem.acquire()
    plus_args = sim_job.sim_args
    if (len(plus_args) > 0):
        args_present = True
    else:
        args_present = False
    arg_list = []
    test_template = Template(ip.hdl_src_test_name_template)
    test_result_dir_template = Template(cfg.test_results_path_template)
    test = sim_job.test
    test_name = test_template.render(name=test)
    simulation_command_file = f"{ip_dir_name}.{sim_str}.sim.cmd.txt"
    test_result_dir = test_result_dir_template.render(ip_vendor=ip.vendor, ip_name=ip.name, test_name=test, seed=sim_job.seed, args=plus_args_list_to_str_list(plus_args), args_present=args_present)
    plus_args["UVM_TESTNAME"] = test_name
    
    plus_args["__MIO_TOKEN"] = user.login()
    
    if sim_job.is_regression:
        common.create_dir   (cfg.regr_results_dir + "/" + ip.name + "_" + sim_job.regression_name)
        common.create_dir   (cfg.regr_results_dir + "/" + ip.name + "_" + sim_job.regression_name + "/" + sim_job.regression_timestamp)
        tests_results_path = cfg.regr_results_dir + "/" + ip.name + "_" + sim_job.regression_name + "/" + sim_job.regression_timestamp + "/" + test_result_dir
    else:
        tests_results_path = cfg.sim_results_dir + "/" + test_result_dir
    
    output = not sim_job.is_regression
    
    simulation_log_path = tests_results_path + "/sim.log"
    cov_path = tests_results_path + "/cov"
    common.create_dir(tests_results_path)
    common.create_dir(tests_results_path + "/trn_log")
    sim_job.results_path = tests_results_path
    sim_job.results_dir_name = test_result_dir
    if sim_job.waves:
        if sim_job.simulator == common.simulators_enum.VIVADO:
            wave_capture_script_path = tests_results_path + "/waves.viv.tcl"
            waves_path = tests_results_path + "/waves.wdb"
            arg_list.append("--wdb "      + waves_path              )
            arg_list.append("--tclbatch " + wave_capture_script_path)
            if not os.path.exists(wave_capture_script_path):
                try:
                    common.create_file(wave_capture_script_path)
                    f = open(wave_capture_script_path, "w")
                    f.write("log_wave -recursive * \n")
                    f.write("run -all \n")
                    f.write("quit \n")
                    f.close()
                except Exception as e:
                    common.fatal("Could not create wave capture script at " + wave_capture_script_path + ": " + str(e))
        elif sim_job.simulator == common.simulators_enum.VCS:
            # TODO Implement waves file for vcs
            pass
        elif sim_job.simulator == common.simulators_enum.METRICS:
            arg_list.append(f"-waves {test_result_dir}.vcd")
        elif sim_job.simulator == common.simulators_enum.XCELIUM:
            # TODO Implement waves file for xcelium
            pass
        elif sim_job.simulator == common.simulators_enum.QUESTA:
            # TODO Implement waves file for questa
            pass
        elif sim_job.simulator == common.simulators_enum.RIVIERA:
            # TODO Implement waves file for riviera
            pass
    
    if sim_job.cov:
        common.create_dir(cov_path)
        if sim_job.simulator == common.simulators_enum.VIVADO:
            arg_list.append("-cov_db_name " + test_name)
            arg_list.append("-cov_db_dir "  + cov_path )
        elif sim_job.simulator == common.simulators_enum.VCS:
            # TODO Implement coverage for vcs
            pass
        elif sim_job.simulator == common.simulators_enum.METRICS:
            arg_list.append(f"-code-cov a")
            arg_list.append(f"-cov-db {test_result_dir}")
        elif sim_job.simulator == common.simulators_enum.XCELIUM:
            # TODO Implement coverage for xcelium
            pass
        elif sim_job.simulator == common.simulators_enum.QUESTA:
            # TODO Implement coverage for questa
            pass
        elif sim_job.simulator == common.simulators_enum.RIVIERA:
            # TODO Implement coverage for riviera
            pass
    
    plus_args["UVM_NO_RELNOTES"                ] = ""
    plus_args["SIM_DIR_RESULTS"                ] = cfg.sim_results_dir
    plus_args["UVM_VERBOSITY"                  ] = "UVM_" + sim_job.verbosity.upper()
    plus_args["UVM_MAX_QUIT_COUNT"             ] = str(sim_job.max_errors)
    
    if sim_job.simulator == common.simulators_enum.METRICS:
        plus_args["UVMX_FILE_BASE_DIR_SIM"         ] = "./.mio/temp"
        plus_args["UVMX_FILE_BASE_DIR_TEST_RESULTS"] = "./.mio/temp"
        common.create_dir(cfg.temp_path + "/trn_log")
        plus_args["UVMX_FILE_BASE_DIR_TB"          ] = os.path.relpath(ip.path + "/" + ip.src_path, cfg.project_dir)
        plus_args["UVMX_FILE_BASE_DIR_TESTS"       ] = os.path.relpath(ip.path + "/" + ip.src_path + "/" + ip.hdl_src_tests_path, cfg.project_dir)
    else:
        plus_args["UVMX_FILE_BASE_DIR_SIM"         ] = cfg.sim_dir
        plus_args["UVMX_FILE_BASE_DIR_TEST_RESULTS"] = tests_results_path
        plus_args["UVMX_FILE_BASE_DIR_TB"          ] = ip.path + "/" + ip.src_path
        plus_args["UVMX_FILE_BASE_DIR_TESTS"       ] = ip.path + "/" + ip.src_path + "/" + ip.hdl_src_tests_path
    
    plus_args_list = convert_plus_args(sim_job)
    if sim_job.simulator == common.simulators_enum.VIVADO:
        arg_list += plus_args_list
        arg_list += vivado_default_simulation_args
        arg_list.append("--log " + simulation_log_path)
        if sim_job.gui:
            arg_list.append("--gui")
        else:
            if not sim_job.waves:
                arg_list.append("--runall")
                arg_list.append("--onerror quit")
        if not sim_job.cov:
            arg_list.append("-ignore_coverage")
        arg_list.append(ip.name)
        arg_list.append("-sv_seed " + str(sim_job.seed))
        write_cmd_to_disk(sim_job, "xsim", arg_list, simulation_command_file)
        sem.release()
        sim_job.bwrap_commands += launch_eda_bin(cfg.vivado_home + "/xsim", arg_list, wd, output=output, dry_run=sim_job.dry_run)
        
    elif sim_job.simulator == common.simulators_enum.VCS:
        arg_list += vcs_default_simulation_args
        # TODO Add simulation output argument for vcs
        write_cmd_to_disk(sim_job, "simv", arg_list, simulation_command_file)
        sem.release()
        sim_job.bwrap_commands += launch_eda_bin(cfg.vcs_home + "/simv", arg_list, wd, output=output, dry_run=sim_job.dry_run)
        
    elif sim_job.simulator == common.simulators_enum.METRICS:
        arg_list += metrics_default_simulation_args
        arg_list += plus_args_list
        mtr_simulation_log_path = f"{test_result_dir}.log"
        arg_list.append("-l " + mtr_simulation_log_path)
        arg_list.append("-sv_seed " + str(sim_job.seed))
        arg_list.append(f"-image {ip.vendor}__{ip.name}")
        arg_list.append(f"-sv_lib %UVM_HOME%/src/dpi/libuvm_dpi.so")
        arg_list.append(f"-timescale {cfg.sim_timescale}")
        #arg_list.append(f"-work {ip.vendor}__{ip.name}")
        
        arg_list_str = ""
        for arg in arg_list:
            arg_list_str = arg_list_str + f" {arg}"
        if cfg.dbg:
            arg_list = [f"dsim -v -a '{arg_list_str}'"]
        else:
            arg_list = [f"dsim -a '{arg_list_str}'"]
        write_cmd_to_disk(sim_job, "mdc", arg_list, simulation_command_file)
        sem.release()
        sim_job.bwrap_commands += launch_eda_bin(cfg.metrics_home + "/mdc", arg_list, wd=cfg.project_dir, output=output, dry_run=sim_job.dry_run)
        common.remove_file(f"{cfg.project_dir}/_downloaded_{mtr_simulation_log_path}")
        sim_job.bwrap_commands += launch_eda_bin(cfg.metrics_home + "/mdc", ["download", mtr_simulation_log_path], wd=cfg.project_dir, dry_run=sim_job.dry_run)
        if not sim_job.dry_run:
            common.move_file(f"{cfg.project_dir}/_downloaded_{mtr_simulation_log_path}", simulation_log_path)
            if sim_job.waves:
                common.remove_file(f"{cfg.project_dir}/_downloaded_{test_result_dir}.vcd")
                sim_job.bwrap_commands += launch_eda_bin(cfg.metrics_home + "/mdc", ["download", f"{test_result_dir}.vcd"], wd=cfg.project_dir, dry_run=sim_job.dry_run)
                common.move_file(f"{cfg.project_dir}/_downloaded_{test_result_dir}.vcd", f"{tests_results_path}/waves.vcd")
        
    elif sim_job.simulator == common.simulators_enum.XCELIUM:
        arg_list += xcelium_default_simulation_args
        # TODO Add simulation output argument for nc
        write_cmd_to_disk(sim_job, "xrun", arg_list, simulation_command_file)
        sem.release()
        sim_job.bwrap_commands += launch_eda_bin(cfg.nc_home + "/xrun", arg_list, wd, output=output, dry_run=sim_job.dry_run)
        
    elif sim_job.simulator == common.simulators_enum.QUESTA:
        arg_list += questa_default_simulation_args
        arg_list += plus_args_list
        arg_list.append("-l " + simulation_log_path)
        arg_list.append("-sv_seed " + str(sim_job.seed))
        arg_list.append(f" {ip.name}")
        write_cmd_to_disk(sim_job, "vsim", arg_list, simulation_command_file)
        sem.release()
        sim_job.bwrap_commands += launch_eda_bin(cfg.questa_home + "/vsim", arg_list, wd, output=output, dry_run=sim_job.dry_run)
        
    elif sim_job.simulator == common.simulators_enum.RIVIERA:
        arg_list += riviera_default_simulation_args
        # TODO Add simulation output argument for riviera
        write_cmd_to_disk(sim_job, "vsim", arg_list, simulation_command_file)
        sem.release()
        sim_job.bwrap_commands += launch_eda_bin(cfg.riviera_home + "/vsim", arg_list, wd, output=output, dry_run=sim_job.dry_run)
    
    sim_job.sim_log_file_path = simulation_log_path


def write_cmd_to_disk(sim_job, executable_name, arg_list, command_filename):
    arg_list_str = ""
    for arg in arg_list:
        arg_list_str = f"{arg_list_str} {arg}"
    if sim_job.simulator == common.simulators_enum.VIVADO:
        command_str = f"$MIO_VIVADO_HOME/{executable_name}{arg_list_str}"
    elif sim_job.simulator == common.simulators_enum.METRICS:
        command_str = f"$MIO_METRICS_HOME/{executable_name}{arg_list_str}"
    elif sim_job.simulator == common.simulators_enum.VCS:
        command_str = f"$MIO_VCS_HOME/{executable_name}{arg_list_str}"
    elif sim_job.simulator == common.simulators_enum.QUESTA:
        command_str = f"$MIO_QUESTA_HOME/{executable_name}{arg_list_str}"
    elif sim_job.simulator == common.simulators_enum.XCELIUM:
        command_str = f"$MIO_XCELIUM_HOME/{executable_name}{arg_list_str}"
    elif sim_job.simulator == common.simulators_enum.RIVIERA:
        command_str = f"$MIO_RIVIERA_HOME/{executable_name}{arg_list_str}"
    
    try:
        path = cfg.temp_path + "/" + command_filename
        cmd_file = open(path, 'w')
        cmd_file.write(command_str)
        cmd_file.close()
    except Exception as e:
        common.fatal(f"Could not write command to disk: {e}")


def set_uvm_version(sim_job):
    found_uvm_ver = False
    if sim_job.simulator == common.simulators_enum.METRICS:
        config_path = cfg.project_dir + "/.mdc/config.yml"
        try:
            with open(config_path, 'r') as cfg_file:
                cfg_yaml = yaml.load(cfg_file, Loader=SafeLoader)
                if 'toolchain' not in cfg_yaml:
                    cfg_yaml['toolchain'] = {}
                if 'packages' not in cfg_yaml['toolchain']:
                    cfg_yaml['toolchain']['packages'] = []
                for pkg in cfg_yaml['toolchain']['packages']:
                    if pkg['name'] == 'uvm':
                        found_uvm_ver = True
                        pkg['version'] = cfg.uvm_version
                        break
                if not found_uvm_ver:
                    cfg_yaml['toolchain']['packages'].append({"name":"uvm", "version":cfg.uvm_version})
            with open(config_path, 'w') as cfg_file_write:
                yaml.dump(cfg_yaml, cfg_file_write)
        except Exception as e:
            common.fatal(f"Failed to set UVM version for Metrics simulator: {e}")


def dut_elab_to_arg_list(ip, sim_job):
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    args = []
    if (ip.dut_ip_type == "fsoc"):
        file_path_partial_name = re.sub(r':', '_', ip.dut_fsoc_full_name)
        eda_file_dir = cfg.fsoc_dir + "/" + ip.dut_fsoc_name + "/sim-xsim"
        eda_file_path = eda_file_dir + "/" + file_path_partial_name + "_0.eda.yml"
        try:
            if os.path.exists(eda_file_path):
                with open(eda_file_path, 'r') as edafile:
                    eda_yaml = yaml.load(edafile, Loader=SafeLoader)
                    if eda_yaml:
                        elab_options = eda_yaml['tool_options']['xsim']['xelab_options']
                        if sim_job.simulator == common.simulators_enum.METRICS:
                            args.append("-L " + "fsoc__" + ip.dut_fsoc_name)
                        else:
                            args.append("-L " + ip.dut_fsoc_name + "=" + cfg.sim_output_dir + "/" + sim_str + "/cmp_out/@fsoc__" + ip.dut_fsoc_name)
                    else:
                        common.fatal("ERROR: Unable to parse FuseSoC output " + eda_file_path)
            else:
                common.fatal("ERROR: Unable to parse FuseSoC output " + eda_file_path)
        except Exception as e:
            common.fatal("ERROR: Unable to find FuseSoC core output for '" + ip.dut_fsoc_name + "': " + str(e))
    else:
        dut_ip = ip.dut.target_ip_model
        dut_ip_dir_name = f"{dut_ip.vendor}__{dut_ip.name}"
        if dut_ip.sub_type == "vivado":
            if sim_job.simulator != common.simulators_enum.VIVADO:
                common.fatal("Vivado Projects are currently only compatible with the Vivado simulator.")
            for construct in dut_ip.hdl_src_top_constructs:
                args.append(construct)
            for lib in dut_ip.vproj_libs:
                args.append("-L " + lib)
        else:
            # Performed by get_dep_list()
            pass
            #if sim_job.simulator == common.simulators_enum.METRICS:
            #    if dut_ip.vendor == "@global":
            #        lib_str = f"-L global__{dut_ip.name}"
            #    else:
            #        lib_str = f"-L {dut_ip.vendor}__{dut_ip.name}"
            #elif sim_job.simulator == common.simulators_enum.QUESTA:
            #    lib_str = f"-L {dut_ip.vendor}__{dut_ip.name}"
            #else:
            #    lib_str = "-L " + dut_ip.name + "=" + cfg.sim_output_dir + "/" + sim_str + "/cmp_out/" + dut_ip_dir_name
            #args.append(lib_str)
    common.dbg("DUT args list: " + str(args))
    return args


def get_ip_flist_path(ip, sim_job, include_uvm=True):
    ip_str = f"{ip.vendor}/{ip.name}"
    ip_dir = f"{ip.vendor}__{ip.name}"
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    found_flist = False
    flist_path = ""
    
    if ip.hdl_src_flists[sim_job.simulator] != "":
        found_flist = True
        if ip.is_global and (sim_job.simulator == common.simulators_enum.METRICS):
            flist_path = f".mio/temp/{ip_dir}/{ip.hdl_src_flists[sim_job.simulator]}"
        else:
            if ip.is_encrypted:
                flist_path = f"{ip.path}/{ip.src_path}.{sim_str}/{ip.hdl_src_flists[sim_job.simulator]}"
            else:
                flist_path = f"{ip.path}/{ip.src_path}/{ip.hdl_src_flists[sim_job.simulator]}"
    if not found_flist:
        flist_path = gen_flist(ip, sim_job, include_uvm)
    return flist_path


def gen_master_flist(ip, sim_job, deps, fsoc_core_name, fsoc_core_flist_path):
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    
    if sim_job.simulator == common.simulators_enum.VIVADO:
        flist_path = cfg.temp_path + "/" + ip.vendor + "__" + ip.name + ".prj"
        gen_prj_file(sim_job, ip, flist_path)
    else:
        flists = gen_flists(ip, deps, sim_job, False)
        flist_path = cfg.temp_path + "/" + ip.vendor + "__" + ip.name + ".top." + sim_str + ".flist"
        if sim_job.simulator == common.simulators_enum.METRICS:
            final_flists = []
            if fsoc_core_flist_path != "":
                final_flists.append(fsoc_core_flist_path.replace(".mio/temp/", ""))
            for flist in flists:
                final_flist = os.path.relpath(flist, cfg.temp_path)
                final_flists.append(final_flist)
            flists = final_flists
        gen_mflist_file(sim_job.simulator, ip.vendor, ip.name, flist_path, [], flists)
        if sim_job.simulator == common.simulators_enum.METRICS:
            flist_path = os.path.relpath(flist_path, cfg.project_dir)
            #flist_path = flist_path.replace(cfg.project_dir, "")
    
    return flist_path


def gen_prj_file(sim_job, ip, flist_path):
    ip_str = f"{ip_vendor}/{ip_name}"
    ip_dir = f"{ip.vendor}__{ip.name}"
    sim_str = common.get_simulator_short_name(simulator)
    try:
        flist_template = cfg.templateEnv.get_template(f"viv.prj.j2")
        common.dbg(f"Generating Vivado Project file for IP '{ip_str}'")
        outputText = flist_template.render(target=ip_dir, defines=defines, filelists=filelists)
        with open(path,'w') as flist_file:
            flist_file.write(outputText)
            flist_file.close()
    except Exception as e:
        common.fatal(f"Failed to create Vivado Project file for IP '{ip_str}': {e}")


def gen_mflist_file(simulator, ip_vendor, ip_name, path, defines, filelists):
    ip_str = f"{ip_vendor}/{ip_name}"
    sim_str = common.get_simulator_short_name(simulator)
    
    try:
        flist_template = cfg.templateEnv.get_template(f"{sim_str}.mflist.j2")
        common.dbg(f"Generating master filelist for IP '{ip_str}' and simulator '{sim_str}' with filelists='{filelists}'")
        outputText = flist_template.render(defines=defines, filelists=filelists)
        with open(path,'w') as flist_file:
            flist_file.write(outputText)
            flist_file.close()
    except Exception as e:
        common.fatal(f"Failed to create master filelist for IP '{ip_str}': {e}")


def gen_flists(ip, deps, sim_job, include_uvm=True):
    flists = []
    for dep in deps:
        flists.append(get_ip_flist_path(dep, sim_job, include_uvm))
    flists.append(get_ip_flist_path(ip, sim_job, include_uvm))
    return flists


def gen_flist(ip, sim_job, include_uvm=True):
    ip_str = f"{ip.vendor}/{ip.name}"
    ip_dir = f"{ip.vendor}__{ip.name}"
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    flist_path = ""
    defines = convert_defines(sim_job)
    if len(ip.hdl_src_top_files) == 0:
        common.fatal(f"No 'top-files' defined under section 'hdl-src' in descriptor for IP '{ip_str}'")
    if len(ip.hdl_src_directories) == 0:
        common.fatal(f"No 'directories' entry under section 'hdl-src' in descriptor for IP '{ip_str}'")
    
    rel_ip_path = os.path.relpath(ip.path, cfg.temp_path)
    simulator = sim_str
    flist_template = cfg.templateEnv.get_template(f"{simulator}.flist.j2")
    directories = []
    for dir in ip.hdl_src_directories:
        if dir == ".":
            if sim_job.simulator == common.simulators_enum.METRICS:
                if ip.is_global:
                    directories.append(f"{ip_dir}")
                else:
                    if ip.is_encrypted:
                        directories.append(f"{rel_ip_path}/{ip.src_path}.{sim_str}")
                    else:
                        directories.append(f"{rel_ip_path}/{ip.src_path}")
            else:
                directories.append("${MIO_" + ip.name.upper() + "_SRC_PATH}")
        else:
            if sim_job.simulator == common.simulators_enum.METRICS:
                if ip.is_global:
                    directories.append(f"{ip_dir}/{dir}")
                else:
                    if ip.is_encrypted:
                        directories.append(f"{rel_ip_path}/{ip.src_path}.{sim_str}/{dir}")
                    else:
                        directories.append(f"{rel_ip_path}/{ip.src_path}/{dir}")
            else:
                directories.append("${MIO_" + ip.name.upper() + "_SRC_PATH}/" + dir)
    
    top_files = []
    for file in ip.hdl_src_top_files:
        if sim_job.simulator == common.simulators_enum.METRICS:
            if ip.is_global:
                top_files.append(f"{ip_dir}/{file}")
            else:
                if ip.is_encrypted:
                    top_files.append(f"{rel_ip_path}/{ip.src_path}.{sim_str}/{file}")
                else:
                    top_files.append(f"{rel_ip_path}/{ip.src_path}/{file}")
        else:
            top_files.append("${MIO_" + ip.name.upper() + "_SRC_PATH}/" + file)
    
    flist_path = cfg.temp_path + "/" + ip.vendor + "__" + ip.name + "." + simulator + ".flist"
    if include_uvm:
        if ip.type == "dv":
            include_uvm = True
        else:
            include_uvm = False
    gen_flist_file(sim_job.simulator, ip.vendor, ip.name, flist_path, defines, [], directories, top_files, include_uvm)
    common.dbg(f"Using filelist '{flist_path}' for IP '{ip_str}'")
    
    return flist_path


def gen_flist_file(simulator, ip_vendor, ip_name, path, defines, filelists, directories, files, include_uvm):
    ip_str = f"{ip_vendor}/{ip_name}"
    ip_dir = f"{ip_vendor}__{ip_name}"
    sim_str = common.get_simulator_short_name(simulator)
    
    if include_uvm:
        if simulator == common.simulators_enum.METRICS:
            directories.insert(0, "$UVM_HOME/src")
            files      .insert(0, "$UVM_HOME/src/uvm_pkg.sv")
        if simulator == common.simulators_enum.QUESTA:
            directories.insert(0, "$(MIO_UVM_HOME)/src")
            files      .insert(0, "$(MIO_UVM_HOME)/src/uvm_pkg.sv")
    
    try:
        flist_template = cfg.templateEnv.get_template(f"{sim_str}.flist.j2")
        common.dbg(f"Generating filelist for IP '{ip_str}' and simulator '{sim_str}' with files='{files}' and dirs='{directories}'")
        outputText = flist_template.render(target=ip_dir, defines=defines, filelists=filelists, files=files, dirs=directories)
        with open(path,'w') as flist_file:
            flist_file.write(outputText)
            flist_file.close()
    except Exception as e:
        common.fatal(f"Failed to create filelist for IP '{ip_str}': {e}")


def convert_defines(sim_job):
    defines = sim_job.cmp_args
    args = []
    for define in defines:
        if sim_job.simulator == common.simulators_enum.VIVADO:
            if defines[define] != "":
                args.append("--define " + define + "=" + defines[define])
            else:
                args.append("--define " + define)
        else:
            if defines[define] != "":
                args.append("+define+" + define + "=" + defines[define])
            else:
                args.append("+define+" + define)
    return args


def convert_plus_args(sim_job):
    plus_args = sim_job.sim_args
    args = []
    for arg in plus_args:
        if sim_job.simulator == common.simulators_enum.VIVADO:
            if plus_args[arg] != "":
                args.append("-testplusarg \"" + arg + "=" + plus_args[arg] + "\"")
            else:
                args.append("-testplusarg \"" + arg + "\"")
        else:
            if plus_args[arg] != "":
                args.append("+" + arg + "=" + plus_args[arg])
            else:
                args.append("+" + arg)
    return args


def convert_deps_to_args(deps, sim_job):
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    args = []
    for dep in deps:
        if dep.name != "uvm":
            if sim_job.simulator == common.simulators_enum.METRICS:
                if dep.vendor == "@global":
                    dep_dir_name = f"global__{dep.name}"
                elif dep.vendor == "@fsoc":
                    dep_dir_name = f"fsoc__{dep.name}"
                else:
                    dep_dir_name = f"{dep.vendor}__{dep.name}"
                lib_str = f"-L {dep_dir_name}"
            elif sim_job.simulator == common.simulators_enum.QUESTA:
                dep_dir_name = f"{dep.vendor}__{dep.name}"
                lib_str = f"-L {dep_dir_name}"
            else:
                dep_dir_name = f"{dep.vendor}__{dep.name}"
                lib_str = "-L " + dep.name + "=" + cfg.sim_output_dir + "/" + sim_str + "/cmp_out/" + dep_dir_name
            args.append(lib_str)
    return args


def get_dep_list(ip, sim_job):
    final_dep_list = []
    if ip.has_dut:
        if ip.dut_ip_type == "":
            final_dep_list.append(ip.dut.target_ip_model)
    dep_list = ip.get_ordered_deps()
    for dep in dep_list:
        if dep.name == "uvm": # UVM is considered part of the simulator
            continue
        final_dep_list.append(dep)
    return final_dep_list


def get_incdir_list(deps, sim_job):
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    incdir_list = []
    for dep in deps:
        for dir in dep.hdl_src_directories:
            if dep.is_global and (sim_job.bwrap or sim_job.simulator == common.simulators_enum.METRICS):
                src_path = f"{cfg.temp_path}/{dep.vendor}__{dep.name}/{dir}"
            else:
                if dep.is_encrypted:
                    src_path = f"{dep.path}/{dep.src_path}.{sim_str}/{dir}"
                else:
                    src_path = f"{dep.path}/{dep.src_path}/{dir}"
            if sim_job.simulator == common.simulators_enum.VIVADO:
                incdir_list.append("-i " + src_path)
            else:
                if (sim_job.bwrap or sim_job.simulator == common.simulators_enum.METRICS):
                    src_path = os.path.relpath(src_path, cfg.project_dir)
                incdir_list.append("+incdir+" + src_path)
    return incdir_list


def get_all_so_libs(ip, sim_job):
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    so_libs = {}
    for dep in ip.dependencies:
        dep_so_libs = get_all_so_libs(dep.target_ip_model, sim_job)
        common.merge_dict(so_libs, dep_so_libs)
    for so_lib in ip.hdl_src_so_libs:
        so_lib_flat_name = f"{ip.vendor}__{ip.name}__{so_lib}.{sim_str}.so"
        so_lib_path = f"{ip.path}/{ip.scripts_path}/{so_lib}.{sim_str}.so"
        so_libs[so_lib_flat_name] = so_lib_path
    return so_libs


def convert_compilation_args(sim_job):
    args = []
    return args


def convert_elaboration_args(sim_job):
    args = []
    if sim_job.simulator == common.simulators_enum.VIVADO:
        if sim_job.waves or sim_job.cov or sim_job.gui:
            args.append("--debug all")
    return args


def invoke_fsoc(ip, core, sim_job):
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    fsc_args = argparse.Namespace()
    fsc_args.setup       = True
    fsc_args.build       = False
    fsc_args.run         = False
    fsc_args.no_export   = True
    fsc_args.tool        = "xsim"
    fsc_args.target      = ip.dut_fsoc_target
    fsc_args.system      = ip.dut_fsoc_full_name
    fsc_args.backendargs = ""
    fsc_args.system_name = ""
    fsc_args.build_root  = cfg.fsoc_dir + "/" + core.sname
    fsc_args.flag = []
    fsc_cores_root = [core.dir]
    
    
    try:
        fusesoc.main.init_logging(False, False)
        fsc_cfg = fusesoc.main.Config()
        fsc_cm  = fusesoc.main.init_coremanager(fsc_cfg, fsc_cores_root)
        fusesoc.main.run(fsc_cm, fsc_args)
        file_path_partial_name = re.sub(r':', '_', core.name)
        eda_file_dir = cfg.fsoc_dir + "/" + core.sname + "/sim-xsim"
        eda_file_path = eda_file_dir + "/" + file_path_partial_name + "_0.eda.yml"
        core_rel_path = os.path.relpath(core.dir, eda_file_dir)
        if sim_job.simulator == common.simulators_enum.METRICS:
            core_base_path = os.path.relpath(core.dir, cfg.temp_path)
        else:
            core_base_path = "$MIO_" + core.sname.replace("-", "_").upper() + "_SRC_PATH"
        if not os.path.exists(eda_file_path):
            common.fatal("Could not find FuseSoC output file " + eda_file_path)
        else:
            with open(eda_file_path, 'r') as edafile:
                eda_yaml = yaml.load(edafile, Loader=SafeLoader)
                if not eda_yaml:
                    common.fatal("Could not parse FuseSoC output file " + eda_file_path)
                dirs    = []
                files   = []
                defines = []
                for file in eda_yaml['files']:
                    if file['file_type'] == "systemVerilogSource":
                        if 'is_include_file' in file:
                            if 'include_path' in file:
                                dir_path = file['include_path']
                                dir_path = dir_path.replace(core_rel_path, core_base_path)
                                dirs.append(dir_path)
                        else:
                            file_path = file['name']
                            dir_path = pathlib.Path(f"{eda_file_dir}/{file_path}").parent.resolve()
                            dir_path = os.path.relpath(dir_path, eda_file_dir)
                            dir_path = dir_path.replace(core_rel_path, core_base_path)
                            file_path = file_path.replace(core_rel_path, core_base_path)
                            files.append(file_path)
                            dirs.append(dir_path)
                
                for param in eda_yaml['parameters']:
                    if eda_yaml['parameters'][param]['datatype'] == 'bool':
                        new_define = {};
                        #new_define['boolean'] = True
                        new_define['name'] = param
                        if eda_yaml['parameters'][param]['default'] == True:
                            new_define['value'] = 1
                        else:
                            new_define['value'] = 0
                        defines.append(new_define)
                    else:
                        common.fatal("Support for non-bool FuseSoC parameters is not currently implemented")
                sim_nickname = "xsim"
                #if sim_job.simulator == common.simulators_enum.VIVADO:
                #    sim_nickname = "xsim"
                for option in eda_yaml['tool_options'][sim_nickname]['xelab_options']:
                    if (re.match("--define", option)):
                        new_define = {};
                        matches = re.search("--define\s+(\w+)\s*(?:=\s*(\S+))?", option)
                        if matches:
                            new_define['name'] = matches.group(1)
                            if len(matches.groups()) > 2:
                                new_define['value'] = matches.group(2)
                            else:
                                new_define['boolean'] = True
                            defines.append(new_define)
                #else:
                #    common.fatal("FuseSoC cores not yet supported for " + sim_str)
                flist_template = cfg.templateEnv.get_template(f"{sim_str}.flist.j2")
                outputText = flist_template.render(defines=defines, files=files, dirs=dirs)
                flist_file_path = str(pathlib.Path(cfg.temp_path + "/" + file_path_partial_name + "_0.flist").resolve())
                with open(flist_file_path,'w') as flist_file:
                    flist_file.write(outputText)
                flist_file.close()
                
                if sim_job.simulator == common.simulators_enum.METRICS:
                    flist_file_path = os.path.relpath(flist_file_path, cfg.project_dir)
                
                return flist_file_path
    except Exception as e:
        common.fatal("Failed to convert FuseSoC output data for core '" + core.name + "': "+ str(e))


def encrypt_tree(ip_name, location, app):
    global bar
    tcl_script = ""
    files      = []
    
    for file in glob.iglob(location + '**/**', recursive=True):
        file_path = os.path.join(location, file)
        if (file_path[-2:] == ".v") or (file_path[-3:] == ".vh") or (file_path[-3:] == ".sv") or (file_path[-4:] == ".svh"):  # TODO Add support for VHDL files
            common.dbg(f"Adding '{file_path}' to files to be encrypted")
            files.append(file_path)
    
    if app == "viv":
        if not os.path.exists(cfg.encryption_key_path_vivado):
            common.fatal(f"Could not find vivado encryption key at '{cfg.encryption_key_path_vivado}'")
        
        tcl_script += f"encrypt -key {cfg.encryption_key_path_vivado} -lang ver "  # TODO Add support for VHDL files
        for file in files:
            tcl_script += f"{file} "
        common.dbg(f"TCL Script being passed to vivado for encryption: '\n{tcl_script}'")
        tcl_script_path = cfg.temp_path + "/" + ip_name + ".encrypt.viv.tcl"
        try:
            f = open(tcl_script_path, "w")
            f.write(tcl_script)
            f.close()
        except Exception as e:
            common.fatal(f"Failed to write encryption script to disk: {e}")
        launch_eda_bin(cfg.vivado_home + "/vivado", [f"-mode batch", f" -source {tcl_script_path}"], cfg.temp_path, cfg.dbg)
    elif app == "mdc":
        if not os.path.exists(cfg.encryption_key_path_metrics):
            common.fatal(f"Could not find metrics encryption key at '{cfg.encryption_key_path_metrics}'")
        mtr_key_local_path = f"{cfg.temp_path}/metrics.key"
        mtr_key_rel_path = os.path.relpath(mtr_key_local_path, cfg.temp_path)
        common.copy_file(cfg.encryption_key_path_metrics, mtr_key_local_path)
        num_files = len(files)
        with tqdm(total=num_files) as pbar:
        #with alive_bar(num_files, bar = 'smooth', stats="{eta} estimated", monitor=True, elapsed=True) as bar:
            for file in files:
                filename = os.path.basename(file)
                pbar.set_description(f"{filename}")
                file_dir_path = file.replace(filename, "")
                file_dir_rel_path = os.path.relpath(file_dir_path, cfg.temp_path)
                
                file_r = open(file,mode='r')
                file_text = file_r.read()
                file_r.close()
                file_w = open(file,mode='w')
                file_w.write("`pragma protect begin\n")
                file_w.write(file_text)
                file_w.write("`pragma protect end")
                file_w.close()
                file_rel_path = os.path.relpath(file, cfg.temp_path)
                args = [file_rel_path, f"-i {mtr_key_rel_path}", f"-o {file_rel_path}.e"]
                arg_list_str = ""
                for arg in args:
                    arg_list_str = arg_list_str + f" {arg}"
                if cfg.dbg:
                    arg_list = [f"dvlencrypt -a '{arg_list_str}'"]
                else:
                    arg_list = [f"dvlencrypt -a '{arg_list_str}'"]
                launch_eda_bin(cfg.metrics_home + "/mdc", arg_list, cfg.temp_path, cfg.dbg)
                launch_eda_bin(cfg.metrics_home + "/mdc", ["download", f"{file_rel_path}.e"], cfg.temp_path, cfg.dbg)
                common.move_file(f"{cfg.temp_path}/_downloaded_{filename}.e", file)
                pbar.update(1)
    else:
        common.fatal("Only vivado and metrics are currently supported for encryption")


def launch_eda_bin(path, args, wd, output=False, shell=True, dry_run=False):
    global eda_processes
    args_str = ""
    commands = []
    for arg in args:
        args_str = args_str + "  " + arg
    if not dry_run:
        os.chdir(wd)
        common.dbg("Launching " + path + " with arguments '" + args_str + "' from " + wd)
        if output:
            p = subprocess.Popen(path + " " + args_str, shell=shell)
        else:
            p = subprocess.Popen(path + " " + args_str + " > /dev/null 2>&1", shell=shell)
        eda_processes.append(p)
        p.wait()
    rel_wd = os.path.relpath(wd, cfg.project_dir)
    commands.append(f"cd {wd}")
    commands.append(f"{path} {args_str}")
    return commands


def kill_all_processes():
    global eda_processes
    for p in eda_processes:
        p.terminate()
        p.wait()
atexit.register(kill_all_processes)


def scan_cmp_log_file_for_errors(log_file_path, sim_job):
    common.dbg("Scanning compilation log file " + log_file_path + " for errors")
    errors = []
    if sim_job.simulator == common.simulators_enum.VIVADO:
        regexes = vivado_cmp_log_error_regexes
    elif sim_job.simulator == common.simulators_enum.VCS:
        regexes = vcs_cmp_log_error_regexes
    elif sim_job.simulator == common.simulators_enum.METRICS:
        regexes = metrics_cmp_log_error_regexes
    elif sim_job.simulator == common.simulators_enum.XCELIUM:
        regexes = xcelium_cmp_log_error_regexes
    elif sim_job.simulator == common.simulators_enum.QUESTA:
        regexes = questa_cmp_log_error_regexes
    elif sim_job.simulator == common.simulators_enum.RIVIERA:
        regexes = riviera_cmp_log_error_regexes
    try:
        for i, line in enumerate(open(log_file_path)):
            for regex in regexes:
                matches = re.search(regex, line)
                if matches:
                    errors.append(line.replace("\n", ""))
    except Exception as e:
        common.fatal("Failed while parsing compilation log file " + log_file_path + ": " + str(e))
    return errors


def scan_elab_log_file_for_errors(log_file_path, sim_job):
    common.dbg("Scanning elaboration log file " + log_file_path + " for errors")
    errors = []
    if sim_job.simulator == common.simulators_enum.VIVADO:
        regexes = vivado_elab_log_error_regexes
    elif sim_job.simulator == common.simulators_enum.VCS:
        regexes = vcs_elab_log_error_regexes
    elif sim_job.simulator == common.simulators_enum.METRICS:
        regexes = metrics_elab_log_error_regexes
    elif sim_job.simulator == common.simulators_enum.XCELIUM:
        regexes = xcelium_elab_log_error_regexes
    elif sim_job.simulator == common.simulators_enum.QUESTA:
        regexes = questa_elab_log_error_regexes
    elif sim_job.simulator == common.simulators_enum.RIVIERA:
        regexes = riviera_elab_log_error_regexes
    try:
        for i, line in enumerate(open(log_file_path)):
            for regex in regexes:
                matches = re.search(regex, line)
                if matches:
                    errors.append(line.replace("\n", ""))
    except Exception as e:
        common.fatal("Failed while parsing elaboration log file " + log_file_path + ": " + str(e))
    return errors


def scan_gen_image_log_file_for_errors(log_file_path, sim_job):
    common.dbg("Scanning compilation/elaborationn log file " + log_file_path + " for errors")
    errors = []
    if sim_job.simulator == common.simulators_enum.VIVADO:
        regexes = vivado_gen_image_log_error_regexes
    elif sim_job.simulator == common.simulators_enum.VCS:
        regexes = vcs_gen_image_log_error_regexes
    elif sim_job.simulator == common.simulators_enum.METRICS:
        regexes = metrics_gen_image_log_error_regexes
    elif sim_job.simulator == common.simulators_enum.XCELIUM:
        regexes = xcelium_gen_image_log_error_regexes
    elif sim_job.simulator == common.simulators_enum.QUESTA:
        regexes = questa_gen_image_log_error_regexes
    elif sim_job.simulator == common.simulators_enum.RIVIERA:
        regexes = riviera_gen_image_log_error_regexes
    try:
        for i, line in enumerate(open(log_file_path)):
            for regex in regexes:
                matches = re.search(regex, line)
                if matches:
                    errors.append(line.replace("\n", ""))
    except Exception as e:
        common.fatal("Failed while parsing compilation/elaboration log file " + log_file_path + ": " + str(e))
    return errors


def log_cmp_history_fsoc(core, log_path, sim_job, timestamp_start, timestamp_end):
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    common.dbg("Updating history with FuseSoC core '" + core.name + "' compilation")
    if core.name not in cfg.job_history:
        cfg.job_history[core.name] = {}
    if 'compilation' not in cfg.job_history[core.name]:
        cfg.job_history[core.name]['compilation'] = []
    cfg.job_history[core.name]['compilation'].append({
        "simulator"       : sim_str,
        'timestamp_start' : timestamp_start,
        'timestamp_end'   : timestamp_end,
        'log_path'        : log_path
    })


def log_cmp_history_ip(ip, log_path, sim_job, timestamp_start, timestamp_end):
    ip_str = f"{ip.vendor}/{ip.name}"
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    common.dbg("Updating history with IP '" + ip_str + "' compilation")
    if ip_str not in cfg.job_history:
        cfg.job_history[ip_str] = {}
    if 'compilation' not in cfg.job_history[ip_str]:
        cfg.job_history[ip_str]['compilation'] = []
    cfg.job_history[ip_str]['compilation'].append({
        "simulator"       : sim_str,
        'timestamp_start' : timestamp_start,
        'timestamp_end'   : timestamp_end,
        'log_path'        : log_path
    })


def log_cmp_history_vivado_project(ip, log_path_vlog, log_path_vhdl, sim_job, timestamp_start, timestamp_end):
    ip_str = f"{ip.vendor}/{ip.name}"
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    common.dbg("Updating history with Vivado Project IP '" + ip_str + "' compilation")
    if ip_str not in cfg.job_history:
        cfg.job_history[ip_str] = {}
    if 'compilation' not in cfg.job_history[ip_str]:
        cfg.job_history[ip_str]['compilation'] = []
    cfg.job_history[ip_str]['compilation'].append({
        "simulator"       : sim_str,
        'timestamp_start' : timestamp_start,
        'timestamp_end'   : timestamp_end,
        'log_path_vlog'   : log_path_vlog,
        'log_path_vhdl'   : log_path_vhdl
    })


def log_elab_history(ip, log_path, sim_job, timestamp_start, timestamp_end):
    ip_str = f"{ip.vendor}/{ip.name}"
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    common.dbg("Updating history with IP '" + ip_str + "' elaboration")
    if ip_str not in cfg.job_history:
        cfg.job_history[ip_str] = {}
    if 'elaboration' not in cfg.job_history[ip_str]:
        cfg.job_history[ip_str]['elaboration'] = []
    cfg.job_history[ip_str]['elaboration'].append({
        "simulator"            : sim_str,
        'timestamp_start'      : timestamp_start,
        'timestamp_end'        : timestamp_end,
        'log_path'             : log_path,
        "is_regression"        : sim_job.is_regression,
        "regression_name"      : sim_job.regression_name,
        "regression_timestamp" : sim_job.regression_timestamp
    })


def log_gen_image_history_ip(ip, log_path, sim_job, timestamp_start, timestamp_end):
    ip_str = f"{ip.vendor}/{ip.name}"
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    common.dbg("Updating history with IP '" + ip_str + "' compilation/elaboration")
    if ip_str not in cfg.job_history:
        cfg.job_history[ip_str] = {}
    if 'gen-image' not in cfg.job_history[ip_str]:
        cfg.job_history[ip_str]['gen-image'] = []
    cfg.job_history[ip_str]['gen-image'].append({
        "simulator"            : sim_str,
        'timestamp_start'      : timestamp_start,
        'timestamp_end'        : timestamp_end,
        'log_path'             : log_path,
        "is_regression"        : sim_job.is_regression,
        "regression_name"      : sim_job.regression_name,
        "regression_timestamp" : sim_job.regression_timestamp
    })


def log_sim_start_history(ip, sim_job, timestamp):
    ip_str = f"{ip.vendor}/{ip.name}"
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    common.dbg("Updating history with IP '" + ip_str + "' simulation start")
    if ip_str not in cfg.job_history:
        cfg.job_history[ip_str] = {}
    if 'simulation' not in cfg.job_history[ip_str]:
        cfg.job_history[ip_str]['simulation'] = []
    cfg.job_history[ip_str]['simulation'].append({
        "type"                 : "start",
        "simulator"            : sim_str,
        'timestamp'            : timestamp,
        'test_name'            : sim_job.test,
        'seed'                 : sim_job.seed,
        'waves'                : sim_job.waves,
        'cov'                  : sim_job.cov,
        'gui'                  : sim_job.gui,
        "args"                 : plus_args_to_str(sim_job),
        "is_regression"        : sim_job.is_regression,
        "regression_name"      : sim_job.regression_name,
        "regression_timestamp" : sim_job.regression_timestamp
    })


def log_sim_end_history(ip, sim_job, timestamp_start, timestamp_end):
    ip_str = f"{ip.vendor}/{ip.name}"
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    common.dbg("Updating history with IP '" + ip_str + "' simulation end")
    if ip_str not in cfg.job_history:
        cfg.job_history[ip_str] = {}
    if 'simulation' not in cfg.job_history[ip_str]:
        cfg.job_history[ip_str]['simulation'] = []
    common.dbg(f"{str(len(cfg.job_history[ip_str]['simulation']))} job history items before append()")
    entry = {
        "type"                 : "end",
        "simulator"            : sim_str,
        'timestamp_start'      : timestamp_start,
        'timestamp_end'        : timestamp_end,
        'log_path'             : sim_job.sim_log_file_path,
        'test_name'            : sim_job.test,
        'seed'                 : sim_job.seed,
        'waves'                : sim_job.waves,
        'cov'                  : sim_job.cov,
        'gui'                  : sim_job.gui,
        'path'                 : sim_job.results_path,
        "args"                 : plus_args_to_str(sim_job),
        "is_regression"        : sim_job.is_regression,
        "regression_name"      : sim_job.regression_name,
        "regression_timestamp" : sim_job.regression_timestamp
    }
    cfg.job_history[ip_str]['simulation'].append(entry)
    common.dbg(f"{str(len(cfg.job_history[ip_str]['simulation']))} job history items after append()")


def plus_args_to_str(sim_job):
    cli_args = sim_job.sim_args
    str = ""
    for arg in cli_args:
        str += f" {arg}"
    return str


def plus_args_list_to_str_list(plus_args):
    str_list = []
    for arg in plus_args:
        if plus_args[arg] == "":
            str_list.append(f"+{arg}")
        else:
            str_list.append(f"+{arg}={plus_args[arg]}")
    return str_list


