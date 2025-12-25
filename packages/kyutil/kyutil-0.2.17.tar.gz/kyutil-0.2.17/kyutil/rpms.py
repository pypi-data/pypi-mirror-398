# -*- coding: UTF-8 -*-
"""
@File    ：log.py
"""
import os
import os.path

import koji
import logzero

from kyutil.config import BUILD_PATH_LOGGER_FILE
from kyutil.log import zero_log
from kyutil.shell import run_get_str

logger = zero_log(__file__, BUILD_PATH_LOGGER_FILE)


def read_rpm_header(rpm_filepath: str):
    """
    获取rpm信息
    @param rpm_filepath:
    @return: header
    """
    try:
        import rpm
    except ImportError:
        print("请安装python3-rpm软件包")
    try:
        transaction = rpm.TransactionSet()
        transaction.setVSFlags(-1)
        f = os.open(rpm_filepath, os.O_RDONLY)
        header = transaction.hdrFromFdno(f)
        os.close(f)
        return header
    except Exception as e:
        logger.error(f"rpm检测失败，rpm包不符合规范，{e}")
        return None


def get_rpm_sign(rpm_filepath: str):
    """
    获取rpm的签名信息
    Args:
        rpm_filepath:
    Returns:
        签名信息
    """
    if rpm_filepath.endswith(".rpm"):
        cmd = f"rpm -qpi {rpm_filepath}"
        return run_get_str(cmd, "Signature")
    return ""


def get_rpm_srpm_info(rpm_path: str, prefix: list = ('AppStream', 'BaseOS', 'PowerTools', 'Plus', 'addons')) -> tuple:
    """
    获取rpm的源码包信息，并返回 rpm，srpm
    Args:
        prefix:
        rpm_path:
    Returns:
        rpm,srpm
        eg: AppStream: kylin-release-10-24.6.p138.ky10.x86_64.rpm AppStream: kylin-release-10-24.6.p138.ky10.src.rpm
    """
    from kyutil.file import get_file_sha256sum
    try:
        import rpm
    except ImportError:
        print("请安装python3-rpm软件包")

    rpm_dict = srpm_dict = r_dir = ""
    try:
        if rpm_path.endswith(".rpm"):
            header = read_rpm_header(rpm_path)
            srpm_n, srpm_v, srpm_r = get_nvr(header["SourceRPM"])
            for i in prefix:
                r_dir = i + ":" if rpm_path.lower().find(i.lower()) > 0 else ""
            r_dir += rpm_path.split('/')[-2]
            if header:
                rpm_name = r_dir + "/" + rpm_path.split('/')[-1]
                rpm_dict = {
                    rpm_name: {
                        "name": header["name"],
                        "version": header["version"],
                        "release": header["release"],
                        "key": koji.get_sigpacket_key_id(header[rpm.RPMTAG_SIGPGP]) if header[rpm.RPMTAG_SIGPGP] else "Not Sign!",
                        "dir": r_dir,
                        "hash": get_file_sha256sum(rpm_path)
                    }
                }
                srpm_dict = {
                    r_dir + "/" + header['SourceRPM']: {
                        "name": srpm_n,
                        "version": srpm_v,
                        "release": srpm_r,
                        "key": koji.get_sigpacket_key_id(header[rpm.RPMTAG_SIGPGP]) if header[
                            rpm.RPMTAG_SIGPGP] else "Not Sign!",
                        "dir": r_dir,
                        "hash": get_file_sha256sum(rpm_path)
                    }
                }
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"==Fail to get_rpm_srpm,err: {e}")
    return rpm_dict, srpm_dict


def common_split_filename(filename):
    """
    Pass in a standard style rpm fullname

    Return a name,version,release,epoch,arch,e.g.::
        foo-1.0-1.i386.rpm returns foo,1.0,1,i386
        1:bar-9-123a.ia64.rpm returns bar,9,123a,1,ia64
    """

    if filename.strip().endswith(".rpm"):
        filename = filename[:-4]

    arch_index = filename.rfind(".")
    arch = str(filename[arch_index + 1:])

    rel_index = filename[:arch_index].rfind("-")
    rel = str(filename[rel_index + 1: arch_index])

    ver_index = filename[:rel_index].rfind("-")
    ver = str(filename[ver_index + 1: rel_index])

    epoch_index = filename.find(":")
    epoch = "" if epoch_index == -1 else str(filename[:epoch_index])
    name = str(filename[epoch_index + 1: ver_index])

    return name, ver, rel, epoch, arch


def check_rpm_name_blacklist(pkgs_filepath: str, black_filepath: str, logger_=logzero.logger):
    """
    包含部分携带rhel的包
    检验iso内包名，看是否存在黑名单中指定包名
    @param pkgs_filepath: package目录地址
    @param black_filepath:
    @param logger_:
    @return: 包含的黑名单包名
    """
    err_exit_rpms = []
    if os.path.isfile(pkgs_filepath) and os.path.isfile(black_filepath):
        with open(pkgs_filepath, "r") as f_packages:
            # 仅获取包名
            iso_rpm_names = [i.strip("\n") for i in f_packages.readlines()]
        with open(black_filepath, "r") as f_packages:
            # 仅获取包名
            blacklist_rpm_names = [i.strip("\n") for i in f_packages.readlines()]
        for _ in iso_rpm_names:
            err_exit_rpms.extend([x for x in blacklist_rpm_names if x == _])
    else:
        logger_.error(f"包列表或者黑名单文件不存在：{pkgs_filepath} 、 黑名单：{black_filepath}")
    return err_exit_rpms


def check_rpm_name_sensitive(pkgs_filepath: str, should_not_exits=None, logger_=logzero.logger):
    """
    包含部分携带rhel的包
    检验iso内包名，看是否存在敏感软件
    @param pkgs_filepath: package目录地址
    @param logger_:
    @param should_not_exits:  ["Red_Hat", "redhat", "rhel", "rhsm", "openEuler", ".oe1."]
    @return: 包含的敏感词的单包名
    """
    err_exit_rpms = []

    if os.path.exists(pkgs_filepath):
        with open(pkgs_filepath, "r") as f_packages:
            # 仅获取包名
            iso_rpm_names_with_version = [i.strip("\n") for i in f_packages.readlines()]
            # 仅匹配红帽关键字, 筛选出包含特殊字段的软件包
            for err_exit in should_not_exits:
                err_exit_rpms.extend(
                    list(filter(lambda x, iter_i=err_exit: x.find(str(iter_i)) >= 0, iso_rpm_names_with_version))
                )
            err_exit_rpms = [common_split_filename(i)[0] for i in err_exit_rpms]
    else:
        logger_.error(f"包列表文件不存在：{pkgs_filepath}")

    return err_exit_rpms


def get_nvr(package_name):
    if package_name.count("-") < 2:
        return package_name, '', ''
    return package_name.rsplit("-", 2)


def get_package_name(package_name):
    return [get_nvr(x)[0] for x in package_name]
