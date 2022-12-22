# Copyright 2022 Datum Technology Corporation
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
########################################################################################################################


from mio import common
from mio import cfg
from mio import clean
from mio import cov
from mio import dox
from mio import results

import sys
import re
import os
import toml
from datetime import datetime
import yaml
from yaml.loader import SafeLoader
import collections
import pathlib
import semver
import time
import fusesoc



ip_paths    = {}
ip_metadata = {}
fsoc_ip_dir_name = {}

ip_cache   = {}
core_cache = {}


class FCore:
    """FuseSoC Core Mode"""
    
    def __init__(self, dir="", path=""):
        self.dir  = dir
        self.path = path
        if path != "":
            self.core_yml_hash = common.calc_file_hash(path)
        else:
            self.core_yml_hash = ""
        self.name = ""
        self.sname = ""
        self.core_yml = {}
        self.is_installed = False
        self.is_compiled = {}
        self.is_compiled[common.simulators_enum.VIVADO ] = False
        self.is_compiled[common.simulators_enum.METRICS] = False
        self.is_compiled[common.simulators_enum.VCS    ] = False
        self.is_compiled[common.simulators_enum.XCELIUM] = False
        self.is_compiled[common.simulators_enum.QUESTA ] = False
        self.is_compiled[common.simulators_enum.RIVIERA] = False
    
    def parse_from_core_yml(self):
        try:
            with open(self.path, 'r') as ymlfile:
                yml = yaml.load(ymlfile, Loader=SafeLoader)
                self.name = yml['name'].strip()
                self.sname = self.name[(self.name.rindex(":")+1):]
                self.core_yml = yml
        except Exception as e:
            common.warning("Core file " + self.path + " is malformed and will be ignored: " + str(e))
    
    def parse_from_cache_yml(self, yml):
        self.dir  = yml['dir']
        self.path = yml['path']
        self.core_yml_hash = yml['core_yml_hash']
        self.name  = yml['name']
        self.sname = yml['sname']
        self.core_yml = yml['core_yml']
        self.is_installed = yml['is_installed']
        self.is_compiled[common.simulators_enum.VIVADO ] = yml['is_compiled']['viv']
        self.is_compiled[common.simulators_enum.METRICS] = yml['is_compiled']['mdc']
        self.is_compiled[common.simulators_enum.VCS    ] = yml['is_compiled']['vcs']
        self.is_compiled[common.simulators_enum.XCELIUM] = yml['is_compiled']['xcl']
        self.is_compiled[common.simulators_enum.QUESTA ] = yml['is_compiled']['qst']
        self.is_compiled[common.simulators_enum.RIVIERA] = yml['is_compiled']['riv']
    
    def convert_to_cache_dict(self):
        dict = {}
        dict['dir']  = self.dir
        dict['path'] = self.path
        dict['core_yml_hash'] = self.core_yml_hash
        dict['name']  = self.name
        dict['sname'] = self.sname
        dict['core_yml'] = self.core_yml
        dict['is_installed'] = self.is_installed
        dict['is_compiled'] = {}
        dict['is_compiled']['viv'] = self.is_compiled[common.simulators_enum.VIVADO ]
        dict['is_compiled']['mdc'] = self.is_compiled[common.simulators_enum.METRICS]
        dict['is_compiled']['vcs'] = self.is_compiled[common.simulators_enum.VCS    ]
        dict['is_compiled']['xcl'] = self.is_compiled[common.simulators_enum.XCELIUM]
        dict['is_compiled']['qst'] = self.is_compiled[common.simulators_enum.QUESTA ]
        dict['is_compiled']['riv'] = self.is_compiled[common.simulators_enum.RIVIERA]
        return dict
    
    def integrity_check(self):
        if os.path.exists(self.path):
            return True
        else:
            return False


