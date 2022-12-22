# Copyright 2022 Datum Technology Corporation
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
########################################################################################################################




from mio import cfg
from mio import clean
from mio import cov
from mio import dox
from mio import results
from mio import cache
from mio import common
from mio import eal
from mio import install
from mio import doctor
from tqdm import tqdm
from tqdm import trange
from threading import Thread
from multiprocessing.pool import ThreadPool
from threading import BoundedSemaphore
import threading
import time
import os
from datetime import datetime
import yaml
from yaml.loader import SafeLoader
import math
import re
import atexit
import tarfile




bwrap_ignore_list = [
    "xsim.dir", ".str", ".Xil", ".jou", ".log", ".wdb", ".vcd", ".log", ".sdb", ".rlx", ".pb", ".o", ".png", ".jpg",
    ".svg", ".vsdx", ".docx", ".xlsx", ".pptx", ".md", "sync", "workspace"
]

bwrap_ignore_dirs = [ ".git", ".svn" ]

regex_define_pattern  = "\+define\+((?:\w|_|\d)+)(?:\=((?:\w|_|\d)+))?"
regex_plusarg_pattern = "\+((?:\w|_|\d)+)(?:\=((?:\w|_|\d)+))?"
seconds_waited = 0
num_deps_to_compile = 0
sem = BoundedSemaphore(1)
pbar = None



class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self,  *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()




class SimulationJob:
    """Simulation Job model"""
    
    def __init__(self, ip_str):
        self.vendor, self.ip = common.parse_dep(ip_str)
        self.simulator       = ""
        self.one_shot        = True
        self.fsoc            = False
        self.compile         = False
        self.elaborate       = False
        self.simulate        = False
        self.test            = ""
        self.seed            = 0
        self.max_errors      = 0
        self.gui             = False
        self.verbosity       = ""
        self.waves           = False
        self.cov             = False
        self.dry_run         = False
        self.raw_args        = []
        self.cmp_args        = {}
        self.elab_args       = {}
        self.sim_args        = {}
        
        self.bwrap           = False
        self.bwrap_commands  = []
        self.bwrap_flists    = {}
        
        self.is_regression        = False
        self.regression_name      = ""
        self.regression_timestamp = ""
        
        self.timestamp_start    = ""
        self.timestamp_end      = ""
        self.filelist_path      = ""
        self.results_path       = ""
        self.results_dir_name   = ""
        self.cmp_log_file_path  = ""
        self.elab_log_file_path = ""
        self.sim_log_file_path  = ""
        




def main(sim_job):
    global est_time
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    common.dbg(f"Starting simulation job: '{sim_job.vendor}/{sim_job.ip}'")
    if sim_job.vendor == "":
        ip = cache.get_anon_ip(sim_job.ip, True)
    else:
        ip = cache.get_ip(sim_job.vendor, sim_job.ip, True)
    if ip == None:
        common.fatal(f"Cannot find IP '{sim_job.vendor}/{sim_job.ip}'")
    ip_str = f"{ip.vendor}/{ip.name}"
    
    if sim_job.compile:
        if not ip.are_deps_installed():
            deps_to_install = ip.get_deps_to_install()
            if len(deps_to_install) > 0:
                install_deps_str = ""
                while (install_deps_str != "y") and (install_deps_str != "n"):
                    install_deps_str = common.prompt(f"{len(deps_to_install)} dependencies must first be installed.  Would you like to do so now? [y/n]").strip().lower()
                if install_deps_str == "y":
                    local_str = ""
                    while (local_str != "y") and (local_str != "n"):
                        local_str = common.prompt("Local install (vs. global)? [y/n]").strip().lower()
                    if local_str == "y":
                        global_install = False
                    else:
                        global_install = True
                    common.info(f"Installing {len(deps_to_install)} dependencies ...")
                    while len(deps_to_install) > 0:
                        try:
                            install.install_ip_dep_list(ip, deps_to_install, global_install)
                        except Exception as e:
                            common.fatal("Error during '" + ip_str + "' IP installation: " + str(e))
                        cache.scan_and_load_ip_metadata()
                        deps_to_install = ip.get_deps_to_install()
                else:
                    common.fatal("Cannot continue without first installing '" + ip_str + "' IP dependencies.")
    
    if not doctor.check_simulator_executables(sim_job.simulator):
        common.fatal("Simulator '" + sim_job.simulator + "' not installed properly or environment variable missing")
    
    if sim_job.simulator == common.simulators_enum.METRICS:
        eal.init_metrics_workspace()
    
    convert_cli_args_to_defines (sim_job)
    convert_cli_args_to_plusargs(sim_job)
    create_sim_directories()
    
    check_dependencies(ip)
    ip.update_is_compiled_elaborated(sim_job.simulator)
    
    if sim_job.one_shot:
        one_step_sim(sim_job)
    else:
        multi_step_sim(sim_job)
    
    if sim_job.bwrap:
        bubble_wrap(sim_job)


