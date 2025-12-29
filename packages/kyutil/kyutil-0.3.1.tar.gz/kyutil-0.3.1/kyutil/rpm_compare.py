# -*- coding: UTF-8 -*-
"""client iso compare module"""
import os
import time
import uuid

import logzero

from kyutil.file import get_file_list
from kyutil.iso_utils import unmount
from kyutil.rpms import get_rpm_srpm_info
from kyutil.shell import run_command_ll, run_command_with_return


# 挂载iso到tmp目录下
def mount_iso(iso_path, logger=logzero.logger):
    """
    挂载iso
    @param iso_path:
    @param logger:
    @return:
    """
    logger.info(f'iso_path:{iso_path}')
    name = os.path.basename(iso_path)
    mount_dir = "/tmp/" + name + uuid.uuid4().hex[:4]
    cmd = f'mount -o loop  {iso_path} {mount_dir}'
    logger.info(f" === mount iso path :{iso_path} -> {mount_dir}")

    # 判断是否已经挂载
    if os.path.ismount(mount_dir):
        run_command_ll(f'umount -fl {mount_dir}', logger)

    if not os.path.exists(mount_dir):
        os.makedirs(mount_dir)
        print(f"挂载目录{mount_dir}创建成功。")

    if os.path.exists(iso_path) and os.path.isdir(mount_dir):
        for _ in range(60):
            ok, err = run_command_with_return(cmd)
            if not ok and err.find("already mounted") >= 0:
                print(f"ISO已经挂载：{err}。 等5秒重试")
                time.sleep(5)
            elif ok:
                print(f"挂载到 {mount_dir} 成功。")
                break
            else:
                print(f"挂载命令：{cmd} 执行失败。")
                return ""
    else:
        print(f"挂载之后：{mount_dir} 目录不存在。")
        logger.error(f'Mount failed. cmd is ：{cmd}')
        return ""
    return mount_dir


def parse_rpm(mount_dir) -> tuple:
    """
    解析rpm
    @param mount_dir:
    @return:
    """
    rpm_info = {}
    srpm_info = {}
    rpms = get_file_list(mount_dir)

    for fp, fn in rpms:
        if not fn.endswith('.rpm'):
            continue
        rpm, srpm = get_rpm_srpm_info(fp + os.sep + fn)
        rpm_info.update(rpm)
        srpm_info.update(srpm)

    return rpm_info, srpm_info


def compare_and_add(rpm_list, srpm_list, ce):
    """
    比对和添加信息到结果
    @param rpm_list:
    @param srpm_list:
    @param ce:
    @return:
    """
    a_rpm = rpm_list[0]
    b_rpm = rpm_list[1]
    a_srpm = srpm_list[0]
    b_srpm = srpm_list[1]
    result = [common_compare(a_rpm, b_rpm), common_compare(a_srpm, b_srpm)]
    key_error = {}
    for i in range(2):
        if i == 0:
            compare_type = 'rpm'
            key_error = result[i].get("key_error")
        else:
            compare_type = 'srpm'
        ce.add_compare_info(0, result[i].get("a_update"), result[i].get("b_update"), compare_type)
        ce.add_compare_info(1, result[i].get("a_downgrade"), result[i].get("b_downgrade"), compare_type)
        ce.add_common(2, result[i].get("both_have"), compare_type)
        ce.add_common(3, result[i].get("a_only"), compare_type)
        ce.add_common(4, result[i].get("b_only"), compare_type)
    return key_error


def calc_up_down(a_version, a_release, b_version, b_release, a_update, a_key, b_update, b_key, a_downgrade, b_downgrade, both_have):
    a = [a_version, a_release]
    b = [b_version, b_release]
    if n_v_r_compare(a, b) == 1:
        a_update.append(f'{a_key}')
        b_update.append(f'{b_key}')
    elif n_v_r_compare(a, b) == -1:
        a_downgrade.append(f'{a_key}')
        b_downgrade.append(f'{b_key}')
    else:
        both_have.append(f'{a_key}')
    return a_version, a_release, b_version, b_release, a_update, a_key, b_update, b_key, a_downgrade, b_downgrade, both_have