class IP:
    """IP Model"""
    
    def __init__(self, is_local, is_global=False, path=""):
        self.is_new       = True
        self.is_local     = is_local
        self.is_global    = is_global
        self.path         = path
        self.name         = "undefined"
        if path != "":
            self.ip_yml_hash  = common.calc_file_hash(path + "/ip.yml")
        else:
            self.ip_yml_hash  = ""
        self.is_licensed                                   = False
        self.code_timestamp                                = ""
        self.fresh_code_timestamp                          = ""
        self.is_installed                                  = False # TODO Use package manager lib to resolve this
        self.is_encrypted                                  = False
        self.is_fsoc_processed                             = False
        self.is_compiled                                   = {}
        self.is_compiled  [common.simulators_enum.VIVADO ] = False
        self.is_compiled  [common.simulators_enum.METRICS] = False
        self.is_compiled  [common.simulators_enum.VCS    ] = False
        self.is_compiled  [common.simulators_enum.XCELIUM] = False
        self.is_compiled  [common.simulators_enum.QUESTA ] = False
        self.is_compiled  [common.simulators_enum.RIVIERA] = False
        self.is_elaborated                                 = {}
        self.is_elaborated[common.simulators_enum.VIVADO ] = False
        self.is_elaborated[common.simulators_enum.METRICS] = False
        self.is_elaborated[common.simulators_enum.VCS    ] = False
        self.is_elaborated[common.simulators_enum.XCELIUM] = False
        self.is_elaborated[common.simulators_enum.QUESTA ] = False
        self.is_elaborated[common.simulators_enum.RIVIERA] = False
        self.vendor                     = "@global"
        self.version                    = None
        self.full_name                  = ""
        self.type                       = ""
        self.sub_type                   = ""
        self.description                = ""
        self.home_page                  = ""
        self.repo_uri                   = ""
        self.bugs_uri                   = ""
        self.aliases                    = []
        self.logo                       = ""
        self.block_diagram              = ""
        self.languages                  = []
        self.simulators_supported       = {}
        self.simulators_supported[common.simulators_enum.VIVADO ] = ""
        self.simulators_supported[common.simulators_enum.METRICS] = ""
        self.simulators_supported[common.simulators_enum.VCS    ] = ""
        self.simulators_supported[common.simulators_enum.XCELIUM] = ""
        self.simulators_supported[common.simulators_enum.QUESTA ] = ""
        self.simulators_supported[common.simulators_enum.RIVIERA] = ""
        self.tags                        = []
        self.copyright_holders           = []
        self.licenses                    = []
        self.scripts_path                = ""
        self.docs_path                   = ""
        self.examples_path               = ""
        self.src_path                    = ""
        self.dependencies                = []
        self.hdl_src_directories         = []
        self.hdl_src_top_files           = []
        self.hdl_src_top_constructs      = []
        self.hdl_src_so_libs             = []
        self.hdl_src_tests_path          = ""
        self.hdl_src_test_name_template  = ""
        self.hdl_src_flists              = {}
        self.hdl_src_flists[common.simulators_enum.VIVADO ] = ""
        self.hdl_src_flists[common.simulators_enum.METRICS] = ""
        self.hdl_src_flists[common.simulators_enum.VCS    ] = ""
        self.hdl_src_flists[common.simulators_enum.XCELIUM] = ""
        self.hdl_src_flists[common.simulators_enum.QUESTA ] = ""
        self.hdl_src_flists[common.simulators_enum.RIVIERA] = ""
        self.has_dut                    = False
        self.dut                        = None
        self.dut_core                   = None
        self.dut_ip_type                = ""
        self.dut_fsoc_name              = ""
        self.dut_fsoc_full_name         = ""
        self.dut_fsoc_target            = ""
        self.vproj_name                 = ""
        self.vproj_libs                 = []
        self.vproj_vlog                 = ""
        self.vproj_vhdl                 = ""
    
    def parse_from_ip_yml(self):
        ip_yml_path = self.path + "/ip.yml"
        try:
            with open(ip_yml_path, 'r') as ymlfile:
                yml = yaml.load(ymlfile, Loader=SafeLoader)
                
                if 'ip' not in yml:
                    raise Exception(f"No 'ip' section found!")
                if 'structure' not in yml:
                    raise Exception(f"No 'structure' section found!")
                
                self.name      = yml["ip"]["name"].strip().lower()
                self.version   = yml["ip"]["version"]#semver.VersionInfo.parse(yml["ip"]["version"])
                self.full_name = yml["ip"]["full-name"].strip()
                self.type      = yml["ip"]["type"].strip().lower()
                
                if 'vendor' in yml["ip"]:
                    self.vendor = yml["ip"]["vendor"].strip().lower()
                if 'sub-type' in yml["ip"]:
                    self.sub_type = yml["ip"]["sub-type"].strip().lower()
                if 'description' in yml["ip"]:
                    self.description = yml["ip"]["description"].strip()
                if 'home-page' in yml["ip"]:
                    self.home_page = yml["ip"]["home-page"].strip().lower()
                if 'repo-uri' in yml["ip"]:
                    self.repo_uri = yml["ip"]["repo-uri"].strip().lower()
                if 'bugs' in yml["ip"]:
                    self.bugs_uri = yml["ip"]["bugs"].strip().lower()
                if 'logo' in yml["ip"]:
                    self.logo = yml["ip"]["logo"].strip()
                if 'block-diagram' in yml["ip"]:
                    self.block_diagram = yml["ip"]["block-diagram"].strip()
                if 'licensed' in yml["ip"]:
                    self.is_licensed = yml["ip"]["licensed"]
                
                if 'aliases' in yml["ip"]:
                    for alias in yml["ip"]['aliases']:
                        self.aliases.append(alias.strip().lower())
                if 'languages' in yml["ip"]:
                    for lang in yml["ip"]['languages']:
                        self.languages.append(lang.strip().lower())
                if 'tags' in yml["ip"]:
                    for tag in yml["ip"]['tags']:
                        self.tags.append(tag.strip().lower())
                if 'copyright-holders' in yml["ip"]:
                    for holder in yml["ip"]['copyright-holders']:
                        self.copyright_holders.append(holder.strip())
                if 'licenses' in yml["ip"]:
                    for license in yml["ip"]['licenses']:
                        self.licenses.append(license.strip())
                
                if 'simulators-supported' in yml['ip']:
                    if 'viv' in yml['ip']['simulators-supported']:
                        self.simulators_supported[common.simulators_enum.VIVADO] = yml['ip']['simulators-supported']['viv'].strip().lower()
                    if 'vcs' in yml['ip']['simulators-supported']:
                        self.simulators_supported[common.simulators_enum.VCS] = yml['ip']['simulators-supported']['vcs'].strip().lower()
                    if 'mdc' in yml['ip']['simulators-supported']:
                        self.simulators_supported[common.simulators_enum.METRICS] = yml['ip']['simulators-supported']['mdc'].strip().lower()
                    if 'xcl' in yml['ip']['simulators-supported']:
                        self.simulators_supported[common.simulators_enum.XCELIUM] = yml['ip']['simulators-supported']['xcl'].strip().lower()
                    if 'qst' in yml['ip']['simulators-supported']:
                        self.simulators_supported[common.simulators_enum.QUESTA] = yml['ip']['simulators-supported']['qst'].strip().lower()
                    if 'riv' in yml['ip']['simulators-supported']:
                        self.simulators_supported[common.simulators_enum.RIVIERA] = yml['ip']['simulators-supported']['riv'].strip().lower()
                
                self.scripts_path  = yml['structure']['scripts-path'] .strip()
                self.docs_path     = yml['structure']['docs-path']    .strip()
                self.examples_path = yml['structure']['examples-path'].strip()
                self.src_path      = yml['structure']['src-path']     .strip()
                
                if 'dependencies' in yml:
                    if type(yml['dependencies']) is dict:
                        for dep in yml['dependencies']:
                            dep_model = Dependency(self, dep, yml['dependencies'][dep])
                            self.dependencies.append(dep_model)
                
                if 'hdl-src' in yml:
                    if 'encrypted' in yml['hdl-src']:
                        self.is_encrypted = yml['hdl-src']['encrypted']
                    if 'directories' in yml['hdl-src']:
                        for dir in yml['hdl-src']['directories']:
                            self.hdl_src_directories.append(dir.strip())
                    if 'top-files' in yml['hdl-src']:
                        for file in yml['hdl-src']['top-files']:
                            self.hdl_src_top_files.append(file.strip())
                    if 'top-constructs' in yml['hdl-src']:
                        for construct in yml['hdl-src']['top-constructs']:
                            self.hdl_src_top_constructs.append(construct.strip())
                    if 'so-libs' in yml['hdl-src']:
                        for lib in yml['hdl-src']['so-libs']:
                            self.hdl_src_so_libs.append(lib.strip())
                    if 'tests-path' in yml['hdl-src']:
                        self.hdl_src_tests_path = yml['hdl-src']['tests-path'].strip()
                    if 'test-name-template' in yml['hdl-src']:
                        self.hdl_src_test_name_template = yml['hdl-src']['test-name-template'].strip()
                    
                    if 'flist' in yml['hdl-src']:
                        if 'viv' in yml['hdl-src']['flist']:
                            self.hdl_src_flists[common.simulators_enum.VIVADO] = yml['hdl-src']['flist']['viv'].strip()
                        if 'vcs' in yml['hdl-src']['flist']:
                            self.hdl_src_flists[common.simulators_enum.VCS] = yml['hdl-src']['flist']['vcs'].strip()
                        if 'mdc' in yml['hdl-src']['flist']:
                            self.hdl_src_flists[common.simulators_enum.METRICS] = yml['hdl-src']['flist']['mdc'].strip()
                        if 'xcl' in yml['hdl-src']['flist']:
                            self.hdl_src_flists[common.simulators_enum.XCELIUM] = yml['hdl-src']['flist']['xcl'].strip()
                        if 'qst' in yml['hdl-src']['flist']:
                            self.hdl_src_flists[common.simulators_enum.QUESTA] = yml['hdl-src']['flist']['qst'].strip()
                        if 'riv' in yml['hdl-src']['flist']:
                            self.hdl_src_flists[common.simulators_enum.RIVIERA] = yml['hdl-src']['flist']['riv'].strip()
                
                if self.sub_type == "vivado":
                    if 'viv-project' not in yml:
                        raise Exception(f"No 'viv-project' section found!")
                    self.vproj_name = yml["viv-project"]["name"]
                    self.vproj_libs = yml["viv-project"]["libs"]
                    self.vproj_vlog = yml["viv-project"]["vlog"]
                    self.vproj_vhdl = yml["viv-project"]["vhdl"]
                
                if 'dut' in yml:
                    if isinstance(yml['dut'], str):
                        self.has_dut = True
                        self.dut_ip_type = ""
                        self.dut = Dependency(self, yml['dut'].strip().lower(), "@local")
                    elif 'type' in yml['dut']:
                        self.has_dut = True
                        if 'type' in yml['dut']:
                            self.dut_ip_type = yml['dut']['type'].lower().strip()
                        if self.dut_ip_type == "fsoc":
                            self.dut_fsoc_name      = yml['dut']['name']     .strip().lower()
                            self.dut_fsoc_full_name = yml['dut']['full-name'].strip().lower()
                            self.dut_fsoc_target    = yml['dut']['target']   .strip().lower()
                        elif (self.dut_ip_type == "") or (self.dut_ip_type == "mio") or (self.dut_ip_type == "ip"):
                            self.dut_ip_type = ""
                            self.dut = Dependency(self, yml['dut']['name'].strip().lower(), "@local")
                        else:
                            raise Exception(f"Invalid dut type: {self.dut_ip_type}")
                    else:
                        raise Exception(f"Malformed dut section")
                
                if (self.is_licensed == True) and (self.is_encrypted == True):
                    if not ((self.vendor == "datum") and (self.name == "uvml_mio_lic")):
                        dep_model = Dependency(self, "datum/uvml_mio_lic", "^")
                        self.dependencies.append(dep_model)
        except Exception as e:
            common.warning("IP file " + ip_yml_path + " is malformed and will be ignored: " + str(e))
    
    def parse_from_cache_yml(self, yml):
        try:
            self.code_timestamp    = yml['code_timestamp']
            self.is_licensed       = yml['is_licensed']
            self.is_local          = yml['is_local']
            self.is_global         = yml['is_global']
            self.path              = yml['path']
            self.name              = yml['name']
            self.ip_yml_hash       = yml['ip_yml_hash']
            self.is_installed      = yml['is_installed']
            self.is_encrypted      = yml['is_encrypted']
            self.is_fsoc_processed = yml['is_fsoc_processed']
            self.is_compiled  [common.simulators_enum.VIVADO ] = yml['is_compiled']['viv']
            self.is_compiled  [common.simulators_enum.METRICS] = yml['is_compiled']['mdc']
            self.is_compiled  [common.simulators_enum.VCS    ] = yml['is_compiled']['vcs']
            self.is_compiled  [common.simulators_enum.XCELIUM] = yml['is_compiled']['xcl']
            self.is_compiled  [common.simulators_enum.QUESTA ] = yml['is_compiled']['qst']
            self.is_compiled  [common.simulators_enum.RIVIERA] = yml['is_compiled']['riv']
            self.is_elaborated[common.simulators_enum.VIVADO ] = yml['is_elaborated']['viv']
            self.is_elaborated[common.simulators_enum.METRICS] = yml['is_elaborated']['mdc']
            self.is_elaborated[common.simulators_enum.VCS    ] = yml['is_elaborated']['vcs']
            self.is_elaborated[common.simulators_enum.XCELIUM] = yml['is_elaborated']['xcl']
            self.is_elaborated[common.simulators_enum.QUESTA ] = yml['is_elaborated']['qst']
            self.is_elaborated[common.simulators_enum.RIVIERA] = yml['is_elaborated']['riv']
            self.vendor                     = yml["vendor"]
            self.version                    = yml["version"]#semver.VersionInfo.parse(yml["version"])
            self.full_name                  = yml["full_name"]
            self.type                       = yml["type"]
            self.sub_type                   = yml["sub_type"]
            self.description                = yml["description"]
            self.home_page                  = yml["home_page"]
            self.repo_uri                   = yml["repo_uri"]
            self.bugs_uri                   = yml["bugs_uri"]
            self.aliases                    = yml["aliases"]
            self.logo                       = yml["logo"]
            self.block_diagram              = yml["block_diagram"]
            self.languages                  = yml["languages"]
            self.simulators_supported[common.simulators_enum.VIVADO ] = yml['simulators_supported']['viv']
            self.simulators_supported[common.simulators_enum.METRICS] = yml['simulators_supported']['mdc']
            self.simulators_supported[common.simulators_enum.VCS    ] = yml['simulators_supported']['vcs']
            self.simulators_supported[common.simulators_enum.XCELIUM] = yml['simulators_supported']['xcl']
            self.simulators_supported[common.simulators_enum.QUESTA ] = yml['simulators_supported']['qst']
            self.simulators_supported[common.simulators_enum.RIVIERA] = yml['simulators_supported']['riv']
            self.tags                       = yml["tags"]
            self.copyright_holders          = yml["copyright_holders"]
            self.licenses                   = yml["licenses"]
            self.scripts_path               = yml["scripts_path"]
            self.docs_path                  = yml["docs_path"]
            self.examples_path              = yml["examples_path"]
            self.src_path                   = yml["src_path"]
            self.hdl_src_directories        = yml["hdl_src_directories"]
            self.hdl_src_top_files          = yml["hdl_src_top_files"]
            self.hdl_src_top_constructs     = yml["hdl_src_top_constructs"]
            self.hdl_src_so_libs            = yml["hdl_src_so_libs"]
            self.hdl_src_tests_path         = yml["hdl_src_tests_path"]
            self.hdl_src_test_name_template = yml["hdl_src_test_name_template"]
            self.hdl_src_flists[common.simulators_enum.VIVADO ] = yml['hdl_src_flists']['viv']
            self.hdl_src_flists[common.simulators_enum.METRICS] = yml['hdl_src_flists']['mdc']
            self.hdl_src_flists[common.simulators_enum.VCS    ] = yml['hdl_src_flists']['vcs']
            self.hdl_src_flists[common.simulators_enum.XCELIUM] = yml['hdl_src_flists']['xcl']
            self.hdl_src_flists[common.simulators_enum.QUESTA ] = yml['hdl_src_flists']['qst']
            self.hdl_src_flists[common.simulators_enum.RIVIERA] = yml['hdl_src_flists']['riv']
            self.has_dut                    = yml["has_dut"]
            self.dut_ip_type                = yml["dut_ip_type"]
            self.dut_fsoc_name              = yml["dut_fsoc_name"]
            self.dut_fsoc_full_name         = yml["dut_fsoc_full_name"]
            self.dut_fsoc_target            = yml["dut_fsoc_target"]
            self.vproj_name                 = yml["vproj_name"]
            self.vproj_libs                 = yml["vproj_libs"]
            self.vproj_vlog                 = yml["vproj_vlog"]
            self.vproj_vhdl                 = yml["vproj_vhdl"]
            
            if self.has_dut:
                if yml["dut_vendor"] != "":
                    dut_name = yml["dut_name"]
                    dut_vendor = yml["dut_vendor"]
                    self.dut = Dependency(self, f"{dut_vendor}/{dut_name}", yml["dut_version"])
                else:
                    self.dut = Dependency(self, yml["dut_name"], yml["dut_version"])
            
            self.dependencies= []
            for dep in yml['dependencies']:
                dep_model = Dependency(self, dep, yml['dependencies'][dep])
                self.dependencies.append(dep_model)
            self.is_new = False
            return True
        except Exception as e:
            common.warning(f"Error during parsing from cache: {e}")
            return False
    
    def convert_to_cache_dict(self):
        dict = {}
        dict['code_timestamp']              = self.code_timestamp
        dict['is_licensed']                 = self.is_licensed
        dict['is_local']                    = self.is_local
        dict['is_global']                   = self.is_global
        dict['path']                        = self.path
        dict['name']                        = self.name
        dict['ip_yml_hash']                 = self.ip_yml_hash
        dict['is_installed']                = self.is_installed
        dict['is_encrypted']                = self.is_encrypted
        dict['is_fsoc_processed']           = self.is_fsoc_processed
        dict['is_compiled']                 = {}
        dict['is_compiled']['viv']          = self.is_compiled  [common.simulators_enum.VIVADO ]
        dict['is_compiled']['mdc']          = self.is_compiled  [common.simulators_enum.METRICS]
        dict['is_compiled']['vcs']          = self.is_compiled  [common.simulators_enum.VCS    ]
        dict['is_compiled']['xcl']          = self.is_compiled  [common.simulators_enum.XCELIUM]
        dict['is_compiled']['qst']          = self.is_compiled  [common.simulators_enum.QUESTA ]
        dict['is_compiled']['riv']          = self.is_compiled  [common.simulators_enum.RIVIERA]
        dict['is_elaborated']               = {}
        dict['is_elaborated']['viv']        = self.is_elaborated[common.simulators_enum.VIVADO ]
        dict['is_elaborated']['mdc']        = self.is_elaborated[common.simulators_enum.METRICS]
        dict['is_elaborated']['vcs']        = self.is_elaborated[common.simulators_enum.VCS    ]
        dict['is_elaborated']['xcl']        = self.is_elaborated[common.simulators_enum.XCELIUM]
        dict['is_elaborated']['qst']        = self.is_elaborated[common.simulators_enum.QUESTA ]
        dict['is_elaborated']['riv']        = self.is_elaborated[common.simulators_enum.RIVIERA]
        dict['vendor']                      = self.vendor
        dict['version']                     = str(self.version)
        dict['full_name']                   = self.full_name
        dict['type']                        = self.type
        dict['sub_type']                    = self.sub_type
        dict['description']                 = self.description
        dict['home_page']                   = self.home_page
        dict['repo_uri']                    = self.repo_uri
        dict['bugs_uri']                    = self.bugs_uri
        dict['aliases']                     = self.aliases
        dict['logo']                        = self.logo
        dict['block_diagram']               = self.block_diagram
        dict['languages']                   = self.languages
        dict['simulators_supported']        = {}
        dict['simulators_supported']['viv'] = self.simulators_supported[common.simulators_enum.VIVADO ]
        dict['simulators_supported']['mdc'] = self.simulators_supported[common.simulators_enum.METRICS]
        dict['simulators_supported']['vcs'] = self.simulators_supported[common.simulators_enum.VCS    ]
        dict['simulators_supported']['xcl'] = self.simulators_supported[common.simulators_enum.XCELIUM]
        dict['simulators_supported']['qst'] = self.simulators_supported[common.simulators_enum.QUESTA ]
        dict['simulators_supported']['riv'] = self.simulators_supported[common.simulators_enum.RIVIERA]
        dict['tags']                       = self.tags
        dict['copyright_holders']          = self.copyright_holders
        dict['licenses']                   = self.licenses
        dict['scripts_path']               = self.scripts_path
        dict['docs_path']                  = self.docs_path
        dict['examples_path']              = self.examples_path
        dict['src_path']                   = self.src_path
        dict['hdl_src_directories']        = self.hdl_src_directories
        dict['hdl_src_top_files']          = self.hdl_src_top_files
        dict['hdl_src_top_constructs']     = self.hdl_src_top_constructs
        dict['hdl_src_so_libs']            = self.hdl_src_so_libs
        dict['hdl_src_tests_path']         = self.hdl_src_tests_path
        dict['hdl_src_test_name_template'] = self.hdl_src_test_name_template
        dict['hdl_src_flists']             = {}
        dict['hdl_src_flists']['viv']      = self.hdl_src_flists[common.simulators_enum.VIVADO ]
        dict['hdl_src_flists']['mdc']      = self.hdl_src_flists[common.simulators_enum.METRICS]
        dict['hdl_src_flists']['vcs']      = self.hdl_src_flists[common.simulators_enum.VCS    ]
        dict['hdl_src_flists']['xcl']      = self.hdl_src_flists[common.simulators_enum.XCELIUM]
        dict['hdl_src_flists']['qst']      = self.hdl_src_flists[common.simulators_enum.QUESTA ]
        dict['hdl_src_flists']['riv']      = self.hdl_src_flists[common.simulators_enum.RIVIERA]
        dict['has_dut']                    = self.has_dut
        dict['dut_ip_type']                = self.dut_ip_type
        dict["dut_fsoc_name"]              = self.dut_fsoc_name
        dict['dut_fsoc_full_name']         = self.dut_fsoc_full_name
        dict['dut_fsoc_target']            = self.dut_fsoc_target
        dict["vproj_name"]                 = self.vproj_name
        dict["vproj_libs"]                 = self.vproj_libs
        dict["vproj_vlog"]                 = self.vproj_vlog
        dict["vproj_vhdl"]                 = self.vproj_vhdl
        
        if self.has_dut and (self.dut != None):
            dict['dut_vendor']  = self.dut.vendor
            dict['dut_name']    = self.dut.target_ip
            dict['dut_version'] = self.dut.semver
        else:
            dict['dut_vendor']  = ""
            dict['dut_name']    = ""
            dict['dut_version'] = ""
        
        dict['dependencies'] = {}
        for dep in self.dependencies:
            dict['dependencies'][f"{dep.vendor}/{dep.target_ip}"] = dep.semver
        return dict
    
    def integrity_check(self):
        if os.path.exists(self.path + "/ip.yml"):
            return True
        else:
            return False
    
    def calc_code_timestamp(self):
        src_path = f"{self.path}/{self.src_path}/"
        self.code_timestamp = common.dir_timestamp(src_path)
        common.dbg(f"{self.vendor}/{self.name}: calc_code_timestamp={self.code_timestamp}")
    
    def reset_is_compiled_elaborated(self):
        clean.clean_ip(self, True)
    
    def update_is_compiled_elaborated(self, simulator):
        needs_update = False
        if self.is_local:
            for dep in self.dependencies:
                if dep.target_ip_model == None:
                    common.fatal(f"Dependency '{dep.vendor}/{dep.target_ip}' is null!")
                dep.target_ip_model.update_is_compiled_elaborated(simulator)
                if not dep.target_ip_model.is_compiled[simulator]:
                    needs_update = True
        if needs_update:
            self.reset_is_compiled_elaborated()
        else:
            if self.fresh_code_timestamp == "":
                src_path = f"{self.path}/{self.src_path}/"
                self.fresh_code_timestamp = common.dir_timestamp(src_path)
                common.dbg(f"{self.vendor}/{self.name}: fresh_timestamp={self.fresh_code_timestamp}")
            if self.fresh_code_timestamp != self.code_timestamp:
                self.reset_is_compiled_elaborated()
    
    def resolve_dependencies(self):
        common.dbg(f"Resolving dependencies for IP '{self.vendor}/{self.name}'")
        if self.has_dut:
            if self.dut_ip_type == "fsoc":
                self.dut_core = get_core(self.dut_fsoc_full_name, True)
            else:
                self.dut.resolve()
                self.dut_vendor = self.dut.target_ip_model.vendor
        for dep in self.dependencies:
            dep.resolve()
    
    def get_ordered_deps(self):
        deps_list = []
        self.dependencies.sort(key= get_key)
        for dep in self.dependencies:
            common.dbg(f"Processing dependency '{dep.vendor}/{dep.target_ip}'")
            deps_deps_list = dep.target_ip_model.get_ordered_deps()
            deps_list += deps_deps_list
            deps_list.append(dep.target_ip_model)
        unique_deps = []
        for dep in deps_list:
            if dep not in unique_deps:
                unique_deps.append(dep)
        return unique_deps
    
    def get_deps_to_install(self):
        deps = []
        for dep in self.dependencies:
            dep_ip = get_ip(dep.vendor, dep.target_ip)
            if dep_ip == None:
                deps.append(f"{dep.vendor}/{dep.target_ip}")
            else:
                deps += dep_ip.get_deps_to_install()
        unique_deps = []
        for dep in deps:
            if dep not in unique_deps:
                unique_deps.append(dep)
        return unique_deps
    
    def get_total_deps(self):
        total_deps = 0
        for dep in self.dependencies:
            total_deps += 1
            if not dep.target_ip_model == None:
                total_deps += dep.target_ip_model.get_total_deps()
        return total_deps
    
    def are_deps_installed(self):
        is_installed = True
        for dep in self.dependencies:
            common.dbg(f"Checking dependency '{dep.vendor}/{dep.target_ip}' to see if it's installed")
            dep_ip = get_ip(dep.vendor, dep.target_ip)
            if dep_ip == None:
                is_installed = False
                break
            else:
                dep_is_installed = dep_ip.are_deps_installed()
                if not dep_is_installed:
                    is_installed = False
                    break
        return is_installed


