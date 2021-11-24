#!/usr/bin/env python
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

import json
import sys
from ctf_utils import iso8601_to_timestamp
from datetime import datetime, timedelta
from github import post, get, put, patch, poll

def create_label(repo_owner, repo_name, label_name, \
        color, desc):

    query = f'/repos/{repo_owner}/{repo_name}/labels'
    issue = {'name': label_name, 'description': desc, 'color': color}
    # Add the label to the repository
    if post(query, json.dumps(issue)) is None:
        print(f'[*] Label already exists in {label_name}')

def update_label(repo_owner, repo_name, issue_no, label):
    query = f'/repos/{repo_owner}/{repo_name}/issues/{issue_no}'
    labels = [label]
    issue = {'labels': labels}
    r = patch(query, json.dumps(issue))
    if r is None:
        print(f'[*] Could not create comment in "{repo_name}/{issue_no}"')
    else:
        print('[*] Successfully updated label')


def make_github_issue(repo_owner, repo_name, title, body):
    '''Create an issue on github.com using the given parameters.'''
    query = f'/repos/{repo_owner}/{repo_name}/issues'
    issue = {'title': title, 'body': body}
    r = post(query, json.dumps(issue), 201)
    if r is None:
        print(f'[*] Could not create issue "{title}"')
        print('[*] Response:', r)
        sys.exit(-1)
    else:
        print(f'[*] Successfully created issue "{title}"')

def get_github_issue(repo_owner, repo_name, issue_no):
    '''Retrieve an issue on github.com using the given parameters.'''
    query = f'/repos/{repo_owner}/{repo_name}/issues/{issue_no}'
    r = get(query)
    if r is None:
        print(f'Could not get Issue from {query}')
        print('Response:', r)
        sys.exit(-1)
    else:
        print(f'[*] Successfully obtained issue #{issue_no}')
        print('[*] title:', r['title'])
        print('[*] creater:', r['user']['login'])
        dt = datetime.strptime(r['created_at'],'%Y-%m-%dT%H:%M:%SZ')
        # XXX do not assume it is in Korea, just use the current tz.
        open_time = dt + timedelta(hours = 9) # Change to the Korea time
        print('[*] open time:', open_time)
        title = r['title']
        submitter = r['user']['login']
        create_time = r['created_at']
        content = r['body']
        create_timestamp = int(iso8601_to_timestamp(create_time))
        return (title, submitter, create_timestamp, content)

def submit_issue(title, encrypted_exploit, target_team, config):
    # Retrieve information from config
    repo_owner = config['repo_owner']
    repo_name = config['teams'][target_team]['repo_name']

    # Read in encrypted file content
    with open(encrypted_exploit, 'r') as f :
        content = f.read().rstrip()

    make_github_issue(repo_owner, repo_name, title, content)

def is_closed(repo_owner, repo_name, issue_no):
    query = f'/repos/{repo_owner}/{repo_name}/issues/{issue_no}'
    r = get(query)
    if r is None:
        print(f'Could not get Issue from {query}')
        print('Response:', r)
        return True     # Not deal with the error case. Just regard as closed
    else:
        if r['closed_at'] == None:
            return False
        else:
            return True

def create_comment(repo_owner, repo_name, issue_no, comment):
    query = f'/repos/{repo_owner}/{repo_name}/issues/{issue_no}/comments'

    issue = {'body': comment}
    r = post(query, json.dumps(issue), 201)
    if r is None:
        print(f'[*] Could not create comment in "{repo_name}/{issue_no}"' )
        print(r)
    else:
        print('[*] Successfully created comment')

def close_issue(repo_owner, repo_name, issue_no):
    query = f'/repos/{repo_owner}/{repo_name}/issues/{issue_no}'

    issue = {'state': 'closed'}
    r = patch(query, json.dumps(issue))
    if r is None:
        print(f'[*] Could not close "{repo_name}/{issue_no}"')
    else:
        print('[*] Successfully closed')


# TODO : maybe we can add main function so this can be used like
# "python issue.py SUBMIT ..." or "python issue.py FETCH ..."