def one_step_sim(sim_job):
    global est_time
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    if sim_job.vendor == "":
        ip = cache.get_anon_ip(sim_job.ip, True)
    else:
        ip = cache.get_ip(sim_job.vendor, sim_job.ip, True)
    if ip == None:
        common.fatal(f"Cannot find IP '{sim_job.vendor}/{sim_job.ip}'")
    ip_str = f"{ip.vendor}/{ip.name}"
    flist_path = ""
    fsoc_core_name = ""
    if ip.dut_ip_type == "fsoc":
        if not ip.dut_core.is_installed:
            flist_path = eal.invoke_fsoc(ip, ip.dut_core, sim_job)
            ip.dut_core.is_installed = True
            fsoc_core_name = ip.dut_core
        else:
            common.info("Skipping processing of DUT FuseSoC core '" + ip.dut_fsoc_full_name + "'.")
    else:
        if ip.dut != None:
            if ip.dut.target_ip_model == None:
                common.fatal(f"Did not resolve DUT dependency ('{ip.dut.vendor}/{ip.dut.target_ip}')!")
            if ip.dut.target_ip_model.sub_type == "vivado":
                common.fatal("Vivado Project DUTs are not yet amenable to single-step compilation/elaboration flow.")
    
    common.info(f"Compiling+Elaborating {ip_str} ...")
    eal.gen_ip_image(ip, sim_job, fsoc_core_name, flist_path)
    if not sim_job.is_regression:
        common.banner(f"Simulating {ip_str} ...")
        eal.simulate(ip, sim_job)
        print_end_of_simulation_message(ip, sim_job)


