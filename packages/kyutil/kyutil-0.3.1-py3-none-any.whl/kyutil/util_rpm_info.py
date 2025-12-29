# -*- coding: UTF-8 -*-
import glob
import hashlib
import itertools
import os
import pickle
import re
import subprocess
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from functools import reduce

from logzero import logger as logging

os.environ['BUILD_PATH'] = "/tmp/"
from kyutil import util_repo_info
from kyutil.base import TMP_PATH, is_url, format_slashes, get_parent_path, get_base_arch
from kyutil.rpm_operation import get_nvr


def get_hash256_for_str(str_one):
    return hashlib.sha256(str(str_one).encode('utf-8')).hexdigest()


def intersection(set_1, set_2):
    """给定两个集合，返回两个集合中共有的元素"""
    return set(set_1) & set(set_2)


def intersection4module(set_1, set_2):
    """给定两个集合，返回两个集合中共有的元素，针对module，排除随机数的影响"""
    set_1 = set(Str4Cmp(_l) for _l in set_1)
    set_2 = set(Str4Cmp(_l) for _l in set_2)
    common_set_temp = set_1 & set_2
    set_1 = set(s_o.str_pre for s_o in set_1 if s_o in common_set_temp)
    set_2 = set(s_o.str_pre for s_o in set_2 if s_o in common_set_temp)
    return set_1 | set_2


def is_local_match(release):
    pattern_list = [r".*ks[\d\._]+"]
    for pattern in pattern_list:
        if re.match(pattern, release):
            return True
    return False


def compare_str_list(*str_list) -> list:
    if len(str_list) == 0:
        return [""]
    elif len(str_list) == 1:
        return list(str_list)
    else:
        str_list = map(list_strip, str_list)
        str_list = list(map(set, str_list))
        common_set = reduce(intersection4module, str_list)
        if len(common_set) == 0:
            return [""] * len(str_list)
        else:
            return ['\n'.join(sorted(set(slo) - common_set)) for slo in str_list]


def list_strip(obj_list, str_strip=' '):
    return list(map(lambda x: str(x).strip(str_strip), obj_list))


def compare_evr_by_shell(evr_1, evr_2) -> tuple:
    """Exit status is   0 if the EVR's are equal,
                        11 if EVR1 is newer, and
                        12 if EVR2 is newer.
                        Other exit statuses indicate problems."""
    if not evr_1 or not evr_2:
        raise RuntimeError("版本比对缺失比对对象")
    if evr_1.strip() == evr_2.strip():
        return 0, "equal"
    evr_1, evr_2 = evr_1.replace(".module+", ".module_"), evr_2.replace(".module+", ".module_")
    cmd_str = f'rpmdev-vercmp {evr_1} {evr_2}'
    res_code, output = subprocess.getstatusoutput(cmd_str)
    return res_code, output


def list_flatten(*obj_all):
    obj_res = []
    for obj_one in obj_all:
        if isinstance(obj_one, list):
            obj_res += obj_one
        elif isinstance(obj_one, str):
            obj_res.append(obj_one)
    return obj_res


def get_fill_value(get_type, fill_str="", fill_list=None, wide=1):
    if fill_list is None:
        fill_list = [""]
    if get_type == str:
        return fill_str * wide
    elif get_type == list:
        return fill_list * wide
    else:
        return None


def del_local_str(str_pre):
    return re.sub(r"\.ks[\d._]+[\d_]+", "", str_pre)


def del_module_str(str_pre):
    return re.sub(r"(\+\d+)(\+\w+)", "", str_pre)


def get_value_from_list(list_one, position, wide):
    if len(list_one) == 0:
        return "" * wide
    elif position >= len(list_one):
        get_type = type(list_one[0])
        return get_fill_value(get_type=get_type, wide=wide)
    return list_one[position]


def get_wide_for_list(obj_all):
    len_wide = []
    for obj_one in obj_all:
        if len(obj_one) == 0:
            len_wide.append(1)
        elif isinstance(obj_one[0], list):
            len_wide.append(len(obj_one[0]))
        else:
            len_wide.append(1)
    return len_wide


def zip_longest(*obj_all):
    if len(obj_all) <= 1:
        return obj_all
    obj_res = []
    len_max = max(map(len, obj_all))  # 最大行数
    len_obj = len(obj_all)
    len_wide = get_wide_for_list(obj_all)  # 每个列表的宽度
    for i in range(len_max):
        obj_one = []
        for j in range(len_obj):
            obj_one.append(get_value_from_list(obj_all[j], i, wide=len_wide[j]))
        obj_res.append(list_flatten(*obj_one))
    return obj_res


def get_map_fullname2rpm_info(rpm_info_list):
    return {rpm_info.fullname: rpm_info for rpm_info in rpm_info_list}


def get_rpm_correspond_sub(*rpm_info_list_obj_list):
    """用于对分组后的进行比对"""
    rpm_info_list_obj_list = [sorted(rpm_info_list, reverse=True) for rpm_info_list in rpm_info_list_obj_list]  # 进行逆向排序
    len_list = [len(rpm_info_list) for rpm_info_list in rpm_info_list_obj_list]
    if 0 in len_list or len(set(len_list)) == 1:  # 如果其中一个仓库没有软件包或只有一个仓库，直接按顺序进行对齐
        rpm_info_list_obj_list = list(itertools.zip_longest(*rpm_info_list_obj_list, fillvalue=""))
        return rpm_info_list_obj_list
    return list(itertools.zip_longest(*rpm_info_list_obj_list, fillvalue=""))


def get_rpm_correspond_sub4module(*rpm_info_list_obj_list):
    """针对模块包进行进一步的对齐，去除 后进行对比"""
    res_correspond_list = []
    common_set = reduce(intersection, rpm_info_list_obj_list)
    for ri_one in common_set:
        corr_rpm_info = [[rpm_info.fullname for rpm_info in rpm_info_list if rpm_info == ri_one]
                         for rpm_info_list in rpm_info_list_obj_list]
        res_correspond_list += list(itertools.zip_longest(*corr_rpm_info, fillvalue=""))
    rpm_info_list_obj_list = [[rpm_info for rpm_info in rpm_info_list if rpm_info not in common_set]
                              for rpm_info_list in rpm_info_list_obj_list]
    return res_correspond_list \
        + get_rpm_correspond_sub(*[[ri.fullname for ri in ri_list] for ri_list in rpm_info_list_obj_list])


