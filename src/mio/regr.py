# Copyright 2022 Datum Technology Corporation
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
########################################################################################################################


from mio import common
from mio import sim
from mio import eal
from mio import cache
from mio import cov
from mio import cfg
from mio import results
from mio import cli

import yaml
from yaml.loader import SafeLoader
from tqdm import tqdm
from multiprocessing import Process
import threading
from threading import BoundedSemaphore
from threading import Thread
import os
import random
import math
import time
from datetime import datetime


bar = None
sem = None
sem_cfg = None


class TestSuite:
    """TestSuite model"""

    def __init__(self, ip, filepath, simulator):
        self.timestamp         = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        self.ip                = ip
        self.filepath          = filepath
        self.name              = ""
        self.ip_name           = ""
        self.cmp_args          = []
        self.elab_args         = []
        self.sim_args          = []
        self.verbosity         = []
        self.sets              = {}
        self.regr              = {}
        self.waves             = []
        self.cov               = []
        self.max_durations     = []
        self.max_jobs          = []
        if simulator == "viv":
            self.simulator = common.simulators_enum.VIVADO
        elif simulator == "mdc":
            self.simulator = common.simulators_enum.METRICS
        elif simulator == "vcs":
            self.simulator = common.simulators_enum.VCS
        elif simulator == "xcl":
            self.simulator = common.simulators_enum.XCELIUM
        elif simulator == "qst":
            self.simulator = common.simulators_enum.QUESTA
        elif simulator == "riv":
            self.simulator = common.simulators_enum.RIVIERA
        else:
            self.simulator = cfg.default_simulator
    
    def parse_yml(self, yml):
        if 'test-suite' not in yml:
            common.fatal("No 'test-suite' entry!")
        common.dbg("Parsing test-suite metadata")
        
        if 'info' not in yml['test-suite']:
            common.fatal("No 'info' entry in 'test-suite'!")
        common.dbg("Parsing test-suite info")
        
        if 'name' not in yml['test-suite']['info']:
            common.fatal("No 'name' entry in 'test-suite'!")
        self.name = yml['test-suite']['info']['name'].strip()
        if not isinstance(self.name, str):
            common.fatal("'name' must be a string!")
        
        if 'ip' not in yml['test-suite']['info']:
            common.fatal("No 'ip' entry in 'test-suite'!")
        self.ip_name = yml['test-suite']['info']['ip'].strip().lower()
        if not isinstance(self.ip_name, str):
            common.fatal("'ip_name' must be a string!")
        
        if 'target' in yml['test-suite']:
            common.dbg("Parsing test-suite target")
            if 'cmp-args' in yml['test-suite']['target']:
                self.cmp_args = yml['test-suite']['target']['cmp-args']
                if type(self.cmp_args) is not list and self.cmp_args != None:
                    common.fatal("'cmp-args' must be a list!")
                for arg in self.cmp_args:
                    if not isinstance(arg, str):
                        common.fatal("'cmp-args' entry key is not a string")
                    if not isinstance(self.cmp_args[arg], str):
                        common.fatal("'cmp-args' entry is not a string")
            
            if 'elab-args' in yml['test-suite']['target']:
                self.elab_args = yml['test-suite']['target']['elab-args']
                if type(self.elab_args) is not list and self.elab_args != None:
                    common.fatal("'elab-args' must be a list!")
                for arg in self.elab_args:
                    if not isinstance(arg, str):
                        common.fatal("'elab-args' entry key is not a string")
                    if not isinstance(self.elab_args[arg], str):
                        common.fatal("'elab-args' entry is not a string")
            
            if 'sim-args' in yml['test-suite']['target']:
                self.sim_args = yml['test-suite']['target']['sim-args']
                if type(self.sim_args) is not list and self.sim_args != None:
                    common.fatal("'sim-args' must be a list!")
                for arg in self.sim_args:
                    if not isinstance(arg, str):
                        common.fatal("'sim-args' entry key is not a string")
                    if not isinstance(self.sim_args[arg], str):
                        common.fatal("'sim-args' entry is not a string")
        
        if 'settings' not in yml['test-suite']:
            common.fatal("No 'settings' entry in 'test-suite'!")
        common.dbg("Parsing test-suite settings")
        
        if 'waves' in yml['test-suite']['settings']:
            self.waves = yml['test-suite']['settings']['waves']
            if type(self.waves) is not list:
                common.fatal("'waves' must be a list!")
                for wave in self.waves:
                    if not isinstance(wave, str):
                        common.fatal("'waves' entry is not a string")
        
        if 'cov' in yml['test-suite']['settings']:
            self.cov = yml['test-suite']['settings']['cov']
            if type(self.cov) is not list:
                common.fatal("'cov' must be a list!")
                for cov in self.cov:
                    if not isinstance(cov, str):
                        common.fatal("'cov' entry is not a string")
        
        if 'verbosity' in yml['test-suite']['settings']:
            self.verbosity = yml['test-suite']['settings']['verbosity']
            if type(self.verbosity) is not dict:
                common.fatal("'max-duration' must be a dictionary!")
            for verb in self.verbosity:
                if not isinstance(verb, str):
                    common.fatal("'verbosity' entry key is not a string!")
                if not (self.verbosity[verb] in cli.uvm_levels):
                    common.fatal(f"'verbosity' entry '{self.verbosity[verb]}' is not valid! Choices are: none, low, medium, high or debug.")
        
        if 'max-duration' in yml['test-suite']['settings']:
            self.max_durations = yml['test-suite']['settings']['max-duration']
            if type(self.max_durations) is not dict:
                common.fatal("'max-duration' must be a dictionary!")
            for duration in self.max_durations:
                if not isinstance(duration, str):
                    common.fatal("'max-duration' entry key is not a string!")
                if not (type(self.max_durations[duration]) == int or float):
                    common.fatal("'max-duration' entry is not a number!")
        else:
            common.fatal("No 'max-duration' entry in test-suite settings!")
        
        if 'max-jobs' in yml['test-suite']['settings']:
            self.max_jobs = yml['test-suite']['settings']['max-jobs']
            if type(self.max_jobs) is not dict:
                common.fatal("'max-jobs' must be a dictionary!")
            for max in self.max_jobs:
                if not isinstance(max, str):
                    common.fatal("'max-jobs' entry key is not a string!")
                if not (type(self.max_jobs[max]) == int):
                    common.fatal("'max-jobs' entry is not an integer!")
        else:
            common.fatal("No 'max-jobs' entry in test-suite settings!")
        
        set_count = 0
        common.dbg("Parsing sets")
        for set in yml:
            if set == "test-suite":
                continue
            if type(yml[set]) is not dict:
                common.fatal(f"Test set '{set}' is not a dictionary!")
            test_set = TestSet(set, self)
            self.add_test_set(test_set)
            common.dbg(f"Parsing set '{set}'")
            for group in yml[set]:
                if type(yml[set][group]) is not dict:
                    common.fatal(f"Test group '{set}.{group}' is not a dictionary!")
                common.dbg(f"Parsing group '{set}.{group}'")
                group_obj = TestGroup(group, test_set)
                test_set.add_test_group(group_obj)
                for test in yml[set][group]:
                    if type(yml[set][group][test]) is not dict:
                        common.fatal(f"Test '{set}.{group}.{test}' is not a dictionary!")
                    for regr in yml[set][group][test]:
                        regr_item = yml[set][group][test][regr]
                        
                        if regr not in self.regr:
                            regression = Regression(regr.strip().lower(), group_obj, set, self)
                            self.add_regression(regression)
                            common.dbg(f"Added regression '{regr}' from '{set}.{group}.{test}'")
                        else:
                            regression = self.regr[regr]
                        args = []
                        
                        if type(regr_item) is not dict:
                            # Inline ("simple") regression entry
                            if type(regr_item) is int:
                                # Specifying how many seeds to run
                                if regr_item <= 0:
                                    common.fatal(f"value of '{regr_item}' is less than 1: '{set}.{group}.{test}.{regr}'")
                                for ii in range(regr_item):
                                    seed = random.randint(1, 2147483646)
                                    regression.add_test(test, seed, args)
                            elif type(regr_item) is list:
                                # Specifying specific seeds to run
                                for seed in regr_item:
                                    if not (type(seed) == int):
                                        common.fatal(f"seed value '{str(seed)}' is not an integer: '{set}.{group}.{test}.{regr}'!")
                                    regression.add_test(test, seed, args)
                            else:
                                common.fatal(f"Illegal regression entry: '{set}.{group}.{test}.{regr}'")
                        else:
                            # Complex regression spec
                            if 'seeds' not in regr_item:
                                common.fatal(f"Regression entry missing 'seeds' entry: '{set}.{group}.{test}.{regr}'")
                            else:
                                if 'args' in regr_item:
                                    # Sim arguments are specified
                                    if type(regr_item['args']) is not list:
                                        common.fatal(f"Regression entry args is not list: '{set}.{group}.{test}.{regr}'")
                                    args = regr_item['args']
                                    for arg in args:
                                        if not isinstance(args[arg], str):
                                            common.fatal(f"Regression entry args entry is not string: '{set}.{group}.{test}.{regr}'")
                                
                                if type(regr_item['seeds']) is int:
                                    # Specifying how many seeds to run
                                    if regr_item['seeds'] <= 0:
                                        common.fatal(f"'seeds' value '{regr_item['seeds']}' is less than 1: '{set}.{group}.{test}.{regr}'")
                                    for ii in range(regr_item['seeds']):
                                        seed = random.randint(1, 2147483646)
                                        regression.add_test(test, seed, args)
                                elif type(regr_item['seeds']) is list:
                                    # Specifying specific seeds to run
                                    for seed in regr['seeds']:
                                        if not (type(seed) == int):
                                            common.fatal(f"seed value '{str(seed)}' is not an integer: '{set}.{group}.{test}.{regr}'!")
                                        regression.add_test(test, seed, args)
                                else:
                                    common.fatal(f"Illegal regression entry: '{set}.{group}.{test}.{regr}'")

    def check_consistency(self):
        if self.ip_name != self.ip.name:
            common.fatal(f"IP '{self.ip_name}' in suite does not match '{self.ip.name}' as specified!")
        if len(self.sets) == 0:
            common.fatal("Test suite does not contain any test sets!")
        test_count = 0
        for regr in self.regr:
            if (self.regr[regr].name == cfg.regression_name):
                test_count = len(self.regr[regr].tests)
        if test_count == 0:
            common.fatal("Regression describes no tests.  Please add entries and try again.")
        if test_count > 1000:
            common.fatal("Regression describes more than 1,000 tests.  Please reduce this and try again.")
        if test_count > 100:
            common.warning(f"Regression describes more than 100 tests ({test_count})")
        #for wave in self.waves:
        #    if wave not in self.regr:
        #        common.fatal(f"'waves' entry '{wave}' is not a regression declared in this test suite")
        #for cov in self.cov:
        #    if cov not in self.regr:
        #        common.fatal(f"'cov' entry '{cov}' is not a regression declared in this test suite")
        #for verb in self.verbosity:
        #    if verb not in self.regr:
        #        common.fatal(f"'verbosity' entry '{verb}' is not a regression declared in this test suite")
        for max in self.max_durations:
            #if max not in self.regr:
            #    common.fatal(f"'max-duration' entry '{max}' is not a regression declared in this test suite")
            if max in self.regr:
                self.regr[max].max_duration = self.max_durations[max]
        for max in self.max_jobs:
            #if max not in self.regr:
            #    common.fatal(f"'max-jobs' entry '{max}' is not a regression declared in this test suite")
            if max in self.regr:
                self.regr[max].max_jobs = self.max_jobs[max]
    
    def add_test_set(self, set):
        if set.name in self.sets:
            common.fatal(f"Test group '{group.name}' already exists within test set '{self.name}'")
        else:
            self.sets[set.name] = set
            set.suite = self
    
    def add_regression(self, regr):
        self.regr[regr.name] = regr
        regr.suite = self
        common.dbg(f"Regression '{regr.name}' added to set '{self.name}'")
    
    def get_cmp_job(self):
        sim_job = sim.SimulationJob(f"{self.ip.vendor}/{self.ip.name}")
        sim_job.is_regression   = True
        sim_job.regression_name = cfg.regression_name
        sim_job.regression_timestamp = self.timestamp
        sim_job.one_shot  = False
        sim_job.compile   = True
        sim_job.elaborate = False
        sim_job.simulate  = False
        sim_job.gui       = False
        sim_job.simulator = self.simulator
        sim_job.raw_args  = self.cmp_args
        if cfg.regression_name in self.waves:
            sim_job.waves = True
        else:
            sim_job.waves = False
        if cfg.regression_name in self.cov:
            sim_job.cov = True
        else:
            sim_job.cov = False
        return sim_job
    
    def get_elab_job(self):
        sim_job = sim.SimulationJob(f"{self.ip.vendor}/{self.ip.name}")
        sim_job.is_regression   = True
        sim_job.regression_name = cfg.regression_name
        sim_job.regression_timestamp = self.timestamp
        sim_job.one_shot  = False
        sim_job.compile   = False
        sim_job.elaborate = True
        sim_job.simulate  = False
        sim_job.gui       = False
        sim_job.simulator = self.simulator
        sim_job.raw_args  = self.elab_args
        if cfg.regression_name in self.waves:
            sim_job.waves = True
        else:
            sim_job.waves = False
        if cfg.regression_name in self.cov:
            sim_job.cov = True
        else:
            sim_job.cov = False
        return sim_job
    
    def get_regression(self, regr_name):
        for reg in self.regr:
            if self.regr[reg].name == regr_name:
                return self.regr[reg]
        commmon.fatal(f"Could not find regression '{regr_name}'")


