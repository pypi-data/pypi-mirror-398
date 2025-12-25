# -*- coding: UTF-8 -*-
import glob
import json
import os
import re
import shutil
import subprocess
import time
import uuid
from logging import INFO
from tempfile import TemporaryDirectory
from typing import Union
from urllib.request import urlretrieve
from xml.etree import ElementTree as ET

from logzero import setup_logger, LogFormatter

from kyutil.config import ROOT_PATH_TMP, BUILD_PATH_LOGGER_FILE, DOWNLOAD_ROOT_PATH
from kyutil.data import REPODATA, XML_GZ_SUFFIX, XML_SUFFIX, REPMOD, ERR_MSG_DICT
from kyutil.download import download_file
from kyutil.enums import ArchEnum
from kyutil.file import read_sha256sum_from_file, mkdir, un_gz
from kyutil.http_util import send_request
from kyutil.log import zero_log
from kyutil.rpms import get_package_name
from kyutil.shell import run_command
from kyutil.sso_login import gen_token
from kyutil.url import url_reachable, fetch_log_files

logger = zero_log(__file__, BUILD_PATH_LOGGER_FILE)


def get_canon_arch(skip_platform=0):  # pragma: no cover
    if not skip_platform and os.access("/etc/rpm/platform", os.R_OK):
        try:
            f = open("/etc/rpm/platform", "r")
            line = f.readline()
            f.close()
            (arch, _, _) = line.split("-", 2)
            return arch
        except Exception:
            pass

    arch = os.uname()[4]
    return arch


def get_base_arch(iso_name):
    if not iso_name:
        return get_canon_arch()
    if iso_name.find("arm64") >= 0:
        return "aarch64"
    elif iso_name.find("aarch64") >= 0:
        return 'aarch64'
    elif iso_name.find("x86_64") >= 0:
        return 'x86_64'
    elif iso_name.find("loongarch64") >= 0:
        return 'loongarch64'
    elif iso_name.find("sw_64") >= 0:
        return 'sw_64'
    else:
        return get_canon_arch()


def is_isohybrid(iso_fp):
    mbr = "DOS/MBR boot sector"
    ok, out = subprocess.getstatusoutput(f"file {iso_fp}")
    if ok:
        return out.find(mbr) >= 0
    return False


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


# 挂在iso到 root_dir 目录下
def mount_iso(iso_path, _logger=logger, root_dir=ROOT_PATH_TMP):
    """ mount_iso(iso_path, logger=logger, root_dir="tmp", **kwargs)"""
    name = os.path.basename(iso_path)
    mount_dir = root_dir + name + uuid.uuid4().hex[:4]

    cmd = 'mount -o loop  %s %s' % (iso_path, mount_dir)
    _logger.info(f"ISO挂载: {iso_path} -> {mount_dir}")

    # 判断是否挂载
    if os.path.ismount(mount_dir):
        run_command('umount -fl %s' % mount_dir, _logger)

    if not os.path.exists(mount_dir):
        os.makedirs(mount_dir)

    if os.path.exists(iso_path) and os.path.isdir(mount_dir):
        run_command(cmd, _logger)
    else:
        _logger.error('Mount failed. cmd is ：【 %s】' % cmd)
    return mount_dir


