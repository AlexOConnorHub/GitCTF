#!/bin/env python3
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

from github import request
from time import time, mktime, strptime
from threading import Timer, Thread
from github import request

def run_listener(data):
    global listener_thread, kill_thread
    while not kill_thread:
        # Wait for submission
        # Check if the submission is valid
        # If valid, add it to the submission queue
        # If invalid, reject it
        pass

def trigger_ctf_end():
    global data, kill_thread, listener_thread
    for team in data['teams']:
        for problem in data['problems']:
            if data['teams'][team].get(problem) == None: # Most likely the instructor
                break
            request(f"/repos/{data['repo_owner']}/{data['teams'][team][problem]['repo_name']}", {"archived": "true"}, 200, "PATCH")
    kill_thread = True
    if "listener_thread" in globals():
        listener_thread.join()

def trigger_ctf_start():
    global data, trigger, listener_thread, kill_thread
    if "trigger" in globals() and trigger != None:
        trigger.cancel()
        trigger = None
    end_time = int(mktime(strptime(data['end_time'], "%Y-%m-%dT%H:%M:%S%z")))
    timezone_hours = int(data['end_time'][-5:-3])
    timezone_minutes = int(data['end_time'][-2:])
    timezone_sign = data['end_time'][-6]
    utc_offset = timezone_hours * 3600 + timezone_minutes * 60
    curr_time = int(time()) + utc_offset if timezone_sign == "+" else int(time()) - utc_offset
    trigger_time = end_time - curr_time
    trigger = Timer(trigger_time, trigger_ctf_end)
    trigger.start()
    for team in data['teams']:
        for problem in data['problems']:
            if data['teams'][team].get(problem) == None: # Most likely the instructor
                break # Consider continue if implementing multiple problems
            request(f"/repos/{data['repo_owner']}/{data['teams'][team][problem]['repo_name']}", {"archived": "false"}, 200, "PATCH")
            request(f"/repos/{data['repo_owner']}/{data['teams'][team][problem]['repo_name']}", {"private": "false"}, 200, "PATCH")
    kill_thread = False
    listener_thread = Thread(target=run_listener, args=(data,))
    listener_thread.start()

def set_start_timer():
    global data, trigger
    start_time = int(mktime(strptime(data['start_time'], "%Y-%m-%dT%H:%M:%S%z")))
    timezone_hours = int(data['start_time'][-5:-3])
    timezone_minutes = int(data['start_time'][-2:])
    timezone_sign = data['start_time'][-6]
    utc_offset = timezone_hours * 3600 + timezone_minutes * 60
    curr_time = int(time()) + utc_offset if timezone_sign == "+" else int(time()) - utc_offset
    trigger_time = start_time - curr_time
    trigger = Timer(trigger_time, trigger_ctf_start)
    trigger.start()

def start_ctf(data_dict):
    global data, trigger
    data = data_dict
    start_time = int(mktime(strptime(data['start_time'], "%Y-%m-%dT%H:%M:%S%z")))
    end_time = int(mktime(strptime(data['end_time'], "%Y-%m-%dT%H:%M:%S%z")))
    timezone_hours = int(data['start_time'][-5:-3])
    timezone_minutes = int(data['start_time'][-2:])
    timezone_sign = data['start_time'][-6]
    utc_offset = timezone_hours * 3600 + timezone_minutes * 60
    curr_time = int(time()) + utc_offset if timezone_sign == "+" else int(time()) - utc_offset
    should_have_started = start_time < curr_time
    should_have_ended = end_time < curr_time
    if should_have_started:
        trigger_ctf_start()
    elif should_have_ended:
        trigger_ctf_end()
    else:
        set_start_timer()

def update_ctf(data_dict):
    global data, trigger
    if data_dict['start_time'] != data['start_time'] or data_dict['end_time'] != data['end_time']:
        trigger.cancel()
        trigger = None
        data = data_dict
        set_start_timer()
    else:
        data = data_dict