def get_key(obj):
    if obj.target_ip_model == None:
        common.fatal(f"Dependency '{obj.target_ip}' is null!")
    return obj.target_ip_model.get_total_deps()


class Dependency:
    """IP Dependency Model"""
    
    def __init__(self, owner_ip, dep_string, semver):
        self.vendor    = ""
        self.target_ip = ""
        self.parse_dep_string(dep_string)
        self.semver    = semver
        self.owner_ip  = owner_ip
        self.target_ip_model = None
        common.dbg(f"Dependency after parsing: vendor='{self.vendor}' , target_ip='{self.target_ip}'")
    
    def parse_dep_string(self, string):
        clean_str = string.lower().strip()
        if "/" in clean_str:
            self.vendor, self.target_ip = clean_str.split("/")
        else:
            self.target_ip = clean_str
            self.vendor = ""
    
    def resolve(self):
        common.dbg(f"Dep '{self.vendor}/{self.target_ip}' resolving ...")
        if self.vendor == "":
            self.target_ip_model = get_anon_ip(self.target_ip)
        else:
            self.target_ip_model = get_ip(self.vendor, self.target_ip)
        if self.target_ip_model != None:
            common.dbg(f"Dep '{self.vendor}/{self.target_ip}' resolved!")
            self.vendor = self.target_ip_model.vendor
            self.semver = self.target_ip_model.version


