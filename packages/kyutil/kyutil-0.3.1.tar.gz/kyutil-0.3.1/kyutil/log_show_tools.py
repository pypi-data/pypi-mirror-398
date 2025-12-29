#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""client log real-time return display module"""

import json
import os
import subprocess
import sys
import time

import cgi

WC_CMD = f"wc -l "
CUT_CMD = f" | cut -d \" \" -f 1 | tr -d '\n' 2>/dev/null"


def get_last_log_lines_from_pos(pos=1):
    """ get_last_log_lines_from_pos(pos)"""
    cmd = f"tail -n {pos} " + log_path
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, encoding='utf-8')
    log_file, _ = process.communicate()
    log_content = list(filter(None, log_file.split("\n")))
    return_dict["loglines"] = log_content

    return_dict["count"] = int(len(log_content))
    return_dict["pos"] = str(pos)
    return_dict["cmd"] = cmd
    return_json = json.dumps(return_dict, ensure_ascii=False)
    print(return_json)


def cmd_out(cmd):  # 解决调用os.popen执行带有中文的cmd命令乱码问题
    with os.popen(cmd) as fp:
        bf = fp._stream.buffer.read()
        try:
            result = bf.decode().strip()
        except UnicodeDecodeError:
            result = bf.decode('gbk').strip()
    return result


if __name__ == "__main__":
    form = cgi.FieldStorage()
    print("Access-Control-Allow-Origin: *")
    print("Access-Control-Allow-Method: *")
    print("Access-Control-Allow-Headers: Origin, x-requested-with, content-type, Authorization")
    print("Content-type:text/html\n\n")

    try:
        log_path = form.getvalue("path") or sys.args[1]
    except Exception as err:
        print(err)
        sys.exit(1)

    return_dict = {"count": "", "loglines": ""}
    return_json = ""

    if not os.path.isfile(str(log_path).strip()):
        print("日志文件不存在")
        for i in range(3):
            log_path_names = log_path.split("/")
            log_path_names[4] = str(str(log_path_names[4]) + str(i))
            log_path_names[6] = str(log_path_names[6].split(".")[0] + str(i) + ".log")
            new_path = "/".join(log_path_names)
            if os.path.exists(new_path):
                log_path = new_path
                file_exists = True

    if not os.path.exists(str(log_path)):
        return_dict["count"] = "-1"
        return_dict["loglines"] = log_path + "   1 日志文件不存在 " + str(os.path.isfile(log_path))
        print(json.dumps(return_dict))
        sys.exit(1)

    safety_max = 20
    time.sleep(0.2)
    num = 300
    get_last_log_lines_from_pos(100)
