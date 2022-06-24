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
RUN pip3 install --no-cache --upgrade pip setuptools python-dateutil docker bottle

# Create directories for the project
RUN mkdir /etc/gitctf
RUN mkdir /usr/local/share/gitctf
RUN mkdir -p /srv/gitctf/css
RUN mkdir -p /srv/gitctf/images
RUN mkdir -p /srv/gitctf/fonts

# Populate the directories
COPY scripts3/* /usr/local/bin/
COPY templates/* /usr/local/share/gitctf/
COPY web/css /srv/gitctf/css
COPY web/images /srv/gitctf/images
COPY web/fonts /srv/gitctf/fonts
COPY web/index.html /srv/gitctf
COPY web/setup.html /srv/gitctf
COPY web/manage.html /srv/gitctf
COPY configuration/* /etc/gitctf/
COPY docker_entry.py /

# sed script
RUN sed -i 's/\.\.\/templates/\/usr\/local\/share\/gitctf\//g' /etc/gitctf/.config.json

ENTRYPOINT [ "/docker_entry.py" ]