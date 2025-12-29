# -*- coding: UTF-8 -*-
import difflib
import glob
import os
import re
import subprocess
import time
import uuid

import pandas as pd

from kyutil.config import ROOT_PATH_TMP, REPODATA_PATH, DOWNLOAD_ROOT_PATH
from kyutil.http_util import send_request
from kyutil.iso_utils import get_diff
from kyutil.reg_exp import LORAX_LOG_PKG
from kyutil.repo import IsoRepo

FILES = (".discinfo", ".kylin-post-actions", ".kylin-post-actions-nochroot", ".productinfo", ".treeinfo")
COMPARE_OK = '对比结果一致'
ISOHYBRID_FLAG = 'DOS/MBR boot sector'


def do_file_compare(mount_dirs):
    """文件比对"""
    hashs = extract_files_hash_dirs(mount_dirs)
    a_hash = []
    b_hash = []

    all_keys = set(hashs[0].keys()) | set(hashs[1].keys())
    s_k = set(hashs[0].items()) & set(hashs[1].items())
    same_keys = [_[0] for _ in list(s_k)]
    other_keys = sorted(set(same_keys) ^ all_keys)
    for _ in other_keys:
        a_ha = hashs[0].get(_)
        b_ha = hashs[1].get(_)
        if a_ha and b_ha:
            a_hash.append(a_ha)
            b_hash.append(b_ha)
        elif not a_ha:
            a_hash.append('')
            b_hash.append(b_ha)
        elif not b_ha:
            a_hash.append(a_ha)
            b_hash.append('')
    return other_keys, a_hash, b_hash


def extract_files_hash_dirs(mount_dirs):
    hashes = [{}, {}]
    for i in range(2):
        ret = subprocess.getoutput(
            r'find %s ! -path "%s/Packages*" ! -path "%s/repodata*" -type f  \( -name "*" \) -exec md5sum {} \;' %
            (mount_dirs[i], mount_dirs[i], mount_dirs[i]))
        lines = ret.split("\n")
        for _ in lines:
            if _.endswith("rpm"):
                continue
            file_hash = _.split("  ")
            hashes[i][os.path.relpath(file_hash[-1], mount_dirs[i])] = file_hash[0]
    return hashes


def do_content_diff(mount_dirs, key=FILES):
    """文件差异"""
    keys = []
    content_diff = []
    for i in range(2):
        keys.append([_ for _ in os.listdir(mount_dirs[i]) if _ in key])
    valid_keys = sorted(set(keys[0]) & set(keys[1]))
    valid_keys.extend(['EFI/BOOT/grub.cfg', 'isolinux/isolinux.cfg'])
    ret_keys = []
    for j in range(len(valid_keys)):
        cmd = r"diff -p %s/%s %s/%s" % (mount_dirs[0], valid_keys[j], mount_dirs[1], valid_keys[j])
        ret = subprocess.getoutput(cmd)
        ret_keys.append(valid_keys[j])
        content_diff.append(ret or COMPARE_OK)
    try:
        cmd = f"diff -p --brief {mount_dirs[0]}/Packages/ {mount_dirs[1]}/Packages/"
        ret = subprocess.getoutput(cmd)
        ret_keys.append("Packages包列表比对：")
        content_diff.append(ret or COMPARE_OK)
    except Exception as e:
        print("软件包列表比对报错", e)
        ret_keys.append("Packages包列表比对：")
        content_diff.append(f"Packages包列表比对出错:{e}")
    try:
        comps_0 = glob.glob(f"{mount_dirs[0]}{REPODATA_PATH}*.xml")[0]  # 假设ISO中有且仅有一个以xml结尾的文件就是comps文件
        comps_1 = glob.glob(f"{mount_dirs[1]}{REPODATA_PATH}*.xml")[0]
        ret = subprocess.getoutput(r"diff -p '%s' '%s'" % (comps_0, comps_1))
        ret_keys.append("*-comps-*.xml")
        content_diff.append(ret or COMPARE_OK)
    except Exception as e:
        ret_keys.append("*-comps-*.xml")
        content_diff.append(f"比对出错：{e}")
    return ret_keys, content_diff


def find_initrd_img(mount_point):
    """在挂载点中找到 initrd.img 文件"""
    for root, dirs, files in os.walk(mount_point):
        if 'initrd.img' in files:
            return os.path.join(root, 'initrd.img')
    return None


def run_lsinitrd(initrd_path):
    """运行 lsinitrd initrd.img | grep Arguments 命令，返回结果"""
    result = subprocess.run(['lsinitrd', initrd_path], capture_output=True, text=True, check=True)
    grep_result = subprocess.run(['grep', 'Arguments'], input=result.stdout, capture_output=True, text=True, check=True)
    return grep_result.stdout.strip()