def iso_edit(iso_path, rpms_dir, new_path, files_relationship, _logger=logger, repo_excluded=None) -> dict:
    """ iso_edit(iso_path, rpms_dir, new_path, **kwargs) -> dict"""
    d = {
        "iso_size": 0,
        "md5": "",
        "result": ""
    }
    process = 0
    try:
        volume_id = subprocess.getoutput("isoinfo -d -i %s | grep 'Volume id' | awk '{print $3}'" % iso_path)
        process = 5

        mount_dir = mount_iso(iso_path, _logger)
        process = 10

        iso_dir_copy = copy_mount_dir(mount_dir, os.path.dirname(rpms_dir), _logger)  # 7min
        process = 15

        unmount(mount_dir, _logger)
        process = 20
        # 删除文件
        del_iso_file(files_relationship, iso_dir_copy, _logger)
        process = 25

        # 新增/替换 文件
        replace_rpm(rpms_dir, iso_dir_copy, files_relationship, _logger)
        process = 30

        if json.dumps(files_relationship).find("rpm") >= 0:
            # 修改Packages中内容，重新做源
            if not re_cr(iso_dir_copy, rpms_dir, _logger, repo_excluded):
                raise RuntimeError
            process = 35

        # mkisofs 重新生成iso
        if not re_mkisofs(iso_dir_copy, volume_id, new_path, _logger):
            raise RuntimeError
        process = 40

        # MD5
        inje_md5(new_path, _logger)
        process = 45

        d["md5"] = get_filename_md5(new_path)
        _logger.info(f"md5 为: {d['md5']}")
        process = 50

        create_md5_file(new_path, _logger)
        process = 55

        d["iso_size"] = get_size(new_path)
        _logger.info(f"iso大小为: {d['iso_size']}")
        process = 100

        # 删除copy的ISO临时路径，保留日志和替换的软件包
        shutil.rmtree(iso_dir_copy)

    except Exception as e:
        _logger.error(f"iso修改失败： {e}")

    d['result'] = ERR_MSG_DICT[process]
    return d


# 卸载
def unmount(mount_dir, _logger=logger):
    """ unmount(mount_dir)"""
    if os.path.ismount(mount_dir):
        run_command('umount -fl %s' % mount_dir, _logger)
        os.removedirs(mount_dir)
        _logger.info("umont 成功")


def get_filename_md5(filename):
    """ get_filename_md5(filename)"""
    return subprocess.getoutput("md5sum %s | awk '{print $1}'" % filename)


def get_size(filename):
    """ get_size(filename)"""
    return os.path.getsize(filename)


def inje_md5(filename, _logger=logger):
    """ inje_md5(filename)"""
    run_command(f"implantisomd5 --force {filename}", _logger)


def create_md5_file(filename, _logger=logger):
    """ create_md5_file(filename)"""
    run_command(f'md5sum {filename} > {filename}.md5', _logger)


def copy_mount_dir(_src, _dest, _logger=logger) -> str:
    """ copy_mount_dir(_src, _dest)"""
    mount_base_dir = os.path.basename(_src)
    _logger.info(f"iso内容目录 :  {mount_base_dir}")

    _logger.info(f"copy 过程：{_src} -> {_dest}")
    run_command(f"cp -af {_src} {_dest}", _logger)
    # 返回/temp/iso_edit/8d3f/*** , *** 为iso挂载路径名
    return str(os.path.join(_dest, mount_base_dir))


def replace_from_relation_dict(relation_dict: dict, src_dir: str, dest_dir: str, _logger: logger):
    """
    根据用户上传的url进行文件替换
    @param relation_dict:
    @param src_dir:
    @param dest_dir:
    @param _logger:
    @return:
    """
    url_l = relation_dict.get("url")
    files_name = relation_dict.get("file_name")
    files = []
    if url_l:
        # 根据url下载， 生成文件列表
        _logger.info("用户通过url上传文件")
        if not isinstance(url_l, (list, tuple)):
            url_l = [url_l, ]
        for _u in list(set(url_l)):
            down_all_file(_u, src_dir, files, _logger)

    if files_name and isinstance(files_name, str):
        files_name = [files_name, ]

    if files_name:
        # 根据用户上传的文件
        files.extend(files_name)
    if files:
        for _f in list(set(files)):
            _src_file = os.path.join(src_dir, _f)
            _desc_file = os.path.join(dest_dir, _f)
            add_replace_file(_src_file, _desc_file, _logger)


