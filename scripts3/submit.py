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
from ctf_git import list_branches
from verify_exploit import verify_exploit
from crypto import encrypt_exploit
from issue import submit_issue
from ctf_utils import rmfile, load_config, prompt_checkout_warning

def submit(exploit_dir, service_dir, branch, target, config_file):
    config = load_config(config_file)
    timeout = config["exploit_timeout"]["exercise_phase"]
    prompt_checkout_warning(service_dir)
    verified_branch = None
    result, _ = verify_exploit(exploit_dir, service_dir, branch, timeout, config)
    if result:
        verified_branch = branch

    if verified_branch is None :
        print("[*] Your exploit did not work against any of the branch")
        sys.exit()

    print(f"[*] Your exploit has been verified against branch '{verified_branch}'")

    # Not encrypt exploit
    signer = config["player"]
    encrypted_exploit = encrypt_exploit(exploit_dir, target, config, signer)
    if encrypted_exploit is None:
        print("[*] Failed to encrypt exploit")
        sys.exit(0)

    # Submit an issue with the encrypted exploit
    issue_title = f"exploit-{verified_branch}"
    submit_issue(issue_title, encrypted_exploit, target, config)

    # Clean up
    rmfile(encrypted_exploit)


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(f"Usage: {sys.argv[0]} [exploit dir] [service dir] [branch] [team] [config]")
        sys.exit()
    exploit_dir = sys.argv[1]
    service_dir = sys.argv[2]
    branch = sys.argv[3]
    target = sys.argv[4]
    config = sys.argv[5]
    submit(exploit_dir, service_dir, branch, target, config)