def multi_step_sim(sim_job):
    global est_time
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    if sim_job.vendor == "":
        ip = cache.get_anon_ip(sim_job.ip, True)
    else:
        ip = cache.get_ip(sim_job.vendor, sim_job.ip, True)
    if ip == None:
        common.fatal(f"Cannot find IP '{sim_job.vendor}/{sim_job.ip}'")
    ip_str = f"{ip.vendor}/{ip.name}"
    
    cmp_ip_count = 0
    if sim_job.compile:
        if ip.has_dut:
            compile_dut = True
            if ip.dut_ip_type == "fsoc":
                compile_dut = True #ip.dut_core.is_compiled[sim_job.simulator]
            else:
                compile_dut = True #ip.is_compiled[sim_job.simulator]
            if compile_dut:
                cmp_ip_count = cmp_ip_count + 1
                if ip.dut_ip_type == "fsoc":
                    dut_str = f"{ip.dut_fsoc_name}"
                else:
                    dut_str = f"{ip.dut.vendor}/{ip.dut.target_ip}"
                if (not sim_job.dry_run) and (dut_str in cfg.job_history):
                    est_time = 0
                    curr_est_time = 0
                    if 'compilation' in cfg.job_history[dut_str]:
                        for job in cfg.job_history[dut_str]['compilation']:
                            start = datetime.strptime(job['timestamp_start'], "%Y/%m/%d-%H:%M:%S")
                            end   = datetime.strptime(job['timestamp_end'  ], "%Y/%m/%d-%H:%M:%S")
                            curr_est_time = end - start
                            curr_est_time = divmod(curr_est_time.seconds, 60)[1]
                            est_time += curr_est_time
                        est_time = math.ceil(est_time / len(cfg.job_history[dut_str]['compilation']))
                        if est_time > 0:
                            pool = ThreadPool(processes=1)
                            pool.apply_async(progress_bar)
                            cmp_dut(ip, sim_job)
                            pool.terminate()
                            pool.join()
                        else:
                            cmp_dut(ip, sim_job)
                    else:
                        cmp_dut(ip, sim_job)
                else:
                    cmp_dut(ip, sim_job)
        
        cmp_ip_count = cmp_ip_count + cmp_dependencies(ip, sim_job)
        
        #if not ip.is_compiled[sim_job.simulator]:
        if True:
            if not sim_job.is_regression:
                common.banner("Compiling IP '" + ip_str + "'")
            cmp_ip_count = cmp_ip_count + 1
            if (not sim_job.dry_run) and (ip_str in cfg.job_history):
                if 'compilation' in cfg.job_history[ip_str]:
                    est_time = 0
                    curr_est_time = 0
                    for job in cfg.job_history[ip_str]['compilation']:
                        start = datetime.strptime(job['timestamp_start'], "%Y/%m/%d-%H:%M:%S")
                        end   = datetime.strptime(job['timestamp_end'  ], "%Y/%m/%d-%H:%M:%S")
                        curr_est_time = end - start
                        curr_est_time = divmod(curr_est_time.seconds, 60)[1]
                        est_time += curr_est_time
                    est_time = math.ceil(est_time / len(cfg.job_history[ip_str]['compilation']))
                    if est_time > 0:
                        pool = ThreadPool(processes=1)
                        pool.apply_async(progress_bar)
                        cmp_target_ip(ip, sim_job)
                        pool.terminate()
                        pool.join()
                    else:
                        cmp_target_ip(ip, sim_job)
                else:
                    cmp_target_ip(ip, sim_job)
            else:
                cmp_target_ip(ip, sim_job)
    
    needs_elaboration = True #not ip.is_elaborated[sim_job.simulator]
    #if cmp_ip_count > 0:
    #    needs_elaboration = True
    
    if sim_job.elaborate and needs_elaboration:
        if sim_job.is_regression:
            common.info("Elaborating IP '" + ip_str + "'")
        else:
            common.banner("Elaborating IP '" + ip_str + "'")
        est_time = 0
        curr_est_time = 0
        if ip_str in cfg.job_history:
            if (not sim_job.dry_run) and ('elaboration' in cfg.job_history[ip_str]):
                for job in cfg.job_history[ip_str]['elaboration']:
                    start = datetime.strptime(job['timestamp_start'], "%Y/%m/%d-%H:%M:%S")
                    end   = datetime.strptime(job['timestamp_end'  ], "%Y/%m/%d-%H:%M:%S")
                    curr_est_time = end - start
                    curr_est_time = divmod(curr_est_time.seconds, 60)[1]
                    est_time += curr_est_time
                est_time = math.ceil(est_time / len(cfg.job_history[ip_str]['elaboration']))
                if est_time > 0:
                    pool = ThreadPool(processes=1)
                    pool.apply_async(progress_bar)
                    eal.elaborate(ip, sim_job)
                    pool.terminate()
                    pool.join()
                else:
                    eal.elaborate(ip, sim_job)
            else:
                eal.elaborate(ip, sim_job)
        else:
            eal.elaborate(ip, sim_job)
    else:
        if sim_job.simulate == False and not sim_job.is_regression:
            print_end_of_compilation_message(ip, sim_job)
    
    if sim_job.simulate:
        if sim_job.gui and sim_job.simulator == common.simulators_enum.METRICS:
            common.warning("The Metrics Cloud Simulator does not support GUI mode")
        if not sim_job.is_regression:
            common.banner("Simulating IP '" + ip_str + "'")
        eal.simulate(ip, sim_job)
        if sim_job.compile == True and not sim_job.is_regression:
            print_end_of_compilation_message(ip, sim_job)
        if sim_job.elaborate == True and not sim_job.is_regression:
            print_end_of_elaboration_message(ip, sim_job)
        if not sim_job.is_regression:
            print_end_of_simulation_message(ip, sim_job)
    else:
        if sim_job.elaborate == True and not sim_job.is_regression:
            if sim_job.compile == True:
                print_end_of_compilation_message(ip, sim_job)
            print_end_of_elaboration_message(ip, sim_job)



