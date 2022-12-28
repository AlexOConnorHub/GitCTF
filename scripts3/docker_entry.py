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

from bottle import request, run, static_file, Bottle, redirect, response
from ctf_utils import rmdir
from evaluate import sync_scoreboard
from github import request as gh
from json import dumps, loads
from os.path import exists, join, getmtime
from setup_env import create_local_repo, setup_env, commit_and_push, create_team_repo
from shutil import move
from string import Template
from manage_ctf import start_ctf, update_ctf

config_file_path = "/etc/gitctf/config.json"
data = {}
data_last_modified = 0


def load_config():
    global data, data_last_modified
    if exists(config_file_path):
        if data_last_modified != getmtime(config_file_path):
            with open(config_file_path, "r") as f:
                data = loads(f.read())
            data_last_modified = getmtime(config_file_path)
        scoreboard_path = f"/usr/local/share/{data.get('repo_owner')}/{data.get('repo_owner')}.github.io"
        if exists(scoreboard_path):
            sync_scoreboard(scoreboard_path)
        return True
    else:
        return False

if exists(config_file_path):
    load_config()

def save_config(push_changes):
    global data, data_last_modified
    scoreboard_path = f"/usr/local/share/{data['repo_owner']}/{data['repo_owner']}.github.io"
    with open(config_file_path, "w") as f:
        f.write(dumps(data, indent=4))
    data_last_modified = getmtime(config_file_path)
    if push_changes and exists(scoreboard_path):
        commit_and_push(scoreboard_path, "Updated config.json")

def get_id(username):
    user_json = gh(f"/users/{username}")
    if user_json is None or "id" not in user_json:
        print(f"[*] Failed to get user id {username}")
        return None
    return user_json["id"]    

def create_team(team_name):
    global data
    print(f"[*] Creating team {team_name}")
    team = gh(f"/orgs/{data['repo_owner']}/teams", {"name": team_name, "description": f"{team_name} Team", "privacy": "closed"}, 201)
    if team is None or "slug" not in team:
        print(f"[*] Failed to create team {team_name}")
        return None
    return team["slug"]

def add_to_team(username, team_slug):
    global data
    print(f"[*] Adding user id {username} to team {team_slug}")
    if gh(f"/orgs/{data['repo_owner']}/teams/{team_slug}/memberships/{username}", method="PUT") is None:
        print(f"[*] Failed to add user id {username} to team {team_slug}")
        return False
    
def remove_from_team(username, team_slug):
    global data
    print(f"[*] Removing user id {username} from team {team_slug}")
    if gh(f"/orgs/{data['repo_owner']}/teams/{team_slug}/memberships/{username}", method="DELETE", expected_code=204) is None:
        print(f"[*] Failed to remove user id {username} from team {team_slug}")
        return False

app = Bottle()

server_root = "/srv/gitctf"
public_files = "/srv/gitctf/public"
try:
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
except:
    pass

@app.route('/favicon.ico')
def return_favicon():
    return static_file('/images/favicon.ico', root=public_files)

@app.route('/setup-form', method='POST')
def setup_config():
    global data
    if "repo_owner" in data:
        rmdir(join("/usr/local/share", data["repo_owner"]))
    owner_json = gh("/user")
    if owner_json is None or "login" not in owner_json:
        return {"error": "Failed to get owner's username"}
    owner = owner_json["login"]
    data = {
        "repo_owner": request.forms['org-name'],
        "intended_pts": request.forms['intended-points'],
        "unintended_pts": request.forms['unintended-points'],
        "round_frequency": request.forms['round-frequency'],
        "start_time": f"{request.forms['start-date']}T{request.forms['start-time']}:00{request.forms['timezone-offset']}",
        "end_time": f"{request.forms['end-date']}T{request.forms['end-time']}:00{request.forms['timezone-offset']}",
        "exploit_timeout": {
            "injection_phase":request.forms['exploit-timeout-injection'],
            "exercise_phase":request.forms['exploit-timeout-exersize'],
        },
        "template_path": "/usr/local/share/gitctf",
        "instructor": owner,
        "problems": {
            "problem-1": {
                "base_image": request.forms["base-image"],
                "sed_cmd": request.forms['sed-cmd'],
                "service_exe_type": request.forms["service-name"],
                "number_of_bugs": request.forms["number-of-bugs"],
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
                "pub_key_id": "PLEASE_SUBMIT_PULL_REQUEST",
            }
        },
        "individuals": {
            owner: {
                "team": "instructor",
                "id": get_id(owner),
                "pub_key_id": "PLEASE_SUBMIT_PULL_REQUEST",
            }
        }
    }
    for x in range(1, 1 + int(request.forms["number-of-teams"])):
        team_key = f"team-{x}"
        team = {
            "pub_key_id": "PLEASE_SUBMIT_PULL_REQUEST",
            "slug": create_team(team_key),
        }
        for problem in data["problems"]:
            team[problem] = {
                "repo_name": f"{team_key}-{problem}",
            }
            for y in range(1, 1 + int(data["problems"][problem]["number_of_bugs"])):
                team[problem][f"bug-{y}"] = "HASH_TO_BE_DETERMINED"
        data["teams"][team_key] = team
    individuals = loads(request.forms["individuals"])
    for name in individuals:
        if (individuals[name] != ""):
            data["individuals"][name] = {
                "team": individuals[name],
                "id": get_id(name),
                "pub_key_id": "PLEASE_SUBMIT_PULL_REQUEST",
            }
        add_to_team(name, data["teams"][individuals[name]]["slug"])
    if (exists(config_file_path)):
        move(config_file_path, f"{config_file_path}.bk")
    save_config(False)
    setup_env(config_file_path, "/usr/local/share")
    start_ctf(data)
    return {"status": "success"}

