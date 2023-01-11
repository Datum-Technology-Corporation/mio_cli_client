# Copyright 2021-2023 Datum Technology Corporation
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
########################################################################################################################

from mio import common
from mio import cfg
from mio import cache
from mio import eal

import yaml
from yaml import SafeLoader

import datetime
from datetime import datetime as date
import requests
import getpass
import tarfile
import json
from pathlib import Path
from base64 import b64encode
import os
import sys
import shutil
from tqdm import tqdm


base_url      = "https://mooreio.com"
jwt_endpoint  = base_url + "/api/authenticate"
user_data = {}
org_name = ""
org_full_name = ""


def login(username="", password="", force=False):
    global user_data
    ask_username = True
    ask_password = True
    
    if not force:
        if (('username' in user_data) and ('token' in user_data) and ('expiration' in user_data)):
            if user_data['username'] != "":
                ask_username = False
                if user_data['token'] != "":
                    expiration_date = common.parse_timestamp(user_data['expiration'])
                    if expiration_date > date.now():
                        token    = user_data['token']
                        username = user_data['username']
                        common.dbg(f"User credentials and token are still valid.  Using token '{token}'")
                        return token
                    else:
                        common.dbg(f"User credentials are valid but token has expired.")
    
    if force:
        if (username != "") and (username != None):
            ask_username = False
        if (password != "") and (password != None):
            ask_password = False
    
    if ask_username:
        while username == None or username == "":
            username = common.prompt("Please enter your Moore.io account username:")
    else:
        if not force:
            username = user_data['username']
    
    if ask_password:
        while password == None or password == "":
            password = getpass.getpass(prompt='\033[31m\033[1m[mio]\033[0m Password: ')
    
    payload = {
        "username"  : username,
        "password"  : password,
        "rememberMe": "true"
    }
    try:
        user_data['username'] = username
        jwt_token_response = requests.post(jwt_endpoint, json=payload)
        common.dbg(f"JSON Response from Moore.io Authentication: '{str(jwt_token_response)}'")
        user_data['token'] = jwt_token_response.json()['id_token']
        user_data['expiration'] = date.now() + datetime.timedelta(days=29) # Token is valid for 30, but play it safe
        user_data['expiration'] = user_data['expiration'].strftime("%Y/%m/%d-%H:%M:%S")
        common.banner(f"Successfully logged in as '{username}'")
    except Exception as e:
        common.fatal(f"Failed to log in: '{e}'")
    return user_data['token']


def get_token():
    if user_data != None:
        if (('username' in user_data) and ('token' in user_data) and ('expiration' in user_data)):
            if user_data['username'] != "":
                if user_data['token'] != "":
                    expiration_date = common.parse_timestamp(user_data['expiration'])
                    if expiration_date > date.now():
                        token    = user_data['token']
                        username = user_data['username']
                        common.dbg(f"User credentials and token are still valid.  Using token '{token}'")
                        return token
                    else:
                        common.dbg(f"User credentials are valid but token has expired.")
                        return None


def load_user_data():
    global user_data
    global org_name
    global org_full_name
    
    if not os.path.exists(cfg.mio_user_dir):
        first_time_setup()
    else:
        try:
            with open(cfg.user_file_path, 'r') as yamlfile:
                user_data = yaml.load(yamlfile, Loader=SafeLoader)
                if 'org-name' not in user_data:
                    first_time_setup()
                elif 'org-full-name' not in user_data:
                    first_time_setup()
                org_name      = user_data['org-name'].strip()
                org_full_name = user_data['org-full-name'].strip()
        except Exception as e:
            common.warning(f"User data file is damaged/malformed.  Starting fresh.")
            first_time_setup()


def write_user_data_to_disk():
    try:
        with open(cfg.user_file_path, 'w') as yaml_file_write:
            yaml.dump(user_data, yaml_file_write)
    except Exception as e:
        print("\033[31m\033[1m[mio-fatal] Could not write User data to disk \033[0m: " + str(e))
        sys.exit(0)


def first_time_setup():
    global user_data
    global org_name
    global org_full_name
    common.banner("New workstation setup")
    org_name = ""
    org_full_name = ""
    while org_name == "":
        org_name = common.prompt("Please enter your organization's name (aka vendor name) (ex: 'Acme'):")
    while org_full_name == "":
        org_full_name = common.prompt("Please enter your organization's full legal name (ex: 'Acme Enterprises Inc.'):")
    user_data['org-name'] = org_name
    user_data['org-full-name'] = org_full_name
    common.create_dir(cfg.mio_user_dir)
    common.create_file(cfg.user_mio_file)