def bubble_wrap(sim_job):
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    run_script_path = f"{cfg.sim_dir}/run.sh"
    readme_path = f"{cfg.sim_dir}/README.txt"
    
    if sim_job.simulator == common.simulators_enum.VIVADO:
        bin_text = "MIO_VIVADO_HOME"
        bin_string = "vivado/bin"
    if sim_job.simulator == common.simulators_enum.METRICS:
        bin_text = "MIO_METRICS_HOME"
        bin_string = "metrics/bin"
    if sim_job.simulator == common.simulators_enum.VCS:
        bin_text = "MIO_VCS_HOME"
        bin_string = "vcs/bin"
    if sim_job.simulator == common.simulators_enum.QUESTA:
        bin_text = "MIO_QUESTA_HOME"
        bin_string = "questa/bin"
    if sim_job.simulator == common.simulators_enum.XCELIUM:
        bin_text = "MIO_XCELIUM_HOME"
        bin_string = "xcelium/bin"
    if sim_job.simulator == common.simulators_enum.RIVIERA:
        bin_text = "MIO_RIVIERA_HOME"
        bin_string = "riviera/bin"
    
    try:
        with open(run_script_path, 'w') as run_script_file:
            run_script_file.write(f"export PROJECT_ROOT_DIR=$(pwd)/..\n\n")
            for flist in sim_job.bwrap_flists:
                run_script_file.write(f"export {flist}={sim_job.bwrap_flists[flist]}\n")
            run_script_file.write("\n\n\n\n")
            for cmd in sim_job.bwrap_commands:
                cmd = cmd.replace(cfg.project_dir , "${PROJECT_ROOT_DIR}")
                cmd = cmd.replace("-f .mio/"      , "-f ${PROJECT_ROOT_DIR}/.mio/")
                cmd = cmd.replace(cfg.vivado_home , "${MIO_VIVADO_HOME}" )
                cmd = cmd.replace(cfg.metrics_home, "${MIO_METRICS_HOME}")
                cmd = cmd.replace(cfg.vcs_home    , "${MIO_VCS_HOME}"    )
                cmd = cmd.replace(cfg.xcelium_home, "${MIO_XCELIUM_HOME}")
                cmd = cmd.replace(cfg.questa_home , "${MIO_QUESTA_HOME}" )
                cmd = cmd.replace(cfg.riviera_home, "${MIO_RIVIERA_HOME}")
                run_script_file.write(f"{cmd}\n\n")
        common.info(f"Wrote {run_script_path}")
        with open(readme_path, 'w') as readme_file:
            readme_file.write(f"1. Set ${bin_text}.  Ex: export {bin_text}=/tools/{bin_string}\n")
            readme_file.write(f"2. Run: bash ./run.sh\n")
        common.info(f"Wrote {readme_path}")
        
        tarball_filename = f"{sim_job.ip}.{sim_job.test}.{sim_job.seed}.{sim_str}.tgz"
        tarball_path = f"{cfg.project_dir}/../{tarball_filename}"
        common.info(f"Writing {tarball_path} ...")
        with tarfile.open(tarball_path, "w:gz") as tar:
            files = os.listdir(cfg.project_dir)
            for file in files:
                file_path = f"{cfg.project_dir}/{file}"
                if os.path.isdir(file_path):
                    if file in bwrap_ignore_dirs:
                        continue
                common.dbg(f"Compressing {file}")
                tar.add(file_path, exclude=bwrap_exclude, arcname=file)
        common.info("Done")
        
    except Exception as e:
        common.fatal(f"Failed to create bubble-wrap tarball: {e}")



