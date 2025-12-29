# -*- coding: UTF-8 -*-
"""client project parameters init"""
import os
import platform

env = os.getenv("SERVER", "dev")  # ENV
# 仅针对linux系统
HOST_ARCH = platform.release().split('.')[-1]
HOST_DOMAIN = HOST_IP = os.getenv('HOST_DOMAIN') or os.getenv('IP', "localhost")
HOST_PORT = 7381
HOST_PORT_HTTPS = 7382

# http相关 /
HTTP = "http://"
HTTPS = "https://"
FILE_SCHEMA = 'file://'
HOST_ADDR = f"{HOST_DOMAIN}:{HOST_PORT}"
HOST_ADDR_HTTPS = f"{HOST_IP}:{HOST_PORT_HTTPS}"
HOST_HTTP = f"{HTTP}{HOST_ADDR}"
HOST_HTTPS = f"{HTTPS}{HOST_ADDR_HTTPS}"

BUILD_PATH = os.getenv("BUILD_PATH", "/mnt/iso_builder/isobuild/")
ROOT_PATH_ISO_PATH = "/opt/integration_iso_files/"
current_file = os.path.abspath(__file__)
SOURCE_PATH = f"{os.path.dirname(current_file)}/../../../client_agent/"
BUILD_PATH_LOGGER_FILE = BUILD_PATH + os.getenv("PREFIX_LOG", '') + "celery.log"

WORK_TOP_DIR = BUILD_PATH + os.sep + "pungi"
ROOT_PATH_TMP = BUILD_PATH + "tmp/"
DOWNLOAD_ROOT_PATH = BUILD_PATH + "downloaded" + os.sep

REPODATA_PATH = "/repodata/"

SIG_KEY = "7a486d9f"
LINE_QEMU_NET = "qemu qemu-net"


def file_http_mapping(_path):
    """
    将本地目录转为http地址
    Args:
        _path: BUILD_PATH/path/a/b/c

    Returns:
        HOST_HTTPS/a/b/c
    """
    if os.path.exists(_path) and BUILD_PATH in _path:
        return _path.replace(BUILD_PATH, HOST_HTTPS)
    else:
        raise FileNotFoundError(_path)


SENSITIVE_KEYWORDS = ["Red_Hat", "redhat", "rhel", "rhsm", "openEuler", ".oe1."]
APACHE_READ_MODEL = 0o777
PYTHON_MINOR_CMD = "python3 -c 'import sys;print(sys.version_info[1])'"
ALLOWED_STATUSES = ("STARTED", "FINISHED", "FINISHED_INCOMPLETE", "DOOMED")
