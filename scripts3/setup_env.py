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
import os
from subprocess import run
from ctf_utils import load_config, prompt_rmdir_warning, rmdir, mkdir, base_dir
from ctf_utils import copy
from command import run_command
from string import Template

def create_remote_repo(repo_owner, repo_name, description = None, path = None):
    print(f'[*] Creating {repo_name} remote repository')
    mkdir()
    r, _, _ = run_command(f"gh repo create {repo_name} --private --description \"{description}\"", os.path.join(path, ".."))
    if r is None:
        print(f'[*] Failed to create remote repository "{repo_name}".')
        print('[*] Response:', r)
    else:
        print(f'[*] Successfully created remote repository "{repo_name}".')

def init_repo(dir_path):
    _, _, r = run_command('git init', dir_path)
    if r != 0:
        print('[*] Failed to git init')
        return False
    _, _, r = run_command(f'git remote add origin https://github.com/{dir_path}.git', dir_path)
    if r != 0:
        print(f'[*] Failed to git remote add origin {dir_path}.')
        return False
    return True

def create_local_repo(repo_name, repo_location):
    print(f'[*] Creating {repo_name} local repositoy at {os.path.join(repo_location, repo_name)}.')
    mkdir(os.path.join(repo_location, repo_name))
    run_command(f"gh repo create {repo_name} --private --confirm", repo_location)
    return True

def commit_and_push(path, msg):
    _, _, r = run_command('git add .', path)
    if r != 0:
        print(f'[*] Failed to git add . in {path}.')
        return False
    _, _, r = run_command(f'git commit -m "{msg}"', path)
    if r != 0:
        print(f'[*] Failed to commit in {path}.')
        return False
    _, _, r = run_command('git push -f origin master', path)
    if r != 0:
        print(f'[*] Failed to push in {path}.')
        return False
    return True

def create_flag(path):
    with open(os.path.join(path, 'flag'), "w") as f:
        f.write('script_will_put_random_string_here')

def create_xinetd_config(problem_info, repo_dir_path, bin_name, template_path):
    with open(os.path.join(base_dir(), template_path, 'xinetd_conf.template'), 'r') as f:
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
    with open(os.path.join(repo_dir_path,  service_conf_name), 'w') as f:
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
    with open(os.path.join(base_dir(), template_path, "dockerfile.template"), 'r') as f:
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

    with open(os.path.join(repo_dir_path, 'Dockerfile'), 'w') as f:
        f.write(dockerfile)

def local_setup(repo_owner, scoreboard_name, problems, template_path, repo_location, teams):
    print('[*] Start local setup')
    # Create root directory for CTF env.
    prompt_rmdir_warning(os.path.join(repo_location, repo_owner))
    rmdir(os.path.join(repo_location, repo_owner))
    mkdir(os.path.join(repo_location, repo_owner))

    # Setup local scoreboard repo
    scoreboard_dir_path = os.path.join(repo_location, repo_owner)
    if create_local_repo( scoreboard_name, scoreboard_dir_path):
        open(os.path.join(scoreboard_dir_path, scoreboard_name, 'score.csv'), 'w').close()
        commit_and_push(os.path.join(scoreboard_dir_path, scoreboard_name), 'Initialize scoreboard')

    # Setup local problems repo
    for team_name in teams:
        if (team_name == "instructor"):
            continue
        team = teams[team_name]
        for problem_name in problems:
            problem = problems[problem_name]
            repo_name = team[problem_name]["repo_name"]
            repo_dir_path = os.path.join(repo_location, repo_owner)
            if create_local_repo(repo_name, repo_dir_path):
                repo_dir_path = os.path.join(repo_dir_path, repo_name)
                print('[*] Copy binary')
                copy(problem['bin_src_path'], repo_dir_path)
                print('[*] Create flag file')
                create_flag(repo_dir_path)
                print('[*] Make Dockerfile')
                create_dockerfile(problem, repo_dir_path, template_path, problem['sed_cmd'])
                commit_and_push(repo_dir_path, f"Add problem: {repo_name}")

def setup_env(admin_config_file, repo_location):
    admin_config = load_config(admin_config_file)
    repo_owner = admin_config['repo_owner']
    scoreboard_name = f"{repo_owner}.github.io"
    problems = admin_config['problems']
    template_path = admin_config['template_path']
    teams = admin_config['teams']
    
    local_setup(repo_owner, scoreboard_name, problems, template_path, repo_location, teams)