def get_rpm_correspond(*rpm_info_list_obj_list):
    """
    输入2个仓库的RpmInfo列表，尝试进行软件包对齐（配对），缺失的补位空对象
    Args:
        *rpm_info_list_obj_list:
                # 仓库1的RPM包信息
                repo1 = [
                    RpmInfo({"fullname": "package1-1-1.0.x86_64", "arch": "x86_64"}),
                    RpmInfo({"fullname": "package2-2-1.0.x86_64", "arch": "x86_64"}),
                    RpmInfo({"fullname": "module1-3-1.0.x86_64", "arch": "x86_64", "is_module": True}),
                    RpmInfo({"fullname": "package4-4-1.0.x86_64", "arch": "x86_64"}),
                ]
                # 仓库2的RPM包信息
                repo2 = [
                    RpmInfo({"fullname": "package1-1-1.0.x86_64", "arch": "x86_64"}),
                    RpmInfo({"fullname": "package1-2-1.0.x86_64", "arch": "x86_64"}),
                    RpmInfo({"fullname": "module2-3-1.0.x86_64", "arch": "x86_64", "is_module": True}),
                    RpmInfo({"fullname": "package4-4-1.0.x86_64", "arch": "x86_64"}),
                ]
                # Add at 2025-12-26 11:13:06
                [<Class(RpmInfo)> fullname:A-Tune-BPF-Collection-1.0.0-7.ky11.src.rpm], [<Class(RpmInfo)> fullname:A-Tune-BPF-Collection-1.0.0-7.ky11.src.rpm]
    Returns: 类似下面这个格式
        # Add at 2025-12-26 11:13:06
        [
            [<Class(RpmInfo)> fullname:A-Tune-BPF-Collection-1.0.0-7.ky11.src.rpm, <Class(RpmInfo)> fullname:A-Tune-BPF-Collection-1.0.0-7.ky11.src.rpm]
        ]
    """

    rpm_info_list_obj_list = list(rpm_info_list_obj_list)

    arch_set = set([rpm_info.arch for rpm_info_list in rpm_info_list_obj_list for rpm_info in rpm_info_list]) ^ {""}  # 所有架构
    map_fullname2rpm_info_obj_list = [get_map_fullname2rpm_info(rpm_info_list) for rpm_info_list in rpm_info_list_obj_list]  # fullname到RpmInfo的映射
    rpm_fullname_list_obj_list = [map_fullname2rpm_info.keys() for map_fullname2rpm_info in map_fullname2rpm_info_obj_list]  # 所有的fullname列表
    common_fullname_set = reduce(intersection, rpm_fullname_list_obj_list)  # 能够匹配的fullname
    exclude_fullname_list_obj_list = [set(rpm_fullname_list) - common_fullname_set for rpm_fullname_list in rpm_fullname_list_obj_list]  # 不能匹配的fullname
    fullname_correspond_list = [[rpm_one] * len(rpm_info_list_obj_list) for rpm_one in common_fullname_set]
    for i in range(len(rpm_info_list_obj_list)):
        rpm_info_list_obj_list[i] = [ri for ri in rpm_info_list_obj_list[i] if ri.fullname in exclude_fullname_list_obj_list[i]]
    for arch in arch_set:  # 进行分组
        fullname_correspond_list += get_rpm_correspond_sub4module(  # 针对非模块包进行一一对应
            *[[ri for ri in ri_list if not ri.is_module and ri.arch == arch] for ri_list in rpm_info_list_obj_list])
        fullname_correspond_list += get_rpm_correspond_sub4module(  # 针对模块包进行一一对应
            *[[ri for ri in ri_list if ri.is_module and ri.arch == arch] for ri_list in rpm_info_list_obj_list])
    res_correspond_list = []
    for fullname_correspond in fullname_correspond_list:
        res_correspond_list_one = []
        for i in range(len(fullname_correspond)):  # 通过fullname转换成RpmInfo
            res_correspond_list_one.append(map_fullname2rpm_info_obj_list[i].get(fullname_correspond[i], RpmInfo()))
        res_correspond_list.append(res_correspond_list_one)
    return res_correspond_list


def get_diff_sheet_data(_rpm_key, _ri_corr_list, _sheet_data):
    """
    该函数用于处理 _ri_corr_list 中的每个元素，生成需要保存的数据项（新增、删除、更新）。

    参数:
        _rpm_key (str): RPM包的键值
        _ri_corr_list (list): 一个包含多个二元组的列表，每个二元组包含两个对象ri_corr

    返回:
        无返回值，将数据保存到 _sheet_data 字典中
    """
    for ri_corr in _ri_corr_list:
        if len(ri_corr) != 2:  # 只有长度为2时才进行对比
            continue
        if ri_corr[0].is_none:
            # 删除
            item_data = [
                _rpm_key,
                "",
                ri_corr[1].fullname,
                "DELETE",
                ri_corr[1].is_module_str,
                "",
                "",
                ri_corr[1].sha256sum,
                "Null",
                [],
                ri_corr[1].pkg_bin_list
            ]
        elif ri_corr[1].is_none:
            # 新增
            item_data = [
                _rpm_key,
                ri_corr[0].fullname,
                "",
                "ADD",
                ri_corr[0].is_module_str,
                "",
                ri_corr[0].sha256sum,
                "",
                "Null",
                ri_corr[0].pkg_bin_list,
                []
            ]
        else:
            # 变更
            cmp_res = ri_corr[0].compare_with(ri_corr[1])
            if cmp_res == "NOT_CHANGED":  # 默认不再显示同版本，若需要显示，注释掉即可
                continue
            item_data = [
                _rpm_key,
                ri_corr[0].fullname,  # n-v-r.src.rpm
                ri_corr[1].fullname,
                cmp_res,  # IjoPackageType
                ri_corr[0].is_module_str,
                ri_corr[0].compare4local_str(ri_corr[1]),
                ri_corr[0].sha256sum,
                ri_corr[1].sha256sum,
                str(ri_corr[0].sha256sum == ri_corr[1].sha256sum),
                ri_corr[0].pkg_bin_list,
                ri_corr[1].pkg_bin_list
            ]
        _sheet_data[_rpm_key] = item_data


