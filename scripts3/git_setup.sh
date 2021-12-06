#!/bin/sh
###############################################################################
# Git-based CTF
###############################################################################
#
# Author: SeongIl Wi <seongil.wi@kaist.ac.kr>
#          Jaeseung Choi <jschoi17@kaist.ac.kr>
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

username=$(gh api /user | jq .login)
git config --global user.name $username
git config --global user.email $(gh api /user/emails | jq .[1].email)
git config --global credential.helper store
echo https://$(gh api /user | jq .id):$GH_TOKEN@github.com > /root/.git-credentials

jq '.instructor = $username' /etc/gitctf/.config.json > /tmp/conf.json.tmp && mv /tmp/conf.json.tmp /etc/gitctf/.config.json 
jq '.repo_owner = $username' /etc/gitctf/.config.json > /tmp/conf.json.tmp && mv /tmp/conf.json.tmp /etc/gitctf/.config.json 

