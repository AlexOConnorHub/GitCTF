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
from bottle import route, run, static_file

### FOR DOCKER SETUP
if (not exists("/root/.gitconfig")):
    system("git_setup.sh")

### FOR BOTTLE SERVER

if (len(argv) > 1):
    public_files = argv[1]
else:
    public_files = "web/"

@route('/favicon.ico')
def return_favicon():
    return static_file('favicon.ico', root=public_files + 'images/') 

@route('/')
@route('/<file:path>')
def hello(file='index.html'):
    return static_file(file, root=public_files) 

run(host='0.0.0.0', port=8080, debug=True) # Change to False