def get_diff_multi_evr_thread_pool(_candidate, pool_size=10) -> list:
    # logging.info(">>> 进行多版本比对(多线程)")
    """
    进行多版本比对(多线程)
    Args:
        _candidate: 配对结果
        pool_size: 线程池大小

    Returns:

    """
    pool = ThreadPoolExecutor(max_workers=pool_size)
    _sheet_data = {}
    for rpm_key, ri_corr_pair in _candidate.items():  # 对比版本升降级
        if ri_corr_pair:
            pool.submit(get_diff_sheet_data, rpm_key, ri_corr_pair, _sheet_data)
    pool.shutdown()
    return list(_sheet_data.values())


def get_repo_dir(iso_dir, is_pungi, mash=False, aarch=None):
    iso_dir = format_slashes(iso_dir.rstrip('/'))
    base_arch = aarch or get_base_arch(iso_dir)
    if is_pungi:
        work_path = get_parent_path(iso_dir, 4)
        return os.path.join(work_path, 'compose/Everything', base_arch, 'os')
    else:
        repo_path = f"{iso_dir}/logs/"
    return repo_path + 'mash/' if mash else repo_path


def get_iso_repo_dir(iso_dir, is_pungi, mash=False, aarch=None):
    iso_dir = format_slashes(iso_dir.rstrip('/'))
    base_arch = aarch or get_base_arch(iso_dir)
    if is_pungi:
        work_path = get_parent_path(iso_dir, 4)
        return os.path.join(work_path, 'compose/Server', base_arch, 'os')
    else:
        repo_path = f"{iso_dir}/logs/"
    return repo_path + 'mash/' if mash else repo_path


def _cmp_repos(repo_dir_1, repo_dir_2, is_pungi, is_pungi2, log_handler):
    """

    Args:
        repo_dir_1: 本ISO仓库地址
        repo_dir_2: 基线ISO仓库地址
        is_pungi:
        is_pungi2:
        log_handler:

    Returns:
        {
          "apache-commons-pool2-2.9.0-1.ky11.src.rpm":{
            "ijo_nvf":"",
            "iso_nvr":"apache-commons-pool2-2.9.0-1.ky11.src.rpm",
            "need":"add",
            "pkg_ijo":[ ],
            "pkg_iso":[
              "apache-commons-pool2-2.9.0-1.ky11.noarch.rpm",
              "apache-commons-pool2-help-2.9.0-1.ky11.noarch.rpm"
            ]
          },
          "glassfish-jsp-2.3.3-1.p02.ky11.src.rpm":{
            "ijo_nvf":"",
            "iso_nvr":"glassfish-jsp-2.3.3-1.p02.ky11.src.rpm",
            "need":"add",
            "pkg_ijo":[ ],
            "pkg_iso":[
              "glassfish-jsp-2.3.3-1.p02.ky11.noarch.rpm",
              "glassfish-jsp-help-2.3.3-1.p02.ky11.noarch.rpm"
            ]
          },
        }
    """
    rim_iso = load_repodata_src2rpm(repo_dir_1, is_pungi)
    rim_base = load_repodata_src2rpm(repo_dir_2, is_pungi2)
    if rim_iso.count_pkg == 0:
        raise RuntimeError(f"读取ISO软件包数量是0.仓库地址： {repo_dir_1}")
    if rim_base.count_pkg == 0:
        raise RuntimeError(f"读取ISO软件包数量是0.仓库地址： {repo_dir_2}")
    if log_handler:
        log_handler.info(f"仓库地址： {repo_dir_1}  软件包数量是：{rim_iso.count_pkg}")
        log_handler.info(f"仓库地址： {repo_dir_2}  软件包数量是：{rim_base.count_pkg}")
    correspond = rim_iso.compare_multi_version_with(rim_base)
    sheet_data = get_diff_multi_evr_thread_pool(correspond)
    _cmp_res = {}
    for i in sheet_data:
        """
        i: 
            [
              "apache-commons-pool2(src)",
              "apache-commons-pool2-2.9.0-1.ky11.src.rpm",
              "",
              "ADD",
              "非模块包",
              "",
              "random_02e9956c0b94ec3f7199f295339ea8380b3fa9f1b8e14c944ce27f",
              "",
              "Null",
              [
                "apache-commons-pool2-2.9.0-1.ky11.noarch.rpm",
                "apache-commons-pool2-help-2.9.0-1.ky11.noarch.rpm"
              ],
              [ ]
            ]
        """
        if i[3].lower() not in ["upgrade", "downgrade", "delete", "add", "not_changed"]:
            continue
        key = i[1] or i[2]
        _cmp_res[key] = {
            "iso_nvr": i[1],
            "ijo_nvf": i[2],
            "need": i[3].lower(),
            "pkg_iso": i[9],
            "pkg_ijo": i[10],
        }
    return _cmp_res


def cmp_repo(iso, base_iso, log_handler=None):
    """
    Args:
        iso:
        base_iso:
        log_handler:

    Returns:
        参考：_cmp_repos
    """
    repo_dir_2 = get_repo_dir(base_iso.root_dir, base_iso.is_pungi, mash=True)
    if repo_dir_2 == "":
        return {"msg": "无基础ISO"}
    repo_dir_1 = get_repo_dir(iso.root_dir, iso.is_pungi, mash=True)
    return _cmp_repos(repo_dir_1, repo_dir_2, iso.is_pungi, base_iso.is_pungi, log_handler)


def cmp_iso_repo(iso, base_iso, log_handler=None):
    """
    获取ISO内的仓库变化
    Args:
        iso:
        base_iso:
        log_handler:

    Returns:
        参考：_cmp_repos
    """
    repo_dir_2 = get_iso_repo_dir(base_iso.root_dir, base_iso.is_pungi, mash=True, aarch=base_iso.aarch)
    if repo_dir_2 == "":
        return {"msg": "无基础ISO"}
    repo_dir_1 = get_iso_repo_dir(iso.root_dir, iso.is_pungi, mash=True, aarch=iso.aarch)
    return _cmp_repos(repo_dir_1, repo_dir_2, iso.is_pungi, base_iso.is_pungi, log_handler)


def load_repodata(repo_dir, **kwargs):
    rim = RpmInfoManage()
    if os.path.exists(repo_dir) or is_url(repo_dir):
        rim.load_from_link_repodata(link_repodata=repo_dir, clear=True)
    else:
        logging.error(f"仓库地址不合法：{repo_dir}， {os.path.exists(repo_dir)} , {is_url(repo_dir)}")
    return rim


