#!/usr/bin/env python
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

import sys
import json
import requests
import getpass
import base64
from command import run_command

def decode_content(response):
    if response['encoding'] == 'base64':
        return base64.b64decode(response['content'])
    else:
        print(('[*] Unknown encoding %s' % response['encoding']))
        sys.exit()

def trim_dot_git(repo_name):
    if repo_name.endswith('.git'):
        return repo_name[:-4]
    else:
        return repo_name

def get_github_path(url):
    if url.startswith('https://github.com/'):
        grp = url[19:].split('/')
    elif url.startswith('git@github.com:'):
        grp = url[15:].split('/')
    else:
        print("[*] Failed to obtain github path")
        sys.exit()
    owner = grp[0]
    repo_name = trim_dot_git(grp[1])
    return (owner + '/' + repo_name) # We just call this `GitHub path`

def result(r, expected_code):
    status_code = int(r[9:12])
    if status_code == expected_code:
        final = json.loads(r.split("\n")[-1])
        final['status_code'] = status_code
        return final
    else:
        print('[*] response content', r)
        return None

def process_data(data):
    data = json.loads(data)
    final = ""
    for key in data:
        final += f" -f {key}=\"{data[key]}\""
    return final
class Github():
    def __init__(self, username, token=None):
        pass

    @property
    def url(self):
        return 'https://api.github.com'

    def post(self, query, data, expected_code=201):
        r, _, _ = run_command(f"gh api {query} -i {process_data(data)}", None)
        r =  result(r, expected_code)
        return r

    def get(self, query, expected_code=200):
        r, _, _ = run_command(f'gh api {query} -i', None)
        return result(r, expected_code)

    def put(self, query, data, expected_code=200):
        r, _, _ = run_command(f"gh api {query} -i {process_data(data)}", None)
        r = result(r)
        return r['status_code'] == expected_code

    def patch(self, query, data, expected_code=200):
        r, _, _ = run_command(f"gh api {query} -i {process_data(data)}", None)
        r = result(r)
        return r['status_code'] == expected_code

    def poll(self, query):
        r, _, _ = run_command(f'gh api {query} -i'), None
        response =  result(r, 200)
        poll_interval = -1
        for row in r:
            if (row.split(":")[0] == 'X-Poll-Interval'):
                poll_interval = int(row.split(":")[1])
        return response, poll_interval
