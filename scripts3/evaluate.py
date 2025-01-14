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
import re
import sys
import csv
import json
import time
import calendar
from issue import is_closed, create_comment, close_issue
from issue import create_label, update_label, get_github_issue
from command import run_command
from ctf_utils import load_config, rmdir, rmfile, iso8601_to_timestamp, is_timeover
from github import request, poll, get_github_path
from ctf_git import clone, checkout, get_next_commit_hash
from verify_issue import verify_issue
import importlib

msg_file = 'msg' # Temporarily store commit message

def failure_action(repo_owner, repo_name, issue_no, comment, id):
    create_label(repo_owner, repo_name, "failed", "000000", \
            "Verification failed.")
    update_label(repo_owner, repo_name, issue_no, "failed")
    create_comment(repo_owner, repo_name, issue_no, comment)
    close_issue(repo_owner, repo_name, issue_no)
    mark_as_read(id)

def get_target_repos(config):
    repos = []
    for team in config['teams']:
        repos.append(config['teams'][team]['repo_name'])
    return repos

def is_issue(noti):
    return noti['subject']['type'] == 'Issue'

def is_target(noti, target_repos):
    return noti['repository']['name'] in target_repos

def get_issue_number(noti):
    return int(noti['subject']['url'].split('/')[-1])

def get_issue_id(noti):
    return noti['url'].split('/')[-1]

def get_issue_gen_time(noti):
    return iso8601_to_timestamp(noti['updated_at'])

def get_issues(target_repos):
    issues = []
    query = '/notifications'
    try:
        notifications, interval = poll(query)
    except ConnectionError:
        return [], 60
    for noti in reversed(notifications):
        if noti['unread'] and is_issue(noti) and is_target(noti, target_repos):
            num = get_issue_number(noti)
            id = get_issue_id(noti)
            gen_time = get_issue_gen_time(noti)
            issues.append((noti['repository']['name'], num, id, gen_time))
    return issues, interval

def mark_as_read(issue_id):
    query = '/notifications/threads/' + issue_id
    return request(query)

def get_defender(config, target_repo):
    teams = config['teams']
    defender = None
    for team in teams:
        if teams[team]['repo_name'] == target_repo:
            defender = team
            break
    return defender

def sync_scoreboard(scoreboard_dir):
    run_command('git reset --hard', scoreboard_dir)
    run_command('git pull', scoreboard_dir)

def write_score(stamp, info, scoreboard_dir, pts):
    with open(os.path.join(scoreboard_dir, 'score.csv'), 'a') as f:
        attacker = info['attacker']
        defender = info['defender']
        branch = info['branch']
        kind = info['bugkind']
        f.write(f'{stamp},{attacker},{defender},{branch},{kind},{pts}\n')

def write_message(info, scoreboard_dir, pts):
    with open(os.path.join(scoreboard_dir, msg_file), 'w') as f:
        attacker = info['attacker']
        defender = info['defender']
        branch = info['branch']
        kind = info['bugkind']
        f.write(f'[Score] {attacker} +{pts}\n\n')
        if pts == 0: # Protocol to indicate successfull defense
            f.write(f'{defender} defended `{branch}` {attacker} with {kind}')
        else:
            f.write(f'{attacker} attacked `{branch}` {kind} of {defender}')

def commit_and_push(scoreboard_dir):
    _, _, r = run_command('git add score.csv', scoreboard_dir)
    if r != 0:
        print('[*] Failed to git add score.csv.')
        return False
    _, _, r = run_command(f'git commit -F {msg_file}', scoreboard_dir)
    if r != 0:
        print('[*] Failed to commit score.csv.')
        return False
    _, _, r = run_command('git push origin master', scoreboard_dir)
    if r != 0:
        print('[*] Failed to push the score.')
        return False
    rmfile(os.path.join(scoreboard_dir, msg_file))
    return True

def find_the_last_attack(scoreboard_dir, timestamp, info):
    last_commit = None
    scoreboard_path = os.path.join(scoreboard_dir, 'score.csv')
    if os.path.isfile(scoreboard_path):
        with open(scoreboard_path) as f:
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                if int(row[0]) >= timestamp and len(row[4]) == 40:
                    if row[1] == info['attacker'] and row[2] == info['defender']:
                        if row[3] == info['branch']:
                            last_commit = row[4]
    return last_commit

