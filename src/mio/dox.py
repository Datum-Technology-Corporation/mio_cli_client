# Copyright 2022 Datum Technology Corporation
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
########################################################################################################################

from mio import common
from mio import cache
from mio import cfg
from mio import eal

import subprocess


def gen_doxygen(ip_str):
    vendor, name = common.parse_dep(ip_str)
    if vendor == "":
        ip = cache.get_anon_ip(name, True)
    else:
        ip = cache.get_ip(vendor, name, True)
    ip_name = f"{ip.vendor}/{ip.name}"
    ip_src_path = ip.path + "/" + ip.src_path
    ip_bin_path = ip.path + "/" + ip.scripts_path
    args  = " PROJECT_NAME='"  + ip.full_name + "'"
    args += " PROJECT_BRIEF='" + ip.full_name + "'"
    args += " IP_NAME='" + ip.name + "'"
    args += " PROJECT_NUMBER='" + ip.name + "'"
    args += " EXAMPLE_PATH=" + ip.path + "/" + ip.examples_path
    args += " OUTPUT_PATH="  + ip.path + "/" + ip.docs_path + "/dox_out"
    args += " SRC_PATH=" + ip_src_path + " MIO_HOME=" + cfg.mio_data_src_dir + " IP_NAME=" + ip_name
    
    args += " DOCS_PATH+=" + ip.path + "/" + ip.docs_path
    #args += " IMAGE_PATH=" + ip_path + "/" + ip_metadata['structure']['docs-path']
    #args += " INPUT+="     + ip_path + "/" + ip_metadata['structure']['docs-path']
    #for input_dir in ip_metadata['hdl-src']['directories']:
    #    if input_dir != "." and input_dir != "":
    #        args += " INPUT+=" + ip_src_path + "/" + input_dir
    #    else:
    #        args += " INPUT+=" + ip_src_path
    common.info(f"Invoking Doxygen on IP '{ip_name}' ({ip_src_path})")
    eal.launch_eda_bin(args + " doxygen", [cfg.mio_data_src_dir + "/doxygen.private.cfg"], cfg.mio_data_dir)
    common.info("Done.  To view documentation: `firefox " + ip.path + "/" + ip.docs_path + "/dox_out/html/index.html &`")
