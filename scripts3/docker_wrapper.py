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

from docker import from_env

def exploit(path, exploit_name, ip, port, timeout):
    client = from_env()
    # Build image named
    client.images.build(path=path, tag=exploit_name, forcerm=True, nocache=True)
    # docker run -it --rm --net="host" --name $EXPLOITNAME \
    # $EXPLOITNAME timeout $TIMEOUT \
    # "/bin/exploit" $SERVICE_IP $SERVICE_PORT
    container = client.containers.run(exploit_name, tty=True, remove=True, network="host", name=exploit_name, timeout=timeout, detach=True)
    exit_code, output = container.exec_run(f"/bin/exploit {ip} {port}", tty=True)
    if exit_code != 0:
        print(output.decode("utf-8"))
        return None
    return output.decode("utf-8")


def service(path, service_name, local_port, container_port):
    client = from_env()
    client.images.build(path=path, tag=service_name, forcerm=True, nocache=True)
    return client.containers.run(service_name, tty=True, remove=True, network="host", name=service_name, detach=True, ports={container_port: local_port})

