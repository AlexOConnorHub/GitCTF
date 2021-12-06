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
# To make small image
FROM alpine:3.14

# Setup python
ENV PYTHONUNBUFFERED=1
RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools python-dateutil requests
COPY scripts3/* /usr/local/bin/

# Setup git, GH_TOKEN sent in as environment variable
RUN apk add --no-cache git github-cli gnupg zip jq

# Setup templates and config files
RUN mkdir /etc/gitctf
COPY configuration/* /etc/gitctf/
RUN mkdir /usr/local/share/gitctf
COPY templates/* /usr/local/share/gitctf/
RUN jq '.template_path = "/usr/local/share/gitctf/"' /etc/gitctf/.config.json > /tmp/conf.json.tmp && mv /tmp/conf.json.tmp /etc/gitctf/.config.json 

# Setup Web interface
RUN pip3 --no-cache install bottle
COPY docker_entry.py /
EXPOSE 80
RUN mkdir -p /srv/gitctf/css
COPY web/css /srv/gitctf/css
RUN mkdir -p /srv/gitctf/images
COPY web/images /srv/gitctf/images
RUN mkdir -p /srv/gitctf/fonts
COPY web/fonts /srv/gitctf/fonts
RUN mkdir -p /srv/gitctf/js
COPY web/js /srv/gitctf/js
COPY web/index.html /srv/gitctf
COPY web/setup.html /srv/gitctf
COPY web/manage.html /srv/gitctf

ENTRYPOINT [ "/docker_entry.py", "/srv/gitctf/" ]