class TestSet:
    """Test Set model"""

    def __init__(self, name, suite):
        self.name         = name
        self.suite        = suite
        self.waves        = False
        self.cov          = False
        self.max_duration = 1
        self.max_jobs     = 1
        self.groups       = {}
    
    def add_test_group(self, group):
        if group.name in self.groups:
            common.fatal(f"Test group '{group.name}' already exists within test set '{self.name}'")
        else:
            self.groups[group.name] = group
            group.set = self
            common.dbg(f"Test group '{group.name}' added to set '{self.name}'")


class TestGroup:
    """Test Group model"""

    def __init__(self, name, set):
        self.name  = name
        self.set   = set
        self.tests = []
    
    def add_test(self, test):
        self.tests.append(test)
        common.fatal(f"Test '{test.name}' added to group '{self.name}'")


class Regression:
    """Regression model"""

    def __init__(self, name, group, set, suite):
        self.name         = name
        self.tests        = []
        self.set          = set
        self.group        = group
        self.suite        = suite
        self.max_duration = 0
        self.max_jobs     = 1
    
    def add_test(self, name, seed, args):
        test = RegressionTest(name, self, self.group, self.set, self.suite, seed, args)
        self.tests.append(test)
        common.dbg(f"Test '{name}' added to group '{self.group.name}'")
    
    def get_tests(self):
        return self.tests
    
    def reduce(self):
        removal_list = []
        ii = 0
        for curr_test in self.tests:
            jj = 0
            for other_test in self.tests:
                if other_test == curr_test:
                    continue
                else:
                    if (jj not in removal_list):
                        if curr_test.is_equal(other_test):
                            removal_list.append(ii)
                jj += 1
            ii += 1
        if len(removal_list) > 0:
            common.warning(f"Found {len(removal_list)} redundancies in regression '{name}'")
            for index in removal_list:
                self.tests[index].remove(index)


