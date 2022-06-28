#!/usr/bin/env python3
###############################################################################
# Git-based CTF
###############################################################################
#
# Author: SeongIl Wi <seongil.wi@kaist.ac.kr>
#         Jaeseung Choi <jschoi17@kaist.ac.kr>
#         Sang Kil Cha <sangkilc@kaist.ac.kr>
#
# Copyright (c) 2018 SoftSec Lab. KAIST
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from sys import exit
from json import loads
from base64 import b64decode
from command import run_command

def decode_content(response):
    if response['encoding'] == 'base64':
        return b64decode(response['content'])
    else:
        print(f"[*] Unknown encoding {response['encoding']}")
        exit()

def trim_dot_git(repo_name):
    return repo_name[:-4] if repo_name.endswith('.git') else repo_name

def get_github_path(url):
    if url.startswith('https://github.com/'):
        grp = url[19:].split('/')
    elif url.startswith('git@github.com:'):
        grp = url[15:].split('/')
    else:
        print("[*] Failed to obtain github path")
        exit()
    owner = grp[0]
    repo_name = trim_dot_git(grp[1])
    return (owner + '/' + repo_name) # We just call this `GitHub path`

def result(r, expected_code):
    data = loads(r.split("\n")[-1])
    data["status_code"] = int(r[9:12])
    if expected_code == data['status_code']:
        return data
    else:
        print('[*] response content', r)
        return None

def process_data(data):
    try:
        data = loads(data)
    except:
        # Assume if loads fails, it's because it's already an object
        pass
    final = ""
    for key in data:
        final += f" -f {key}=\"{data[key]}\""
    return final

def request(url, data="{}", expected_code=200, method=None):
    if method is None:
        method = "POST" if data != "{}" else "GET"
    r, _, _ = run_command(f"gh api --method {method} {url} -i {process_data(data)}", None)
    return result(r, expected_code) if expected_code != 204 else True

def poll(query):
    r, _, _ = run_command(f'gh api {query} -i'), None
    response =  result(r, 200)
    poll_interval = -1
    for row in r:
        if (row.split(":")[0] == 'X-Poll-Interval'):
            poll_interval = int(row.split(":")[1])
    return response, poll_interval