def do_initrd_diff(mount_dirs):
    initrds = []
    ret_obj = {"fp": 'ISO内initrd参数校验', "diff_content": ""}
    for i in mount_dirs:
        initrd_fp = find_initrd_img(i)
        if initrd_fp:
            ret = run_lsinitrd(initrd_fp)
            initrds.append(ret)
        else:
            ret_obj['diff_content'] = f"{mount_dirs}目录内initrd.img文件不存在"
    if len(initrds) == 2:
        if initrds[0] == initrds[1]:
            ret_obj['diff_content'] = "一致: %s" % initrds[0]
        else:
            d = difflib.Differ()
            diff = d.compare(initrds[0].splitlines(), initrds[1].splitlines())
            ret_obj['diff_content'] = "\n".join(list(diff))
    return ret_obj


def do_repodata_diff(mount_dirs):
    """文件差异"""
    res = []
    for mount_dir in mount_dirs:
        try:
            rim = IsoRepo(mount_dir)
            repo_rpms = rim.get_rpm_names()
            iso_rpms = [rpm for rpm in os.listdir(os.path.join(mount_dir, 'Packages')) if rpm.endswith('rpm')]
            if not repo_rpms or not iso_rpms:
                res.append('Error ! 提取软件包信息失败！')
            else:
                res.append(set(repo_rpms) != set(iso_rpms))
        except Exception as e:
            print(e)
            res.append(False)
    return "ISO内repodata是否包含Packages以外软件包:", f"ISO1 :{res[0]}, ISO2 :{res[1]}"


def do_command_diff(iso_names):
    """文件差异"""
    res = []
    for iso in iso_names:
        command_log = find_build_log(iso, 'command')
        build_log = find_build_log(iso, 'build')
        if command_log:
            res.append(fetch_log(command_log, 'command'))
        elif build_log:
            res.append(fetch_log(build_log, 'build'))
        else:
            res.append({})
    same, diff = compare_dict(res)

    return "集成iso用到的关键命令:", f"相同的命令有{same}\n 不同的命令有{diff}"


def find_build_log(isoname, log_type, log_path=DOWNLOAD_ROOT_PATH):
    if isoname:
        isoname = os.path.basename(isoname)
        random_id = isoname.split("-")[0]
        for file in os.listdir(log_path):
            if file.startswith('-'.join([random_id, log_type])):
                return os.path.join(log_path, file)
    return ''


def fetch_log(log_path, log_type) -> dict:
    try:
        res = {}
        if log_type not in ['build', 'command']:
            return res
        with open(log_path, 'r') as f:
            lines = f.readlines()
        df = pd.DataFrame(lines, columns=['log'])
        res['pungi_gather_cmd'] = df[df['log'].str.contains('pungi-gather --config')].iloc[0, 0]
        res['createrepo_cmd'] = df[df['log'].str.contains('createrepo -d -g')].iloc[0, 0]
        res['lorax_cmd'] = df[df['log'].str.contains('lorax -p')].iloc[0, 0]
        res['mkiso_cmd'] = df[df['log'].str.contains('-v -U -J -R -T -V')].iloc[0, 0]
        return format_command(res, log_type)
    except Exception as e:
        print(e)
        return {}


def compare_dict(dicts):
    same = diff = []
    all_keys = set(dicts[0].keys()).union(set(dicts[1].keys()))
    for key in all_keys:
        if key in dicts[0].keys() and key in dicts[1].keys():
            if dicts[0][key] == dicts[1][key]:
                same.append(dicts[0][key])
            else:
                diff.append(f'{key} 不同， iso1 为 {dicts[0][key]} iso2 为 {dicts[1][key]}')
    return same, diff


def format_command(cmd: dict, log_type) -> dict:
    if log_type == 'build':
        pattern = r'CMD:\[(.*?)\]'
    else:
        pattern = r'命令:(.*?)状态:'
    for key in cmd.keys():
        match = re.search(pattern, cmd.get(key, ''))
        if match:
            command = match.group(1).strip()
            cmd[key] = command
        else:
            cmd[key] = ''
    return cmd


def compare_iso_md5_inserted(iso_names):
    try:
        ok, out = subprocess.getstatusoutput(f"checkisomd5 {iso_names[0]}")
        ok2, out2 = subprocess.getstatusoutput(f"checkisomd5 {iso_names[1]}")
        msg = "不一致"
        if ok == ok2 == 0:
            msg = "一致"
        return "ISO内MD5校验:", f"{msg}\n\n{ok}\n{out}\n===============\n{ok2}\n{out2}"
    except Exception as e:
        print(e)
        return "ISO内MD5校验:", f"比对发生异常：{e}"


