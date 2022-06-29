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
from command import run_command
from ctf_utils import load_config, prompt_rmdir_warning, rmdir, mkdir, base_dir, copy
from github import request
from json import dumps
from os.path import join
from shutil import copyfile
from string import Template

def create_local_repo(repo_path):
    _, _, r = run_command(f'git init', repo_path)
    if r != 0:
        print(f'[*] Failed to create empty repository in {repo_path}.')
        return False
    return True

def create_remote_repo(repo_name, repo_location, repo_owner, team=None, public=False):
    print(f'[*] Creating {repo_name} repositoy .')
    public_flag = "public" if public else "private"
    _, e, r = run_command(f"gh repo create {repo_owner}/{repo_name} --{public_flag} --push --source {join(repo_location, repo_name)}" + (f" --team {team}" if (team != None) else ""), repo_location)
    if r != 0:
        print(f'[*] Failed to create repository "{repo_name}".')
        print('[*] Response:', e)
        return False
    if team != None:
        if not request(f"/orgs/{repo_owner}/teams/{team}/repos/{repo_owner}/{repo_name}", dumps({"permission": "push"}), 204, "PUT"):
            print(f'[*] Failed to set team permission for repository "{repo_name}".')
            return False
    return True

def commit_and_push(path, msg):
    if commit(path, msg):
        if push(path, f"Merge for commit {msg}"):
            return True
    return False

def commit(path, msg):
    _, _, r = run_command('git add .', path)
    if r != 0:
        print(f'[*] Failed to git add . in {path}.')
        return False
    _, _, r = run_command(f'git commit -m "{msg}"', path)
    if r != 0:
        print(f'[*] Failed to commit in {path}.')
        return False

def push(path, merge_msg):
    _, _, r = run_command('git push', path)
    if r != 0:
        _, _, r = run_command('git pull', path)
        if r != 0:
            print(f'[*] Failed to git pull in {path}.')
            return False
        _, _, r = run_command(f'git commit -m "{merge_msg}"', path)
        if r != 0:
            print(f'[*] Failed to commit in {path}.')
            return False
        _, _, r = run_command('git push', path)
        if r != 0:
            print(f'[*] Failed to push in {path}.')
            return False
    return True

def make_scoreboard_site(site_path, template_path, repo_owner):
    with open(join(template_path, 'scoreboard', '_config.yml'), 'r') as f:
        site_content = f.read()
    site_index_template = Template(site_content)
    site_index = site_index_template.substitute(repo_owner = site_path)
    with open(join(site_path, '_config.yml'), 'w') as f:
        f.write(site_index)
    copyfile(join(template_path, 'scoreboard', 'index.markdown'), site_path)
    copyfile(join(template_path, 'scoreboard', 'about.markdown'), site_path)
    copyfile(join(template_path, 'scoreboard', '404.html'), site_path)
    copyfile(join(template_path, 'scoreboard', 'Gemfile'), site_path)

def create_flag(path):
    with open(join(path, 'flag'), "w") as f:
        f.write('script_will_put_random_string_here')

def create_xinetd_config(problem_info, repo_dir_path, bin_name, template_path):
    with open(join(base_dir(), template_path, 'xinetd_conf.template'), 'r') as f:
        service_conf = f.read()

    service_conf_name = f'{bin_name}_service_conf'
    bin_dst_path = problem_info['bin_dst_path']
    bin_args = problem_info['bin_args']
    port = problem_info['port']

    s = Template(service_conf)
    service_conf = s.substitute(service_conf_name = service_conf_name, \
                                bin_name = bin_name,  \
                                bin_dst_path = bin_dst_path, \
                                bin_args = bin_args, \
                                port = port)
    with open(join(repo_dir_path,  service_conf_name), 'w') as f:
        f.write(service_conf)

    return service_conf_name

