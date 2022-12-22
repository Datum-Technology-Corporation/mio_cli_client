# Copyright 2022 Datum Technology Corporation
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
########################################################################################################################


from mio import cfg
from mio import clean
from mio import cov
from mio import dox
from mio import results
from mio import sim
from mio import regr
from mio import install
from mio import publish
from mio import cache
from mio import new
from mio import common
from mio import init
from mio import main
from mio import help_text
from mio import user
from mio import doctor

import sys
import argparse
import os
import subprocess
import shutil
import yaml
from datetime import datetime
from yaml.loader import SafeLoader
import re
import random
import pathlib


uvm_levels      = ["none","low","medium","high","debug"]
simulators      = ["viv","mdc","vcs","xcl","qst","riv"]
commands        = ["clean", "cov", "doctor", "dox", "init" ,"install", "login", "new", "package", "publish", "regr", "results", "sim", "!"]
repeat_commands = ["sim"]


def main():
    parser       = build_parser()
    cli_args     = parser.parse_args()
    cfg.dbg      = cli_args.dbg
    common.dbg("CLI arguments: " + str(cli_args))
    cfg.cli_args = cli_args
    
    if cli_args.help:
        print_help_text()
    if cli_args.version:
        print_version()
    
    if cli_args.command == "help":
        print_cmd_help_text(cli_args)
        common.exit(False)
    
    if cli_args.wd != None:
        cfg.set_pwd(cli_args.wd)
    else:
        cfg.pwd = os.getcwd()
    
    user.load_user_data()
    in_project = cfg.find_project_descriptor()
    
    if cli_args.command == "doctor":
        doctor.main()
        common.exit()
    
    if not in_project:
        if cli_args.command != "init":
            common.fatal("Could not find 'mio.toml' project file")
        elif cli_args.command == "init":
            init.new_project(cfg.pwd)
            common.exit(False)
    
    cfg.load_tree()
    cfg.load_configuration()
    common.create_common_files()
    log_cli_args_to_disk()
    cache.scan_and_load_ip_metadata()
    
    if cli_args.command == 'init':
        init.new_ip(cfg.pwd)
        common.exit()
    if cli_args.command == 'new':
        new.menu(cfg.cli_args.template)
        common.exit()
    if cli_args.command == 'install':
        if (cli_args.username != None) and (cli_args.username != ""):
            if (cli_args.password == None) or (cli_args.password == ""):
                common.fatal("Must specify both username AND password")
        vendor, name = common.parse_dep(cli_args.ip.lower())
        install.install_ip_and_deps(vendor, name, cli_args.is_global, cli_args.username, cli_args.password)
        common.exit()
    if cli_args.command == 'login':
        if (cli_args.username != None) and (cli_args.username != ""):
            if (cli_args.password == None) or (cli_args.password == ""):
                common.fatal("Must specify both username AND password")
        user.login(cli_args.username, cli_args.password, True)
        common.exit()
    if cli_args.command == 'package':
        cache.check_ip_str(cli_args.ip.lower())
        publish.cli_package_ip(cli_args.ip.lower(), cli_args.dest, cli_args.no_tarball)
        common.exit()
    if cli_args.command == 'publish':
        if (cli_args.username != None) and (cli_args.username != ""):
            if (cli_args.password == None) or (cli_args.password == ""):
                common.fatal("Must specify both username AND password")
        cache.check_ip_str(cli_args.ip.lower())
        publish.publish_ip(cli_args.ip.lower(), cli_args.username, cli_args.password, cli_args.org)
        common.exit()
    if cli_args.command == 'dox':
        cache.check_ip_str(cli_args.ip.lower())
        dox.gen_doxygen(cli_args.ip.lower())
        common.exit()
    if cli_args.command == 'cov':
        cache.check_ip_str(cli_args.ip.lower())
        common.banner(f"Generating coverage report for '{cli_args.ip.lower()}'")
        report_path = cov.gen_cov_report(cli_args.ip.lower())
        common.info(f"Coverage report: `pushd {report_path}`")
        common.exit()
    if cli_args.command == 'results':
        cache.check_ip_str(cli_args.ip.lower())
        common.banner(f"Parsing simulation results for '{cli_args.ip.lower()}'")
        regr_results = results.main(cli_args.ip.lower(), cli_args.filename)
        common.info(f"HTML Report: '{regr_results.html_report_path}'")
        common.info(f"Jenkins XML: '{regr_results.xml_report_path}'")
        common.exit()
    if cli_args.command == 'clean':
        cache.check_ip_str(cli_args.ip.lower())
        clean.main(cli_args.ip.lower(), cli_args.deep)
        common.exit()
    if cli_args.command == 'sim':
        sim_job = create_sim_job(cli_args)
        cache.check_ip(sim_job.vendor, sim_job.ip)
        user.login()
        sim.main(sim_job)
        common.exit()
    if cli_args.command == '!':
        sim_job = create_repeat_sim_job(cli_args)
        cache.check_ip(sim_job.vendor, sim_job.ip)
        user.login()
        sim.main(sim_job)
        common.exit()
    if cli_args.command == 'regr':
        cache.check_ip_str(cli_args.ip.lower())
        regr.main(cli_args.ip.lower(), cli_args.regr.lower(), cli_args.app, cli_args.dry)
        common.exit()
    
    common.fatal("No command specified")