class RegressionTest:
    """Regression Test model"""

    def __init__(self, name, regression, test_group, set, suite, seed, args):
        self.name       = name
        self.regression = regression
        self.test_group = test_group
        self.set        = set
        self.suite      = suite
        self.seed       = seed
        self.args       = args
    
    def get_sim_job(self):
        sim_job = sim.SimulationJob(f"{self.suite.ip.vendor}/{self.suite.ip.name}")
        sim_job.is_regression   = True
        sim_job.regression_name = cfg.regression_name
        sim_job.regression_timestamp = self.suite.timestamp
        sim_job.test      = self.name
        sim_job.seed      = self.seed
        sim_job.compile   = False
        sim_job.elaborate = False
        sim_job.simulate  = True
        sim_job.gui       = False
        sim_job.simulator = self.suite.simulator
        sim_job.raw_args  = self.args
        if cfg.regression_name in self.suite.waves:
            sim_job.waves = True
        else:
            sim_job.waves = False
        if cfg.regression_name in self.suite.cov:
            sim_job.cov = True
        else:
            sim_job.cov = False
        if cfg.regression_name in self.suite.verbosity:
            sim_job.verbosity = self.suite.verbosity[cfg.regression_name]
        else:
            sim_job.verbosity = "medium"
        
        return sim_job
    
    def is_equal(self, other):
        if self.name != other.name:
            return False
        if self.regression != other.regression:
            return False
        if self.test_group != other.test_group:
            return False
        if self.set != other.set:
            return False
        if self.suite != other.suite:
            return False
        if self.seed != other.seed:
            return False
        if self.args.sort() != other.args.sort():
            return False
        return True


