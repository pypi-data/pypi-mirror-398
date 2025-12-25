#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：kyutil 
@File    ：iso_check.py
@IDE     ：PyCharm 
@Author  ：xuyong@kylinos.cn
@Date    ：2025/5/22 下午4:52 
@Desc    ：说明：ISO CHECK
"""
import glob
import json
import os
import re
import shutil
import subprocess

import xmltodict
from logzero import logger as log

from kyutil.reg_exp import KS_PACKAGES, KS_REPOS, LORAX_LOG_PKG, BUILD_LOG_STEP, BUILD_LOG_CMD
from kyutil.rpm_operation import get_nvr

BUILD_LOG_BLOG = "build-*.log"
ISOBUILD_LOG_BLOG = "isobuild-*.log"
HTML_PARSER = "html.parser"
ROOT_PATH_ISO_PATH = os.getenv("ISO_PATH") or "/opt/integration_iso_files/"


def get_sha256sum(path_file: str = None, path_file_sha256sum: str = None):
    """获取sha256sum
    Args:
        path_file: 如果存在此参数，计算此文件的sha256sum
        path_file_sha256sum: 如果存在此参数，从这个文件中获取已经计算完成的sha256sum
    """
    if path_file_sha256sum and os.path.isfile(path_file_sha256sum):
        return open(path_file_sha256sum, encoding="utf-8").read().split(" ")[0]
    elif path_file and os.path.isfile(path_file):
        import hashlib
        with open(path_file, "rb") as f:
            sha256obj = hashlib.sha256()
            sha256obj.update(f.read())
            hash_value = sha256obj.hexdigest()
            return hash_value
    else:
        return ""


def get_line_list_from_file(path2file):
    try:
        with open(path2file, "r", encoding="utf-8") as f:
            return f.read().split('\n')
    except Exception as e:
        log.error(e)
        return []


def remove_blank_from_list(list_candidate):
    while "" in list_candidate:
        list_candidate.remove("")
    return list_candidate


def read_json_file(path_json):
    """从json文件中读取数据"""
    try:
        with open(path_json) as f_json:
            return json.load(f_json)
    except Exception:
        return {}


def xml2dict(xml_content):
    return xmltodict.parse(xml_content)


def get_package_name(package_name):
    return [get_nvr(x)[0] for x in package_name]


def get_diff(var_1, var_2, head=""):
    """对比两个变量的不同
    Args:
        var_1:变量1（自己）
        var_2:变量2（其他）
        head:提示信息头
    变量可能的类型：【dict|list(set)|str|int|float|None】
    """
    diff_report = []
    if type(var_1) is not type(var_2):
        diff_report.append(f"{head} (值类型不同)：{str(var_1)}({type(var_1)}) 和 {str(var_2)}({type(var_2)})")
    elif isinstance(var_1, dict):
        keys_1, keys_2 = set(var_1.keys()), set(var_2.keys())
        diff_report.append(f"{head} (多出参数)：{str(keys_1 - keys_2)}")
        diff_report.append(f"{head} (缺少参数)：{str(keys_2 - keys_1)}")
        for key in keys_1 & keys_2:
            diff_report.extend(get_diff(var_1[key], var_2[key], f"{head} -> {str(key)}"))
    elif type(var_1) in [list, set]:  # 若列表中的变量不同，不再深入查找，直接返回不同
        diff_report.append(f"{head} (多出参数)：{str(set(get_package_name(var_1)) - set(get_package_name(var_2)))}")
        diff_report.append(f"{head} (缺少参数)：{str(set(get_package_name(var_2)) - set(get_package_name(var_1)))}")
        diff_report.append(f"{head} (集成版本变动)：{str(set(var_2) - set(var_1))}")
    elif var_1 is None or type(var_1) in [str, int, float]:
        if var_1 != var_2:
            diff_report.append(f"{head} (值不同)：{str(var_1)} 和 {str(var_2)}")
    else:
        diff_report.append(f"{head} (未识别类型)：{str(var_1)}({type(var_1)}) 和 {str(var_2)}({type(var_2)})")
    return diff_report


def parse_ks(ks_content):
    """解析KS文件：
        获取ks_content里面的 --xxx=yyy  --> xxx: yyy
        获取ks_content里面的 %packages\npkg_1\npkg_2\n%end  --> packages: [pkg_1, pkg_2]
    """
    ks_info = dict(re.findall(KS_REPOS, ks_content))
    packages_str = re.findall(KS_PACKAGES, ks_content, re.DOTALL)
    packages = [p for p_str in packages_str for p in p_str.split('\n')]
    packages = remove_blank_from_list(set(packages))
    ks_info.update({"packages": packages})
    return ks_info


class LogParse:
    def __init__(self, log_content):
        """解析日志
        Args:
            log_content: 日志的内容，如果传入的是字符串，转成列表
        """
        self._log_content = log_content
        if isinstance(self._log_content, str):
            self._log_content = self._log_content.split('\n')
        if not isinstance(self._log_content, list):
            raise KeyError(f"参数类型无法解析: {type(self._log_content)}")

    @property
    def log_list(self):
        return self._log_content

    def remove_datetime(self, _log_content, pattern=r"^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d+\s+"):
        """去除每行开头的日期和时间"""
        return [re.sub(pattern, "", log_line) for log_line in self._log_content]

    def ignore_level(self, level="DEBUG"):
        """根据当前等级忽略部分等级，如level为INFO时忽略DEBUG
        Args:
            level:解析的等级，可选参数（DEBUG < INFO < WARNING < ERROR < CRITICAL）：
                    1. DEBUG：返回所有
                    2. INFO：返回 INFO、WARNING、ERROR、CRITICAL
                    3. WARNING：返回 WARNING、ERROR、CRITICAL
                    4. ERROR：返回 ERROR、CRITICAL
                    5. CRITICAL：返回 CRITICAL
        """
        level_ignore_list = {"DEBUG": [], "INFO": ["DEBUG"], "WARNING": ["DEBUG", "INFO"],
                             "ERROR": ["DEBUG", "INFO", "WARNING"], "CRITICAL": ["DEBUG", "INFO", "WARNING", "ERROR"]}
        _log_content = self.remove_datetime(self._log_content)
        for level in level_ignore_list.get(level, []):
            _log_content = [log_line for log_line in self._log_content if not log_line.startswith(level)]
        return _log_content

    def merge_multi_line(self, pattern=r"\[\w\s+\d+\s+\d{2}:\d{2}:\d{2}\s+\w+:\d+\]", is_update=False):
        """合并被多行打印的一行日志
        Args:
            pattern:
            is_update:是否将修改应用到日志上
        """
        if len(self._log_content) == 0:
            return self._log_content
        _log_content_new = []
        line_last = self._log_content[0]
        for line_cur in self._log_content[1:]:
            if re.match(pattern, line_cur):
                _log_content_new.append(line_last)
                line_last = line_cur
            else:
                line_last += "\n" + line_cur
        if line_last != "":
            _log_content_new.append(line_last)
        if is_update:
            self._log_content = _log_content_new
        return _log_content_new


class IsoCheck:

    def __init__(self, _logger=log):
        self._logger = _logger

    @staticmethod
    def check_c_002(iso_info, *args, **kwargs) -> dict:
        """ISO哈希值校验文件检查
            检查ISO哈希值是否与 ISO名称.sha256sum文件中内容是否一致
        """
        root_dir = iso_info.get("root_dir")
        path_iso = str(os.path.join(root_dir, iso_info.get("isoname").lstrip('/')))
        path_iso_sha256sum = path_iso + ".sha256sum"
        if os.path.exists(path_iso) and os.path.exists(path_iso_sha256sum):
            iso_sha256sum_calc = get_sha256sum(path_file=path_iso)
            iso_sha256sum_get = get_sha256sum(path_file_sha256sum=path_iso_sha256sum)
            if iso_sha256sum_calc == iso_sha256sum_get:
                return {
                    "msg": "已记录的sha256sum与ISO的sha256sum值一致",
                    "code": 0,
                    "data": {"iso_sha256sum_calc": iso_sha256sum_calc, "iso_sha256sum_get": iso_sha256sum_get}
                }
            else:
                return {
                    "msg": "已记录的sha256sum与ISO的sha256sum值不一致",
                    "code": 40012,
                    "data": {"iso_sha256sum_calc": iso_sha256sum_calc, "iso_sha256sum_get": iso_sha256sum_get}
                }
        elif os.path.exists(path_iso):
            iso_sha256sum_calc = get_sha256sum(path_file=path_iso)
            return {
                "msg": f"缺少文件：{path_iso_sha256sum}",
                "code": 40001,
                "data": {"iso_sha256sum_calc": iso_sha256sum_calc}
            }
        elif os.path.exists(path_iso_sha256sum):
            iso_sha256sum_get = get_sha256sum(path_file_sha256sum=path_iso_sha256sum)
            return {
                "msg": f"缺少文件：{path_iso}",
                "code": 40001,
                "data": {"iso_sha256sum_get": iso_sha256sum_get}
            }
        else:
            return {
                "msg": f"缺少文件：{path_iso} 和 {path_iso_sha256sum}",
                "code": 40001,
                "data": {}
            }

    @staticmethod
    def check_c_007(iso_info, *args, **kwargs) -> dict:
        """ISO光盘软件包列表与黑名单文件检查
            光盘挂载到目录后，对比软件包列表中是否存在黑名单所列出的软件包（研发提供黑名单参考，测试补充）
        """
        path_iso_file_list_candidate = glob.glob(os.path.join(iso_info.get("work_dir"), "*-packages.txt"))
        if len(path_iso_file_list_candidate) > 1:
            return {
                "msg": f"ISO软件包列表文件个数不等于1（{len(path_iso_file_list_candidate)}）",
                "code": 40001,
                "data": {"path_iso_file_list_candidate": path_iso_file_list_candidate}
            }
        elif len(path_iso_file_list_candidate) == 0:
            return {
                "msg": "ISO软件包列表文件不存在",
                "code": 40001,
                "data": {"path_iso_file_list_candidate": path_iso_file_list_candidate}
            }
        pkg_file_list = remove_blank_from_list(get_line_list_from_file(path_iso_file_list_candidate[0]))
        black_file_list = []
        path_black_file_list_candidate = glob.glob(os.path.join(iso_info.get("work_dir"), "conf/*-black.txt"))
        path_black_file_list_candidate += glob.glob(os.path.join(iso_info.get("work_dir"), "conf/black_*.txt"))
        for path_black_file_list in path_black_file_list_candidate:
            black_file_list += get_line_list_from_file(path_black_file_list)
        black_file_list_set = set(remove_blank_from_list(black_file_list))
        map_n2pkg = {}
        for pkg_fullname in pkg_file_list:
            *n, _, _ = pkg_fullname.split('-')
            pkg_name = '-'.join(n)
            if pkg_name not in black_file_list_set:
                continue
            if pkg_name in map_n2pkg:
                map_n2pkg[pkg_name].append(pkg_fullname)
            else:
                map_n2pkg[pkg_name] = [pkg_fullname]
        pkg_name_set = set(map_n2pkg.keys())
        if len(pkg_name_set) == 0:
            return {
                "msg": "ISO光盘中没有软件包在黑名单列表中",
                "code": 0,
                "data": {
                    # "pkg_file_list": pkg_file_list,  # TODO 若需要显示所有的软件包列表，解开注释
                    # "black_file_list": black_file_list,
                    "pkg_file_list_black": []
                }
            }
        else:
            pkg_file_list_black = [pkg for pkg_list in map_n2pkg.values() for pkg in pkg_list]
            return {
                "msg": "ISO光盘中有软件包在黑名单列表中",
                "code": 40013,
                "data": {
                    # "pkg_file_list": pkg_file_list,
                    # "black_file_list": black_file_list,
                    "pkg_file_list_black": pkg_file_list_black
                }
            }

    @staticmethod
    def check_c_089(iso_info, iso_info_other, *args, **kwargs) -> dict:
        """集成配置文件检查
            对比 cfg.json（conf/conf.json）
        """
        config_filename = "conf.json"
        path_json_file_1 = os.path.join(iso_info.get("work_dir"), "conf", config_filename)
        if iso_info_other is None:  # 如果iso_info_other未传入，则仅判断文件是否存在
            return {"msg": "集成配置文件存在（无对比目标）", "code": 0, "data": {}}
        if not os.path.exists(path_json_file_1):
            return {"msg": "当前ISO集成配置文件不存在", "code": 40001, "data": {}}
        path_json_file_2 = os.path.join(iso_info_other.get("work_dir") if iso_info_other else "", "conf", config_filename)
        if not os.path.exists(path_json_file_2):
            return {"msg": "对比ISO集成配置文件不存在", "code": 40001, "data": {}}
        cfg_json_1 = read_json_file(path_json_file_1)
        if len(cfg_json_1) == 0:
            return {"msg": "当前ISO集成配置文件读取失败或为空", "code": 40012, "data": {}}
        cfg_json_2 = read_json_file(path_json_file_2)
        if len(cfg_json_2) == 0:
            return {"msg": "对比ISO集成配置文件读取失败或为空", "code": 40012, "data": {}}
        diff_content = get_diff(cfg_json_1, cfg_json_2, config_filename)
        if len(diff_content) == 0:
            return {"msg": "集成配置文件不存在差异", "code": 0, "data": ""}
        return {"msg": "集成配置文件存在差异", "code": 40013, "data": '\n'.join(diff_content)}

    @staticmethod
    def check_c_090(iso_info, iso_info_other=None, *args, **kwargs):
        comps_file_list = glob.glob(os.path.join(iso_info.get("work_dir"), "conf", "*-comps.xml"))
        comps_file_list += glob.glob(os.path.join(iso_info.get("work_dir"), "conf", "comps-*.xml"))
        if len(comps_file_list) > 1:
            return {"msg": f"当前配置目录中存在多个comps文件：{str(comps_file_list)}", "code": 40008, "data": {}}
        elif len(comps_file_list) == 0:
            return {"msg": "当前配置目录中comps文件不存在", "code": 40001, "data": {}}
        else:
            path_comps_file_1 = comps_file_list[0]
        if iso_info_other is None:  # 如果iso_info_other未传入，则仅判断文件是否存在
            return {"msg": "comps文件存在（无对比目标）", "code": 0, "data": {}}
        comps_file_list_other = glob.glob(os.path.join(iso_info_other.get("work_dir"), "conf", "*-comps.xml"))
        comps_file_list_other += glob.glob(os.path.join(iso_info_other.get("work_dir"), "conf", "comps-*.xml"))
        if len(comps_file_list_other) > 1:
            return {"msg": f"对比配置目录存在多个comps文件：{str(comps_file_list_other)}", "code": 40008, "data": {}}
        elif len(comps_file_list_other) == 0:
            return {"msg": "对比配置目录中comps文件不存在", "code": 40001, "data": {}}
        else:
            path_comps_file_2 = comps_file_list_other[0]
        comps_content_1 = '\n'.join(get_line_list_from_file(path_comps_file_1))
        comps_content_2 = '\n'.join(get_line_list_from_file(path_comps_file_2))
        comps_json_1, comps_json_2 = xml2dict(comps_content_1), xml2dict(comps_content_2)
        diff_content = get_diff(comps_json_1, comps_json_2, "comps")
        if len(diff_content) == 0:
            return {"msg": "comps文件不存在差异", "code": 0, "data": ""}
        return {"msg": "comps文件存在差异", "code": 40013, "data": '\n'.join(diff_content)}

    @staticmethod
    def check_c_091(iso_info, iso_info_other=None, *args, **kwargs) -> dict:
        """安装文件（ks文件）检查
            对比ks文件
        """
        ks_file_list = glob.glob(os.path.join(iso_info.get("work_dir"), "conf", "*.ks"))
        if len(ks_file_list) > 1:
            return {"msg": f"当前配置目录中存在多个KS文件：{str(ks_file_list)}", "code": 40008, "data": {}}
        elif len(ks_file_list) == 0:
            return {"msg": "当前配置目录中KS文件不存在", "code": 40001, "data": {}}
        else:
            path_ks_file_1 = ks_file_list[0]
        if iso_info_other is None:  # 如果iso_info_other未传入，则仅判断文件是否存在
            return {"msg": "安装文件（ks文件）存在（无对比目标）", "code": 0, "data": {}}
        ks_file_list_other = glob.glob(os.path.join(iso_info_other.get("work_dir"), "conf", "*.ks"))
        if len(ks_file_list_other) > 1:
            return {"msg": "对比配置目录存在多个KS文件：{str(ks_file_list_other)}", "code": 40008, "data": {}}
        elif len(ks_file_list_other) == 0:
            return {"msg": "对比配置目录中KS文件不存在", "code": 40001, "data": {}}
        else:
            path_ks_file_2 = ks_file_list_other[0]

        ks_content_1 = '\n'.join(get_line_list_from_file(path_ks_file_1))
        ks_content_2 = '\n'.join(get_line_list_from_file(path_ks_file_2))
        ks_info_1, ks_info_2 = parse_ks(ks_content_1), parse_ks(ks_content_2)
        diff_content = get_diff(ks_info_1, ks_info_2, "KS")
        if len(diff_content) == 0:
            return {"msg": "安装文件（ks文件）不存在差异", "code": 0, "data": ""}
        return {"msg": "安装文件（ks文件）存在差异", "code": 40013, "data": '\n'.join(diff_content)}

    @staticmethod
    def check_c_092(iso_info, iso_info_other=None, *args, **kwargs) -> dict:
        """黑名单文件检查
            对比黑名单文件
        """
        black_file_list = glob.glob(os.path.join(iso_info.get("work_dir"), "conf", "*-black.txt"))
        black_file_list += glob.glob(os.path.join(iso_info.get("work_dir"), "conf", "black_*.txt"))
        if len(black_file_list) > 1:
            return {"msg": f"当前配置目录中存在多个黑名单文件：{str(black_file_list)}", "code": 40008,
                    "data": {"file_list": black_file_list}}
        elif len(black_file_list) == 0:
            return {"msg": "当前配置目录中黑名单文件不存在", "code": 40001, "data": {}}
        else:
            path_black_file_1 = black_file_list[0]
        if iso_info_other is None:  # 如果iso_info_other未传入，则仅判断文件是否存在
            return {"msg": "黑名单文件存在（无对比目标）", "code": 0, "data": {}}
        black_file_list_other = glob.glob(os.path.join(iso_info_other.get("work_dir"), "conf", "*-black.txt"))
        black_file_list_other += glob.glob(os.path.join(iso_info_other.get("work_dir"), "conf", "black_*.txt"))
        if len(black_file_list_other) > 1:
            return {"msg": f"对比配置目录存在多个黑名单文件：{str(black_file_list_other)}", "code": 40008,
                    "data": {"file_list": black_file_list_other}}
        elif len(black_file_list_other) == 0:
            return {"msg": "对比配置目录中黑名单文件不存在", "code": 40001, "data": {}}
        else:
            path_black_file_2 = black_file_list_other[0]

        black_rpm_list_1 = set(get_line_list_from_file(path_black_file_1))
        black_rpm_list_2 = set(get_line_list_from_file(path_black_file_2))
        diff_content = get_diff(black_rpm_list_1, black_rpm_list_2, "black")
        if len(diff_content) == 0:
            return {"msg": "黑名单文件不存在差异", "code": 0, "data": ""}
        return {"msg": "黑名单文件存在差异", "code": 40013, "data": '\n'.join(diff_content)}

    @staticmethod
    def check_c_093(iso_info, iso_info_other=None, *args, **kwargs) -> dict:
        """集成构建lorax日志文件检查（做启动镜像的步骤日志文件检查）
            比对集成构建lorax日志文件
        """
        file_list = glob.glob(os.path.join(iso_info.get("work_dir"), "logs", "lorax", "lorax.log"))
        if len(file_list) > 1:
            return {"msg": f"当前目录中存在多个lorax日志文件：{str(file_list)}", "code": 40008,
                    "data": {"file_list": file_list}}
        elif len(file_list) == 0:
            return {"msg": "当前目录中lorax日志文件不存在", "code": 40001, "data": {}}
        else:
            path_file_1 = file_list[0]
        if iso_info_other is None:  # 如果iso_info_other未传入，则仅判断文件是否存在
            return {"msg": "lorax日志文件存在（无对比目标）", "code": 0, "data": {}}
        file_list_other = glob.glob(os.path.join(iso_info_other.get("work_dir"), "logs", "lorax", "lorax.log"))
        if len(file_list_other) > 1:
            return {"msg": f"对比目录存在多个lorax日志文件：{str(file_list_other)}", "code": 40008,
                    "data": {"file_list": file_list_other}}
        elif len(file_list_other) == 0:
            return {"msg": "对比目录中lorax日志文件不存在", "code": 40001, "data": {}}
        else:
            path_file_2 = file_list_other[0]

        def get_pkg(log_content):
            return re.findall(LORAX_LOG_PKG, log_content)

        pkg_list_1 = get_pkg('\n'.join(get_line_list_from_file(path_file_1)))
        pkg_list_2 = get_pkg('\n'.join(get_line_list_from_file(path_file_2)))
        diff_content = get_diff(pkg_list_1, pkg_list_2, "lorax")
        if len(diff_content) == 0:
            return {"msg": "lorax日志文件不存在差异", "code": 0, "data": ""}
        return {"msg": "lorax日志文件存在差异", "code": 40013, "data": '\n'.join(diff_content)}

    @staticmethod
    def check_c_094(iso_info, iso_info_other=None, *args, **kwargs) -> dict:
        """集成构建日志文件检查（所有阶段的汇总日志文件检查）
            比对集成构建日志文件
        """
        file_list = glob.glob(os.path.join(iso_info.get("work_dir"), "logs", ISOBUILD_LOG_BLOG))
        file_list += glob.glob(os.path.join(iso_info.get("work_dir"), "logs", BUILD_LOG_BLOG))
        if len(file_list) > 1:
            return {"msg": f"当前目录中存在多个日志文件：{str(file_list)}", "code": 40008,
                    "data": {"file_list": file_list}}
        elif len(file_list) == 0:
            return {"msg": "当前目录中日志文件不存在", "code": 40001, "data": {}}
        else:
            path_file_1 = file_list[0]
        if not iso_info_other:  # 如果iso_info_other未传入，则仅判断文件是否存在
            return {"msg": "日志文件存在（无对比目标）", "code": 0, "data": {}}
        file_list_other = glob.glob(os.path.join(iso_info_other.get("work_dir"), "logs", ISOBUILD_LOG_BLOG))
        file_list_other += glob.glob(os.path.join(iso_info_other.get("work_dir"), "logs", BUILD_LOG_BLOG))
        if len(file_list_other) > 1:
            return {"msg": f"对比目录存在多个日志文件：{str(file_list_other)}", "code": 40008,
                    "data": {"file_list": file_list_other}}
        elif len(file_list_other) == 0:
            return {"msg": "对比目录中日志文件不存在", "code": 40001, "data": {}}
        else:
            path_file_2 = file_list_other[0]

        def get_cmd(log_content):
            return re.findall(BUILD_LOG_CMD, log_content, re.DOTALL)

        log_obj_1 = LogParse(get_line_list_from_file(path_file_1))
        log_obj_2 = LogParse(get_line_list_from_file(path_file_2))
        log_obj_1.merge_multi_line(is_update=True)
        log_obj_2.merge_multi_line(is_update=True)
        cmd_list_1 = [cmd for log_line in log_obj_1.log_list for cmd in get_cmd(log_line)]
        cmd_list_2 = [cmd for log_line in log_obj_2.log_list for cmd in get_cmd(log_line)]
        random_str_1 = os.path.basename(os.path.dirname(os.path.abspath(iso_info.get("work_dir"))))
        random_str_2 = os.path.basename(os.path.dirname(os.path.abspath(iso_info_other.get("work_dir"))))
        cmd_list_1 = [cmd.replace(random_str_1, "xxxx") for cmd in cmd_list_1]  # 屏蔽两个随机字符串造成的差异
        cmd_list_2 = [cmd.replace(random_str_2, "xxxx") for cmd in cmd_list_2]
        diff_content = get_diff(cmd_list_1, cmd_list_2, "集成日志")
        if len(diff_content) == 0:
            return {"msg": "日志文件不存在差异", "code": 0, "data": ""}
        return {"msg": "日志文件存在差异", "code": 40013, "data": '\n'.join(diff_content)}

    @staticmethod
    def check_c_095(iso_info, iso_info_other=None, *args, **kwargs) -> dict:
        """集成构建pungi日志文件检查（做镜像源的步骤日志文件检查）
            比对集成构建pungi日志文件
        """
        file_list = glob.glob(os.path.join(iso_info.get("work_dir"), "logs", ISOBUILD_LOG_BLOG))
        file_list += glob.glob(os.path.join(iso_info.get("work_dir"), "logs", BUILD_LOG_BLOG))
        if len(file_list) > 1:
            return {"msg": f"当前目录中存在多个pungi日志文件：{str(file_list)}", "code": 40008,
                    "data": {"file_list": file_list}}
        elif len(file_list) == 0:
            return {"msg": "当前目录中pungi日志文件不存在", "code": 40001, "data": {}}
        else:
            path_file_1 = file_list[0]
        if iso_info_other is None:  # 如果iso_info_other未传入，则仅判断文件是否存在
            return {"msg": "pungi日志文件存在（无对比目标）", "code": 0, "data": {}}
        file_list_other = glob.glob(os.path.join(iso_info_other.get("work_dir"), "logs", ISOBUILD_LOG_BLOG))
        file_list_other += glob.glob(os.path.join(iso_info_other.get("work_dir"), "logs", BUILD_LOG_BLOG))
        if len(file_list_other) > 1:
            return {"msg": f"对比目录存在多个pungi日志文件：{str(file_list_other)}", "code": 40008,
                    "data": {"file_list": file_list_other}}
        elif len(file_list_other) == 0:
            return {"msg": "对比目录中pungi日志文件不存在", "code": 40001, "data": {}}
        else:
            path_file_2 = file_list_other[0]

        def get_step(log_content):
            return re.findall(BUILD_LOG_STEP, log_content, re.DOTALL)

        log_obj_1 = LogParse(get_line_list_from_file(path_file_1))
        log_obj_2 = LogParse(get_line_list_from_file(path_file_2))
        log_obj_1.merge_multi_line(is_update=True)
        log_obj_2.merge_multi_line(is_update=True)
        step_list_1 = [step for log_line in log_obj_1.log_list for step in get_step(log_line)]
        step_list_2 = [step for log_line in log_obj_2.log_list for step in get_step(log_line)]
        if len(step_list_1) == len(step_list_2):
            return {"msg": f"pungi日志Step个数一致: {len(step_list_1)} ", "code": 0, "data": {}}
        return {"msg": f"pungi日志Step个数不一致: {len(step_list_1)} - {len(step_list_2)}", "code": 40013, "data": {}}

    @staticmethod
    def check_c_096(iso_info, *args, **kwargs) -> dict:
        """需求文档检查
            检查是否存在需求文档文件
        """
        file_list = glob.glob(os.path.join(iso_info.get("work_dir"), "*需求*"))
        if len(file_list) > 1:
            return {"msg": f"当前目录中存在多个需求文档：{str(file_list)}", "code": 0,
                    "data": {"file_list": file_list}}
        elif len(file_list) == 0:
            return {"msg": "当前目录中不存在需求文档", "code": 40001, "data": {}}
        else:
            return {"msg": "需求文档存在", "code": 0, "data": ""}

    @staticmethod
    def check_c_097(iso_info, iso_info_other=None, *args, **kwargs) -> dict:
        """集成记录表检查
            对比集成记录表文件是否存在且一致
        """
        file_list = glob.glob(os.path.join(iso_info.get("work_dir"), "*集成记录表*"))
        if len(file_list) > 1:
            return {"msg": f"当前目录中存在多个集成记录表：{str(file_list)}", "code": 40008,
                    "data": {"file_list": file_list}}
        elif len(file_list) == 0:
            return {"msg": "当前目录中集成记录表不存在", "code": 40001, "data": {}}
        if iso_info_other is None:  # 如果iso_info_other未传入，则仅判断文件是否存在
            return {"msg": "集成记录表存在（无对比目标）", "code": 0, "data": {}}
        file_list_other = glob.glob(os.path.join(iso_info_other.get("work_dir"), "*集成记录表*"))
        if len(file_list_other) > 1:
            return {"msg": f"对比目录存在多个集成记录表：{str(file_list_other)}", "code": 40008,
                    "data": {"file_list": file_list_other}}
        elif len(file_list_other) == 0:
            return {"msg": "对比目录中集成记录表不存在", "code": 40001, "data": {}}
        else:
            _ = file_list_other[0]
        return {"msg": "集成记录表存在（有对比目标）", "code": 0, "data": {}}

    @staticmethod
    def check_c_098(iso_info, iso_info_other=None, *args, **kwargs) -> dict:
        """集成工作单检查
            对比集成工作单文件是否存在且一致
        """
        file_list = glob.glob(os.path.join(iso_info.get("work_dir"), "*集成工作单*"))
        if len(file_list) > 1:
            return {"msg": f"当前目录中存在多个集成工作单：{str(file_list)}", "code": 40008,
                    "data": {"file_list": file_list}}
        elif len(file_list) == 0:
            return {"msg": "当前目录中集成工作单不存在", "code": 40001, "data": {}}
        if iso_info_other is None:  # 如果iso_info_other未传入，则仅判断文件是否存在
            return {"msg": "集成工作单存在（无对比目标）", "code": 0, "data": {}}
        file_list_other = glob.glob(os.path.join(iso_info_other.get("work_dir"), "*集成工作单*"))
        if len(file_list_other) > 1:
            return {"msg": f"对比目录存在多个集成工作单：{str(file_list_other)}", "code": 40008,
                    "data": {"file_list": file_list_other}}
        elif len(file_list_other) == 0:
            return {"msg": "对比目录中集成工作单不存在", "code": 40001, "data": {}}
        else:
            _ = file_list_other[0]
        return {"msg": "集成工作单存在（有对比目标）", "code": 0, "data": {}}

    @staticmethod
    def check_c_099(iso_info, iso_info_other=None, *args, **kwargs) -> dict:
        """ISO测试报告
            查看测试报告文件是否存在
            打开测试报告文件查看
            比对ISO安装测试项结果
        """
        file_list = glob.glob(os.path.join(iso_info.get("work_dir"), "*report*"))
        if len(file_list) > 1:
            return {"msg": f"当前目录中存在多个ISO测试报告：{str(file_list)}", "code": 40008,
                    "data": {"file_list": file_list}}
        elif len(file_list) == 0:
            return {"msg": "当前目录中ISO测试报告不存在", "code": 40001, "data": {}}
        if iso_info_other is None:  # 如果iso_info_other未传入，则仅判断文件是否存在
            return {"msg": "ISO测试报告存在（无对比目标）", "code": 0, "data": {}}
        file_list_other = glob.glob(os.path.join(iso_info_other.get("work_dir"), "*report*"))
        if len(file_list_other) > 1:
            return {"msg": f"对比目录存在多个ISO测试报告：{str(file_list_other)}", "code": 40008,
                    "data": {"file_list": file_list_other}}
        elif len(file_list_other) == 0:
            return {"msg": "对比目录中ISO测试报告不存在", "code": 40001, "data": {}}
        else:
            _ = file_list_other[0]
        return {"msg": "ISO测试报告存在（有对比目标）", "code": 0, "data": {}}

    @staticmethod
    def gen_excel(material_info: dict, save_path: str):
        path_template = os.path.abspath(os.path.join(os.getcwd(), "..")) \
                        + '/src/app/templates/ServerISOSelfCheckReportSample.xlsx'
        from kyutil.kyexcel import ExcelObj
        eo = ExcelObj(excel_template=path_template)
        sheet_name = "模板"
        map_position = {num: {
            "is_pass": f"H{int(num.split('-')[1]) + 1}",
            "notes": f"I{int(num.split('-')[1]) + 1}",
        } for num in material_info.keys() if len(num.split('-')) == 2}
        for check_num, check_res in material_info.items():
            if len(check_num.split('-')) != 2:
                continue
            eo.set_sheet_cell_value(sheet_name=sheet_name, position=map_position.get(check_num, {}).get("is_pass", ""),
                                    value={0: "是"}.get(check_res.get("code"), "否"))
            eo.set_color_background(sheet_name=sheet_name, position=map_position.get(check_num, {}).get("is_pass", ""),
                                    color={0: "70ff7f"}.get(check_res.get("code"), "ff7f67"))
            eo.set_sheet_cell_value(sheet_name=sheet_name, position=map_position.get(check_num, {}).get("notes", ""),
                                    value=check_res.get("msg", ""))
        eo.save(save_path)

    def check_c_100(self, iso_info, *args, **kwargs) -> dict:
        """ISO比对报告
            对比软件包变化
            对比文件列表变化
            对比文件内容变化
        """
        file_list = glob.glob(os.path.join(iso_info.get("work_dir"), "*self-check-report*"))
        if kwargs.get("rebuild"):
            for file_path in file_list:
                self._logger.info(f"移除自检报告：{str(file_path)}")
                shutil.move(file_path, "/dev/null")
            file_list = glob.glob(os.path.join(iso_info.get("work_dir"), "*self-check-report*"))
        if len(file_list) > 1:
            return {"msg": f"当前目录中存在多个ISO自检报告：{str(file_list)}", "code": 40008,
                    "data": {"file_list": file_list}}
        elif len(file_list) == 0:
            try:
                material_info = kwargs.get("material_info", {})
                material_info["C-100"] = {"msg": "当前目录中ISO自检报告不存在(已重新生成)", "code": 0, "data": {}}
                self._logger.info(str(material_info.keys()))
                self.gen_excel(material_info, save_path=os.path.join(iso_info.get("work_dir"), "self-check-report"))
                return {"msg": "当前目录中ISO自检报告不存在(已重新生成)", "code": 0, "data": {}}
            except Exception as e:
                self._logger.error(f"生成ISO自检报告失败，原因{str(e)}")
                return {"msg": "当前目录中ISO自检报告不存在", "code": 40001, "data": {}}
        else:
            return {"msg": "ISO自检报告存在（有对比目标）", "code": 0, "data": {}}

    def get_lorax_templates_file(self, conf_dir):
        black_file_list = glob.glob(os.path.join(conf_dir, "lorax-templates-*.rpm"))
        black_file_list += glob.glob(os.path.join(conf_dir, "pungi-*.rpm"))
        if len(black_file_list) > 1:
            return {"msg": f"当前配置目录中存在多个lorax-template文件：{str(black_file_list)}", "code": 40008,
                    "data": {"file_list": black_file_list}}
        elif len(black_file_list) == 0:
            return {"msg": "当前配置目录中lorax-template文件不存在", "code": 40001, "data": {}}
        else:
            return black_file_list[0]

    def get_kylin_release_file(self, conf_dir):
        black_file_list = glob.glob(os.path.join(conf_dir, "*kylin-release-*.rpm"))
        if len(black_file_list) > 1:
            return {"msg": f"当前配置目录中存在多个kylin-release文件：{str(black_file_list)}", "code": 40008,
                    "data": {"file_list": black_file_list}}
        elif len(black_file_list) == 0:
            return {"msg": "当前配置目录中kylin-release文件不存在", "code": 40001, "data": {}}
        else:
            return black_file_list[0]

    def check_c_101(self, iso_info, iso_info_other=None, *args, **kwargs):
        """
        lorax-template文件检查/对比lorax-template文件
        Args:
            iso_info:
            iso_info_other:

        Returns:

        """
        path_black_file_1 = self.get_lorax_templates_file(os.path.join(iso_info.get("work_dir"), "conf"))
        if isinstance(path_black_file_1, dict):
            return path_black_file_1
        if not iso_info_other:
            return {"msg": "黑名单存在（无对比目标）", "code": 0, "data": {}}
        path_black_file_2 = self.get_lorax_templates_file(os.path.join(iso_info_other.get("work_dir", ""), "conf"))
        if isinstance(path_black_file_2, dict):
            return path_black_file_2
        if not os.path.exists(path_black_file_2):  # 如果iso_info_other未传入，则仅判断文件是否存在
            return {"msg": "基线lorax-templates文件不存在（无对比目标）", "code": 0, "data": {}}
        sha1 = get_sha256sum(path_black_file_1)
        sha2 = get_sha256sum(path_black_file_2)
        if sha1 and sha2 and sha2 == sha1:
            return {"msg": "黑名单文件不存在差异", "code": 0, "data": ""}
        else:
            return {"msg": "黑名单文件存在差异", "code": 40013, "data": '\n'.join([f"{path_black_file_1}:{sha1}", f"{path_black_file_2}:{sha2}"])}

    def check_c_102(self, iso_info, iso_info_other=None, *args, **kwargs):
        """
        kylin-release文件检查/对比该文件
        Args:
            iso_info:
            iso_info_other:

        Returns:

        """
        path_black_file_1 = self.get_kylin_release_file(os.path.join(iso_info.get("work_dir"), "conf"))
        if isinstance(path_black_file_1, dict):
            return path_black_file_1
        if not iso_info_other:  # 如果iso_info_other未传入，则仅判断文件是否存在
            return {"msg": "kylin-release文件存在（无对比目标）", "code": 0, "data": {}}

        path_black_file_2 = self.get_kylin_release_file(os.path.join(iso_info_other.get("work_dir", ''), "conf"))
        if isinstance(path_black_file_2, dict):
            return path_black_file_2

        if not os.path.exists(path_black_file_2):  # 如果iso_info_other未传入，则仅判断文件是否存在
            return {"msg": "基线kylin-release文件不存在（无对比目标）", "code": 0, "data": {}}
        else:
            return {"msg": "kylin-release文件都存在", "code": 40013, "data": '\n'.join([path_black_file_1, path_black_file_2])}

    def check_c_103(self, iso_info, iso_info_other=None, *args, **kwargs):
        """
        ISO是否插入md5值检查
        Args:
            iso_info:
            iso_info_other:

        Returns:

        """
        ok1, out1 = subprocess.getstatusoutput(f"checkisomd5 {iso_info}")
        if not ok1:
            return {"msg": "ISO无md5值，请执行implantisomd5", "code": 0, "data": out1}
        if iso_info_other:
            ok2, out2 = subprocess.getstatusoutput(f"checkisomd5 {iso_info_other}")
            if not ok2:
                return {"msg": "基线ISO无md5值，请执行implantisomd5", "code": 0, "data": out2}
            else:
                return {"msg": "2个ISO内含有md5校验值，checkisomd5校验通过", "code": 0, "data": {}}
        return {"msg": "本ISO内含有md5校验值，checkisomd5校验通过", "code": 0, "data": {}}

    def is_isohybrid(self, iso_info):
        mbr = "DOS/MBR boot sector"
        ok, out = subprocess.getstatusoutput(f"file {iso_info}")
        if ok:
            if out.find(mbr) >= 0:
                msg = "本ISO开启了isohybrid"
            else:
                msg = "本ISO未开启isohybrid"
        else:
            msg = f"isohybrid 校验失败：{ok}"
        return msg

    def check_c_104(self, iso_info, iso_info_other=None, *args, **kwargs):
        """
        ISO 是否执行了：isohybrid -u
        Args:
            iso_info:
            iso_info_other:s

        Returns:

        """
        msg = self.is_isohybrid(iso_info)
        msg2 = "没有基线ISO"
        if iso_info_other:
            msg2 = self.is_isohybrid(iso_info_other)

        return {"msg": msg + "\n 基线ISO：" + msg2, "code": 0 if msg == msg2 and msg.find('开启') >= 0 else 40013, "data": msg}