def build_parser():
    parser = argparse.ArgumentParser(prog="mio", description="", add_help=False)
    parser.add_argument("-h"   , "--help"   , help="Show this help message and exit.", action="store_true", default=False, required=False)
    parser.add_argument("-v"   , "--version", help="Print the mio version and exit." , action="store_true", default=False, required=False)
    parser.add_argument("--dbg",              help="Enable mio tracing output."      , action="store_true", default=False, required=False)
    parser.add_argument("-C"   , "--wd"     , help="Run as if mio was started in <path> instead of the current working directory.", type=pathlib.Path, required=False)
    subparsers = parser.add_subparsers(help='Command to be performed by mio', dest='command')
    
    parser_help = subparsers.add_parser('help', description="Provides documentation on specific command")
    parser_help.add_argument("cmd",  help='Command whose documentation to print', choices=commands)
    
    parser_doctor = subparsers.add_parser('doctor', description=help_text.doctor_help_text, add_help=False)
    
    parser_init = subparsers.add_parser('init', description=help_text.init_help_text, add_help=False)
    
    parser_new = subparsers.add_parser('new', help=help_text.new_help_text, add_help=False)
    parser_new.add_argument('-t', '--template', help='Template name', choices=new.templates, required=False)
    
    parser_install = subparsers.add_parser('install', help=help_text.install_help_text, add_help=False)
    parser_install.add_argument('ip'              , help='Target IP'                                       )
    parser_install.add_argument("-g", "--global"  , help="Install dependencies under '~/.mio'." , action="store_true", default=False, required=False, dest="is_global")
    parser_install.add_argument('-u', "--username", help='Moore.io IP Marketplace username', required=False)
    parser_install.add_argument('-p', "--password", help='Moore.io IP Marketplace password', required=False)
    
    parser_login = subparsers.add_parser('login', help=help_text.login_help_text, add_help=False)
    parser_login.add_argument('-u', "--username", help='Moore.io IP Marketplace username', required=False)
    parser_login.add_argument('-p', "--password", help='Moore.io IP Marketplace password', required=False)
    
    parser_publish = subparsers.add_parser('publish', help=help_text.publish_help_text, add_help=False)
    parser_publish.add_argument('ip'              , help='Target IP'                                       )
    parser_publish.add_argument('-u', "--username", help='Moore.io IP Marketplace username', required=False)
    parser_publish.add_argument('-p', "--password", help='Moore.io IP Marketplace password', required=False)
    parser_publish.add_argument('-o', "--org"     , help='Moore.io IP Marketplace Organization client name.  Commercial IPs only.', required=False)
    
    parser_package = subparsers.add_parser('package', help=help_text.package_help_text, add_help=False)
    parser_package.add_argument('ip'            , help='Target IP'                          )
    parser_package.add_argument('dest'          , help='Destination path', type=pathlib.Path)
    parser_package.add_argument('-n', "--no-tgz", help='Do not create compressed tarball', required=False, action="store_true", dest="no_tarball")
    
    parser_sim = subparsers.add_parser('sim', help=help_text.sim_help_text, add_help=False)
    parser_sim.add_argument('ip'               , help='Target IP'                                                                                                                               )
    parser_sim.add_argument('-t', "--test"     , help='Delete compiled IP dependencies.'                                                                                        , required=False)
    parser_sim.add_argument('-s', "--seed"     , help='Specify the seed for constrained-random testing.  If none is provided, a random one will be picked.', type=int           , required=False)
    parser_sim.add_argument('-v', "--verbosity", help='Specify the UVM verbosity level for logging: none, low, medium, high or debug.  Default: medium'    , choices=uvm_levels , required=False)
    parser_sim.add_argument('-e', "--errors"   , help='Specifies the number of errors at which compilation/elaboration/simulation is terminated.'          , type=int           , required=False)
    parser_sim.add_argument('-a', "--app"      , help='Specifies which simulator to use: viv, mdc, vcs, xcl, qst, riv.'                                    , choices=simulators , required=False)
    parser_sim.add_argument('-w', "--waves"    , help='Enable wave capture to disk.'                                                                       , action="store_true", required=False)
    parser_sim.add_argument('-c', "--cov"      , help='Enable code & functional coverage capture.'                                                         , action="store_true", required=False)
    parser_sim.add_argument('-g', "--gui"      , help="Invoke the simulator's Graphical User Interface."                                                   , action="store_true", required=False)
    #parser_sim.add_argument('-p', "--prism"    , help='Enable Moore.io PRISM advanced UVM debugging.'                                                      , action="store_true", required=False)
    parser_sim.add_argument('-S'               , help='Force mio to simulate target IP.  Can be combined with -F, -C and/or -E.'                           , action="store_true", required=False)
    parser_sim.add_argument('-E'               , help='Force mio to elaborate target IP.  Can be combined with -F, -C and/or -S.'                          , action="store_true", required=False)
    parser_sim.add_argument('-C'               , help='Force mio to compile target IP.  Can be combined with -F, -E and/or -S.'                            , action="store_true", required=False)
    parser_sim.add_argument('-F'               , help='Force mio to invoke FuseSoC on core file(s).  Can be combined with -C, -E and/or -S.'               , action="store_true", required=False)
    parser_sim.add_argument('-+', "--args"     , help='Add arguments for compilation (+define+NAME[=VALUE]) or simulation (+NAME[=VALUE])).', nargs='+'    , dest='add_args'    , required=False)
    
    parser_repeat = subparsers.add_parser('!', help=help_text.repeat_help_text, add_help=False)
    parser_repeat.add_argument("cmd",  help='Command to be repeated', choices=repeat_commands)
    parser_repeat.add_argument('-b', "--bwrap", help='Does not run command, only creates bash script and packages project.', action="store_true", default=False , required=False)
    
    parser_sim = subparsers.add_parser('regr', help=help_text.regr_help_text, add_help=False)
    parser_sim.add_argument('ip'         , help='Target IP')
    parser_sim.add_argument('regr'       , help='Regression to be run.  For Test Bench IPs with multiple Test Suites, the suite must be specified. Ex: `mio regr my_ip apbxc.sanity`')
    parser_sim.add_argument('-a', "--app", help='Specifies which simulator to use: viv, mdc, vcs, xcl, qst, riv.', choices=simulators , required=False)
    parser_sim.add_argument('-d', "--dry", help='Compiles and elaborates target IP but only prints out the tests that would be run.', action="store_true", default=False , required=False)
    
    parser_clean = subparsers.add_parser('clean', help=help_text.clean_help_text, add_help=False)
    parser_clean.add_argument('ip'          , help='Target IP'                                                            )
    parser_clean.add_argument('-d', "--deep", help='Delete compiled IP external dependencies.', action="store_true", required=False)
    
    parser_results = subparsers.add_parser('results', help=help_text.results_help_text, add_help=False)
    parser_results.add_argument('ip'      , help='Target IP'      )
    parser_results.add_argument('filename', help='Report filename')
    
    parser_cov = subparsers.add_parser('cov', help=help_text.cov_help_text, add_help=False)
    parser_cov.add_argument('ip', help='Target IP')
    
    parser_dox = subparsers.add_parser('dox', help=help_text.dox_help_text, add_help=False)
    parser_dox.add_argument('ip', help='Target IP')
    
    return parser


