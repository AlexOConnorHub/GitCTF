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
from ctf_utils import prompt_checkout_warning, print_and_log
from ctf_git import list_branches, clone, checkout
from ctf_git import get_latest_commit_hash
from issue import get_github_issue
from crypto import decrypt_exploit
from verify_exploit import verify_exploit
from datetime import datetime
from command import run_command

def verify_issue(defender, repo_name, issue_no, config, target_commit=None):
    timeout = config["exploit_timeout"]["exercise_phase"]
    repo_owner = config['repo_owner']
    title, submitter, create_time, content = \
        get_github_issue(repo_owner, repo_name, issue_no)

    # Issue convention: "exploit-[branch_name]"
    target_branch = title[8:]

    clone(repo_owner, repo_name)

    # Write the fetched issue content to temp file
    tmpfile = f"/tmp/gitctf_{random_string(6)}.issue"
    tmpdir = f"/tmp/gitctf_{random_string(6)}.dir"

    with open(tmpfile, "w") as f:
        f.write(content)

    # Decrypt the exploit
    mkdir(tmpdir)

    team = defender
    decrypt_exploit(tmpfile, config, team, tmpdir, submitter)
    rmfile(tmpfile)

    # Now iterate through branches and verify exploit
    branches = list_branches(repo_name)

    candidates = []
    if (target_branch in branches) and (target_commit is None):
        # Iterate through branches and collect candidates
        commit = get_latest_commit_hash(repo_name, create_time, target_branch)
        candidates.append((target_branch, commit))

    verified_branch = None
    verified_commit = None

    log = f'About {title} (exploit-service branch)\n'

    for (branch, commit) in candidates:
        if branch in title:
            result, log = verify_exploit(tmpdir, repo_name, commit, timeout, \
                    config, log=log)
        else:
            result, _ = verify_exploit(tmpdir, repo_name, commit, timeout, \
                    config)

        if result:
            verified_branch = branch
            verified_commit = commit
            break

    rmdir(tmpdir)
    rmdir(repo_name)

    if verified_branch is None:
        print(f"[*] The exploit did not work against branch '{target_branch}'")
    else:
        print(f"[*] The exploit has been verified against branch '{verified_branch}'")

    return (verified_branch, verified_commit, submitter, log)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} [repo name] [issue no] [config]")
        sys.exit()
    repo_name = sys.argv[1]
    issue_no = sys.argv[2]
    config_file = sys.argv[3]
    config = load_config(config_file)
    verify_issue(repo_name, issue_no, config)