def get_next_commit(last_commit, defender, branch, config):
    repo_name = config['teams'][defender]['repo_name']
    rmdir(repo_name)
    clone(config['repo_owner'], repo_name)
    next_commit_hash = get_next_commit_hash(repo_name, branch, last_commit)
    rmdir(repo_name)
    print(next_commit_hash)
    if next_commit_hash == '':
        return None
    else:
        return next_commit_hash

# XXX: Calling verify_issue() multiple times involves redundant process
# internally. We may consider replacing this by calling fetch() once and then
# calling verify_exploit() multiple times.
def process_unintended(repo_name, num, config, gen_time, info, scoreboard, id, repo_owner):
    unintended_pts = config['unintended_pts']
    target_commit = find_the_last_attack(scoreboard, gen_time, info)

    if target_commit is None:
        # This exploit is previously unseen, give point.
        write_score(gen_time, info, scoreboard, unintended_pts)
        write_message(info, scoreboard, unintended_pts)
        commit_and_push(scoreboard)
    else:
        while True:
            target_commit = get_next_commit(target_commit, \
                    info['defender'], info['branch'], config)
            if target_commit is None:
                print('[*] No more commit to verify against')
                break

            _, verified_commit, _, _ = \
                verify_issue(info['defender'], repo_name, num, config,  target_commit)
            info['bugkind'] = target_commit
            if verified_commit is None:
                # Found a correct patch that defeats the exploit.
                current_time = int(time.time())
                write_score(current_time, info, scoreboard, 0)
                write_message(info, scoreboard, 0)
                commit_and_push(scoreboard)
                mark_as_read(id)
                create_label(repo_owner, repo_name, "defended", "0000ff", \
                        "Defended.")
                update_label(repo_owner, repo_name, num, "defended")
                break
            else:
                # Exploit still works on this commit, update score and continue
                write_score(gen_time, info, scoreboard, unintended_pts)
                write_message(info, scoreboard, unintended_pts)
                commit_and_push(scoreboard)

def process_issue(repo_name, num, id, config, gen_time, scoreboard):
    repo_owner = config['repo_owner']
    if is_closed(repo_owner, repo_name, num):
        mark_as_read(id)
        return


    title, _, _, _ = get_github_issue(repo_owner, repo_name, num)

    create_label(repo_owner, repo_name, "eval", "DA0019", \
            "Exploit is under review.")
    update_label(repo_owner, repo_name, num, "eval")

    defender = get_defender(config, repo_name)
    if defender is None:
        print(f'[*] Fatal error: unknown target {repo_name}.')
        sys.exit()
        return

    branch, commit, attacker, log = verify_issue(defender, repo_name, num, \
            config)
    if branch is None:
        log = "```\n" + log + "```"
        failure_action(repo_owner, repo_name, num, \
                log + '\n\n[*] The exploit did not work.', id)
        return

    if config['individual'][attacker]['team'] == defender:
        failure_action(repo_owner, repo_name, num, \
                f'[*] Self-attack is not allowed: {attacker}.', \
                id)
        return

    create_label(repo_owner, repo_name, "verified", "9466CB", \
            "Successfully verified.")
    update_label(repo_owner, repo_name, num, "verified")

    kind = commit
    info = {'attacker': attacker, 'defender': defender,
            'branch': branch, 'bugkind': kind}
    sync_scoreboard(scoreboard)
    process_unintended(repo_name, num, config, gen_time, info, scoreboard,
            id, repo_owner)

def prepare_scoreboard_repo(url):
    path = get_github_path(url).split('/')
    scoreboard_owner = path[0]
    scoreboard_name = path[1]
    scoreboard_dir = '.score'
    clone(scoreboard_owner, scoreboard_name, False, scoreboard_dir)
    return scoreboard_dir

def start_eval(config):
    target_repos = get_target_repos(config)
    scoreboard = prepare_scoreboard_repo(config['score_board'])
    finalize = False
    while (not finalize):
        if (is_timeover(config)):
            finalize = True
        issues, interval = get_issues(target_repos)
        if not issues:
            print(f'[*] No news. Sleep for {str(interval)} seconds.')
            time.sleep(interval)
            continue
        print((f"[*] {str(len(issues))} new issues."))
        for repo, num, id, gen_time in issues:
            process_issue(repo, num, id, config, gen_time, scoreboard)
    print('[*] Time is over!')
    return

def evaluate(config_file):
    importlib.reload(sys)
    sys.setdefaultencoding('utf-8')
    config = load_config(config_file)
    return start_eval(config)