def create_sim_job(cli_args):
    sim_job = sim.SimulationJob(cli_args.ip.lower())
    sim_job.is_regression = False
    
    if cli_args.app != None:
        cli_args.app = cli_args.app.lower()
        if cli_args.app == "viv":
            sim_job.simulator = common.simulators_enum.VIVADO
        elif cli_args.app == "mdc":
            sim_job.simulator = common.simulators_enum.METRICS
        elif cli_args.app == "vcs":
            sim_job.simulator = common.simulators_enum.VCS
        elif cli_args.app == "xcl":
            sim_job.simulator = common.simulators_enum.XCELIUM
        elif cli_args.app == "qst":
            sim_job.simulator = common.simulators_enum.QUESTA
        elif cli_args.app == "riv":
            sim_job.simulator = common.simulators_enum.RIVIERA
        else:
            common.dbg("Picked default simulator: vivado")
            sim_job.simulator = common.simulators_enum.VIVADO
    else:
        common.dbg("Picked default simulator: vivado")
        sim_job.simulator = common.simulators_enum.VIVADO
    common.dbg("Using simulator " + str(sim_job.simulator))
    
    if not cli_args.C and not cli_args.E and not cli_args.S:
        sim_job.compile   = True
        sim_job.elaborate = True
        sim_job.simulate  = True
    else:
        sim_job.one_shot = False
        if cli_args.C:
            sim_job.compile = True
        else:
            sim_job.compile = False
        if cli_args.E:
            sim_job.elaborate = True
        else:
            sim_job.elaborate = False
        if cli_args.S:
            sim_job.simulate = True
        else:
            sim_job.simulate = False
    
    if sim_job.simulator == common.simulators_enum.VIVADO:
        sim_job.one_shot = False
    
    if cli_args.seed == None:
        sim_job.seed = random.randint(1, 2147483646)
        common.dbg("Seed not specified, picked " + str(sim_job.seed))
    else:
        sim_job.seed = cli_args.seed
    
    if cli_args.errors == None:
        sim_job.max_errors = 10
    else:
        sim_job.max_errors = cli_args.errors
    
    if cli_args.verbosity == None:
       sim_job.verbosity = "medium"
    else:
       sim_job.verbosity = cli_args.verbosity
    
    sim_job.test     = cli_args.test
    sim_job.raw_args = cli_args.add_args
    sim_job.waves    = cli_args.waves
    sim_job.cov      = cli_args.cov
    sim_job.gui      = cli_args.gui
    
    if cli_args.gui:
        sim_job.waves = False
    
    return sim_job


