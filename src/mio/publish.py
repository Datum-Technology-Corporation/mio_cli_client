# Copyright 2022 Datum Technology Corporation
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
########################################################################################################################

from mio import common
from mio import cfg
from mio import cache
from mio import install
from mio import eal
from mio import user

import yaml
from yaml import SafeLoader

import glob
import requests
import getpass
import tarfile
import json
from pathlib import Path
from base64 import b64encode
import os
import shutil
from tqdm import tqdm
import fileinput


base_url          = "https://mooreio.com"#"http://localhost:8080"
jwt_endpoint      = base_url + "/api/authenticate"
ips_endpoint      = base_url + "/api/ips"
versions_endpoint = base_url + "/api/versions"
licenses_endpoint = base_url + "/api/licenses"
headers = {}

ignore_files = [".gitignore", "ip.lock.yml"]


def do_publish_ip(ip_model, token, org):
    name = ip_model.name
    org  = ip_model.vendor
    location = ip_model.path
    common.dbg(f"Publishing IP '{name}' under '{location}'")
    query = {'name': name}
    auth_headers = {
        'Authorization'    : f"Bearer {token}",
        'Accept-Encoding'  : 'gzip, deflate, br',
        'Content-Type'     : 'application/json; charset="UTF-8"'
    }
    
    response = requests.get(ips_endpoint + "?page=0&size=1000000", params=query, headers=auth_headers)
    if response.status_code != 200:
        common.fatal(f"Failed to reach Moore.io IP Marketplace: '{response.status_code}' - {response.reason}")
    json_data = response.json()
    payload = None
    found_ip = False
    
    for ip in json_data:
        if ip['name'] == name:
            ip_id = ip['id']
            common.dbg("Found IP! name=" + name + " id=" + str(ip_id))
            license_type = ip['licenseType']
            if license_type == "FREE_OPEN_SOURCE":
                versions = requests.get(versions_endpoint + "?page=0&size=1000000", headers=auth_headers).json()
                for version in versions:
                    if version['ip']['id'] == ip_id:
                        common.dbg("Found IP version on server: " + name + " v" + version['semver'])
                        found_ip = True
                        update_shrinkwrap_file(ip_model, False)
                        tarball_path = package_ip(ip_model, False)
                        try:
                            with open(tarball_path,'rb') as f:
                                payload = b64encode(f.read())
                        except Exception as e:
                            common.fatal(f"Could not open '{tarball_path}': {e}")
                        url = versions_endpoint + f"/{version['id']}"
                        data = {
                            "id"                       : version['id']     ,
                            "publicPayload"            : str(payload)[2:-1],
                            "publicPayloadContentType" : "application/x-compressed"
                        }
                        common.dbg(f"Creating PATCH request to '{url}'")
                        try:
                            response = requests.patch(url=url, headers=auth_headers, json=data, verify=False)
                        except Exception as e:
                            common.fatal(f"Failed to publish IP '{name}': {e}")
                        if response.status_code != 200:
                            common.fatal(f"Failed to publish IP '{name}': '{response.status_code}' - {response.reason}")
                        break
            if license_type == "COMMERCIAL":
                if org == "" or org == None:
                    common.fatal(f"Organization name must be specified for commercial IPs")
                licenses = requests.get(licenses_endpoint + "?page=0&size=1000000", headers=auth_headers).json()
                for license in licenses:
                    if license['targetIp']['id'] == ip_id:
                        common.dbg("Found IP license on server: " + name)
                        if license['owner']['name'].strip().lower() == org.strip().lower():
                            common.dbg(f"Found IP '{name}' license on server for '{org}'")
                            found_ip = True
                            ip_key = license['key']
                            org_id = license['owner']['id']
                            update_shrinkwrap_file(ip_model, True)
                            tarball_path = package_ip(ip_model, True, "", True, org_id, ip_id, ip_key)
                            try:
                                with open(tarball_path,'rb') as f:
                                    payload = b64encode(f.read())
                            except Exception as e:
                                common.fatal(f"Could not open '{tarball_path}': {e}")
                            url = licenses_endpoint + f"/{license['id']}"
                            data = {
                                "id"                 : license['id']     ,
                                "payload"            : str(payload)[2:-1],
                                "payloadContentType" : "application/x-compressed"
                            }
                            common.dbg(f"Creating PATCH request to '{url}'")
                            try:
                                response = requests.patch(url=url, headers=auth_headers, json=data, verify=False)
                            except Exception as e:
                                common.fatal(f"Failed to publish IP '{name}': {e}")
                            if response.status_code != 200:
                                common.fatal(f"Failed to publish IP '{name}': '{response.status_code}' - {response.reason}")
                            break
    if found_ip:
        common.remove_file(tarball_path)
        common.info(f"Published IP '{name}' successfully")
    else:
        common.fatal(f"Could not find IP '{name}' on Moore.io IP Marketplace")