def check_ip(vendor, name):
    if vendor == "":
        ip = get_anon_ip(name)
    else:
        ip = get_ip(vendor, name)
    if ip == None:
        common.fatal(f"Could not find target IP {vendor}/{name}")


def check_ip_str(ip_str):
    vendor, name = common.parse_dep(ip_str)
    if vendor == "":
        ip = get_anon_ip(name)
    else:
        ip = get_ip(vendor, name)
    if ip == None:
        common.fatal(f"Could not find target IP {vendor}/{name}")


def get_ip(vendor, ip_name, fail_if_not_found=False):
    found_ip = False
    ip = None
    if vendor in ip_cache:
        if ip_name in ip_cache[vendor]:
            found_ip = True
            ip = ip_cache[vendor][ip_name]
        else:
            common.dbg(f"IP '{ip_name}' not found in vendor '{vendor}' cache!")
    else:
        common.dbg(f"Vendor '{vendor}' not found in cache!")
    if found_ip == False:
        if fail_if_not_found:
            common.fatal(f"Cannot find IP '{vendor}/{ip_name}'.")
    return ip


def get_anon_ip(ip_name, fail_if_not_found=False):
    found_ip = False
    ip = None
    for vendor in ip_cache:
        if ip_name in ip_cache[vendor]:
            found_ip = True
            ip = ip_cache[vendor][ip_name]
            break
    if found_ip == False:
        if fail_if_not_found:
            common.fatal(f"Cannot find IP '{ip_name}'.")
    return ip