def main(ip_str, regression, simulator, dry_mode):
    vendor, name = common.parse_dep(ip_str)
    if vendor == "":
        ip = cache.get_anon_ip(name, True)
    else:
        ip = cache.get_ip(vendor, name, True)
    deps_to_install = len(ip.get_deps_to_install())
    if deps_to_install > 0:
        common.fatal(f"You must first install this IP's dependencies ({deps_to_install}): `mio install {name}`")
    
    timestamp_start = datetime.now()
    test_suite = scan_target_ip_for_test_suite(ip, simulator)
    regression = test_suite.get_regression(cfg.cli_args.regr)
    regression.reduce()
    tests      = regression.get_tests()
    prep_target_ip(ip, test_suite)
    
    sim_job_list = []
    for test in tests:
        sim_job_list.append(test.get_sim_job())
    
    launch_sim_jobs(ip, test_suite, regression, sim_job_list, dry_mode)
    timestamp_end = datetime.now()
    if not dry_mode:
        regr_results = results.main(f"{ip.vendor}/{ip.name}", "", True, test_suite.name, regression.name, test_suite.timestamp)
        cov_report_path = cov.gen_cov_report(f"{ip.vendor}/{ip.name}", True, test_suite.name, regression.name, test_suite.timestamp)
        print_end_of_regression_msg(ip, regr_results, cov_report_path, test_suite, regression, sim_job_list, timestamp_start, timestamp_end)