def cli_package_ip(ip_str, destination, no_tarball):
    vendor, name = common.parse_dep(ip_str)
    if vendor == "":
        ip = cache.get_anon_ip(name)
    else:
        ip = cache.get_ip(vendor, name)
    create_tarball = not no_tarball
    common.banner(f"Packaging IP '{ip.vendor}/{ip.name}' ...")
    update_shrinkwrap_file(ip, ip.is_licensed)
    path = package_ip(ip, ip.is_licensed, str(destination.resolve()), create_tarball)
    if create_tarball:
        common.info(f"Compressed archive created at {path}")
    else:
        if encrypt:
            common.info(f"Encrypted IP code output to {path}")
        else:
            common.info(f"IP code output to {path}")


def package_ip(ip, encrypt=False, destination="", create_tarball=True, org_id="", ip_id="", ip_key=""):
    ip_name = ip.name
    ip_str = f"{ip.vendor}/{ip.name}"
    tarball_path = cfg.temp_path + "/" + ip_name + ".tgz"
    location = ip.path
    scripts_src_dir      = ip.scripts_path
    docs_src_dir         = ip.docs_path
    examples_src_dir     = ip.examples_path
    src_dir              = ip.src_path
    ip_src_directories   = ip.hdl_src_directories
    common.dbg(f"Creating tarball '{location}' -> '{tarball_path}'")
    temp_location        = cfg.temp_path + "/" + ip_name
    ip_yml_file_path     = temp_location + "/ip.yml"
    shrinkwrap_file_path = temp_location + "/ip.shrinkwrap.yml"
    lock_file_path       = temp_location + "/ip.lock.yml"
    
    if destination != "":
        tarball_path = destination + "/" + ip_name + ".tgz"
    
    if encrypt:
        sims_supported = 0
        if ip.simulators_supported[common.simulators_enum.VIVADO] != "":
            sims_supported = sims_supported + 1
        if ip.simulators_supported[common.simulators_enum.METRICS] != "":
            sims_supported = sims_supported + 1
        if ip.simulators_supported[common.simulators_enum.VCS] != "":
            sims_supported = sims_supported + 1
        if ip.simulators_supported[common.simulators_enum.XCELIUM] != "":
            sims_supported = sims_supported + 1
        if ip.simulators_supported[common.simulators_enum.QUESTA] != "":
            sims_supported = sims_supported + 1
        if ip.simulators_supported[common.simulators_enum.RIVIERA] != "":
            sims_supported = sims_supported + 1
        if sims_supported == 0:
            common.fatal(f"IP '{ip_str}' does not have any simulators supported!")
        common.dbg(f"Encrypting IP '{ip_str}'")
        vendor = ip.vendor
        common.copy_directory(location, temp_location)
        common.copy_file(shrinkwrap_file_path, ip_yml_file_path)
        common.remove_file(shrinkwrap_file_path)
        common.remove_file(lock_file_path)
        src_dir = temp_location + "/" + ip.src_path
        insert_key_checks(src_dir, ip, org_id, ip_id, ip_key)
        
        if ip.simulators_supported[common.simulators_enum.VIVADO] != "":
            viv_src_dir = src_dir + ".viv"
            common.copy_directory(src_dir, viv_src_dir)
            eal.encrypt_tree(ip_name, viv_src_dir, "viv")
        
        if ip.simulators_supported[common.simulators_enum.VCS] != "":
            vcs_src_dir = src_dir + ".vcs"
            common.copy_directory(src_dir, vcs_src_dir)
            eal.encrypt_tree(ip_name, vcs_src_dir, "vcs")
        
        if ip.simulators_supported[common.simulators_enum.METRICS] != "":
            mtr_src_dir = src_dir + ".mdc"
            common.copy_directory(src_dir, mtr_src_dir)
            eal.encrypt_tree(ip_name, mtr_src_dir, "mdc")
        
        if ip.simulators_supported[common.simulators_enum.QUESTA] != "":
            qst_src_dir = src_dir + ".qst"
            common.copy_directory(src_dir, qst_src_dir)
            eal.encrypt_tree(ip_name, qst_src_dir, "qst")
        
        if ip.simulators_supported[common.simulators_enum.XCELIUM] != "":
            xcl_src_dir = src_dir + ".xcl"
            common.copy_directory(src_dir, xcl_src_dir)
            eal.encrypt_tree(ip_name, xcl_src_dir, "xcl")
        
        if ip.simulators_supported[common.simulators_enum.RIVIERA] != "":
            riv_src_dir = src_dir + ".riv"
            common.copy_directory(src_dir, riv_src_dir)
            eal.encrypt_tree(ip_name, riv_src_dir, "riv")
        
        if create_tarball:
            try:
                with tarfile.open(tarball_path, "w:gz") as tar:
                    if os.path.exists(temp_location + "/" + ip.scripts_path):
                        tar.add(temp_location + "/" + scripts_src_dir , arcname=scripts_src_dir)
                    if os.path.exists(temp_location + "/" + docs_src_dir):
                        tar.add(temp_location + "/" + docs_src_dir, arcname=docs_src_dir)
                    if os.path.exists(temp_location + "/" + examples_src_dir):
                        tar.add(temp_location + "/" + examples_src_dir, arcname=examples_src_dir)
                    
                    if ip.simulators_supported[common.simulators_enum.VIVADO] != "":
                        tar.add(viv_src_dir, arcname="src.viv")
                    
                    if ip.simulators_supported[common.simulators_enum.VCS] != "":
                        tar.add(vcs_src_dir, arcname="src.vcs")
                    
                    if ip.simulators_supported[common.simulators_enum.METRICS] != "":
                        tar.add(mtr_src_dir, arcname="src.mdc")
                    
                    if ip.simulators_supported[common.simulators_enum.QUESTA] != "":
                        tar.add(qst_src_dir, arcname="src.qst")
                    
                    if ip.simulators_supported[common.simulators_enum.XCELIUM] != "":
                        tar.add(xcl_src_dir, arcname="src.xcl")
                    
                    if ip.simulators_supported[common.simulators_enum.RIVIERA] != "":
                        tar.add(riv_src_dir, arcname="src.riv")
                    
                    for path in os.listdir(temp_location):
                        file_path = os.path.join(temp_location, path)
                        if os.path.isfile(file_path):
                            if path not in ignore_files:
                                tar.add(file_path, arcname=path)
                common.remove_dir(temp_location)
            except Exception as e:
                common.fatal(f"Failed to create tarball for IP '{ip_str}': {e}")
    
    else:
        if create_tarball:
            try:
                common.copy_directory(location, temp_location)
                common.copy_file(shrinkwrap_file_path, ip_yml_file_path)
                common.remove_file(shrinkwrap_file_path)
                common.remove_file(lock_file_path)
                with tarfile.open(tarball_path, "w:gz") as tar:
                    if os.path.exists(temp_location + "/" + scripts_src_dir):
                        tar.add(temp_location + "/" + scripts_src_dir , arcname=scripts_src_dir)
                    if os.path.exists(temp_location + "/" + docs_src_dir):
                        tar.add(temp_location + "/" + docs_src_dir, arcname=docs_src_dir)
                    if os.path.exists(temp_location + "/" + examples_src_dir):
                        tar.add(temp_location + "/" + examples_src_dir, arcname=examples_src_dir)
                    tar.add(temp_location + "/" + src_dir, arcname=src_dir)
                    for path in os.listdir(temp_location):
                        file_path = os.path.join(temp_location, path)
                        if os.path.isfile(file_path):
                            if path not in ignore_files:
                                tar.add(file_path, arcname=path)
                    common.remove_dir(temp_location)
            except Exception as e:
                common.fatal(f"Failed to create tarball for IP '{ip_str}': {e}")
        else:
            common.copy_directory(location, destination + "/" + ip.name)
    
    if create_tarball:
        return tarball_path
    else:
        return destination + "/" + ip.name