def get_core(core_name, fail_if_not_found=False):
    if core_name in core_cache:
        return core_cache[core_name]
    else:
        if fail_if_not_found:
            common.fatal(f"Could not find core '{core_name}'")
        return None


def load_ip_cache():
    global ip_cache
    try:
        with open(cfg.ip_cache_file_path, 'r') as ymlfile:
            yml = yaml.load(ymlfile, Loader=SafeLoader)
            for vendor in yml['ip']:
                for ip in yml['ip'][vendor]:
                    ip_model = IP(False)
                    if ip_model.parse_from_cache_yml(yml['ip'][vendor][ip]):
                        if ip_model.vendor not in ip_cache:
                            ip_cache[ip_model.vendor] = {}
                        ip_cache[ip_model.vendor][ip_model.name] = ip_model
                        common.dbg(f"Loaded IP '{ip_model.vendor}/{ip_model.name}' from cache")
    except Exception as e:
        common.warning(f"IP cache is corrupt, starting fresh: {e}")
        ip_cache = {}


def load_core_cache():
    global core_cache
    try:
        with open(cfg.fsoc_cache_file_path, 'r') as ymlfile:
            yml = yaml.load(ymlfile, Loader=SafeLoader)
            for core in yml['cores']:
                core_model = FCore()
                if core_model.parse_from_cache_yml(yml['cores'][core]):
                    core_cache[core_model.name] = core_model
                    commong.dbg(f"Loaded Core '{core_model.name}' from cache")
    except:
        common.warning("Core cache is corrupt.  Starting fresh.")
        core_cache = {}