def bwrap_exclude(filename):
    for regex in bwrap_ignore_list:
        if filename.endswith(regex):
            return True



def kill_progress_bar():
    pass
atexit.register(kill_progress_bar)



def progress_bar():
    global pbar
    global seconds_waited
    with tqdm(total=est_time) as pbar:
        for i in range(est_time):
            sleep(1)
            pbar.update(1)
    #with tqdm(total=seconds) as pbar:
    #    for i in range(seconds):
    #        sleep(1)
    #        pbar.update(1)
        
    #with alive_bar(seconds, bar = 'smooth', stats="{eta} estimated", monitor=False, elapsed=True) as bar:
    #    bar.text("estimated")
    #    for x in range(seconds):
    #        time.sleep(1)
    #        seconds_waited += 1
    #        bar()




def convert_cli_args_to_defines(sim_job):
    defines = {}
    args = sim_job.raw_args
    if args != None:
        if type(args) is list:
            for item in args:
                regex = "\+define\+(\w+)(?:\=(\w+))?"
                result = re.match(regex, item)
                if result:
                    if len(result.groups()) > 1:
                        arg_name  = result.group(1)
                        arg_value = result.group(2)
                        if arg_value == None:
                            arg_value = ""
                    elif len(result.groups()) == 1:
                        arg_name  = result.group(1)
                        arg_value = ""
                    else:
                        continue
                else:
                    continue
                defines[arg_name] = arg_value
                common.dbg("Added define '" + arg_name + "' with value '" + arg_value + "' to list")
        else:
            all_args = re.sub("\"", "", args)
            for arg in all_args:
                result = re.match(regex_define_pattern, arg)
                if result:
                    define_name = result.group(1)
                    if len(result.groups()) > 1:
                        define_value = result.group(2)
                        if define_value == None:
                            arg_value = ""
                    else:
                        define_value = ""
                    defines[define_name] = define_value
                    common.dbg("Added define '" + define_name + "' with value '" + define_value + "' to list")
    sim_job.cmp_args = defines


def convert_cli_args_to_plusargs(sim_job):
    define_regex = "\+define\+(\w+)(?:\=(\w+))?"
    plus_args = {}
    args = sim_job.raw_args
    if args != None:
        if type(args) is list:
            for item in args:
                result = re.match(define_regex, item)
                if result:
                    continue
                regex = "\+(\w+)(?:\=(\w+))?"
                result = re.match(regex, item)
                if result:
                    if len(result.groups()) > 1:
                        arg_name  = result.group(1)
                        arg_value = result.group(2)
                        if arg_value == None:
                            arg_value = ""
                    elif len(result.groups()) == 1:
                        arg_name  = result.group(1)
                        arg_value = ""
                    else:
                        continue
                else:
                    continue
                plus_args[arg_name] = arg_value
                common.dbg("Added plus arg '" + arg_name + "' with value '" + arg_value + "' to list")
        else:
            all_args = re.sub("\"", "", args)
            for arg in all_args:
                result = re.match(regex_define_pattern, arg)
                if not result:
                    result = re.match(regex_plusarg_pattern, arg)
                    if result:
                        arg_name = result.group(1)
                        if len(result.groups()) > 1:
                            arg_value = result.group(2)
                            if arg_value == None:
                                arg_value = ""
                        else:
                            arg_value = ""
                        plus_args[arg_name] = arg_value
                        common.dbg("Added plus arg '" + arg_name + "' with value '" + arg_value + "' to list")
    sim_job.sim_args = plus_args


