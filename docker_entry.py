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

from sys import argv
from os import system
from os.path import exists
from bottle import route, post, request, run, static_file
from json import dumps, loads

### FOR DOCKER ENVIRONMENT SETUP
if (not exists("/root/.gitconfig")):
    system("git_setup.sh")

### FOR BOTTLE SERVER

public_files = "/srv/gitctf/"

@route('/favicon.ico')
def return_favicon():
    return static_file('favicon.ico', root=public_files + 'images/')

@route('/')
@route('/<file:path>')
def hello(file='index.html'):
    return static_file(file, root=public_files)

@post('/setup')
def setup_config():
    data = str(loads(request.body.read()))
    print(data)
    system(f"mv /etc/gitctf/.config.json /etc/gitctf/.config.json.bk")
    system(f"echo '{dumps(data)}' | jq > /etc/gitctf/.config.json")

@post('/create')
def setup_config():
    if not request.body.read():
       return False
    system(f"gitctf.py setup --admin-conf /etc/gitctf/.config.json")

run(host='0.0.0.0', port=80, debug=True) # Change to False