def check_ip_cache_integrity():
    list = {}
    for vendor in ip_cache:
        for ip in ip_cache[vendor]:
            if not ip_cache[vendor][ip].integrity_check():
                list[vendor] = ip
                common.warning(f"Removed IP '{vendor}/{ip}' from cache")
    for vendor in list:
        ip_cache[vendor].pop(list[vendor])


def check_core_cache_integrity():
    for core in core_cache:
        if not core_cache[core].integrity_check():
            core_cache.pop(core)
            common.warning(f"Removed core '{core}' from cache")


def scan_and_load_ip_metadata():
    load_ip_cache()
    load_core_cache()
    find_external_ip_files(cfg.user_global_ips_path, True)
    find_external_ip_files(cfg.dependencies_path)
    for ip_path in cfg.global_ips_path:
        full_ip_path = os.path.join(cfg.project_dir, ip_path)
        find_fsoc_cores(full_ip_path)
        find_external_ip_files(full_ip_path, True)
    for ip_path in cfg.ip_paths:
        full_ip_path = os.path.join(cfg.project_dir, ip_path)
        find_fsoc_cores(full_ip_path)
        find_local_ip_files(full_ip_path)
    find_external_ip_files(cfg.builtin_ip_path)
    check_ip_cache_integrity()
    check_core_cache_integrity()
    resolve_ip_dependencies()


