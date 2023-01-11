# Copyright 2021-2023 Datum Technology Corporation
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
########################################################################################################################


from mio import common
from mio import cfg
from mio import cov
from mio import dox
from mio import results
from mio import sim
from gen import new_agent_serial
from gen import new_agent_parallel
from gen import new_block
from gen import new_lib
from gen import new_singleton
from gen import new_ss
from gen import new_ral

import jinja2
from jinja2 import Template
import zipfile
import shutil
import os
import sys


templates = ["block_tb","ss_tb","ral","parallel_agent","serial_agent","lib","vseq","test","obj","comp","reg_block","reg"]
singleton_names = ["vseq","test","obj","comp","reg_block","reg"]

def menu(template_name=""):
    global singleton_names
    template_num = 0
    prompt = True
    if template_name != "":
        template_num = 0
        for template in templates:
            if template_name == template:
                prompt = False
                break
            template_num += 1
    else:
        prompt = True
    if prompt:
        common.info("***********************************************************************************************************************")
        common.info("  The following Moore.io UVM Framework templates are available:")
        common.info("***********************************************************************************************************************")
        common.info("  [ 0] - UVM Block-Level Environment & Test Bench")
        common.info("  [ 1] - UVM Sub-System Environment & Test Bench")
        common.info("  [ 2] - UVM Register Model (from .csv)")
        common.info("  [ 3] - UVM Agent - Parallel Interface")
        common.info("  [ 4] - UVM Agent - Serial Interface")
        common.info("  [ 5] - UVM Library")
        common.info("-------------------------------------------------")
        common.info("  [ 6] - UVM Virtual Sequence")
        common.info("  [ 7] - UVM Test")
        common.info("  [ 8] - UVM Object")
        common.info("  [ 9] - UVM Component")
        common.info("  [10] - UVM Register Block")
        common.info("  [11] - UVM Register")
        common.warning("Not yet implemented.")
        common.exit()
        template_num_str = common.prompt("Please enter the index of the template you wish to run: ").strip()
        template_num = int(template_num_str)
    
    if template_num == 0:
        new_block.main()
    elif template_num == 1:
        new_ss.main()
    elif template_num == 2:
        new_ral.main()
    elif template_num == 3:
        new_agent_parallel.main()
    elif template_num == 4:
        new_agent_serial.main()
    elif template_num == 5:
        new_lib.main()
    else:
        if template_num >= 6 and template_num <= 11:
            new_singleton.main(singleton_names[template_num-6])
        else:
            common.fatal("Invalid option: " + str(template_num))



