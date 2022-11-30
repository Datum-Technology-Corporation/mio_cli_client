# Copyright 2022 Datum Technology Corporation
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
########################################################################################################################


from mio import cache
from mio import common
from mio import cfg
from mio import cov
from mio import dox
from mio import results
from mio import sim

import os


def main():
    common.info("Checking EDA tool installations ...")
    check_simulator_executables(cfg.default_simulator)
    common.banner("The Moore.io CLI Client is properly installed and ready to go")


def check_simulator_executables(simulator):
    if simulator == common.simulators_enum.VIVADO:
        if not os.path.exists(cfg.vivado_home):
            common.fatal("Path for vivado executables could not be found " + cfg.vivado_home)
    elif simulator == common.simulators_enum.METRICS:
        if not os.path.exists(cfg.metrics_home):
            common.fatal("Path for metrics executables could not be found " + cfg.metrics_home)
    elif simulator == common.simulators_enum.VCS:
        if not os.path.exists(cfg.vcs_home):
            common.fatal("Path for vcs executables could not be found " + cfg.vcs_home)
    elif simulator == common.simulators_enum.XCELIUM:
        if not os.path.exists(cfg.xcelium_home):
            common.fatal("Path for xcelium executables could not be found " + cfg.xcelium_home)
    elif simulator == common.simulators_enum.QUESTA:
        if not os.path.exists(cfg.questa_home):
            common.fatal("Path for questa executables could not be found " + cfg.questa_home)
    elif simulator == common.simulators_enum.RIVIERA:
        if not os.path.exists(cfg.riviera_home):
            common.fatal("Path for riviera executables could not be found " + cfg.riviera_home)
    return True