def resolve_ip_dependencies():
    global ip_cache
    for vendor in ip_cache:
        for ip in ip_cache[vendor]:
            ip_cache[vendor][ip].resolve_dependencies()


def find_fsoc_cores(path):
    global core_cache
    add_core = False
    for dirpath, dirnames, filenames in os.walk(path):
        for dir in dirnames:
            current_dir_path       = os.path.join(path            , dir)
            current_core_file_path = os.path.join(current_dir_path, dir + ".core")
            if os.path.exists(current_core_file_path):
                common.dbg("Found FuseSoC core file at '" + current_core_file_path + "'")
                core = FCore(current_dir_path, current_core_file_path)
                core.parse_from_core_yml()
                if core.name not in core_cache:
                    core_cache[core.name] = core
                    common.dbg(f"Added core '{core.name}' to the cache")
                else:
                    if core.core_yml_hash != core_cache[core.name].core_yml_hash:
                        core_cache[core.name] = core
                        common.dbg(f"Updated core '{core.name}'")
                    else:
                        common.dbg(f"Core '{core.name}' cache data is up-to-date")


def find_local_ip_files(path):
    global ip_cache
    for dirpath, dirnames, filenames in os.walk(path):
        for dir in dirnames:
            current_dir_path     = os.path.join(path            , dir)
            current_ip_file_path = os.path.join(current_dir_path, "ip.yml")
            if os.path.exists(current_ip_file_path):
                common.dbg("Found ip.yml at '" + current_dir_path + "'")
                ip = IP(True, False, current_dir_path)
                ip.parse_from_ip_yml()
                if ip.vendor not in ip_cache:
                    ip.calc_code_timestamp()
                    ip_cache[ip.vendor] = {}
                    ip_cache[ip.vendor][ip.name] = ip
                    common.dbg(f"Added local IP '{ip.vendor}/{ip.name}'")
                else:
                    if ip.name not in ip_cache[ip.vendor]:
                        ip.calc_code_timestamp()
                        ip_cache[ip.vendor][ip.name] = ip
                        common.dbg(f"Added local IP '{ip.vendor}/{ip.name}'")
                    else:
                        if ip_cache[ip.vendor][ip.name].is_local:
                            if ip.ip_yml_hash != ip_cache[ip.vendor][ip.name].ip_yml_hash:
                                ip.calc_code_timestamp()
                                ip_cache[ip.vendor][ip.name] = ip
                                common.dbg(f"Updated local IP '{ip.vendor}/{ip.name}'")
                            else:
                                common.dbg(f"Local IP '{ip.vendor}/{ip.name}' cache data is up-to-date")
                        else:
                            ip.calc_code_timestamp()
                            ip_cache[ip.vendor][ip.name] = ip
                            common.dbg(f"Updated local IP '{ip.vendor}/{ip.name}'")