def create_sim_directories():
    common.dbg("Creating sim directories")
    common.create_dir(cfg.sim_dir)
    common.create_dir(cfg.sim_output_dir)
    common.create_dir(cfg.sim_output_dir + "/viv"                     )
    common.create_dir(cfg.sim_output_dir + "/viv/cov_wd"              )
    common.create_dir(cfg.sim_output_dir + "/viv/cmp_out"             )
    common.create_dir(cfg.sim_output_dir + "/viv/sim_wd"              )
    common.create_dir(cfg.sim_output_dir + "/viv/regr_wd"             )
    common.create_dir(cfg.sim_output_dir + "/viv/so_libs"             )
    common.create_dir(cfg.sim_output_dir + "/mdc"                     )
    common.create_dir(cfg.sim_output_dir + "/mdc/so_libs"             )
    common.create_dir(cfg.sim_output_dir + "/vcs"                     )
    common.create_dir(cfg.sim_output_dir + "/vcs/cov_wd"              )
    common.create_dir(cfg.sim_output_dir + "/vcs/cmp_out"             )
    common.create_dir(cfg.sim_output_dir + "/vcs/sim_wd"              )
    common.create_dir(cfg.sim_output_dir + "/vcs/regr_wd"             )
    common.create_dir(cfg.sim_output_dir + "/vcs/so_libs"             )
    common.create_dir(cfg.sim_output_dir + "/xcl"                     )
    common.create_dir(cfg.sim_output_dir + "/xcl/cov_wd"              )
    common.create_dir(cfg.sim_output_dir + "/xcl/cmp_out"             )
    common.create_dir(cfg.sim_output_dir + "/xcl/sim_wd"              )
    common.create_dir(cfg.sim_output_dir + "/xcl/regr_wd"             )
    common.create_dir(cfg.sim_output_dir + "/xcl/so_libs"             )
    common.create_dir(cfg.sim_output_dir + "/qst"                     )
    common.create_dir(cfg.sim_output_dir + "/qst/cov_wd"              )
    common.create_dir(cfg.sim_output_dir + "/qst/cmp_out"             )
    common.create_dir(cfg.sim_output_dir + "/qst/sim_wd"              )
    common.create_dir(cfg.sim_output_dir + "/qst/regr_wd"             )
    common.create_dir(cfg.sim_output_dir + "/qst/so_libs"             )
    common.create_dir(cfg.sim_output_dir + "/riv"                     )
    common.create_dir(cfg.sim_output_dir + "/riv/cov_wd"              )
    common.create_dir(cfg.sim_output_dir + "/riv/cmp_out"             )
    common.create_dir(cfg.sim_output_dir + "/riv/sim_wd"              )
    common.create_dir(cfg.sim_output_dir + "/riv/regr_wd"             )
    common.create_dir(cfg.sim_output_dir + "/riv/so_libs"             )
    common.create_dir(cfg.sim_dir + "/cmp")
    common.create_dir(cfg.sim_dir + "/elab")
    common.create_dir(cfg.regr_results_dir)
    common.create_dir(cfg.sim_results_dir)


def check_dependencies(ip):
    for dep in ip.dependencies:
        common.dbg(f"Checking dependency '{dep.vendor}/{dep.target_ip}'")
        found_ip = cache.get_ip(dep.vendor, dep.target_ip)
        if found_ip == None:
            common.fatal(f"Could not find IP dependency '{dep.vendor}/{dep.target_ip}'")
        else:
            check_dependencies(found_ip)