def replace_rpm(rpms_dir, target_dir, files_relationship, _logger=logger):
    """
    根据 "目录": "文件" 字典关系, 新增/替换 文件
    @param rpms_dir:
    @param target_dir:
    @param files_relationship:
    @param _logger:
    @return:
    """
    add_d = files_relationship.get("add_path")
    if add_d:
        _logger.info("开始新增/替换文件")
        if not isinstance(add_d, (list, tuple)):
            add_d = [add_d, ]
        for _d in add_d:
            desc_dir = str(os.path.join(target_dir, _d["path"].strip("/")))
            if not os.path.exists(desc_dir):
                _logger.info(f"目标存储文件目录不存在,创建目录{desc_dir}")
                os.makedirs(desc_dir)
            replace_from_relation_dict(_d, rpms_dir, desc_dir, _logger)


def get_file(url: list, save_dir: str, _logger=logger):
    """
    根据url列表下载文件到指定目录
    :param url:
    :param save_dir:
    :param _logger:
    :return:
    """
    if url:
        for _u in url:
            save_path = save_dir + os.sep + _u.split("/")[-1]
            _logger.info(f"下载地址为： {_u}, 存储路径为： {save_path}")
            try:
                if not download_file(_u, save_path):
                    _logger.error(f"单文件 {_u} 下载失败")
            except Exception as e:
                _logger.error(f"单文件 {_u} 下载失败: {e}")
    else:
        _logger.error("文件下载失败: url列表为空")


def re_cr(iso_dir_copy, root_dir, _logger=logger, repo_excluded=None):
    """
    重做源
    1. 源内comps检测备份，按照源内的xml文件内容中是否存在comps根节点判断；
    2. 去除旧源；
    3. 重做源，依据旧comps文件 createrepo -g /XXX/XXX/XXXX-comps.xml /XXXX/iso12345/；
    @param iso_dir_copy:
    @param root_dir:
    @param _logger:
    @param repo_excluded: Createrepo排除的目录
    @return:
    """
    _repo_path = str(os.path.join(iso_dir_copy, REPODATA))
    _logger.info(f"重建iso源路径为：{iso_dir_copy}")
    if os.path.exists(_repo_path):
        baked_xml = traverse_repodata_folder_to_bak_comps(_repo_path, root_dir, _logger)
        baked_xml = baked_xml.replace(" ", "\\ ")  # 兼容7系的神奇空格
        if not baked_xml:
            _logger.error("备份指定repodata中的comps失败， 可能不存在comps文件")
            return False

        _logger.info(f"备份 {_repo_path} 中的 comps -> {baked_xml} 成功")

        _logger.info(f"去除旧repodata ： {_repo_path}")
        shutil.rmtree(_repo_path)
        excluded = ""
        if repo_excluded:
            for i in repo_excluded.split(","):
                excluded += f" -x '{i}' "

        _logger.info("createrepo -g %s %s %s" % (baked_xml, excluded, iso_dir_copy))
        run_command("createrepo -g %s %s %s" % (baked_xml, excluded, iso_dir_copy), _logger)

        for f in os.listdir(_repo_path):
            if f.endswith(XML_SUFFIX) and f.find(XML_GZ_SUFFIX) < 0 and f.find(REPMOD):
                to_remove_repo_comps_xml = os.path.join(_repo_path, f)
                _logger.info("移除repo源内多余comps文件 %s" % to_remove_repo_comps_xml)
                os.remove(to_remove_repo_comps_xml)

        return True
    else:
        logger.error(f"重建repodata失败，{_repo_path}不存在")
        return False


def re_mkisofs(iso_dir_copy, volume_id, new_path, _logger=logger):
    """re_mkisofs(iso_dir_copy, volume_id, new_path)"""
    if mkdir(os.path.dirname(new_path)):
        x86_cmd = f"mkisofs -joliet-long -v -U -J -R -T -V {volume_id} -m repoview -m boot.iso -b isolinux/isolinux.bin " \
                  f"-c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -eltorito-alt-boot " \
                  f"-e images/efiboot.img -no-emul-boot -o {new_path} {iso_dir_copy}"
        arch_cmd = f"mkisofs -joliet-long -v -U -J -R -T -V {volume_id} -m repoview -m boot.iso -eltorito-alt-boot " \
                   f"-e images/efiboot.img -no-emul-boot -o {new_path} {iso_dir_copy}"
        # 架构不同，iso重新制作方式不同
        re_mkiso_cmd = arch_cmd
        if new_path.find("x86") >= 0:
            re_mkiso_cmd = x86_cmd

        _logger.info("重新制作iso命令为： ")
        if not run_command(re_mkiso_cmd, _logger):
            _logger.error(f"重新制作iso命令执行失败，命令为：{re_mkiso_cmd}")
            return False

        return True
    else:
        _logger.error(f"新iso的存储路径创建失败，路径为{new_path}")
        return False


