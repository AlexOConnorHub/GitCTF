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
# from os import system, popen
from os.path import exists, join
from shutil import move
from string import Template
from subprocess import check_output

### FOR DOCKER ENVIRONMENT SETUP
if (not exists("~/.gitconfig")):
    check_output(["git_setup.sh"])

### FOR BOTTLE SERVER

app = Bottle()

server_root = "/srv/gitctf"
public_files = "/srv/gitctf/public"
data = {}
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
with open(join(server_root, 'pages/manage.js'), 'r') as f:
    manage_js = f.read()
with open(join(server_root, 'pages/setup.js'), 'r') as f:
    setup_js = f.read()

@app.route('/favicon.ico')
def return_favicon():
    return static_file('/images/favicon.ico', root=public_files)

@app.route('/setup-form', method='POST')
def setup_config():
    global data
    owner = check_output(["gh", "api", "/user", "-q", ".login"]).decode()[:-1]
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
        },
        "teams": {
            "instructor": {
                "repo_name": "-",
                "pub_key_id": "PLEASE_SUBMIT_PULL_REQUEST",
            }
        },
        "individuals": {
            owner: {
                "team": "instructor",
                "pub_key_id": "PLEASE_SUBMIT_PULL_REQUEST",
            }
        }
    }
    for x in range(1, 1 + int(request.forms["number-of-teams"])):
        team_key = {
            "pub_key_id": "PLEASE_SUBMIT_PULL_REQUEST",
        }
        for problem in data["problems"]:
            team_key[problem] = {
                "repo_name": f"team-{x}-{problem}",
            }
            for y in range(int(request.forms["number-of-bugs"])):
                team_key[problem][f"bug-{y}"] = "HASH_TO_BE_DETERMINED"
        data["teams"][f"team-{x}"] = team_key
    individuals = loads(request.forms["individuals"])
    for name in individuals:
        if (individuals[name] != ""):
            data["individuals"][name] = {
                "team": individuals[name],
                "pub_key_id": "PLEASE_SUBMIT_PULL_REQUEST",
            }
    if (exists("/etc/gitctf/.config.json")):
        move("/etc/gitctf/.config.json", "/etc/gitctf/.config.json.bk")
    with open("/etc/gitctf/.config.json", "w") as f:
        f.write(dumps(data, indent=4))
    main("setup", ["--admin-conf", "/etc/gitctf/.config.json", "--repo_location", "/usr/local/share/"])
    return {"status": "success"}

@app.route('/<file:path>')
def root(file):
    return static_file(file, root=public_files)

@app.route('/')
@app.route('/index')
@app.route('/index.html')
def index_page():
    return Template(index).substitute(header = header, navbar = navbar)


@app.route('/setup')
@app.route('/setup.html')
def setup_page():
    config_script = ""
    if (exists("/etc/gitctf/.config.json")):
        config_script = """
        if (!confirm('You already have a configuration. Do you want to overwrite it?')) { 
            window.location.href = '/manage'; 
        }"""
    i = Template(setup)
    c = Template(config_form)
    config = c.substitute(
        action = "",
        organization = "",
        managing = "",
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
    return i.substitute(header = header, navbar = navbar, form = config, modal = user_modal, setup_script = setup_js + "\n" + config_script)

@app.route('/manage')
@app.route('/manage.html')
def manage_page():
    global data
    if not exists("/etc/gitctf/.config.json"):
        redirect("/setup")
    i = Template(manage)
    c = Template(config_form)
    config = c.substitute(
        action = "/manage-form",
        organization = data["repo_owner"],
        managing = "disabled",
        startdate = data["start_time"][:10],
        starttime = data["start_time"][11:16],
        enddate = data["end_time"][:10],
        endtime = data["end_time"][11:16],
        intended = data["intended_pts"],
        unintended = data["unintended_pts"],
        round = data["round_frequency"],
        injection_timeout = data["exploit_timeout"]["injection_phase"],
        exersize_timeout = data["exploit_timeout"]["exercise_phase"],
        image = data["problems"]["problem-1"]["base_image"],
        number_of_teams = len(data["teams"]) - 1,
        port = data["problems"]["problem-1"]["port"],
        bugs = len(data["teams"]["team-1"]) - 2,
        stand_alone_selected = "selected" if data["problems"]["problem-1"]["service_exe_type"] == "stand_alone" else "",
        xinitd_selected = "selected" if data["problems"]["problem-1"]["service_exe_type"] == "xinitd" else "",
        packages = data["problems"]["problem-1"]["required_packages"],
        sed = data["problems"]["problem-1"]["sed_cmd"],
        args = data["problems"]["problem-1"]["bin_args"],
    )
    return i.substitute(header = header, navbar = navbar, form = config, modal = user_modal, manage_script = manage_js)

@app.route("/scoreboard")
@app.route("/scoreboard.html")
def scoreboard_page():
    global data
    if not exists("/etc/gitctf/.config.json"):
        redirect("/setup")
    return Template(scoreboard).substitute(header = header, navbar = navbar, src = f"https://{data['repo_owner']}.github.io")

run(app, host='0.0.0.0', port=80, debug=True) # TODO: Change to False
