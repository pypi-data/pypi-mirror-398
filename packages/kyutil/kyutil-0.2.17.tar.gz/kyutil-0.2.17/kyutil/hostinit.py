# -*- coding: UTF-8 -*-
import base64
import os
import sys
import uuid
from shutil import copyfile

import ansible_runner

ENTRY_YML = "ansible/entry.yml."


def str_replace(filepath, orig, target):
    """
    对文件进行字符匹配替换
    Args:
        filepath:
        orig:
        target:

    Returns:

    """
    file_data = ""
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if orig in line:
                line = line.replace(orig, target)
            file_data += line
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(file_data)


def host_init(ip_addr, remote_user, remote_user_password, task, queue, host_type, server, ansible_root_path="/opt/ctdy/build_iso_server/src/app/utils/") -> int:
    """

    Args:
        ip_addr:                待执行的目标主机的 IP地址
        remote_user:            目标主机的用户名
        remote_user_password:   目标主机的密码（有root权限）或普通用户的sudo密码
        task:                   任务类型
        queue:                  队列类型
        host_type:              主机类型
        server:                 测试环境/正式环境
        ansible_root_path:

    Returns:

    """
    random_gen = uuid.uuid4().hex[:8]
    copyfile(ansible_root_path + "ansible/entry.yml", ansible_root_path + ENTRY_YML + str(random_gen))
    str_replace(ansible_root_path + ENTRY_YML + str(random_gen), "root", remote_user)
    str_replace(ansible_root_path + ENTRY_YML + str(random_gen), "REPLACE_SERVER", server)
    str_replace(ansible_root_path + ENTRY_YML + str(random_gen), "REPLACE_TASK", ",".join(task))
    str_replace(ansible_root_path + ENTRY_YML + str(random_gen), "REPLACE_HOSTTYPE", host_type)
    str_replace(ansible_root_path + ENTRY_YML + str(random_gen), "REPLACE_QUEUE", queue)
    copyfile(ansible_root_path + "ansible/hosts", ansible_root_path + "ansible/hosts." + str(random_gen))
    with open(ansible_root_path + "ansible/hosts." + str(random_gen), encoding="utf-8", mode="a") as f:
        msg = f'{ip_addr} ansible_ssh_user={remote_user} ansible_ssh_pass="{remote_user_password}"'
        f.write(msg)
    ssh_pass_sk_raw = "RmExYzBuQEt5bGluMTAyMzYxCg=="
    ssh_pass_sk = base64.b64decode(bytes(ssh_pass_sk_raw, 'utf-8')).decode()

    out, err, rc = ansible_runner.run_command(
        executable_cmd='ansible-playbook',
        cmdline_args=[ansible_root_path + ENTRY_YML + str(random_gen), '-i',
                      ansible_root_path + 'ansible/hosts.' + str(random_gen), '--extra-vars',
                      "ansible_become_pass=" + ssh_pass_sk],
        input_fd=sys.stdin,
        output_fd=sys.stdout,
        error_fd=sys.stderr
    )
    print("R C: {}".format(rc))
    print("OUT: {}".format(out))
    print("ERR: {}".format(err))

    os.remove(ansible_root_path + ENTRY_YML + str(random_gen))
    os.remove(ansible_root_path + 'ansible/hosts.' + str(random_gen))
    return rc

# host_init("10.44.34.91", "root", "qwer1234!@#$", "build", "el8_x86_64_task", "el8_x86_64", "199")
