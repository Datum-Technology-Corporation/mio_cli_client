# Copyright 2021-2023 Datum Technology Corporation
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
########################################################################################################################


from mio import common
from mio import cfg
from mio import clean
from mio import dox
from mio import results
from mio import sim
from mio import eal
from mio import cache

import os
import yaml
from yaml.loader import SafeLoader
from datetime import datetime


#xcrg  -dir a1  -dir b1  -db_name d1  -db_name   d2  -merge_dir    m1   -merge_db_name   n1 -log result.txt  -report_format   html  -report_dir    report1
def gen_cov_report(ip_str, is_regression=False, test_suite="", regression_name="", regression_timestamp=""):
    vendor, name = common.parse_dep(ip_str)
    if vendor == "":
        ip = cache.get_anon_ip(name, True)
    else:
        ip = cache.get_ip(vendor, name, True)
    sim_lib = f"{ip.vendor}/{ip.name}"
    dir_string = ""
    db_name_string = ""
    if is_regression:
        cov_path    = cfg.regr_results_dir + f"/{ip.name}_{regression_name}/{regression_timestamp}/cov"
        merge_path  = cfg.regr_results_dir + f"/{ip.name}_{regression_name}/{regression_timestamp}/cov/merge"
        report_path = cfg.regr_results_dir + f"/{ip.name}_{regression_name}/{regression_timestamp}/cov/report"
    else:
        cov_path    = cfg.sim_dir + f"/cov"
        merge_path  = cfg.sim_dir + f"/cov/merge/{ip.name}/"
        report_path = cfg.sim_dir + f"/cov/reports/{ip.name}/"
    common.create_dir(cov_path)
    common.create_dir(merge_path)
    common.create_dir(report_path)
    
    merge_string = "-merge_dir " + merge_path + " -merge_db_name " + sim_lib
    now = datetime.now()
    timestamp = now.strftime("%Y/%m/%d-%H:%M:%S")
    if not sim_lib in cfg.job_history:
        common.fatal(f"No record of simulations for IP '{sim_lib}'")
    else:
        if not 'simulation' in cfg.job_history[sim_lib]:
            common.fatal(f"No record of simulations for IP '{sim_lib}'")
        else:
            for sim in cfg.job_history[sim_lib]['simulation']:
                if sim['simulator'] != 'vivado':
                    continue
                if sim['type'] != 'end':
                    continue
                cov_path = sim['path'] + "/cov"
                if sim['cov']:
                    dir_string     = dir_string + " -dir " + cov_path
                    db_name_string = db_name_string + " -db_name " + sim['test_name'] + "_" + str(sim['seed'])
    wd = cfg.sim_output_dir + "/viv/cov_wd"
    eal.launch_eda_bin(cfg.vivado_home + "/xcrg", [dir_string, db_name_string, merge_string, "-report_format html", f"-report_dir {report_path}"], wd)
    return report_path

