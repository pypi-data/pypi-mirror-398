#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：kyutil 
@File    ：ansible.py
@IDE     ：PyCharm 
@Author  ：xuyong@kylinos.cn
@Date    ：2025/5/22 下午4:39 
@Desc    ：说明：
"""
import base64
import os
import random
import sys
from shutil import copyfile

import ansible_runner
from logzero import logger as log


def gen_random_base_64_str() -> bytes:
    flag = "flag{**flag**}".encode("utf-8")
    b64list = [lambda x: base64.b16encode(x), lambda x: base64.b32encode(x), lambda x: base64.b64encode(x)]
    for _ in range(10):
        choice = random.choice([0, 1, 2])
        flag = b64list[choice](flag)
    encoded = {
        '16': lambda x: base64.b16encode(x),
        '32': lambda x: base64.b32encode(x),
        '64': lambda x: base64.b64encode(x)
    }
    choice = random.choice(['16', '32', '64'])
    flag = encoded[choice](flag)
    return flag[7:32]


def execute_playbook(operation_type, host_ip, logger=log) -> bool:
    bp_prefix = "/opt/ctdy/build_iso_server/src/app/bp/"
    b64random = bytes.decode(gen_random_base_64_str())
    host_file = f"{bp_prefix}ansible/hosts.{str(b64random)}"
    random_file = f"{bp_prefix}ansible/{operation_type}.yaml." + str(b64random)

    copyfile(f"{bp_prefix}ansible/{operation_type}.yaml", random_file)
    copyfile(bp_prefix + "ansible/hosts", host_file)
    ssh_pass_sk_raw = "RmExYzBuQEt5bGluMTAyMzYxCg=="
    ssh_pass_sk = base64.b64decode(bytes(ssh_pass_sk_raw, 'utf-8')).decode()
    with open(host_file, encoding="utf-8", mode="a") as f:
        f.write("\n" + host_ip + " ansible_ssh_user=root ansible_ssh_pass=\"" + ssh_pass_sk.strip() + "\"")
    out, err, rc = ansible_runner.run_command(
        executable_cmd='ansible-playbook',
        cmdline_args=[random_file, '-i', host_file, '--extra-vars', "ansible_become_pass=" + ssh_pass_sk],
        input_fd=sys.stdin,
        output_fd=sys.stdout,
        error_fd=sys.stderr
    )
    os.remove(random_file)
    os.remove(host_file)
    if rc == 0:
        logger.debug(f"Playbook执行成功:{out}. RC:{rc} ERR:{err}")
        return True
    else:
        logger.error(f"Playbook执行失败:{err}. RC:{rc}")
        return False


def hosts_restart(host_list, logger=log):
    oks, errs = [], []
    for host in host_list:
        ok = execute_playbook("restart", host.hostip)
        if ok:
            oks.append(host.hostip)
        else:
            errs.append(host.hostip)
            logger.error(f"重启主机失败: {host.hostip}")
    return oks, errs
