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

FROM ubuntu:latest
# ======================================
# Install your package here
# sample sed command to replace default mirrors with custom mirror
# RUN sed -i 's/deb.debian.org/ftp.daumkakao.com/g' /etc/apt/sources.list
RUN echo Using default mirrors
RUN apt-get update
RUN apt-get upgrade
RUN apt-get install -y xinetd sudo
# ======================================

RUN adduser vuln64

COPY flag /var/ctf/flag
COPY vuln64 /service/vuln

RUN chown root:vuln64 /var/ctf/flag /service/vuln
RUN chmod 0550 /service/vuln
RUN chmod 0440 /var/ctf/flag

# ======================================
# Execute service
COPY vuln64_service_conf /etc/xinetd.d
RUN echo "vuln64_service_conf 2000/tcp" >> /etc/services
RUN service xinetd restart
ENTRYPOINT ["xinetd", "-dontfork"]
# ======================================