def common_compare(info_a, info_b) -> dict:
    """
    比对逻辑
    @param info_a:
    @param info_b:
    @return:
    """
    a_update = []
    b_update = []
    a_downgrade = []
    b_downgrade = []
    both_have = []
    if not all([info_b, info_a]):
        return {}

    a_only, b_only, key_error = only_compare(info_a, info_b)

    for a_key, a_value in info_a.items():
        for b_key, b_value in info_b.items():
            a_dir = get_info_by_dir(a_value.get("dir"))
            b_dir = get_info_by_dir(b_value.get("dir"))
            a_version, a_release = a_value.get("version"), a_value.get("release")
            b_version, b_release = b_value.get("version"), b_value.get("release")
            a_name, b_name = a_value.get("name"), b_value.get("name")

            if a_key == b_key and a_dir == b_dir:
                both_have.append(f'{a_key}')
                continue
            if a_name == b_name and a_dir == b_dir:  # 同软件包，且同目录
                a_version, a_release, b_version, b_release, a_update, a_key, b_update, b_key, a_downgrade, b_downgrade, both_have = (
                    calc_up_down(a_version, a_release, b_version,
                                 b_release, a_update, a_key,
                                 b_update, b_key, a_downgrade,
                                 b_downgrade, both_have))
    # 比较单iso存在的pakages
    return {
        "a_update": a_update,
        "b_update": b_update,
        "a_downgrade": a_downgrade,
        "b_downgrade": b_downgrade,
        "both_have": both_have,
        "a_only": a_only,
        "b_only": b_only,
        "key_error": key_error
    }


def n_v_r_compare(a, b) -> int:
    """
    @param a:
    @param b:
    @return:  1 升级 0 无变化 -1 降级
    """
    for i in range(len(a)):
        res = compare(a[i], b[i])
        if res != 0:
            return res
    return 0


def get_info_by_dir(_dir):
    """ get_info_by_dir(_dir)"""
    return f'{_dir}: ' if _dir else ""


def only_compare(a, b) -> tuple:
    """
    @param a:
    @param b:
    @return:
    """
    a_only = []
    b_only = []
    a_info = {}
    b_info = {}
    err_sign_key = {}
    if a and b:
        for key, value in a.items():
            a_info[value['dir'] + os.sep + value['name']] = [f'{key}', value["key"]]
        for key, value in b.items():
            b_info[value['dir'] + os.sep + value['name']] = [f'{key}', value["key"]]

        a_only = [a_info[key][0] for key in set(a_info.keys()) - set(b_info.keys())]
        b_only = [b_info[key][0] for key in set(b_info.keys()) - set(a_info.keys())]

        # 获取签名不一样的包
        for key in set(b_info.keys()) & set(a_info.keys()):
            if a_info[key][1] != b_info[key][1]:
                err_sign_key[key] = [a_info[key][1], b_info[key][1]]
    return a_only, b_only, err_sign_key


def bytes_to_str(_b):
    """ bytes_to_str(_b)"""
    return _b.decode() if isinstance(_b, bytes) else _b


def compare(left, right) -> int:
    """
    比较版本信息差异
    @param left:
    @param right:
    @return: 1 升级 0 无变化 -1 降级
    """
    left = bytes_to_str(left)
    right = bytes_to_str(right)
    res1_arr = left.split('.')
    res2_arr = right.split('.')
    min_len = min(len(res1_arr), len(res2_arr))
    for i in range(min_len):
        if res1_arr[i].isdigit() and res2_arr[i].isdigit():
            int_res1 = int(res1_arr[i])
            int_res2 = int(res2_arr[i])
            if int_res1 < int_res2:
                return 1
            elif int_res1 > int_res2:
                return -1
        else:
            if res1_arr[i] < res2_arr[i]:
                return 1
            elif res1_arr[i] > res2_arr[i]:
                return -1

    if len(res1_arr) == len(res2_arr):
        return 0
    return 1 if min_len == len(res1_arr) else -1


def unmounts(mount_dirs):
    """
    卸载所有目录
    @param mount_dirs:
    @return:
    """
    for _ in mount_dirs:
        unmount(_)


def do_iso_compare(paths, logger_=logzero.logger):
    """ do_iso_compare(paths)"""
    rpm_list = []
    srpm_list = []
    mount_dirs = []
    msg = ""

    for _path in paths:  # 提取两个iso的rpm信息
        mount_dir = mount_iso(_path, logger_)  # 挂载iso
        if mount_dir:
            mount_dirs.append(mount_dir)
            # 避免挂载后无包
            time.sleep(10)
            rpm_dict, srpm_dict = parse_rpm(mount_dir)
            # 解析处理Packages-gcc 以外的所有文件的md5值
            rpm_list.append(rpm_dict)
            srpm_list.append(srpm_dict)
        else:
            msg = f"无法挂载ISO：{_path}"

    return rpm_list, srpm_list, msg, mount_dirs
