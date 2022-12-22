# Copyright 2022 Datum Technology Corporation
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
########################################################################################################################



from mio import cfg
from mio import cache
from mio import user
from mio import eal
import sys
import collections
import os
import yaml
import shutil
import re
import platform
import time
from enum import Enum
from yaml.loader import SafeLoader
from datetime import datetime
import hashlib
from tqdm import tqdm
from distutils.dir_util import copy_tree
from distutils.dir_util import remove_tree


class simulators_enum(Enum):
    VIVADO  = "viv"
    METRICS = "mdc"
    VCS     = "vcs"
    XCELIUM = "xcl"
    QUESTA  = "qst"
    RIVIERA = "riv"


def dbg(msg):
    if cfg.dbg:
        print("\033[32m\033[1m[mio-dbg] " + msg + " \033[0m")


def info(msg):
    print("\033[34m\033[1m[mio]\033[0m " + msg)


def warning(msg):
    print("\033[33m\033[1m[mio-warning] " + msg + " \033[0m")


def error(msg):
    print("\033[31m\033[1m[mio-error] " + msg + " \033[0m")


def fatal(msg, dump_cache=True):
    print("\033[31m\033[1m[mio-fatal] " + msg + " \033[0m")
    if dump_cache:
        cache.write_caches_to_disk()
        user.write_user_data_to_disk()
    print()
    sys.exit(0)


def banner(msg):
    print("\033[1;35m[mio] *** " + msg + " ***\033[0m")


def prompt(msg):
    return input("\033[35m\033[1m[mio]\033[0m " + msg + " ")


def exit(dump_cache=True):
    dbg("Exiting gracefully")
    if dump_cache:
        cache.write_caches_to_disk()
        user.write_user_data_to_disk()
    #remove_dir(cfg.temp_path)
    print()
    sys.exit(0)


def get_simulator_short_name(simulator):
    if simulator == simulators_enum.VIVADO:
        return "viv"
    elif simulator == simulators_enum.VCS:
        return "vcs"
    elif simulator == simulators_enum.METRICS:
        return "mdc"
    elif simulator == simulators_enum.XCELIUM:
        return "xcl"
    elif simulator == simulators_enum.QUESTA:
        return "qst"
    elif simulator == simulators_enum.RIVIERA:
        return "riv"


def get_simulator_long_name(simulator):
    if simulator == simulators_enum.VIVADO:
        return "vivado"
    elif simulator == simulators_enum.VCS:
        return "vcs"
    elif simulator == simulators_enum.METRICS:
        return "metrics"
    elif simulator == simulators_enum.XCELIUM:
        return "xcelium"
    elif simulator == simulators_enum.QUESTA:
        return "questa"
    elif simulator == simulators_enum.RIVIERA:
        return "riviera"


def merge_dict(d1, d2):
    """
    Modifies d1 in-place to contain values from d2.  If any value
    in d1 is a dictionary (or dict-like), *and* the corresponding
    value in d2 is also a dictionary, then merge them in-place.
    """
    for k, v2 in d2.items():
        v1 = d1.get(k)  # returns None if v1 has no value for this key
        if (type(v1) is dict) and (type(v2) is dict):
            merge_dict(v1, v2)
        else:
            d1[k] = v2


def timestamp():
    return datetime.now().strftime("%Y/%m/%d-%H:%M:%S")


def parse_timestamp(string):
    return datetime.strptime(string, "%Y/%m/%d-%H:%M:%S")


def dir_timestamp(path):
    timestamps = []
    for root, subdirs, files in os.walk(path):
        for file in files:
            file_p = os.path.join(root, file)
            if platform.system() == 'Windows':
                modTimesinceEpoc = os.path.getctime(file_p)
            else:
                statbuf = os.stat(file_p)
                modTimesinceEpoc = statbuf.st_mtime
            modificationTime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(modTimesinceEpoc))
            timestamps.append(modificationTime)
    if len(timestamps) > 0:
        latest_timestamp = max(timestamps)
        latest_timestamp_str = datetime.strptime(latest_timestamp, '%Y-%m-%d %H:%M:%S')
    else:
        latest_timestamp_str = timestamp()
    return latest_timestamp_str