# 根据路径或者URL获取ISO名称
def get_iso_name_by_path(url_or_path):
    """ get_iso_name_by_path(url_or_path)"""
    return url_or_path.split("/")[-1].split(".")[0]


def download_iso_with_sha256sum_check(url, root_path, logger_=logger, **kwargs) -> str:
    """
    下载ISO
    通过url，判断url+.sha256sum文件是否存在，如果存在，就进行判断本地是否存在此文件。
    本地和远端同时存在，就进行校验，如果一致，不再下载
    Args:
        url: ISO下载地址。https://server.kylinos.cn/release/Release/build/os/ISO/V10SP3/aarch64/2023/09/20230926/Kylin-Server-V10-SP3-Release-202309-ARM64.iso
        root_path: ISO存放根目录。下面会有很多ISO文件
        logger_:
    Returns:
        ISO的绝对路径
    """
    sha_url = url.strip() + ".sha256sum"
    random_str = kwargs.get("random_str") or uuid.uuid4().hex[:4] + "-"
    if url_reachable(sha_url, logger=logger_):
        sha_value = send_request(sha_url, verify=False).text.strip().split(" ")[0]
        # 判断本地是否有
        sha256sum_map = {}
        for local_path_sha256sum in glob.glob(os.path.join(root_path, "*.sha256sum")):
            sha256sum_map[read_sha256sum_from_file(local_path_sha256sum)] = re.sub(r".sha256sum$", "",
                                                                                   local_path_sha256sum)
        if sha_value in sha256sum_map:
            if os.path.isfile(sha256sum_map[sha_value]):
                return sha256sum_map[sha_value]
        return download_iso_with_log(url, random_str, root_path, logger_, **kwargs)
    else:
        ok = download_file(url, dir_=root_path, name_=random_str + os.path.basename(url), logger=logger_)  # 下载iso文件
        if ok:
            return str(os.path.join(root_path, random_str + os.path.basename(url)))


def download_iso_with_log(url, random_str, root_path, logger_=None, **kwargs) -> str:
    command_log = fetch_log_files(os.path.dirname(url) + '/logs', prefix='command', suffix='txt')
    build_log = fetch_log_files(os.path.dirname(url) + '/logs', prefix='build', suffix='log')
    sha256_file = url + '.sha256sum'
    downloads = [url, sha256_file]

    for log in [command_log, build_log]:
        if log:
            downloads.append(concat_paths([os.path.dirname(url), 'logs', log]))

    for download in downloads:
        if url_reachable(download, logger=logger_):
            download_file(download, root_path, name_=random_str + os.path.basename(download), logger=logger_,
                          token=kwargs.get("token"))  # 下载iso等文件

    return str(os.path.join(root_path, random_str + os.path.basename(url)))


def concat_paths(paths: list):
    return os.path.join(*paths)


def get_create_ts(fp):
    """ get_create_ts(fp)"""
    return os.path.getctime(fp)


def is_file_exit(path):
    """ is_file_exit(path)"""
    return 1 if path and os.path.isfile(path) else 0


def remove_file(path, ts=0):
    """ remove_file(path, ts=0)"""
    if not isinstance(path, (list, tuple)):
        path = [path, ]
    for _path in path:
        if ts and is_file_exit(_path) and time.time() - os.path.getmtime(_path) > ts:
            if int(time.time()) - get_create_ts(_path) > ts:
                os.remove(_path)
        elif is_file_exit(_path):
            os.remove(_path)
        else:
            return 1

    if not (is_file_exit(path[0]) and is_file_exit(path[1])):
        return 1
    return 0