def launch_sim_jobs(ip, test_suite, regression, sim_job_list, dry_mode):
    global bar
    global sem
    global sem_cfg
    threads = []
    regression_name = ""
    if cfg.test_suite_name == "":
        regression_name = f"{cfg.regression_name}"
        common.banner(f"Running regression '{cfg.regression_name}': {str(len(sim_job_list))} test(s) with {str(regression.max_duration)} hour(s) timeout")
    else:
        regression_name = f"{cfg.test_suite_name}.{cfg.regression_name}"
        common.banner(f"Running regression '{cfg.regression_name}' from test suite '{cfg.test_suite_name}': {str(len(sim_job_list))} test(s) with {str(regression.max_duration)} hour(s) timeout")
    
    common.create_dir(cfg.regr_results_dir + "/" + cfg.target_ip_name + "_" + regression_name)
    common.create_dir(cfg.regr_results_dir + "/" + cfg.target_ip_name + "_" + regression_name + "/" + test_suite.timestamp)
    sem = BoundedSemaphore(regression.max_jobs)
    sem_cfg = BoundedSemaphore(1)
    with tqdm(sim_job_list) as bar:
    #with alive_bar(len(sim_job_list), bar = 'smooth') as bar:
        for sim_job in sim_job_list:
            common.dbg("Launching test threads")
            thread = Thread(target=launch_test, args=(ip,test_suite,sim_job,dry_mode,))
            thread.daemon = True
            threads.append(thread)
            thread.start()
            time.sleep(10) # HACK!!!!! or else threads step on top of each other
        timeout = Thread(target=timeout_process, args=(regression.max_duration,))
        timeout.daemon = True
        timeout.start()
        common.dbg("Waiting for threads to end")
        for thread in threads:
            if thread.is_alive():
                thread.join()


def timeout_process(hours):
    total_minutes = 0
    common.dbg(f"Starting timeout process for {str(hours)} hour(s)")
    for n in range(math.ceil(hours*60)):
        time.sleep(60)
        total_minutes += 1
    common.fatal(f"Regression timed out after {str(hours)} hour(s)")


def prep_target_ip(ip, test_suite):
    if cfg.test_suite_name != "":
        regression_name = cfg.test_suite_name + "_" + cfg.regression_name
    else:
        regression_name = cfg.regression_name
    cmp_job  = test_suite.get_cmp_job ()
    elab_job = test_suite.get_elab_job()
    cmp_job .regression_name = regression_name
    elab_job.regression_name = regression_name
    sim.main(cmp_job )
    sim.main(elab_job)


def launch_test(ip, test_suite, sim_job, dry_mode):
    global sem_cfg
    sem_cfg.acquire()
    if cfg.test_suite_name != "":
        regression_name = cfg.test_suite_name + "_" + cfg.regression_name
    else:
        regression_name = cfg.regression_name
    sim_job.regression_name = regression_name
    plus_args = sim.convert_cli_args_to_plusargs(sim_job)
    common.dbg("Waiting turn for simulating:\n" + str(sim_job))
    sem_cfg.release()
    wait_for_turn()
    common.dbg("Done waiting. Starting thread for simulating:\n" + str(sim_job))
    if dry_mode:
        common.info(f"  dry-run: test='{sim_job.test}' seed='{str(sim_job.seed)}' args='{str(sim_job.args)}' waves='{str(sim_job.waves)}' cov='{str(sim_job.cov)}'")
    else:
        eal.simulate(ip, sim_job)
    common.dbg("Done simulating:\n" + str(sim_job))
    bar.update(1)
    done_with_turn()


