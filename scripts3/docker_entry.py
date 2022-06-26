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

from bottle import request, run, static_file, Bottle, redirect
from gitctf import main
from json import dumps, loads
from os import system, popen
from os.path import exists, join
from shutil import move
from string import Template

### FOR DOCKER ENVIRONMENT SETUP
if (not exists("~/.gitconfig")):
    system("git_setup.sh")

### FOR BOTTLE SERVER

app = Bottle()

server_root = "/srv/gitctf"
public_files = "/srv/gitctf/public"
with open(join(server_root, 'templates/header.html'), 'r') as f:
    header = f.read()
with open(join(server_root, 'templates/navbar.html'), 'r') as f:
    navbar = f.read()
with open(join(server_root, 'templates/config_form.html'), 'r') as f:
    config_form = f.read()
with open(join(server_root, 'templates/user_modal.html'), 'r') as f:
    user_modal = f.read()
with open(join(server_root, 'pages/index.html'), 'r') as f:
    index = f.read()
with open(join(server_root, 'pages/setup.html'), 'r') as f:
    setup = f.read()
with open(join(server_root, 'pages/manage.html'), 'r') as f:
    manage = f.read()
with open(join(server_root, 'pages/scoreboard.html'), 'r') as f:
    scoreboard = f.read()

@app.route('/favicon.ico')
def return_favicon():
    return static_file('/images/favicon.ico', root=public_files)

@app.route('/setup-form', method='POST')
def setup_config():
    # get all the data from the bottle form into "data"
    print(request.forms.keys())
    owner = popen("gh api /user -q .login").read()[:-1]
    data = {
        "repo_owner": request.forms['org-name'],
        "intended_pts": request.forms['intended-points'],
        "unintended_pts": request.forms['unintended-points'],
        "round_frequency": request.forms['round-frequency'],
        "start_time": f"{request.forms['start-date']}T{request.forms['start-time']}:00{request.forms['timezone-offset']}",
        "end_time": f"{request.forms['end-date']}T{request.forms['end-time']}:00{request.forms['timezone-offset']}",
        "exploit_timeout": {
            "injection_phase":request.forms['exploit-timeout-exersize'],
            "exercise_phase":request.forms['exploit-timeout-injection'],
        },
        "template_path": "/usr/local/share/gitctf",
        "instructor": owner,
        "problems": {
            "problem-1": {
                "base_image": request.forms["base-image"],
                "sed_cmd": request.forms['sed-cmd'],
                "service_exe_type": request.forms["service-name"],
                "description": f"service repositoy",
                "bin_src_path": "/usr/local/share/vuln64",
                "bin_dst_path": "/service/vuln",
                "flag_dst_path": "/var/ctf/flag",
                "bin_args": request.forms["bin-args"],
                "port": request.forms["port-number"],
                "required_packages": request.forms["packages"],
            }
        }
    }
    problems = ["problem-1"]
    data["teams"] = {
        "instructor": {
            "repo_name": "-",
            "pub_key_id": "PLEASE_SET_YOUR_PUBLIC_KEY_ID",
        }
    }
    for x in range(1, 1 + int(request.forms["number-of-teams"])):
        team_key = {
            "pub_key_id": "PLEASE_SUBMIT_PULL_REQUEST",
        }
        for problem in problems:
            team_key[problem] = {
                "repo_name": f"team-{x}-{problem}",
            }
            for y in range(int(request.forms["number-of-bugs"])):
                team_key[problem][f"bug-{y}"] = "HASH_TO_BE_DETERMINED"
        data["teams"][f"team-{x}"] = team_key
    data["individuals"] = {}
    individuals = loads(request.forms["individuals"])
    for name in individuals:
        if (individuals[name] != ""):
            data["individuals"][name] = {
                "team": individuals[name],
                "pub_key_id": "PLEASE_SUBMIT_PULL_REQUEST",
            }
    encoded_json = dumps(data, indent=4)
    if (exists("/etc/gitctf/.config.json")):
        move("/etc/gitctf/.config.json", "/etc/gitctf/.config.json.bk")
    with open("/etc/gitctf/.config.json", "w") as f:
        f.write(encoded_json)
    main("setup", ["--admin-conf", "/etc/gitctf/.config.json", "--repo_location", "/usr/local/share/"])
    return {"status": "success"}

@app.route('/<file:path>')
def root(file):
    return static_file(file, root=public_files)

@app.route('/')
@app.route('/index')
@app.route('/index.html')
def index_page():
    i = Template(index)
    return i.substitute(header = header, navbar = navbar)


@app.route('/setup')
@app.route('/setup.html')
def setup_page():
    with open(join(server_root, 'pages/setup.js'), 'r') as f:
        setup_js = f.read()
    i = Template(setup)
    c = Template(config_form)
    config = c.substitute(
        action = "",
        organization = "",
        startdate = "",
        starttime = "",
        enddate = "",
        endtime = "",
        intended = "",
        unintended = "",
        round = "",
        exersize_timeout = "",
        injection_timeout = "",
        image = "",
        number_of_teams = "",
        port = "",
        bugs = "",
        stand_alone_selected = "",
        xinitd_selected = "",
        packages = "",
        sed = "",
        args = "",
    )
    return i.substitute(header = header, navbar = navbar, form = config, modal = user_modal, setup_script = setup_js)

@app.route('/manage')
@app.route('/manage.html')
def manage_page():
    with open(join(server_root, 'pages/manage.js'), 'r') as f:
        manage_js = f.read()
    i = Template(manage)
    c = Template(config_form)
    if not exists("/etc/gitctf/.config.json"):
        redirect("/setup")
    with open("/etc/gitctf/.config.json", "r") as f:
        config_contents = loads(f.read())
    config = c.substitute(
        action = "/manage-form",
        organization = config_contents["repo_owner"],
        startdate = config_contents["start_time"][:10],
        starttime = config_contents["start_time"][11:16],
        enddate = config_contents["end_time"][:10],
        endtime = config_contents["end_time"][11:16],
        intended = config_contents["intended_pts"],
        unintended = config_contents["unintended_pts"],
        round = config_contents["round_frequency"],
        injection_timeout = config_contents["exploit_timeout"]["injection_phase"],
        exersize_timeout = config_contents["exploit_timeout"]["exercise_phase"],
        image = config_contents["problems"]["problem-1"]["base_image"],
        number_of_teams = len(config_contents["teams"]) - 1,
        port = config_contents["problems"]["problem-1"]["port"],
        bugs = len(config_contents["teams"]["team-1"]) - 2,
        stand_alone_selected = "selected" if config_contents["problems"]["problem-1"]["service_exe_type"] == "stand_alone" else "",
        xinitd_selected = "selected" if config_contents["problems"]["problem-1"]["service_exe_type"] == "xinitd" else "",
        packages = config_contents["problems"]["problem-1"]["required_packages"],
        sed = config_contents["problems"]["problem-1"]["sed_cmd"],
        args = config_contents["problems"]["problem-1"]["bin_args"],
    )
    return i.substitute(header = header, navbar = navbar, form = config, modal = user_modal, manage_script = manage_js)

@app.route("/scoreboard")
@app.route("/scoreboard.html")
def scoreboard_page():
    if not exists("/etc/gitctf/.config.json"):
        redirect("/setup")
    with open("/etc/gitctf/.config.json", "r") as f:
        config = loads(f.read())
    s = Template(scoreboard)
    return s.substitute(header = header, navbar = navbar, src = f"https://{config['repo_owner']}.github.io")

run(app, host='0.0.0.0', port=80, debug=True) # TODO: Change to False