def del_iso_file(file_key: dict, root_path: str, _logger=logger):
    """
    根据字典，删除指定文件
    @param file_key:
    @param root_path:
    @param _logger:
    @return:
    """
    _logger.info(f"文件目录关系对应字典为： {file_key}")
    del_info = file_key.get("del_path")
    if del_info:
        if not isinstance(del_info, (list, tuple)):
            del_info = [del_info, ]

        for _d in list(set(del_info)):
            _p = os.path.normpath(f"{root_path}/{_d}")
            remove_file(_p)
            _logger.info(f"删除文件完成，删除：{_p}")
    else:
        _logger.info("本次修改未删除文件")


def reset_edit_log(root_path: str):
    # 修改记录日志
    log_path = root_path.rstrip("rpms") + "iso_edit.log"
    formatter = LogFormatter(color=False)
    _log = setup_logger(
        name="install_log",
        logfile=log_path,
        formatter=formatter,
        level=INFO,
    )
    return _log, log_path


def get_url(base_url, _loger=logger):
    """
    :param base_url:给定一个网址
    :param _loger:
    :return: 获取给定网址中的所有链接
    """
    urls = []
    text = send_request(base_url).text
    # 根据nginx 网页元素拼接修改
    reg = '<a href="(.*?)"'
    # 去除类似" ?C=N&amp;O=D ", 和传入的url
    urls = [
        base_url + url
        for url in re.findall(reg, text)
        if url != "../" and "?" not in url and url != base_url
    ]

    return urls


def is_file(url, _logger=logger):
    """
    判断一个链接是否是文件
    :param url:
    :param _logger:
    :return:
    """

    _re = send_request(url=url, method="HEAD")
    if _re.headers.get("Content-Length"):
        return True
    if _re.headers["Content-Type"].find("text/html") == -1:
        return True
    return False


def download_urlretrive(url, save_dir, _logger=logger):
    """
    :param url:文件链接
    :param save_dir:文件存储路径
    :param _logger:logger
    :return: 下载文件，自动创建目录
    """
    filename = url.rsplit("/")[-1]
    if not os.path.exists(save_dir):
        os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.normpath(os.path.join(save_dir, filename))
    _logger.info(f"根据url: {url}, 存储 : {filename} -> {save_path}")

    urlretrieve(url, save_path)


def down_all_file(url, save_dir, file_name: list, _logger=logger, depth=3):
    """
    递归下载网站的文件
    :param url:  指定的url
    :param file_name: 获取url中的所有文件名
    :param save_dir: 存储路径
    :param _logger: 日志handler
    :param depth: 递归深度
    :return:
    """
    if is_file(url, _logger):
        file_name.append(url.split("/")[-1])
        _logger.info(f"单文件下载 {url} ")
        download_urlretrive(url, save_dir, _logger)
    else:
        if depth > 1:
            urls = get_url(url, _logger)
            if not urls:
                _logger.error("网页为空, 无可下载内容")
            else:
                for u in list(set(urls)):
                    down_all_file(u, save_dir, file_name, _logger, depth=depth - 1)


def add_replace_file(_src_file: str, _desc_file: str, _logger):
    """
    新增 / 替换文件
    _desc_file 存在，替换为 _src_file
    _desc_file 不存在，新增 _src_file
    @param _src_file:
    @param _desc_file:
    @param _logger:
    @return:
    """
    if not os.path.exists(_src_file):
        _logger.error(f"替换/新增 文件错误, 源文件不存在 {_src_file}")

    # 目标文件是否存在,存在 -> 删除 -> copy; 不存在 -> 新增
    if os.path.exists(_desc_file):
        _logger.info(f"替换:{_desc_file}")
        os.remove(_desc_file)
        shutil.copy2(_src_file, _desc_file)
    else:
        _logger.info(f"增加:{_desc_file}")
        shutil.copy2(_src_file, _desc_file)