def create_dir(path):
    try:
        if not os.path.exists(path):
            dbg("Creating directory at " + path)
            os.mkdir(path)
            dbg("Created directory at " + path)
        else:
            dbg("Not creating directory at " + path + " because it already exists")
    except:
        fatal(f"Failed to create directory {path}")


def create_file(path):
    try:
        if not os.path.exists(path):
            dbg("Creating file at " + path)
            f = open(path, "x")
            f.close()
            dbg("Created file at " + path)
        else:
            dbg("Not creating file at " + path + " because it already exists")
    except:
        fatal(f"Failed to create file {path}")


def remove_dir(path):
    if os.path.exists(path):
        dbg(f"Removing directory '{path}'")
        remove_tree(path)


def remove_file(path):
    if os.path.exists(path):
        dbg(f"Removing file '{path}'")
        os.remove(path)


def copy_file(src, dst):
    dbg(f"Copying file from '{src}' to '{dst}'")
    shutil.copyfile(src, dst)


def move_file(src, dst):
    dbg(f"Moving file from '{src}' to '{dst}'")
    shutil.move(src, dst)


def copy_directory(src, dst, symlinks=False, ignore=None):
    dbg(f"Copying directory from '{src}' to '{dst}'")
    try:
        copy_tree(src, dst)
    except Exception as e:
        fatal(f"Failed to copy from '{src}' to '{dst}': {e}")


def calc_file_hash(path):
    hash = hashlib.md5(open(path,'rb').read()).hexdigest()
    dbg("Hash for file " + path  + " is '" + hash + "'")
    return hash


def create_common_files():
    dbg("Creating common directories and files")
    try:
        create_dir(cfg.mio_data_dir        )
        create_dir(cfg.temp_path           )
        create_dir(cfg.dependencies_path   )
        create_dir(cfg.mio_user_dir        )
        create_dir(cfg.user_global_ips_path)
        create_dir(cfg.sim_output_dir      )
        create_file(cfg.job_history_file_path)
        create_file(cfg.ip_cache_file_path   )
        create_file(cfg.fsoc_cache_file_path )
        create_file(cfg.user_file_path       )
        
        with open(cfg.job_history_file_path, 'r') as yaml_file_read:
            ymlr = yaml.load(yaml_file_read, Loader=SafeLoader)
            if not ymlr:
                ymlr = { "history" : {}}
                dbg("Initializing job history file at " + cfg.job_history_file_path)
                with open(cfg.job_history_file_path, 'w') as yaml_file_write:
                    yaml.dump(ymlr, yaml_file_write)
            cfg.job_history = ymlr['history']
        
        with open(cfg.ip_cache_file_path, 'r') as yaml_file_read:
            ymlr = yaml.load(yaml_file_read, Loader=SafeLoader)
            if not ymlr:
                ymlr = {"ip" : {}}
                dbg("Initializing IP cache file at " + cfg.ip_cache_file_path)
                cfg.fresh_ip_cache = True
                with open(cfg.ip_cache_file_path, 'w') as yaml_file_write:
                    yaml.dump(ymlr, yaml_file_write)
        
        with open(cfg.fsoc_cache_file_path, 'r') as yaml_file_read:
            ymlr = yaml.load(yaml_file_read, Loader=SafeLoader)
            if not ymlr:
                ymlr = {"cores" : {}}
                dbg("Initializing FuseSoC cache file at " + cfg.fsoc_cache_file_path)
                cfg.fresh_soc_cache = True
                with open(cfg.fsoc_cache_file_path, 'w') as yaml_file_write:
                    yaml.dump(ymlr, yaml_file_write)
        
        with open(cfg.user_file_path, 'r') as yaml_file_read:
            ymlr = yaml.load(yaml_file_read, Loader=SafeLoader)
            if not ymlr:
                ymlr = {"user" : {}}
                dbg("Initializing User cache file at " + cfg.user_file_path)
                with open(cfg.user_file_path, 'w') as yaml_file_write:
                    yaml.dump(ymlr, yaml_file_write)
    except Exception as e:
        print(f"\033[31m\033[1m[mio-fatal] Could not create work directories and files: {e}\033[0m")
        sys.exit(0)


def parse_dep(string):
    vendor = ""
    ip = ""
    clean_str = string.lower().strip()
    if "/" in clean_str:
        vendor, ip = clean_str.split("/")
    else:
        ip = clean_str
        vendor = ""
    return [vendor, ip]