def find_external_ip_files(path, is_global=False):
    global ip_cache
    common.dbg(f"Looking for external IPs under '{path}'")
    for dirpath, dirnames, filenames in os.walk(path):
        for dir in dirnames:
            current_dir_path     = os.path.join(path            , dir)
            current_ip_file_path = os.path.join(current_dir_path, "ip.yml")
            if os.path.exists(current_ip_file_path):
                common.dbg("Found ip.yml at '" + current_dir_path + "'")
                ip = IP(False, is_global, current_dir_path)
                ip.parse_from_ip_yml()
                if ip.vendor not in ip_cache:
                    ip_cache[ip.vendor] = {}
                    ip_cache[ip.vendor][ip.name] = ip
                    common.dbg(f"Added external IP '{ip.vendor}/{ip.name}'")
                else:
                    if ip.name not in ip_cache[ip.vendor]:
                        ip_cache[ip.vendor][ip.name] = ip
                        common.dbg(f"Added external IP '{ip.vendor}/{ip.name}'")
                    else:
                        if ip.ip_yml_hash != ip_cache[ip.vendor][ip.name].ip_yml_hash:
                            ip_cache[ip.vendor][ip.name] = ip
                            common.dbg(f"Updated external IP '{ip.vendor}/{ip.name}'")
                        else:
                            common.dbg(f"External IP '{ip.vendor}/{ip.name}' cache data is up-to-date")


def write_caches_to_disk():
    if cfg.ip_cache_file_path == "":
        # We're running doctor or a similar command, we don't complain
        return
    try:
        with open(cfg.ip_cache_file_path, 'w') as yaml_file_write:
            ip_yml = {}
            ip_yml['ip'] = {}
            for vendor in ip_cache:
                ip_yml['ip'][vendor] = {}
                for ip in ip_cache[vendor]:
                    ip_yml['ip'][vendor][ip] = ip_cache[vendor][ip].convert_to_cache_dict()
            yaml.dump(ip_yml, yaml_file_write)
        
        with open(cfg.fsoc_cache_file_path, 'w') as yaml_file_write:
            core_yml = {}
            core_yml['cores'] = {}
            for core in core_cache:
                core_yml['cores'][core] = core_cache[core].convert_to_cache_dict()
            yaml.dump(core_yml, yaml_file_write)
        
        with open(cfg.job_history_file_path, 'w') as yamlfile:
            yaml.dump({"history" : cfg.job_history}, yamlfile)
        
    except Exception as e:
        print("\033[31m\033[1m[mio-fatal] Could not write caches to disk \033[0m: " + str(e))
        sys.exit(0)