def check_compose_by_the_content(f: str) -> bool:
    """解析xml文件，根据根节点tag是否为comps判断为compose文件
    """
    try:
        tree = ET.parse(f)
        root = tree.getroot()
        if root.tag == "comps":
            return True
        else:
            return False
    except Exception as e:
        logger.error("comps xml解析失败 %s" % e)
        return False


def traverse_repodata_folder_to_bak_comps(repodata_path: str, to_bak_path: str, _logger=logger) -> str:
    """
    遍历repoda目录下文件，获取comps文件，并备份到指定文件
    @param repodata_path:   ISO挂载后的源路径
    @param to_bak_path:     需要将comps文件备份到的路径， comps 将按照repodata 中去掉.gz的名称存储，如: XXXX-comps.xml
    @param _logger:         自定以logger
    @return:
        成功： 返回备份后的xml绝对路径
        失败： 返回空字符串
    """
    if repodata_path.find(REPODATA) < 0:
        _logger.error("指定路径 %s 错误，非repodata路径, %s 不存在" % (repodata_path, REPODATA))
        return ""

    if not os.path.exists(repodata_path):
        _logger.error("指定repodata源路径: %s 不存在" % repodata_path)
        return ""

    if not os.path.exists(to_bak_path):
        _logger.error("指定备份文件夹 %s 不存在" % to_bak_path)
        return ""

    try:
        with TemporaryDirectory(dir=ROOT_PATH_TMP) as tmp_dir:
            # ISO内的所有xml.gz 文件 copy到临时目录
            for f in os.listdir(repodata_path):
                if f.endswith(XML_GZ_SUFFIX):
                    src_file = os.path.join(repodata_path, f)
                    dst_file = os.path.join(tmp_dir, f)
                    shutil.copy(src_file, dst_file)

            # 解压、判断 临时目录内的xml 文件是否根节点未comps
            for f in os.listdir(tmp_dir):
                file = os.path.join(tmp_dir, f)
                xml_file = file.replace(XML_GZ_SUFFIX, ".xml")
                if not un_gz(file, xml_file):
                    _logger.error("解压缩xml文件 %s -> %s 失败" % (file, xml_file))
                    continue

                is_comps = check_compose_by_the_content(xml_file)
                if is_comps:
                    comps_file = os.path.join(to_bak_path, f.replace(XML_GZ_SUFFIX, ".xml"))
                    shutil.copy(xml_file, comps_file)
                    _logger.info("comps文件复制： %s -> %s 成功" % (xml_file, comps_file))
                    break

        return comps_file

    except IOError as e:
        _logger.error("xml文件复制失败，原因: %s" % e)

    return ""


def download_single_iso(url, index, res_msg, username, password, client_id, client_secret, random_str) -> Union[
    str, None]:
    """下载单个ISO文件"""
    token = None
    if url.find('server.kylinos.cn/release') >= 0:
        token = gen_token(username, password, client_id, client_secret)
    try:
        logger.info(f"比对 开始下载 iso{index + 1}； url：{url}")
        fp = download_iso_with_sha256sum_check(url, random_str=random_str, root_path=DOWNLOAD_ROOT_PATH, logger_=logger,
                                               token=token)
        if fp:
            return fp
        else:
            logger.error(f"iso{index + 1}无法下载；")
            return None
    except Exception as e:
        logger.error(e)
        res_msg["url"] = ""
        res_msg["msg"] = f"iso{index + 1}，下载失败，报错信息为 {e}；"
        logger.error(f"iso{index + 1} [{url}]，下载失败，报错信息为[{e}]；")
        return None

def find_arch_by_name(iso_name: str = None):
    """
    根据名称获取系列
    @param iso_name:ISO名称
    @return: 系列名：ns7,ns8,ovirt,v10sp1,v10sp2
    """
    iso_name = iso_name.lower()
    for arch in ArchEnum.archs.value:
        if iso_name.find(arch) >= 0:
            return arch
    return ArchEnum.x86_64