def load_repodata_src2rpm(repo_dir, is_pungi=False):
    rim = RpmInfoManage()
    if os.path.exists(repo_dir) or is_url(repo_dir):
        rim.load_src_only_from_link_repodata(link_repodata=repo_dir, clear=True, is_pungi=is_pungi)
    else:
        logging.error(f"仓库地址不合法：{repo_dir},  {os.path.exists(repo_dir)} , {is_url(repo_dir)}")
    return rim


def get_reason_for_pkg_in_iso(compare_result: dict) -> str:
    """
    ISO中有变化的软件包，但是仓库没变化的原因梳理
    Args:
        compare_result: 比对结果，参考 _cmp_repos

    Returns:

    """
    d = {"add": "被依赖引入", "delete": "不在被依赖"}
    return d.get(compare_result['need'].lower(), f"其他变化：{compare_result['need']}")


class Str4Cmp:
    def __init__(self, str_pre):
        self.str_pre = str_pre
        self.str_deal = self.str_deal_pre = self.str_pre.replace('.module_', '.module+')
        self.deal()

    def deal(self):
        self.str_deal = del_module_str(self.str_deal_pre)
        self.str_deal = del_local_str(self.str_deal)

    def __eq__(self, other):
        return self.str_deal == other.str_deal

    def __hash__(self):
        return hash(self.str_deal)

    def __repr__(self):
        return self.str_deal


class RpmInfo:
    """rpm包信息类，记录rpm包信息"""

    def __init__(self, rpm_info=None, rpm_header=None, repo_name="") -> None:
        if rpm_info is None:
            rpm_info = {"is_none": True}
        self.arch_candidate = ["x86_64", "i686", "noarch", "src"]
        self.rpm_info = {
            "filepath": "",
            "rpm_name": "",  # n
            "fullname": "",  # nvra
            "requires": [],
            "provides": [],
            "src_name": "",
            "version": "",
            "release": "",
            "evr": "",
            "arch": "",
            "is_module": False,
            "repo_name": repo_name,
            "pkg_bin_list": []
        }
        self.rpm_info_update(rpm_info)
        self.cache_evr_cmp_map = {}
        self.cache_evr_cmp_map4local = {}
        self.rpm_header = rpm_header
        self.compare = self.compare4local  # 选择对比器 compare_default（默认）|compare4local（忽略字研补丁）

    @property
    def is_none(self):
        return self.rpm_info.get("is_none", False)

    @property
    def filepath(self):
        return self.rpm_info.get("filepath")

    @property
    def rpm_name(self):
        return self.rpm_info.get("rpm_name")

    @property
    def rpm_key(self):
        """
        n+arch+module
        Returns:

        """
        rpm_name = self.rpm_name
        module = "(module)" if self.is_module else ""
        arch = f"({self.arch})"
        return rpm_name + arch + module

    @property
    def rpm_key4module(self):
        return self.rpm_key + self.version + self.release.split(".module")[0]

    @property
    def fullname(self):
        return self.rpm_info.get("fullname", "")  # n-v-r.src.rpm

    @property
    def fullname_without_rpm(self):
        return self.fullname.rstrip(".rpm")

    @property
    def sha256sum(self):
        sha256sum = self.rpm_info.get("sha256sum", "") or self.rpm_info.get("checksum", "")
        if sha256sum in ["", None]:
            sha256sum = "random_" + get_hash256_for_str(uuid.uuid4().hex[:4] + time.strftime("%Y%m%d%H%M%S"))[10:]
        return sha256sum

    @property
    def requires(self):
        return self.rpm_info.get("requires", [])

    @property
    def provides(self):
        return self.rpm_info.get("provides", [])

    @property
    def src_name(self):
        src_name = self.rpm_info.get("src_name", "")
        if src_name in ["", None]:
            if self.arch == "src":
                src_name = self.fullname
            else:
                src_name = ""
        return src_name

    @property
    def rpm_vendor(self):
        return self.rpm_info.get("rpm_vendor", "")

    @property
    def epoch(self):
        return self.rpm_info.get("epoch", "")

    @property
    def version(self):
        return self.rpm_info.get("version", "")

    @property
    def release(self):
        return self.rpm_info.get("release", "")

    @property
    def release_del_module(self):
        return self.rpm_info.get("release_del_module", "")

    @property
    def release_del_module_local(self):
        return self.rpm_info.get("release_del_module_local", "")

    @property
    def evr(self):
        return self.rpm_info.get("evr", "")

    @property
    def vr(self):
        return self.evr

    @property
    def nvr(self):
        return '-'.join([self.rpm_name, self.vr])

    @property
    def evr_del_module(self):
        return self.rpm_info.get("evr_del_module", "")

    @property
    def evr_del_module_local(self):
        return self.rpm_info.get("evr_del_module_local", "")

    @property
    def arch(self):
        return self.rpm_info.get("arch", "")

    @property
    def pkg_bin_list(self):
        pkg_bin_list = self.rpm_info.get("pkg_bin_list", [])
        if len(pkg_bin_list) == 0 and self.arch != "src":
            return [self.fullname]
        return pkg_bin_list

    @property
    def is_module(self):
        return self.rpm_info.get("is_module", "")

    @property
    def is_module_str(self):
        return {True: "模块包", False: "非模块包"}.get(self.is_module, "未知")

    @property
    def is_local(self):
        return self.rpm_info.get("is_local", "")

    @property
    def is_local_str(self):
        return {True: "修改过", False: "未修改"}.get(self.is_local, "未知")

    @property
    def repo_name(self):
        return self.rpm_info.get("repo_name", "")

    def rpm_info_update(self, rpm_info={}):
        self.rpm_info.update(rpm_info)
        if self.fullname == "" and self.filepath != "":
            self._update_fullname()
        if self.fullname:
            self._update_is_module()
            self._update_nvr_and_is_local()
            self._update_arch()
        if self.release_del_module == "" and self.release != "":
            self.rpm_info["release_del_module"] = del_module_str(self.release)
        if self.release_del_module_local == "" and self.release_del_module != "":
            self.rpm_info["release_del_module_local"] = del_local_str(self.release_del_module)
        if self.evr == "":
            self.rpm_info["evr"] = '-'.join([self.version, self.release])
        if self.evr_del_module == "":
            self.rpm_info["evr_del_module"] = '-'.join([self.version, self.release_del_module])
        if self.evr_del_module_local == "":
            self.rpm_info["evr_del_module_local"] = '-'.join([self.version, self.release_del_module_local])
        if self.is_local == "" and self.release != "":
            self.rpm_info["is_local"] = is_local_match(self.release)

    def _update_fullname(self):
        self.rpm_info['fullname'] = os.path.basename(self.filepath)

    def _update_is_module(self):
        self.rpm_info['is_module'] = ".module" in self.fullname

    def _update_nvr_and_is_local(self):
        if self.rpm_name == "":
            self.rpm_info["rpm_name"], self.rpm_info["version"], self.rpm_info["release"] = get_nvr(self.fullname)
            self.rpm_info["is_local"] = is_local_match(self.release)

    def _update_arch(self):
        arch_maybe_list = self.fullname.split('.')
        for arch_maybe in arch_maybe_list:
            if arch_maybe in self.arch_candidate:
                self.rpm_info["arch"] = arch_maybe

    def compare_with(self, __o: object) -> str:
        """

        Args:
            __o:

        Returns:
            IjoPackageType里的key
        """
        if self.compare(__o) == -1:
            return "DOWNGRADE"
        elif self.compare(__o) == 1:
            return 'UPGRADE'
        elif self.compare(__o) == 0:
            return 'NOT_CHANGED'
        elif self.compare(__o) == 127:
            return '比较版本失败，需要安装：yum install rpmdevtools'
        else:
            return 'ERROR_CMP'

    def compare_default(self, __o: object) -> int:
        """ 返回 1：小于、-1：大于、0：等于 """
        if __o.evr_del_module in self.cache_evr_cmp_map:
            res_code = self.cache_evr_cmp_map[__o.evr_del_module]
        else:
            res_code, _ \
                = self.cache_evr_cmp_map[__o.evr_del_module], _ \
                = compare_evr_by_shell(self.evr_del_module, __o.evr_del_module)
        return {0: 0, 11: 1, 12: -1, 127: 127}.get(res_code, 0)

    def compare4local(self, __o: object) -> int:
        """ 针对被修改的包进行对比，忽略自研补丁，返回 1：小于、-1：大于、0：等于 """
        if not self.is_local and not __o.is_local:
            return self.compare_default(__o)
        if __o.evr_del_module_local in self.cache_evr_cmp_map4local:  # and False:
            res_code = self.cache_evr_cmp_map4local[__o.evr_del_module_local]
        else:
            res_code, _ \
                = self.cache_evr_cmp_map4local[__o.evr_del_module], _ \
                = compare_evr_by_shell(self.evr_del_module_local, __o.evr_del_module_local)
        return {0: 0, 11: 1, 12: -1, 127: 127}.get(res_code, None)

    def compare4local_str(self, __o: object) -> str:
        """ 如果版本相同，仅有自研补丁，返回本地化包，否则返回空字符串 """
        if not self.is_local and not __o.is_local:
            return ""
        res_code = self.compare4local(__o)
        return {0: "本地化包"}.get(res_code, "")

    def compare_requires_with(self, __o: object, *__other: object) -> list:
        return compare_str_list(self.requires, __o.requires, *list(map(lambda x: x.requires, __other)))

    def compare_provides_with(self, __o: object, *__other: object) -> list:
        return compare_str_list(self.provides, __o.provides, *list(map(lambda x: x.provides, __other)))

    def __repr__(self) -> str:
        return "<Class(RpmInfo)> fullname:" + self.fullname

    def __lt__(self, __o: object) -> bool:
        return True if self.compare(__o) == 1 else False

    def __gt__(self, __o: object) -> bool:
        return True if self.compare(__o) == -1 else False

    def __le__(self, __o: object) -> bool:
        return True if self.compare(__o) != -1 else False

    def __ge__(self, __o: object) -> bool:
        return True if self.compare(__o) != 1 else False

    def __eq__(self, __o: object) -> bool:
        if __o is None:
            return False
        return True if self.compare(__o) == 0 else False

    def __ne__(self, __o: object) -> bool:
        return True if self.compare(__o) != 0 else False

    def __lshift__(self, __o: object) -> list:
        """比较requires"""
        return self.compare_requires_with(__o)

    def __rshift__(self, __o: object) -> list:
        """比较provides"""
        return self.compare_provides_with(__o)

    def __hash__(self):
        return hash((self.rpm_key + self.evr_del_module_local))  # 进行hash的时候，针对模块包进行兼容


