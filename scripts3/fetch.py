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

import sys
import json
import os
from ctf_utils import load_config, rmfile, mkdir, random_string, rmdir
from ctf_utils import prompt_rmdir_warning
from issue import get_github_issue
from crypto import decrypt_exploit

def fetch(team, issue_no, config):
    repo_owner = config['repo_owner']
    repo_name = config['teams'][team]['repo_name']

    _, submitter, create_time, content = \
        get_github_issue(repo_owner, repo_name, issue_no)

    # Write the fetched issue content to temp file
    tmpfile = f"/tmp/gitctf_{random_string(6)}.issue"
    with open(tmpfile, "w") as f:
        f.write(content)

    # Decrypt the exploit
    out_dir = f"exploit-{submitter}-{create_time}"
    prompt_rmdir_warning(out_dir)
    rmdir(out_dir)
    mkdir(out_dir)
    team = config["player_team"]
    out_dir = decrypt_exploit(tmpfile, config, team, out_dir, submitter)
    if out_dir is not None:
        print(f"Exploit fetched into {out_dir}")

    # Clean up
    rmfile(tmpfile)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} [team] [issue no] [config]")
        sys.exit()
    team = sys.argv[1]
    issue_no = sys.argv[2]
    config_file = sys.argv[3]
    config = load_config(config_file)
    fetch(team, issue_no, config)