def make_xinetd_exec_env(problem_info, repo_dir_path, bin_name, template_path):
    service_conf_name = \
            create_xinetd_config(problem_info, repo_dir_path, bin_name, template_path)
    exec_command = f'COPY {service_conf_name} /etc/xinetd.d\n'
    exec_command += f'RUN echo "{service_conf_name} {problem_info["port"]}/tcp" >> /etc/services\n'
    exec_command += 'RUN service xinetd restart\n'
    exec_command += 'ENTRYPOINT ["xinetd", "-dontfork"]'
    return exec_command

def create_dockerfile(problem_info, repo_dir_path, template_path, sed_cmd):
    with open(join(base_dir(), template_path, "dockerfile.template"), 'r') as f:
        dockerfile = f.read()

    base_image = problem_info['base_image']
    required_packages = problem_info['required_packages']

    flag_dst_path = problem_info['flag_dst_path']

    bin_src_path = problem_info['bin_src_path']
    bin_name = bin_src_path.split('/')[-1]
    bin_dst_path = problem_info['bin_dst_path']

    if problem_info['service_exe_type'] == 'xinetd':
        exec_command = make_xinetd_exec_env(problem_info, repo_dir_path, \
                bin_name, template_path)
    elif problem_info['service_exe_type'] == 'stand-alone':
        exec_command = 'ENTRYPOINT ["/bin/sh", "-c"]'
    else:
        print(f'[*] Failed to make Dockerfile from {repo_dir_path}')
        return

    s = Template(dockerfile)
    dockerfile = s.substitute(base_image = base_image, \
                              sed_cmd = sed_cmd, \
                              required_packages = required_packages, \
                              flag_dst_path = flag_dst_path, \
                              bin_name = bin_name, \
                              bin_dst_path = bin_dst_path, \
                              exec_command = exec_command)

    with open(join(repo_dir_path, 'Dockerfile'), 'w') as f:
        f.write(dockerfile)

def local_setup(repo_owner, scoreboard_name, problems, template_path, repo_location, teams, admin_config_file=None):
    print('[*] Start local setup')
    # Create root directory for CTF env.
    repo_root_dir_path = join(repo_location, repo_owner)
    prompt_rmdir_warning(repo_root_dir_path)
    rmdir(repo_root_dir_path)
    mkdir(repo_root_dir_path)

    # Create repo for scoreboard, and add files
    repo_path = join(repo_root_dir_path, scoreboard_name)
    mkdir(repo_path)
    open(join(repo_path, 'score.csv'), 'w').close()
    make_scoreboard_site(repo_path, template_path, repo_owner)
    run_command(f"ln {admin_config_file} {join(repo_path, 'config.json')}")
    print(f'[*] Creating empty repositoy in {repo_location}.')
    create_local_repo(repo_path)
    commit(repo_path, 'Initial commit')
    create_remote_repo( scoreboard_name, repo_root_dir_path, repo_owner, public=True)

    # Setup local problems repo
    for team_name in teams:
        if (team_name == "instructor"):
            continue
        team = teams[team_name]
        for problem_name in problems:
            problem = problems[problem_name]
            repo_name = team[problem_name]["repo_name"]
            repo_path = join(repo_root_dir_path, repo_name)
            mkdir(repo_path)
            print('[*] Copy binary')
            copy(problem['bin_src_path'], repo_path)
            print('[*] Create flag file')
            create_flag(repo_path)
            print('[*] Make Dockerfile')
            create_dockerfile(problem, repo_path, template_path, problem['sed_cmd'])
            print(f'[*] Creating empty repositoy in {repo_location}.')
            create_local_repo(repo_path)
            commit(repo_path, 'Initial commit') # Will fail
            create_remote_repo(repo_name, repo_root_dir_path, repo_owner, team=team["slug"])

def setup_env(admin_config_file, repo_location):
    admin_config = load_config(admin_config_file)
    repo_owner = admin_config['repo_owner']
    scoreboard_name = f"{repo_owner}.github.io"
    problems = admin_config['problems']
    template_path = admin_config['template_path']
    teams = admin_config['teams']
    individuals = admin_config['individuals']

    local_setup(repo_owner, scoreboard_name, problems, template_path, repo_location, teams, admin_config_file)