class RpmInfoManage:
    """RpmInfo管理类，用于缓存rpm包信息"""

    def __init__(self) -> None:
        self.keyword_set = set()  # 黑名单。
        self.rpm_info_list = []  # 参考: rpm_info_list_title, 通过 load_from_sqlite、load_from_xml来实现
        self.rpm_info_list_sqlite = []  # packages 表的sql 查询结果列表。
        self.rpm_info_list_sqlite_header = []  # package 软件包的列字段名称
        self.rpm_info_map = {}  # 是什么？get_rpm_info_obj_list
        self.repo_info = {}  # 是什么？什么时候会赋值
        self.arch_set = set()  # 是什么？什么时候会赋值

    def __sub__(self, __o: object) -> list:
        """比较软件包缺失，self比__o多的软件包"""
        return list(sorted(set(self.rpm_info_map.keys()) - set(__o.rpm_info_map.keys())))

    def __and__(self, __o: object) -> list:
        """获取两个仓库软件包的交集"""
        return list(sorted(set(self.rpm_info_map.keys()) & set(__o.rpm_info_map.keys())))

    def __or__(self, __o: object) -> list:
        """获取两个仓库软件包的并集"""
        return list(sorted(set(self.rpm_info_map.keys()) | set(__o.rpm_info_map.keys())))

    def __isub__(self, other):
        logging.info("！基于sha256sum获取仓库增量")
        ri_list_this = self.get_rpm_info_obj_list_all()
        sha256sum_this = [ri.sha256sum for ri in ri_list_this]
        sha256sum_other = [ri.sha256sum for ri in other.get_rpm_info_obj_list_all()]
        sha256sum_set = set(sha256sum_this) - set(sha256sum_other)
        logging.info(f"！当前仓库：{str(self.repo_info.get('load_source'))}，仓库软件包 {len(sha256sum_this)} 个")
        logging.info(f"！上次仓库：{str(other.repo_info.get('load_source'))}，仓库软件包 {len(sha256sum_other)} 个")
        logging.info(f"！通过sha256sum， 获取增量更新 {len(sha256sum_set)} 个")
        ri_list_this = [ri for ri in ri_list_this if ri.sha256sum in sha256sum_set]
        self.gen_rpm_key2rpm_info_map(rpm_info_list=ri_list_this, clear=True)
        return self

    @property
    def count_pkg(self):
        return sum(map(lambda x: len(x), self.rpm_info_map.values()))

    @property
    def count_module(self):
        return sum(map(lambda x: len([_x for _x in x if _x.is_module]), self.rpm_info_map.values()))

    @property
    def black_keyword_set(self):
        return set(self.keyword_set)

    def get_rpm_info_obj_list(self, rpm_key, rpm_info_map=None, **kwargs):
        """
        Returns:
            [<Class(RpmInfo)>rubygem-i18n-1.8.11-1.ky11.src.rpm, <Class(RpmInfo)>nekohtml-1.9.22-9.ky11.src.rpm, <Class(RpmInfo)>rubygem-multipart-post-2.3.0-1.ky11.src.rpm]
        """
        """若key不存在，需要指定filepath或一些其他信息"""
        rpm_info_map = rpm_info_map or self.rpm_info_map
        if rpm_key not in rpm_info_map:
            # logging.warning("~~~ 未缓存软件包：" + str(rpm_key))
            kwargs["is_none"] = True
            ri = RpmInfo(kwargs)
            rpm_key = ri.rpm_key
            self.gen_rpm_key2rpm_info_map(rpm_info_list=[ri], clear=False)
        return rpm_info_map[rpm_key]

    def get_rpm_info_obj_list_all(self):
        rpm_info_obj_list = [rpm_info_obj for _rpm_info_obj in self.rpm_info_map.values()
                             for rpm_info_obj in _rpm_info_obj if not rpm_info_obj.is_none]
        return rpm_info_obj_list

    def get_rpm_fullname_list_all(self):
        return [ri.fullname for ri in self.get_rpm_info_obj_list_all()]

    def get_srpm_fullname_list_all(self):
        return [ri.src_name for ri in self.get_rpm_info_obj_list_all()]

    def get_rpm_fullname_without_rpm_list_all(self):
        return [ri.fullname_without_rpm for ri in self.get_rpm_info_obj_list_all()]

    def get_rpm_nvr_list_all(self):
        return [ri.nvr for ri in self.get_rpm_info_obj_list_all()]

    def get_rpm_info_obj_list_by_list(self, rpm_key_list, rpm_info_map=None):
        return [self.get_rpm_info_obj_list(rpm_key, rpm_info_map) for rpm_key in rpm_key_list]

    def get_src_name_list_by_list(self, rpm_key_list, rpm_info_map=None):
        rpm_info_obj_list_list = self.get_rpm_info_obj_list_by_list(rpm_key_list, rpm_info_map)
        return [[rpm_info_obj.src_name for rpm_info_obj in rpm_info_obj_list] for rpm_info_obj_list in
                rpm_info_obj_list_list]

    def get_full_name_list_by_list(self, rpm_key_list, rpm_info_map=None):
        rpm_info_obj_list_list = self.get_rpm_info_obj_list_by_list(rpm_key_list, rpm_info_map)
        return [[rpm_info_obj.fullname for rpm_info_obj in rpm_info_obj_list] for rpm_info_obj_list in
                rpm_info_obj_list_list]

    def get_is_module_list_by_list(self, rpm_key_list, rpm_info_map=None):
        rpm_info_obj_list_list = self.get_rpm_info_obj_list_by_list(rpm_key_list, rpm_info_map)
        return [[rpm_info_obj.is_module_str for rpm_info_obj in rpm_info_obj_list]
                for rpm_info_obj_list in rpm_info_obj_list_list]

    def save(self, save_dir="cache", flag=""):
        """通过flag来标记不同的cache，用于缓存不同的仓库"""
        save_dir = os.path.join(save_dir, flag)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        time_str = time.strftime("%Y%m%d%H%M%S")
        file_name = f"ri_map_{time_str}_{id(self)}.ri_map"
        file_path = os.path.join(save_dir, file_name)
        logging.info(f"<<< 保存缓存：{file_path}")
        with open(file_path, 'wb') as f:
            pickle.dump(self.rpm_info_map, f)

    def save_obj(self, save_dir="cache", flag=""):
        """缓存整个rim类"""
        save_dir = os.path.join(save_dir, flag)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        time_str = time.strftime("%Y%m%d%H%M%S")
        file_name = f"rim_{time_str}_{id(self)}.rim"
        file_path = os.path.join(save_dir, file_name)
        logging.info(f"<<< 保存类缓存：{file_path}")
        with open(file_path, 'wb') as f:
            pickle.dump(self, f)
        return os.path.abspath(file_path)

    def load(self, save_dir="cache", flag=""):
        save_dir = os.path.join(save_dir, flag)
        file_path_list = sorted(glob.glob(os.path.join(save_dir, "*.rim")))
        if len(file_path_list) == 0:
            return False
        logging.info(f"<<< 加载缓存：{file_path_list[-1]}")
        with open(file_path_list[-1], "rb") as f:
            self.rpm_info_map.update(pickle.load(f))
        return True

    def gen_rpm_key2rpm_info_map(self, rpm_info_list=None, clear=False):
        if clear:
            self.rpm_info_map = {}
        if rpm_info_list is not None and isinstance(rpm_info_list, list):
            self.rpm_info_list = rpm_info_list[:]
        for ri in self.rpm_info_list:
            self.arch_set.add(ri.arch)
            if ri.rpm_key in self.rpm_info_map:
                self.rpm_info_map[ri.rpm_key].append(ri)
            else:
                self.rpm_info_map[ri.rpm_key] = [ri]

    def load_from_pkg_dir(self, pkg_dir_path):
        logging.info(f"<<< 正在从目录（{pkg_dir_path}）中加载软件包信息...")
        self.rpm_info_list = []
        for rpm_path in glob.glob(os.path.join(pkg_dir_path, "*.rpm")):
            self.rpm_info_list.append(RpmInfo({"filepath": rpm_path}))
        self.gen_rpm_key2rpm_info_map(clear=True)

    def load_from_sqlite(self, file_path_sqlite, clear=True, use_cache=False, repo_name="",
                         is_load_requires=False, is_load_provides=False):
        if use_cache and self.load(flag=os.path.basename(file_path_sqlite)):
            return
        logging.info(f"<<< 正在从sqlite文件（{file_path_sqlite}）中加载软件包信息...")
        rpm_info_list_title = [
            "pkgKey", "sha256sum", "rpm_name", "arch", "version", "epoch", "release",
            "summary", "description", "url", "time_file", "time_build",
            "rpm_license", "rpm_vendor", "rpm_group", "rpm_buildhost",
            "src_name", "rpm_header_start", "rpm_header_end", "rpm_packager",
            "size_package", "size_installed", "size_archive", "filepath",
            "location_base", "checksum_type"
        ]  # 转换到RpmInfo中的名字
        rpm_pkg_key2requires_map = util_repo_info.search_rpm_requires_from_sqlite(file_path_sqlite) \
            if is_load_requires else {}
        rpm_pkg_key2provides_map = util_repo_info.search_rpm_provides_from_sqlite(file_path_sqlite) \
            if is_load_provides else {}
        self.rpm_info_list_sqlite = util_repo_info.search_rpm_info_from_sqlite(file_path_sqlite)
        self.rpm_info_list_sqlite_header = util_repo_info.get_rpm_info_header_from_sqlite(file_path_sqlite)
        self.rpm_info_list = []
        # logging.info(">>> 构建软件包信息")
        for rpm_info_one in self.rpm_info_list_sqlite:
            pkg_key = rpm_info_one[0]
            rpm_info = dict(zip(rpm_info_list_title, rpm_info_one))
            rpm_info["requires"] = rpm_pkg_key2requires_map.get(pkg_key, [])
            rpm_info["provides"] = rpm_pkg_key2provides_map.get(pkg_key, [])
            self.rpm_info_list.append(RpmInfo(rpm_info, repo_name=repo_name))
        self.gen_rpm_key2rpm_info_map(clear=clear)

    def load_from_xml(self, file_path_xml, clear=True, use_cache=False, repo_name=""):
        if use_cache and self.load(flag=os.path.basename(file_path_xml)):
            return
        logging.info(f"<<< 正在从xml文件（{file_path_xml}）中加载软件包信息...")
        rpm_info_list = util_repo_info.get_rpm_info_from_xml(file_path_xml)
        logging.info(">>> 构建软件包信息")
        for rpm_info in rpm_info_list:
            self.rpm_info_list.append(RpmInfo(rpm_info, repo_name=repo_name))
        self.gen_rpm_key2rpm_info_map(clear=clear)

    def load_from_link_repodata(self, link_repodata, save_path=TMP_PATH, clear=False, use_cache=False, repo_name="",
                                **kwargs):
        """
        给定repodata的链接,填充 rpm_info_list rpm_info_list_sqlite rpm_info_map
        Args:
            link_repodata:
            save_path:
            clear:
            use_cache:
            repo_name:
            **kwargs:

        Returns:

        """
        self.repo_info["load_source"] = link_repodata
        logging.info(f"<<< 获取数据，地址：{str(link_repodata)}")
        try:
            link_repodata = link_repodata if "repodata" in link_repodata else link_repodata + "/repodata/"
            file_path_sqlite = util_repo_info.get_sqlite_from_repodata(link_repodata, save_path)
            self.load_from_sqlite(file_path_sqlite, clear=clear, use_cache=use_cache, repo_name=repo_name, **kwargs)
        except Exception as e:
            logging.info(f"!!! 当前repodata链接中primary.sqlite文件不可用，接下来尝试从primary.xml中获取数据，{str(e)}")
            try:
                file_path_xml = util_repo_info.get_primary_xml_from_repodata(link_repodata, save_path)
                self.load_from_xml(file_path_xml, clear=clear, use_cache=use_cache, repo_name=repo_name)
            except Exception as e:
                logging.error(f"error in load_from_link_repodata：当前repodata链接中无可用数据，错误：{str(e)}")

    def load_from_pungi_repodata(self, link_repodata, clear=False, use_cache=False, repo_name=""):
        """给定repodata的链接"""
        self.repo_info["load_source"] = link_repodata
        logging.info(f"<<< 获取数据，地址：{str(link_repodata)}")
        link_repodata = link_repodata if "repodata" in link_repodata else link_repodata + "/repodata/"
        try:
            file_path_xml = util_repo_info.get_primary_xml_from_local_repodata(link_repodata)
            self.load_from_xml(file_path_xml, clear=clear, use_cache=use_cache, repo_name=repo_name)
        except Exception as e:
            logging.info(f"!!! 当前repodata链接中数据库文件解压失败，{str(e)}")

    def load_src_only_from_link_repodata(self, link_repodata, save_path=TMP_PATH, clear=False, is_pungi=False):
        """
        给定repodata的链接,返回 源码包到二进制包的映射关系
        Args:
            link_repodata:
            save_path:
            clear:
            is_pungi:

        Returns:
            []
        """
        map_src2bin = {}
        for ri in self.rpm_info_list:
            map_src2bin[ri.src_name] = map_src2bin.get(ri.src_name, []) + [ri.fullname]
        src_name_list_last = [ri.src_name for ri in self.rpm_info_list]
        self.load_from_link_repodata(link_repodata, save_path=save_path, clear=clear)
        for ri in self.rpm_info_list:
            map_src2bin[ri.src_name] = map_src2bin.get(ri.src_name, []) + [ri.fullname]
        src_name_list = list(set(src_name_list_last + [ri.src_name for ri in self.rpm_info_list]))
        self.rpm_info_list = []
        self.load_from_fullname_list(src_name_list, map_src2bin=map_src2bin, clear=True)
        return src_name_list

    def load_from_fullname_list(self, fullname_list, map_src2bin=None, clear=False, repo_name=""):
        """
        通过软件包全名称来填充 rpm_info_list、rpm_info_map
        Args:
            fullname_list: ["kylin-release", "kernel ] #  源码包名称
            map_src2bin:
            clear:
            repo_name:

        Returns:
            rpm_info_list、rpm_info_map 填充为新数据
        """
        fullname_list += [ri.src_name for ri in self.rpm_info_list]
        self.rpm_info_list = []
        for fullname in set(fullname_list):
            pkg_bin_list = map_src2bin.get(fullname, []) if map_src2bin else []
            self.rpm_info_list.append(RpmInfo({
                "fullname": fullname,
                "src_name": fullname,
                "sha256sum": "random_" + get_hash256_for_str(fullname + time.strftime("%Y%m%d%H%M%S"))[10:],
                "pkg_bin_list": pkg_bin_list
            }, repo_name=repo_name))
        self.rpm_info_map = {}
        self.gen_rpm_key2rpm_info_map(clear=clear)

    def load_from_fullname_list_file(self, path_fullname_list, clear=False):
        if not os.path.exists(path_fullname_list):
            return
        try:
            with open(path_fullname_list, "r", encoding="utf-8") as f:
                fullname_list = f.read().split('\n')
                self.load_from_fullname_list(fullname_list, clear=clear)
        except Exception:
            logging.error(f"error in load_from_fullname_list_file：加载fullname列表文件{str(path_fullname_list)}失败")

    def load_from_koji_by_tag(self, tag="ns8.6-AppStream", path_koji_conf="repo/conf_koji/koji_242.conf"):
        cmd_str = f"koji -c {path_koji_conf} list-tagged {tag} --inherit 2> /dev/null"
        res_str = os.popen(cmd_str).read()
        res_list = res_str.split('\n')[2:]  # 从第三行开始，因为前两行是title
        fullname_list = [rpm_one.split()[0] + ".src.rpm" for rpm_one in res_list if rpm_one != ""]
        logging.info(f"加载Tag({tag})，命令：{cmd_str}，获取{len(fullname_list)}个软件包")
        self.load_from_fullname_list(fullname_list)

    def compare_multi_version_with(self, __o: object) -> dict:
        """
        通过比对2个对象，获取比对结果
        Args:
            __o: self类的的比对对象
        Returns:
            {"rpm_key": [RpmInfo, RpmInfo2]}
            例如：{'lkrg-kyextend(src)': [[<Class(RpmInfo)> fullname:lkrg-kyextend-0.9.7-05~RC1.ky11.src.rpm, <Class(RpmInfo)> fullname:lkrg-kyextend-0.9.7-05~RC0.ky11.src.rpm]]}
        """
        # logging.info(">>> 进行多版本关系对应")
        common_rpm_key_list = self | __o
        res_compare = {}
        for rpm_key in common_rpm_key_list:
            res_compare[rpm_key] = get_rpm_correspond(self.get_rpm_info_obj_list(rpm_key),
                                                      __o.get_rpm_info_obj_list(rpm_key))
        return res_compare

    def compare_multi_version_with_all(self, __o: object) -> dict:
        common_rpm_key_list = self | __o
        res_compare = {}
        for rpm_key in common_rpm_key_list:
            res_compare[rpm_key] = get_rpm_correspond(self.get_rpm_info_obj_list(rpm_key),
                                                      __o.get_rpm_info_obj_list(rpm_key))
        return res_compare

    def get_rpm_info_map_ignore_module(self, rpm_info_map=None):
        logging.info(">>> 忽略module，进行映射融合")
        rpm_info_map_ignore_module = {}
        rpm_info_map = rpm_info_map or self.rpm_info_map
        for rpm_key, rpm_info_list in rpm_info_map.items():
            rpm_key.replace("(module)", "")
            if rpm_key in rpm_info_map_ignore_module:
                rpm_info_map_ignore_module[rpm_key] += rpm_info_list
            else:
                rpm_info_map_ignore_module[rpm_key] = rpm_info_list
        return rpm_info_map_ignore_module

    def get_rpm_info_map_ignore_module_and_arch(self, rpm_info_map=None):
        logging.info(">>> 忽略module，进行映射融合")
        rpm_info_map_ignore_module = {}
        rpm_info_map = rpm_info_map or self.rpm_info_map
        for rpm_key, rpm_info_list in rpm_info_map.items():
            # rpm_key.replace("(module)", "")
            rpm_key = rpm_key.split('(')[0]
            if rpm_key in rpm_info_map_ignore_module:
                rpm_info_map_ignore_module[rpm_key] += rpm_info_list
            else:
                rpm_info_map_ignore_module[rpm_key] = rpm_info_list
        return rpm_info_map_ignore_module

    def get_rpm_key_both_rpm_and_module(self) -> list:
        """忽略架构和模块的区别，获取rpm_key列表"""
        rpm_key_list = []
        rpm_info_map_ignore_module = self.get_rpm_info_map_ignore_module_and_arch()
        for rpm_key, rpm_info_list in rpm_info_map_ignore_module.items():
            is_module_list = [rpm_info.is_module for rpm_info in rpm_info_list]
            if len(set(is_module_list)) == 2:
                rpm_key_list.append(rpm_key)
        return rpm_key_list

    def filter_by_keyword(self, keyword):
        """根据关键词，移除软件包名中包含此关键词的包"""
        if keyword == "":
            return []
        removed_rpm_key = []
        rpm_key_list = list(self.rpm_info_map.keys())
        for rpm_key in rpm_key_list:
            if keyword in rpm_key:
                removed_rpm_key.append(rpm_key)
                self.rpm_info_map.pop(rpm_key)
        return removed_rpm_key

    def filter_by_keyword_list(self, keyword_list=None, keyword_file_path=""):
        """通过给定的关键字列表进行过滤（会合并keyword_list与keyword_file_path文件中的列表）"""
        if keyword_list is None:
            keyword_list = []
        if os.path.exists(keyword_file_path):
            with open(keyword_file_path, "r", encoding="utf-8") as f:
                keyword_list += f.read().split('\n')
        elif keyword_file_path != "":
            logging.error(f"Error: 文件<{keyword_file_path}>不存在")
        self.keyword_set = keyword_list = set(keyword_list)
        rpm_key_removed = []
        for keyword in keyword_list:
            rpm_key_removed += self.filter_by_keyword(keyword)
        logging.info(f">>> 通过关键词({', '.join(keyword_list)})，共移除{len(rpm_key_removed)}个RpmKey")
        return rpm_key_removed


if __name__ == '__main__':
    from logzero import logger

    r = _cmp_repos("/Users/xuyonghui/code/py/kyutil/tests/data/repo/iso/repodata/", "/Users/xuyonghui/code/py/kyutil/tests/data/repo/base/repodata/", False, False, logger)
