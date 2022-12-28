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

# if [ "$#" -ne 1 ]; then
#     echo "Usage: $0 [container name]"
#     exit 1
# fi
# CONTAINER=$1

# docker kill $CONTAINER
# docker rm $CONTAINER
# docker images -qf dangling=true | xargs docker rmi


# Translate the above script to Python

import sys
import subprocess
import docker

if len(sys.argv) != 2:
    print(f"Usage: ${sys.argv[0]} [container name]")
    exit(1)

container = sys.argv[1]

client = docker.from_env()
# kill the docker container
if container in client.containers.list():
    client.containers.get(container).kill()
# subprocess.run(["docker", "kill", container])
# remove the docker container
if container in client.containers.list():
    client.containers.get(container).remove()
# subprocess.run(["docker", "rm", container])
# Cleanup dangling images
client = docker.from_env()
for image in client.images.list(filters={"dangling": True}):
    client.images.remove(image.id)