def wait_for_turn():
    global sem
    sem.acquire()


def done_with_turn():
    global sem
    sem.release()



def scan_target_ip_for_test_suite(ip, simulator):
    ip_str = f"{ip.vendor}/{ip.name}"
    cfg.regression_name = cfg.cli_args.regr
    suite = None
    test_suite_name = ""
    if "." in cfg.regression_name:
        split_string = regr_name.split(".")
        cfg.test_suite_name = split_string[0]
        cfg.regression_name = split_string[1]
        common.dbg(f"Test suite name is '{test_suite_name}' and regression name is '{cfg.regression_name}'")
    else:
        common.dbg(f"Test suite name is empty and regression name is '{cfg.regression_name}'")
    
    if ip.hdl_src_tests_path == "":
        common.fatal(f"IP '{ip_str}' does not have 'hdl-src.tests-path' defined in its ip.yml")
    ip_tests_path = ip.path + "/" + ip.src_path + "/" + ip.hdl_src_tests_path
    for dirpath, dirnames, filenames in os.walk(ip_tests_path):
        for file in filenames:
            if cfg.test_suite_name == "":
                common.dbg(f"looking at file {file}")
                if file.endswith("ts.yml"):
                    filepath = dirpath + "/" + file
                    common.dbg(f"Found target test suite descriptor file at {filepath}")
                    suite = parse_test_suite_file(ip, simulator, filepath)
                    break
            else:
                if file.endswith(".ts.yml"):
                    filepath = dirpath + "/" + file
                    ts_name = file.replace(".ts.yml", "")
                    ts_name = ts_name.replce(dirpath, "")
                    common.dbg(f"Found test suite '{ts_name}' descriptor file at {filepath}")
                    if ts_name == cfg.test_suite_name:
                        common.dbg(f"Found target test suite '{ts_name}' descriptor file at {filepath}")
                        suite = parse_test_suite_file(ip, simulator, filepath)
                        break
    if suite == None:
        common.fatal("Could not find test suite")
    return suite


def parse_test_suite_file(ip, simulator, file):
    test_suite = None
    try:
        with open(file, 'r') as yamlfile:
            ts_yaml = yaml.load(yamlfile, Loader=SafeLoader)
            if ts_yaml:
                test_suite = TestSuite(ip, file, simulator)
                test_suite.parse_yml(ts_yaml)
                test_suite.check_consistency()
            else:
                common.fatal(f"Failed to parse test suite yml '{file}':" + str(e))
    except Exception as e:
        common.fatal(f"Failed to parse test suite '{file}': " + str(e))
    return test_suite


def print_end_of_regression_msg(ip, results, cov_report_path, test_suite, regression, sim_job_list, timestamp_start, timestamp_end):
    duration = timestamp_end - timestamp_start
    hours = math.floor(duration.total_seconds() / 3600)
    minutes = math.floor((duration.total_seconds() - (hours*3600)) / 60)
    seconds = math.ceil(duration.total_seconds() - (hours*3600) - (minutes*60))
    duration_str = f"{str(hours)} hour(s), {str(minutes)} minute(s), {str(seconds)} second(s)"
    
    if cfg.test_suite_name != "":
        regression_name = cfg.test_suite_name + "_" + cfg.regression_name
    else:
        regression_name = cfg.regression_name
    
    results_path = cfg.regr_results_dir + "/" + ip.name + "_" + regression.name + "/" + test_suite.timestamp
    
    if results.passed:
        common.info("************************************************************************************************************************")
        common.info(f"  \033[32m\033[1m'{regression_name}' regression PASSED\033[0m")
        common.info("************************************************************************************************************************")
        common.info(f"  Duration: {duration_str}")
    else:
        common.info("************************************************************************************************************************")
        common.info(f"  \033[31m\033[1m'{regression_name}' regression FAILED: {str(results.num_failed_tests)} failure(s)\033[0m")
        common.info("************************************************************************************************************************")
        common.info(f"  Duration      : {duration_str}")
        common.info(f"  # tests passed: {str(results.num_passed_tests)}")
        common.info(f"  Passing rate  : {str(results.pct_passed)} %")
    
    common.info(f"")
    common.info(f"  HTML report      : firefox {results.html_report_path} &")
    common.info(f"  Coverage report  : pushd   {cov_report_path}")
    common.info(f"  Results directory: pushd   {results_path}")