def cmp_dependencies(ip, sim_job):
    global bar
    global est_time
    global num_deps_to_compile
    deps = ip.get_ordered_deps()
    deps_to_cmp = []
    for dep in deps:
        common.dbg(f"Processing dep {dep.vendor}/{dep.name} to be compiled")
        if dep.name == "uvm":
            continue
        #if not dep.is_compiled[sim_job.simulator]:
        deps_to_cmp.append(dep)
    num_deps = len(deps_to_cmp)
    if num_deps > 0:
        if num_deps == 1:
            msg = f"Compiling 1 dependency"
        else:
            msg = f"Compiling {num_deps} dependencies"
        common.info(msg)
    else:
        return 0
    
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    defines = sim_job.cmp_args
    est_time = num_deps
    num_deps_to_compile = num_deps
    with tqdm(deps_to_cmp) as pbar:
        for dep in tqdm(deps_to_cmp):
            dep_str = f"{dep.vendor}/{dep.name}"
            pbar.set_description(dep_str)
            eal.compile_ip(dep, sim_job)
    #with alive_bar(num_deps, bar = 'smooth', stats="{eta} estimated", monitor=True, elapsed=True) as bar:
    #    for dep in deps_to_cmp:
    #        dep_str = f"{dep.vendor}/{dep.name}"
    #        bar.text(dep_str)
    #        eal.compile_ip(dep, sim_job)
    #        bar()
    return num_deps_to_compile


def cmp_dep(dep, sim_job):
    global num_deps_to_compile
    dep_str = f"{dep.vendor}/{dep.name}"
    common.dbg(f"Compiling IP dependency '{dep_str}'")
    eal.compile_ip(dep, sim_job)
    sem.acquire()
    bar.text(dep_str)
    num_deps_to_compile = num_deps_to_compile - 1
    sem.release()


def cmp_dut(ip, sim_job):
    defines = sim_job.cmp_args
    
    if ip.dut_ip_type == "fsoc":
        if not ip.dut_core.is_installed or sim_job.fsoc:
            flist_path = eal.invoke_fsoc(ip, ip.dut_core, sim_job)
            ip.dut_core.is_installed = True
        else:
            common.info("Skipping processing of DUT FuseSoC core '" + ip.dut_fsoc_full_name + "'.")
        eal.compile_fsoc_core(flist_path, ip.dut_core, sim_job)
    else:
        if ip.dut != None:
            if ip.dut.target_ip_model == None:
                common.fatal(f"Did not resolve DUT dependency ('{ip.dut.vendor}/{ip.dut.target_ip}')!")
            dut_ip_str = f"{ip.dut.vendor}/{ip.dut.target_ip}"
            compile_dut = False
            if ip.dut.target_ip_model.is_local:
                common.dbg("Found local IP DUT '" + dut_ip_str + "'")
                compile_dut = True
            else:
                common.dbg("Found external IP DUT '" + dut_ip_str + "'")
                if not ip.dut.target_ip_model.is_compiled[sim_job.simulator]:
                    compile_dut = True
            if compile_dut:
                if ip.dut.target_ip_model.sub_type == "vivado":
                    common.info("Compiling Vivado Project DUT IP '" + dut_ip_str + "'")
                    eal.compile_vivado_project(ip.dut.target_ip_model, sim_job)
                else:
                    common.info("Compiling DUT IP '" + dut_ip_str + "'")
                    eal.compile_ip(ip.dut.target_ip_model, sim_job)
            else:
                common.info("Skipping compilation of DUT IP '" + dut_ip_str + "'.")
        else:
            common.fatal("Could not find DUT IP '" + dut_ip_str + "'.")


def cmp_target_ip(ip, sim_job):
    defines = sim_job.cmp_args
    ip_str = f"{ip.vendor}/{ip.name}"
    if ip.sub_type == "vivado":
        #common.info(f"Compiling Vivado Project '{ip_str}'")
        eal.compile_vivado_project(ip_yml, sim_job)
    else:
        #common.info(f"Compiling '{ip_str}'")
        eal.compile_ip(ip, sim_job)