def compare_iso_isohybrid(iso_names):
    try:
        ok, out = subprocess.getstatusoutput(f"file {iso_names[0]}")
        ok2, out2 = subprocess.getstatusoutput(f"file {iso_names[1]}")
        if ok == ok2 == 0:
            if out.find(ISOHYBRID_FLAG) >= 0 and out2.find(ISOHYBRID_FLAG) >= 0:
                msg = "一致,且都开启 isohybrid"
            elif out.find(ISOHYBRID_FLAG) >= 0 > out2.find(ISOHYBRID_FLAG):
                msg = "不一致,ISO2 未开启 isohybrid"
            elif out2.find(ISOHYBRID_FLAG) >= 0 > out.find(ISOHYBRID_FLAG):
                msg = "不一致,ISO1 未开启 isohybrid"
            else:
                msg = "一致,ISO1 和 ISO2 都未开启 isohybrid"
        else:
            msg = f"校验失败,ISO1：{ok}/ISO2：{ok2}"
        return "ISO isohybrid校验", f"{msg}\n{ok}\n{out}\n===============\n{ok2}\n{out2}"
    except Exception as e:
        print(e)
        return "ISO isohybrid校验", f"比对发生异常：{e}"


def compare_iso_size(iso_names):
    """
    比较2个ISO的大小，并返回变化率
    Args:
        iso_names:

    Returns:

    """
    size1 = os.path.getsize(iso_names[0])
    size2 = os.path.getsize(iso_names[1])
    if abs(size2 - size1) / size1 > 0.1:
        return "ISO文件大小", f"相差超过10%:{size1} -> {size2}"
    else:
        return "ISO文件大小", f"相差不超过10%{size1} -> {size2}"


def compare_lorax_install_pkg(urls):
    """
    比较2个lorax install pkg
    Args:
        urls:

    Returns:

    """
    key = "LORAX安装文件列表"
    lorax_log_url1 = urls[0][:urls[0].rfind("/")] + "/logs/lorax/lorax.log"
    lorax_log_url2 = urls[1][:urls[1].rfind("/")] + "/logs/lorax/lorax.log"
    r1 = send_request(lorax_log_url1)
    r2 = send_request(lorax_log_url2)
    if r1.status_code == 200 and r2.status_code == 200:
        log1, log2 = r1.text, r2.text
        pkg_list_1 = re.findall(LORAX_LOG_PKG, log1)
        pkg_list_2 = re.findall(LORAX_LOG_PKG, log2)
        diff_content = get_diff(pkg_list_1, pkg_list_2, "lorax")
        return key, "请核对是否存在差异\n" + '\n'.join(diff_content)
    else:
        return key, f"lorax log不存在？iso1:{r1.status_code} iso2:{r1.status_code} "


def compare_files_and_add(mount_dirs, ce, key_error=None, iso_names=None, urls=None):
    other_keys, a_hash, b_hash = do_file_compare(mount_dirs)
    # 写入错误的key
    for k, v in key_error.items():
        other_keys.append(k)
        a_hash.append(v[0])
        b_hash.append(v[1])
    valid_keys, content_diff = do_content_diff(mount_dirs)
    if iso_names is not None:
        # isoinfo
        valid_key_iso_info, content_diff_iso_info = compare_iso_info(iso_names)
        if content_diff_iso_info:
            valid_keys.append(valid_key_iso_info)
            content_diff.append(content_diff_iso_info)

        # checkisomd5
        valid_key, valid_value = compare_iso_md5_inserted(iso_names)
        valid_keys.append(valid_key)
        content_diff.append(valid_value)

        # isohybrid
        valid_key2, valid_value2 = compare_iso_isohybrid(iso_names)
        valid_keys.append(valid_key2)
        content_diff.append(valid_value2)

        # 文件大小
        valid_key3, valid_value3 = compare_iso_size(iso_names)
        valid_keys.append(valid_key3)
        content_diff.append(valid_value3)

        # lorax安装文件列表
        valid_key3, valid_value3 = compare_lorax_install_pkg(urls)
        valid_keys.append(valid_key3)
        content_diff.append(valid_value3)

        # iso内Packages和repodata目录比对
        valid_key4, valid_value4 = do_repodata_diff(mount_dirs)
        valid_keys.append(valid_key4)
        content_diff.append(valid_value4)

        # iso内Packages和repodata目录比对
        valid_key5, valid_value5 = do_command_diff(iso_names)
        valid_keys.append(valid_key5)
        content_diff.append(valid_value5)

    initrd_diff = do_initrd_diff(mount_dirs)

    ce.add_files(5, other_keys, a_hash, b_hash)
    ce.add_content_diff(6, valid_keys, content_diff, initrd_diff)


def compare_iso_info(iso_names) -> (str, str):
    try:
        iso_info_0 = os.path.join(ROOT_PATH_TMP, time.strftime("%Y%m%d%H%M%S") + str(uuid.uuid4())[:8])
        iso_info_1 = os.path.join(ROOT_PATH_TMP, time.strftime("%Y%m%d%H%M%S") + str(uuid.uuid4())[:8])
        subprocess.getoutput(f"isoinfo -R -l -f -i {iso_names[0]} &> {iso_info_0}")
        subprocess.getoutput(f"isoinfo -R -l -f -i {iso_names[1]} &> {iso_info_1}")
        ret = subprocess.getoutput(r"diff -p %s %s" % (iso_info_0, iso_info_1))
        return "对比isoinfo", ret
    except Exception as e:
        print(e)
        return "对比isoinfo", f"比对发生异常：{e}"
