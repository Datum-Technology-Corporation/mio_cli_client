# Copyright 2022 Datum Technology Corporation
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
########################################################################################################################

from mio import common
from mio import cfg
from mio import cache
from mio import user

import yaml
from yaml import SafeLoader

import requests
import getpass
import tarfile
import json
from pathlib import Path
from base64 import b64decode
import os
import shutil
from tqdm import tqdm


base_url          = "https://mooreio.com"#"http://localhost:8080"
jwt_endpoint      = base_url + "/api/authenticate"
ips_endpoint      = base_url + "/api/ips"
versions_endpoint = base_url + "/api/versions"
version_endpoint  = base_url + "/api/version/"
licenses_endpoint = base_url + "/api/licenses"
headers = {}


def install_ip(vendor, name, global_install, username="", password=""):
    if global_install:
        location = cfg.user_global_ips_path
    else:
        location = cfg.dependencies_path
    common.dbg(f"Installing IP '{vendor}/{name}' under '{location}'")
    query = {'name': name}
    
    token = user.get_token()
    if token == None:
        token = user.login(username, password)
    
    headers = {'Authorization':'Bearer ' + token}
    response = requests.get(ips_endpoint + "?page=0&size=1000000", params=query, headers=headers)
    json_data = response.json()
    common.dbg(f"Response from Moore.io IP Marketplace: '{response}'")
    payload = None
    found_payload = False
    version_str = ""
    for ip in json_data:
        if ip['name'] == name:
            ip_id = ip['id']
            common.dbg("Found IP! name=" + name + " id=" + str(ip_id))
            license_type = ip['licenseType']
            if license_type == "FREE_OPEN_SOURCE":
                versions = requests.get(versions_endpoint + "?page=0&size=1000000", headers=headers).json()
                for version in versions:
                    if version['ip']['id'] == ip_id:
                        version_str = version['semver']
                        common.dbg("Found IP version on server: " + name + " v" + version_str)
                        payload = version['publicPayload']
                        found_payload = True
                        filename = Path(location + "/" + vendor + "__" + name + '.tgz')
                        filename.write_bytes(b64decode(payload))
                        tar = tarfile.open(filename, "r:gz")
                        ip_destination_path = f"{location}/{vendor}__{name}"
                        common.remove_dir(ip_destination_path)
                        common.create_dir(ip_destination_path)
                        tar.extractall(ip_destination_path)
                        tar.close()
                        common.remove_file(filename)
                        break
            if license_type == "COMMERCIAL":
                licenses = requests.get(licenses_endpoint + "?page=0&size=1000000", headers=headers).json()
                for license in licenses:
                    if license['targetIp']['id'] == ip_id:
                        version_str = license['version']['semver']
                        common.dbg("Found IP license on server: " + name)
                        payload = license['payload']
                        found_payload = True
                        filename = Path(location + "/" + vendor + "__" + name + '.tgz')
                        filename.write_bytes(b64decode(payload))
                        tar = tarfile.open(filename, "r:gz")
                        ip_destination_path = f"{location}/{vendor}__{name}"
                        common.remove_dir(ip_destination_path)
                        common.create_dir(ip_destination_path)
                        tar.extractall(ip_destination_path)
                        tar.close()
                        common.remove_file(filename)
    if not found_payload:
        common.fatal(f"Could not find IP '{vendor}/{name}' on Moore.io IP Marketplace")
    
    return version_str


def install_ip_dep_list(ip, ip_list, global_install, username="", password=""):
    versions = {}
    if len(ip_list) > 0:
        #with alive_bar(len(ip_list), bar = 'smooth') as bar:
        with tqdm(ip_list) as pbar:
            for dep_ip in ip_list:
                vendor, name = common.parse_dep(dep_ip)
                ip_str = f"{vendor}/{name}"
                pbar.set_description(ip_str)
                versions[ip_str] = install_ip(vendor, name, global_install, username="", password="")
                pbar.update(1)
        cache.scan_and_load_ip_metadata()
        update_lock_file(ip, versions)


def install_ip_and_deps(vendor, name, global_install, username="", password=""):
    ip = {}
    if vendor == "":
        ip = cache.get_anon_ip(name)
    else:
        ip = cache.get_ip(vendor, name)
    if ip == None:
        common.banner(f"Installing IP '{vendor}/{name}'")
        install_ip(vendor, name, global_install, username="", password="")
        cache.scan_and_load_ip_metadata()
        ip = cache.get_ip(vendor, name)
    
    ip_list = []
    for dep in ip.dependencies:
        if dep.target_ip_model == None:
            ip_str = f"{dep.vendor}/{dep.target_ip}"
            ip_list.append(ip_str)
        else:
            if dep.target_ip_model.is_local == False:
                ip_str = f"{dep.vendor}/{dep.target_ip}"
                ip_list.append(ip_str)
    common.info(f"Installing {len(ip_list)} dependencies")
    install_ip_dep_list(ip, ip_list, global_install, username="", password="")


def update_lock_file(ip, versions={}):
    ip_file_path   = ip.path + "/ip.yml"
    lock_file_path = ip.path + "/ip.lock.yml"
    try:
        common.copy_file(ip_file_path, lock_file_path)
        with open(lock_file_path, 'r') as yaml_file_read:
            ymlr = yaml.load(yaml_file_read, Loader=SafeLoader)
            if 'dependencies' in ymlr:
                if type(ymlr['dependencies']) is dict:
                    for dep in ymlr['dependencies']:
                        if dep in versions:
                            ymlr['dependencies'][dep] = versions[dep]
                        else:
                            vendor, name = common.parse_dep(dep.strip().lower().replace("@", ""))
                            if vendor == "":
                                dep_ip = cache.get_anon_ip(name, True)
                            else:
                                dep_ip = cache.get_ip(vendor, name, True)
                            if dep_ip.is_local:
                                ymlr['dependencies'][dep] = '@local'
                            else:
                                ymlr['dependencies'][dep] = dep_ip.version
        with open(lock_file_path, 'w') as yaml_file_write:
            yaml.dump(ymlr, yaml_file_write)
    except Exception as e:
        common.fatal(f"Failed to update '{lock_file_path}': {e}")