def create_repeat_sim_job(cli_args):
    last_cli_args = get_last_job()
    parser        = build_parser()
    sim_args      = parser.parse_args(last_cli_args)
    sim_job = create_sim_job(sim_args)
    sim_job.dry_run = cli_args.bwrap
    sim_job.bwrap   = cli_args.bwrap
    return sim_job


def print_help_text():
    print(help_text.main_help_text)
    common.exit(False)


def print_cmd_help_text(cli_args):
    if cli_args.cmd == "clean":
        print(help_text.clean_help_text)
    if cli_args.cmd == "cov":
        print(help_text.cov_help_text)
    if cli_args.cmd == "doctor":
        print(help_text.doctor_help_text)
    if cli_args.cmd == "dox":
        print(help_text.dox_help_text)
    if cli_args.cmd == "init":
        print(help_text.init_help_text)
    if cli_args.cmd == "install":
        print(help_text.install_help_text)
    if cli_args.cmd == "login":
        print(help_text.login_help_text)
    if cli_args.cmd == "new":
        print(help_text.new_help_text)
    if cli_args.cmd == "package":
        print(help_text.package_help_text)
    if cli_args.cmd == "publish":
        print(help_text.publish_help_text)
    if cli_args.cmd == "regr":
        print(help_text.regr_help_text)
    if cli_args.cmd == "results":
        print(help_text.results_help_text)
    if cli_args.cmd == "sim":
        print(help_text.sim_help_text)
    if cli_args.cmd == "!":
        print(help_text.repeat_help_text)


def print_version():
    print(help_text.version_text)
    common.exit(False)


def get_last_job():
    try:
        if not os.path.exists(cfg.commands_file_path):
            common.fatal(f"No command history exists!")
        with open(cfg.commands_file_path, 'r') as yaml_file_read:
            ymlr = yaml.load(yaml_file_read, Loader=SafeLoader)
            timestamps = sorted(ymlr)
            common.dbg(str(ymlr[timestamps[-1]]))
            job = ymlr[timestamps[-1]]
            job.pop(0)
            return job
    except Exception as e:
        common.fatal("Failed to load command history from disk: " + str(e))



def log_cli_args_to_disk():
    if "!" in sys.argv:
        return
    try:
        common.create_file(cfg.commands_file_path)
        with open(cfg.commands_file_path, 'r') as yaml_file_read:
            ymlr = yaml.load(yaml_file_read, Loader=SafeLoader)
            if not ymlr:
                ymlr = {}
            ymlr[common.timestamp()] = sys.argv
            with open(cfg.commands_file_path, 'w') as yaml_file_write:
                yaml.dump(ymlr, yaml_file_write)
    except Exception as e:
        common.warning("Failed to log command history to disk: " + str(e))
