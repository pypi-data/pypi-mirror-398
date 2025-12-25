# -*- coding: UTF-8 -*-
"""host.py"""
import os

import logzero
import paramiko
from retry import retry

from kyutil.celery_util import get_active_task, get_active_queues


@retry(delay=0.5, tries=3)
def parse_host_info(host_msg, hosts_status, celery_app):
    """ parse_host_info(host_msg, hosts_status)"""
    active_queues = get_active_queues(celery_app)
    for item in host_msg:
        item['hosttask'] = "-1"
        item['hostload'] = '0.0, 0.0, 0.0'
        item['hostpid'] = '0'
        item['tasks'] = []
        item['queue'] = get_worker_queue(item['hostname'], active_queues) if active_queues else []
        for host in hosts_status:
            if host['hostname'] != item['hostname']:
                continue
            item['hostload'] = str(host['loadavg'])
            item['hostpid'] = str(host['pid'])
            if host['status'] is True:
                item['hosttask'] = '0'
            if host['active'] != 0:
                item['tasks'] = get_worker_tasks(item['hostname'], names=['long_task', 'mash_gather_task'], celery_app=celery_app)
            break
    return host_msg


def get_worker_queue(worker_name=None, active_queues=None) -> list:
    """
    获取节点的queue列表
    Args:
        active_queues:
        worker_name: 机器节点

    Returns:

    """
    r = []
    if not active_queues:
        return r
    for i in active_queues.get(worker_name, []):
        r.append(i['name'])
    return r


def get_worker_tasks(worker_name, names: list = None, celery_app=None):
    """
    获取工作节点的任务ID
    Args:
        worker_name: 机器节点
        names: 任务类型
        celery_app: app

    Returns:

    """
    if names is None:
        names = []
    active_task = get_active_task(celery_app)
    tasks = active_task[worker_name] \
        if active_task is not None and worker_name in active_task and active_task[worker_name] else []
    ret = []
    for i in tasks:
        for name in names:
            if str(i['type']).find(name) > 0:
                ret.append(i['id'])
                break
    return ret


class SshClient:
    """远程登录主机相关类"""

    def __init__(self, **kwargs):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.logger = kwargs.get("logger", logzero.logger)

    def login_client(self, host_ip, host_user, host_passwd, host_port=22):
        try:
            self.ssh.connect(hostname=host_ip, port=host_port, username=host_user, password=host_passwd)
        except Exception as e:
            self.logger.error(f"SSH 登录失败：{e} ， INFO： {host_user}@{host_ip}:{host_port} -P {host_passwd}")

    def _ssh_command(self, _cmd):
        _, stdout, _ = self.ssh.exec_command(_cmd)
        self.logger.error(stdout.read().decode('utf-8'))

    def _ssh_sftp_upload(self, local_abs_file: str, remote_abs_file: str):
        if not os.path.exists(local_abs_file):
            raise IOError(f"{local_abs_file} not exist")
        sftp = self.ssh.open_sftp()
        sftp.put(local_abs_file, remote_abs_file, callback=None, confirm=True)

    def _ssh_sftp_dir_upload(self, local_abs_file: str, remote_abs_file: str):
        """支持单层目录文件上传"""
        sftp = self.ssh.open_sftp()
        if os.path.isdir(local_abs_file):
            for i in os.listdir(local_abs_file):
                sftp.put(i, f"{remote_abs_file}/{i}", callback=None, confirm=True)
        else:
            raise IOError(f"{local_abs_file} not dirs")

    def _ssh_sftp_files_upload(self, local_remote_file: dict):
        """支持多组文件上传"""
        sftp = self.ssh.open_sftp()
        for i, v in local_remote_file.items():
            if not os.path.exists(i):
                raise IOError(f"{i} not exist")
            sftp.put(i, v)

    def build_client(self, **kwargs):
        """执行的文件、指令列表"""
        try:
            self._ssh_sftp_upload(kwargs.get("local_file"), kwargs.get("remote_file"))
            for i in kwargs.get("shell"):
                self._ssh_command(i)
        except Exception as e:
            self.logger.error(f"集成端创建失败  {e}")

    def close_client(self):
        self.ssh.close()