@app.route("/manage-form", method="POST")
def manage_form():
    global data
    load_config()
    form_start = f"{request.forms['start-date']}T{request.forms['start-time']}:00{request.forms['timezone-offset']}",
    form_end = f"{request.forms['end-date']}T{request.forms['end-time']}:00{request.forms['timezone-offset']}",
    form_intended_pts = request.forms['intended-points']
    form_unintended_pts = request.forms['unintended-points']
    form_round_frequency = request.forms['round-frequency']
    form_exploit_timeout_injection = request.forms['exploit-timeout-injection']
    form_exploit_timeout_exersize = request.forms['exploit-timeout-exersize']
    form_number_of_teams = request.forms['number-of-teams']
    dirty = False
    if (data["start_time"] != form_start):
        data["start_time"] = form_start
        dirty = True
    if (data["end_time"] != form_end):
        data["end_time"] = form_end
        dirty = True
    if (data["intended_pts"] != form_intended_pts):
        data["intended_pts"] = form_intended_pts
        dirty = True
    if (data["unintended_pts"] != form_unintended_pts):
        data["unintended_pts"] = form_unintended_pts
        dirty = True
    if (data["round_frequency"] != form_round_frequency):
        data["round_frequency"] = form_round_frequency
        dirty = True
    if (data["exploit_timeout"]["injection_phase"] != form_exploit_timeout_injection):
        data["exploit_timeout"]["injection_phase"] = form_exploit_timeout_injection
        dirty = True
    if (data["exploit_timeout"]["exercise_phase"] != form_exploit_timeout_exersize):
        data["exploit_timeout"]["exercise_phase"] = form_exploit_timeout_exersize
        dirty = True
    if (len(data["teams"]) - 1 != int(form_number_of_teams)):
        if (len(data["teams"]) - 1 > int(form_number_of_teams)):
            response.status = 400
            return {"status": "error", "message": "The number of teams is too small"}
        for x in range(1, 1 + int(form_number_of_teams)):
            team_key = f"team-{x}"
            if (team_key not in data["teams"]):
                data["teams"][team_key] = {
                    "pub_key_id": "PLEASE_SUBMIT_PULL_REQUEST",
                    "slug": create_team(team_key),
                }
                for problem_name in data["problems"]:
                    data["teams"][team_key][problem_name] = {
                        "repo_name": f"{team_key}-{problem_name}",
                    }
                    for y in range(1, 1 + int(data["problems"][problem_name]["number_of_bugs"])):
                        data["teams"][team_key][problem_name][f"bug-{y}"] = "HASH_TO_BE_DETERMINED"
                    problem = data["problems"][problem_name]
                    repo_name = data["teams"][team_key][problem_name]["repo_name"]
                    repo_location = join("/usr/local/share", data["repo_owner"])
                    create_team_repo(problem, repo_name, repo_location, data["template_path"], data["repo_owner"], team=data["teams"][team_key]["slug"])
                dirty = True
    if (dirty):
        save_config(True)
        update_ctf(data)
    return {"status": "success"}

@app.route("/individuals/update", method="POST")
def individuals_update():
    global data
    load_config()
    individuals = loads(request.forms["individuals"])
    dirty = False
    stored_items = {}
    for individual in data["individuals"]:
        stored_items[individual] = {
            "team": data["individuals"][individual]["team"],
            "id": data["individuals"][individual]["id"],
            "pub_key_id": data["individuals"][individual]["pub_key_id"],
        }
    data["individuals"] = {
            data["instructor"] : {
                "team": "instructor",
                "id": get_id(data["instructor"]) if "instructor" not in stored_items else stored_items["instructor"]["id"],
                "pub_key_id": "PLEASE_SUBMIT_PULL_REQUEST" if "instructor" not in stored_items else stored_items["instructor"]["pub_key_id"],
            }
        }
    for name in individuals:
        if (individuals[name] != ""):
            data["individuals"][name] = {
                "team": individuals[name],
                "id": get_id(name) if name not in stored_items else stored_items[name]["id"],
                "pub_key_id": "PLEASE_SUBMIT_PULL_REQUEST" if name not in stored_items else stored_items[name]["pub_key_id"],
            }
            if individuals[name] != stored_items[name]["team"]:
                remove_from_team(name, data["teams"][stored_items[name]["team"]]["slug"])
                add_to_team(name, data["teams"][individuals[name]]["slug"])
        dirty = True
    if (dirty):
        save_config(True)
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
    if (exists(config_file_path)):
        config_script = """
        if (!confirm('You already have a configuration. Do you want to overwrite it?')) { 
            window.location.href = '/manage'; 
        }"""
    i = Template(setup)
    c = Template(config_form)
    config = c.substitute(
        action = "/setup-form",
        organization = "",
        managing = "",
        startdate = "",
        starttime = "",
        enddate = "",
        endtime = "",
        intended = "",
        unintended = "",
        round = "",
        injection_timeout = "",
        exersize_timeout = "",
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
    if not exists(config_file_path):
        redirect("/setup")
    load_config()
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
        bugs = data["problems"]["problem-1"]["number_of_bugs"],
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
    if not exists(config_file_path):
        redirect("/setup")
    return Template(scoreboard).substitute(header = header, navbar = navbar, src = f"https://{data['repo_owner']}.github.io")

@app.route("/individuals")
def individuals_ajax():
    global data
    load_config()
    return data["individuals"]
    

if __name__ == "__main__":
    if (data != {}):
        start_ctf(data)
    run(app, host='0.0.0.0', port=80, debug=True) # TODO: Change to False
