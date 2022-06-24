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

from os import system, popen
from os.path import exists
from bottle import redirect, request, run, static_file, Bottle
from json import dumps

### FOR DOCKER ENVIRONMENT SETUP
if (not exists("/root/.gitconfig")):
    system("git_setup.sh")

### FOR BOTTLE SERVER

app = Bottle()

public_files = "/srv/gitctf"

@app.route('/favicon.ico')
def return_favicon():
    return static_file('/images/favicon.ico', root=public_files)

@app.route('/setup-form', method='POST')
def setup_config():
    # get all the data from the bottle form into "data"
    data = {}
    print(request.forms)
    
    # data = loads(request.forms)
    data["scoreboard_name"] = f"{request.forms['org-name']}.github.io"
    data['repo_owner'] = request.forms['org-name']
    data["template_path"] = "/usr/local/share/gitctf"
    data['start_time'] = f"{request.forms['start-date']}T{request.forms['start-time']}:00{request.forms['timezone-offset']}"
    data['end_time'] = f"{request.forms['end-date']}T{request.forms['end-time']}:00{request.forms['timezone-offset']}"
    data['number_of_bugs'] = request.forms['number-of-bugs']
    owner = popen("gh api /user -q .login").read()[:-1]
    data['instructor'] = owner
    data['sed_cmd'] = request.forms['sed-cmd']
    data["problems"] = {}
    for x in range(int(request.forms["number-of-teams"])):
        data["problems"][f"problem-{x}"] = {
            "base_image": request.forms["base-image"],
            "service_exe_type": request.forms["service-name"],
            "repo_name": f"team-{x}",
            "description": f"team-{x} service repositoy",
            "bin_src_path": "/usr/local/share/vuln64",
            "bin_dst_path": "/service/vuln",
            "flag_dst_path": "/var/ctf/flag",
            "bin_args": request.forms["bin-args"],
            "port": request.forms["port-number"],
            "required_packages": request.forms["packages"]
        }
    encoded_json = dumps(data, indent=4)
    system(f"mv /etc/gitctf/.config.json /etc/gitctf/.config.json.bk")
    system(f"echo '{encoded_json}' > /etc/gitctf/.config.json")
    system(f"gitctf.py setup --admin-conf /etc/gitctf/.config.json --repo_location /usr/local/share/")
    return redirect('/manage.html')

@app.route('/')
@app.route('/<file:path>')
def hello(file='index.html'):
    return static_file(file, root=public_files)

run(app, host='0.0.0.0', port=80, debug=True) # TODO: Change to False