def print_end_of_compilation_message(ip, sim_job):
    if sim_job.dry_run:
        return
    ip_str = f"{ip.vendor}__{ip.name}"
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    if sim_job.elaborate:
        common.info("************************************************************************************************************************")
        common.info("* Compilation results: " + cfg.sim_dir + "/cmp/" + ip_str + "." + sim_str + ".cmp.log")
    else:
        common.info("************************************************************************************************************************")
        common.info("* Compilation results:")
        common.info("************************************************************************************************************************")
        common.info("  emacs " + cfg.sim_dir + "/cmp/" + ip_str + "." + sim_str + ".cmp.log &")
        common.info("  gvim  " + cfg.sim_dir + "/cmp/" + ip_str + "." + sim_str + ".cmp.log &")
        common.info("  vim   " + cfg.sim_dir + "/cmp/" + ip_str + "." + sim_str + ".cmp.log")
        common.info("")


def print_end_of_elaboration_message(ip, sim_job):
    if sim_job.dry_run:
        return
    ip_str = f"{ip.vendor}__{ip.name}"
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    if sim_job.simulate:
        common.info("************************************************************************************************************************")
        common.info("* Elaboration results: " + cfg.sim_dir + "/elab/" + ip_str + "." + sim_str + ".elab.log")
    else:
        common.info("************************************************************************************************************************")
        common.info("* Elaboration results")
        common.info("************************************************************************************************************************")
        common.info("  emacs " + cfg.sim_dir + "/elab/" + ip_str + "." + sim_str + ".elab.log &")
        common.info("  gvim  " + cfg.sim_dir + "/elab/" + ip_str + "." + sim_str + ".elab.log &")
        common.info("  vim   " + cfg.sim_dir + "/elab/" + ip_str + "." + sim_str + ".elab.log")
        common.info("")


def print_end_of_simulation_message(ip, sim_job):
    if sim_job.dry_run:
        return
    ip_str = f"{ip.vendor}/{ip.name}"
    sim_str = common.get_simulator_short_name(sim_job.simulator)
    results_path = sim_job.results_path
    common.info("************************************************************************************************************************")
    common.info("* Simulation results")
    common.info("************************************************************************************************************************")
    if (sim_job.waves):
        if sim_job.simulator == common.simulators_enum.VIVADO:
            common.info("* Waveforms: $MIO_VIVADO_HOME/xsim -gui " + results_path + "/waves.wdb &")
        elif sim_job.simulator == common.simulators_enum.VCS:
            common.info("* Waveforms: $MIO_VCS_HOME/dve -gui " + results_path + "/waves.wdb &")
        elif sim_job.simulator == common.simulators_enum.METRICS:
            common.info(f"* Waveforms: $MIO_METRICS_HOME/mdc view wave {sim_job.results_dir_name}.vcd &")
        elif sim_job.simulator == common.simulators_enum.XCELIUM:
            common.info("* Waveforms: $MIO_XCELIUM_HOME/simvision -gui " + results_path + "/waves.wdb &")
        elif sim_job.simulator == common.simulators_enum.QUESTA:
            common.info("* Waveforms: $MIO_QUESTA_HOME/visualizer -gui " + results_path + "/waves.wdb &")
        elif sim_job.simulator == common.simulators_enum.RIVIERA:
            common.info("* Waveforms: $MIO_RIVIERA_HOME/??? -gui " + results_path + "/waves.wdb &")
        common.info("")
    common.info("* Main log: emacs " + results_path + "/sim.log &")
    common.info("            gvim  " + results_path + "/sim.log &")
    common.info("            vim   " + results_path + "/sim.log")
    common.info("")
    common.info("* Transaction logs: pushd " + results_path + "/trn_log")
    common.info("* Test result dir : pushd " + results_path)
    common.info("")