def publish_ip(ip_str, username="", password="", org=""):
    vendor, name = common.parse_dep(ip_str)
    if vendor == "":
        ip = cache.get_anon_ip(name, True)
    else:
        ip = cache.get_ip(vendor, name, True)
    target_name = f"{ip.vendor}/{ip.name}"
    if not ip.is_local:
        common.fatal(f"IP '{target_name}' is not local.")
    if (username == "") or (username == None):
        token = user.login()
    else:
        token = user.login(username, password, True)
    do_publish_ip(ip, token, org)


def insert_key_checks(location, ip, org_id, ip_id, ip_key):
    ip_name = ip.name
    ip_vendor = ip.vendor
    text_to_search = "`MIO_LICENSE_CHECK"
    replacement_text = f"uvml_mio_lic_pkg::uvml_mio_lic_server_c::check_key(\"@{ip_vendor}/{ip_name}\", \"{ip_id}\", \"{org_id}\", \"{ip_key}\");"
    for file in glob.iglob(location + '**/**', recursive=True):
        file_path = os.path.join(location, file)
        if (file_path[-2:] == ".v") or (file_path[-3:] == ".vh") or (file_path[-3:] == ".sv") or (file_path[-4:] == ".svh"):  # TODO Add support for VHDL files
            try:
                with open(file_path, "r") as file:
                    content = file.read().replace(text_to_search, replacement_text)
                file = open(file_path, "w")
                file.write(content)
                file.close()
            except Exception as e:
                common.fatal(f"Error while processing file '{file_path}' for key check insertion: {e}")


def update_shrinkwrap_file(ip, encrypted=False):
    install.update_lock_file(ip)
    lock_file_path       = ip.path + "/ip.lock.yml"
    shrinkwrap_file_path = ip.path + "/ip.shrinkwrap.yml"
    try:
        common.copy_file(lock_file_path, shrinkwrap_file_path)
        with open(shrinkwrap_file_path, 'r') as yaml_file_read:
            ymlr = yaml.load(yaml_file_read, Loader=SafeLoader)
            ymlr['hdl-src']['encrypted'] = encrypted
        with open(shrinkwrap_file_path, 'w') as yaml_file_write:
            yaml.dump(ymlr, yaml_file_write)
    except Exception as e:
        common.fatal(f"Failed to update '{shrinkwrap_file_path}': {e}")
