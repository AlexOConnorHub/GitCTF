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
import sys
from command import run_command
from ctf_git import clone, checkout
from ctf_utils import base_dir, rmdir, docker_cleanup, load_config

def setup(repo_name, container_name, service_port, host_port):
    script = os.path.join(base_dir(), "setup_service.sh")
    setup_cmd = f'{script} "{container_name}" {service_port} {host_port}'
    _, err, e = run_command(setup_cmd, repo_name)
    if e != 0:
        print(f"[*] Failed to launch {container_name}")
        print(err)
        sys.exit()

def check_liveness(container_name, host_port):
    _, _, e = run_command(f'nc -z 127.0.0.1 {host_port}', None)
    if e != 0:
            print(f"[*] {container_name} service is not running.")
    else:
        print(f"[*] {container_name} service looks well.")

def verify_service(team, branch, service_port, host_port, config_file):
    config = load_config(config_file)
    repo_owner = config['repo_owner']
    repo_name = config['teams'][team]['repo_name']
    container_name = f"{repo_name}-{branch}"
    clone(repo_owner, repo_name)
    docker_cleanup(container_name)
    checkout(repo_name, branch)
    setup(repo_name, container_name, int(service_port), int(host_port))
    check_liveness(container_name, int(host_port))
    docker_cleanup(container_name)
    rmdir(repo_name)
    sys.exit()

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print(f'Usage: {sys.argv[0]} [team] [branch] [service port] [host port] [config]')
        sys.exit()
    team = sys.argv[1]
    branch = sys.argv[2]
    service_port = sys.argv[3]
    host_port = sys.argv[4]
    config_file = sys.argv[5]
    verify_service(team, branch, service_port, host_port, config_file)

