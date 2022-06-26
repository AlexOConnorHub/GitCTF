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

# Small image, and easy to install the few things we need
FROM alpine:3.14

# Environment setup
EXPOSE 80
ENV PYTHONUNBUFFERED=1
ARG GH_TOKEN_BUILD="PLEASE_SET_GH_TOKEN_BUILD"
ENV GH_TOKEN=$GH_TOKEN_BUILD

# Download and install packages needed
RUN apk add --update --no-cache python3 git github-cli gnupg zip
RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade setuptools python-dateutil docker bottle

# Create directories for the project
RUN mkdir -p /etc/gitctf
RUN mkdir -p /usr/local/share/gitctf
RUN mkdir -p /srv/gitctf/public/css
RUN mkdir -p /srv/gitctf/public/images
RUN mkdir -p /srv/gitctf/public/fonts
RUN mkdir -p /srv/gitctf/templates
RUN mkdir -p /srv/gitctf/pages

# Populate the directories
COPY templates/*     /usr/local/share/gitctf/
COPY web/fonts/*     /srv/gitctf/public/fonts/
COPY web/images/*    /srv/gitctf/public/images/
COPY web/css/*       /srv/gitctf/public/css/
COPY web/templates/* /srv/gitctf/templates/
COPY web/pages/*     /srv/gitctf/pages/
COPY scripts3/*      /usr/local/bin/

ENTRYPOINT [ "/usr/local/bin/docker_entry.py" ]
