# -*- coding: UTF-8 -*-
"""
@Project ：kyutil 
@File    ：build_base.py
@IDE     ：PyCharm 
@Author  ：xuyong@kylinos.cn
@Date    ：2025/3/27 下午11:13 
@Desc    ：说明：
"""
import bz2
import glob
import json
import lzma
import os
import re
import shutil
import sqlite3
import subprocess
import tempfile
import time
import traceback
import uuid
from datetime import datetime
from pathlib import Path

import wget
from celery import states, exceptions
from retry import retry

from kyutil.celery_util import celery_state_update as _update_celery
from kyutil.config import BUILD_PATH, SIG_KEY, FILE_SCHEMA, REPODATA_PATH, APACHE_READ_MODEL, SENSITIVE_KEYWORDS, \
    HOST_IP, BUILD_PATH_LOGGER_FILE, HTTPS, ROOT_PATH_ISO_PATH
from kyutil.config import PYTHON_MINOR_CMD
from kyutil.data import ISOErrorEnum, KOJI_SERVER_PORT
from kyutil.date_utils import extract_time_from_line
from kyutil.download import download_file, wget_remote_dirs
from kyutil.exceptions import BuildException, BizAssert
from kyutil.file import copy_dirs, move_dirs, delete_dirs, file_write, reset_dirs, get_file_list, \
    get_comps_list, get_ks_list, get_file_sha256sum, get_file_size
from kyutil.file_compare import run_lsinitrd
from kyutil.http_util import send_request
from kyutil.inject_ks import insert_install_ks
from kyutil.iso_utils import is_isohybrid, get_base_arch, find_arch_by_name
from kyutil.log import zero_log
from kyutil.mock import into_chroot_env, exit_chroot_env, generate_mock_config
from kyutil.reg_exp import URL_REPODATA_SQLITE, BUILD_PARAMS
from kyutil.release_dependency import ReleaseDependency
from kyutil.rpms import common_split_filename, get_rpm_sign, read_rpm_header, check_rpm_name_blacklist, \
    check_rpm_name_sensitive
from kyutil.shell import run_command, rum_command_and_log, run_command_with_return
from kyutil.url import url_reachable, url_filename
from kyutil.util_rpm_info import load_repodata

EXT_SHA256SUM = ".sha256sum"

logger = zero_log(__file__, BUILD_PATH_LOGGER_FILE)


class ReleaseOSBase(ReleaseDependency):
    """集成构建基类"""
    user = 'pungier'  # 集成构建用户
    process = 0  # 当前任务进度，取值从0-100

    def __init__(self, **kwargs):
        """init初始化函数-基类"""
        self.command_logger = None
        self.mash_sum = None
        self.mash_list = None
        self.mash_log_name = None
        self.mash_log = None
        self.mash_httpd_path = None
        self.series = "Base"
        self.nkvers = None
        self.repos = None
        self.repo_create_time = None
        # 保存mock文件路径
        self.mock_cfg_file = None
        self.isos_inmock = '/root/isos'
        self.dracut = ""

        # kwargs 是API调用celery函数是传的参数，需要增加8.2的参数

        # 时间参数
        self.cur_day = kwargs.get("cur_day", time.strftime('%Y%m%d', time.localtime(time.time())))
        # celery状态更新参数
        self._update_celery = kwargs.get("state")
        self.task_id = kwargs.get("id")
        self.params = kwargs.get("params")
        self.target_arch = self.params.get('target_arch')

        # 本地构建目录
        self.build_path = f"{BUILD_PATH}/{self.cur_day}/{self.params.get('tag')}/{self.params.get('target_arch')}/{self.task_id[0:4]}"
        self.build_isos = f"{self.build_path}/iso"
        self.build_log = f"{self.build_isos}/logs"
        self.build_cfg_dir = f"{self.build_isos}/conf/"

        self.build_logfile = f"{self.build_log}/build-{self.task_id[0:4]}.log"

        self.build_warn_file = f"{self.build_log}/WARNING.txt"
        self.build_env = f"{self.build_log}/build_env-{self.task_id[0:4]}.txt"
        self.command_env = f"{self.build_log}/command-{self.task_id[0:4]}.txt"
        # 配置文件夹定义
        self.cfg_file = f"{self.build_cfg_dir}/build.cfg.txt"
        self.before_repo_package = f"{self.build_path}/before_repo_package/"
        self.after_repo_package = f"{self.build_path}/after_repo_package/"
        self.boot_file = f"{self.build_path}/boot_file/"
        self.not_boot_file = f"{self.build_path}/not_boot_file/"
        self.scripts_dir = f"{self.build_path}/scripts_dir/"
        # 配置文件名称
        self.ks_file = url_filename(self.params.get('ks_path'))
        self.comps_file = url_filename(self.params.get('comps_path'))
        self.ks_file_path = os.path.join(self.build_cfg_dir, self.ks_file)
        self.comps_file_path = os.path.join(self.build_cfg_dir, self.comps_file)

        # mock环境构建目录
        self.build_mocktag = f"{self.params.get('tag')}-{self.task_id[0:4]}"
        self.build_mockroot = f"/var/lib/mock/{self.build_mocktag}/root/"
        self.build_inmock = "/root/buildiso"
        self.os_patch_inmock = f"/root/buildiso/{self.params.get('release')}/{self.target_arch}/os/"
        self.build_inmock_packages = f"{self.build_mockroot}/root/buildiso/Packages/"
        # 通用iso输出名称，子函数调用
        self.iso_name = self.params.get('iso_name') if self.params.get('iso_name') else \
            f"{self.params.get('release')}-{self.params.get('target_arch')}" \
            f"-{self.params.get('build')}-{self.cur_day}.iso"

        self.mash_httpd = kwargs.get("mash")  # 非双目录的
        self.mash_result = kwargs.get("mash")
        self.pkg_list = None
        self.ks_file_path = None
        # mash源，repo源软件包列表解压
        self.yum_url = self.params.get("yum_url")
        self.iso_pkgs_list = f"{self.build_isos}/logs/pkg_list_iso.txt"
        self.src_pkgs_list = f"{self.isos_inmock}/%s" % '-'.join(
            [self.params.get('release'), self.params.get('target_arch'), 'src_packages.txt'])
        self.yum_pkgs_list = f"{self.build_isos}/logs/pkg_list_yum_repo.txt"
        self.mash_pkgs_list = f"{self.build_isos}/logs/pkg_list_mash_repo.txt"
        self.compress_sqlite_name = self.build_log + "/com_primary.sqlite"
        self.decompress_sqlite_name = self.build_log + "/primary.sqlite"
        self.rpm_graph_dot = self.build_log + "/dependency.dot"
        self.rpm_graph_pdf = self.build_log + "/dependency_graph.pdf"
        self.rpm_dep_csv = self.build_log + "/dependency.csv"
        self.lorax_templates_url = self.params.get("lorax_templates_url")

        self.addon_repodata = '/root/addon_repo'
        self.tags = eval(self.params.get('tags')) if self.params.get('tags') else []
        self.product_file = ""
        self.lorax_templates_sha256sum = ""
        self.build_logger = zero_log(__file__, self.build_logfile)
        self.command_logger = zero_log("command", self.command_env)

    def init_run_env_base(self):
        """获取配置参数，初始化目录"""
        self.process = 10
        os.chmod(self.build_logfile, APACHE_READ_MODEL)
        self._update_status("获取配置参数，下载配置文件", self.process, None)
        # 获取配置参数并写入文件
        reset_dirs(self.build_cfg_dir)
        file_write(self.cfg_file, "接收使用的配置参数如下：\n")
        with open(self.cfg_file, 'a+') as f:
            json.dump(self.params, f, indent=4)
        # 重置本地配置文件目录
        reset_dirs(self.before_repo_package)
        reset_dirs(self.after_repo_package)
        reset_dirs(self.boot_file)
        reset_dirs(self.not_boot_file)
        reset_dirs(self.scripts_dir)
        # 下载配置文件ks/comps/release.srpm
        self.build_logger.info("开始下载集成所需文件到集成目录")
        download_file(self.params.get('ks_path'), dir_=self.build_cfg_dir, logger=self.build_logger)
        download_file(self.params.get('comps_path'), dir_=self.build_cfg_dir, logger=self.build_logger)
        if self.lorax_templates_url and self.lorax_templates_url.startswith("http"):
            download_file(self.params.get('lorax_templates_url'), dir_=self.build_cfg_dir, logger=self.build_logger)
        download_file(self.params.get('scripts_dir'), dir_=self.scripts_dir, logger=self.build_logger)
        self.ks_file_path = os.path.join(self.build_cfg_dir, self.ks_file)
        self._update_status("参数获取完成： " + str(self.params), self.process, None)

    def check_mash(self, **kwargs):
        self.mash_httpd_path = str(kwargs.get("mash_repo", kwargs.get("mash_httpd", ''))).strip()
        self.mash_httpd_path = self.mash_httpd_path.replace(",", "\n").replace("，", "\n")
        self.build_logger.info(f" mash仓库地址是： {self.mash_httpd_path}")
        file_write(self.cfg_file, f"\n mash-repo:{self.mash_httpd_path}")
        BizAssert.has_value(self.mash_httpd_path, "mash失败，无法进行集成。")

        self.mash_log = str(kwargs.get("mash_log", ""))
        if url_reachable(self.mash_log, logger=self.build_logger) and '.log' in self.mash_log:
            self.mash_log_name = os.path.basename(self.mash_log)
        else:
            self.mash_log = None
            self.mash_log_name = None
        self.mash_list = str(kwargs.get("mash_list", ""))
        self.mash_sum = str(kwargs.get("mash_sum", ""))
        self.check_iso_log()

    @retry(delay=3, backoff=3, tries=5)
    def _update_status(self, msg, percent, status):
        """celery实时状态更新以及信息回传"""
        _update_celery(self._update_celery, self.build_logger, msg, percent, status, self.task_id)

    def init_mock_env(self, config_root_dir="/etc/mock/"):
        """初始化mock环境"""
        self.process = 25
        self._update_status("初始化mock构建环境", self.process, None)
        if self.params.get("mock_cfg"):
            self.mock_cfg_file = f'/etc/mock/{self.params.get("mock_cfg")}.cfg'
        else:
            self.mock_cfg_file = generate_mock_config(self.params, self.build_mocktag, self.build_logger,
                                                      config_root_dir=config_root_dir)
        if self.params.get('pungi_url') or self.params.get('lorax_url'):
            cmd = f"sh {config_root_dir}mock_.sh  {self.lorax_templates_url} {self.build_mocktag} " \
                  f"{self.params.get('target_arch')} {self.params.get('pungi_url')} {self.params.get('lorax_url')}"
        else:
            cmd = f"sh {config_root_dir}mock_.sh  {self.lorax_templates_url} {self.build_mocktag} " \
                  f"{self.params.get('target_arch')}"
        if self.mock_cfg_file:
            res = run_command(cmd, self.build_logger, error_message="mock环境初始化失败")
            self.command_logger.info(f'【CMD】mock初始化\t命令:{cmd}\t状态:{res}')
            if f"{res}" != "0":
                self.build_logger.info("mock环境初始化失败！")
                return False
            else:
                self.build_logger.info(f"mock环境初始化成功！Tag:{self.params.get('tag')}")
                return True
        self.build_logger.info("mock配置文件生成失败！")
        return False

    def copy_iso_to_dir(self, mock_isos_dir):
        """01-拷贝iso文件至本地构建目录"""
        if os.path.exists(mock_isos_dir) and os.path.exists(self.build_isos):
            self._update_status('move ' + mock_isos_dir + ' to ' + self.build_isos, self.process, None)
            self.build_logger.info("将Mock的ISO移动到 build目录")
            move_dirs(mock_isos_dir, self.build_isos)
        # 下载mash的日志到本地
        if self.mash_log:
            wget_remote_dirs(self.build_logger, self.mash_log, self.build_log)
            self.build_logger.info(f"下载mash的日志到本地：{self.build_log}")
        else:
            self.build_logger.warning(f"没有mash任务，无Mash日志文件。mash地址：{self.mash_httpd_path}")

    def find_iso_name(self):
        """02-列出iso名称"""
        if os.path.isdir(self.build_isos):
            for root, dirs, files in os.walk(self.build_isos):
                for f in files:
                    file_name = os.path.join(root, f)
                    if file_name.endswith('.iso') and file_name.find('netinst') == -1:
                        iso_path = file_name.replace(BUILD_PATH, '')
                        return iso_path
        return ""

    def get_iso_size(self):
        """03-检查iso大小"""
        for root, dirs, files in os.walk(self.build_isos):
            for f in files:
                file_name = os.path.join(root, f)
                if file_name.endswith('.iso') and file_name.find('netinst') == -1:
                    iso_size = os.path.getsize(file_name)
                    return iso_size
        return ""

    def check_iso_log(self):
        """04-获取iso_log路径"""
        self.build_logger.info(f"【Step-01/11】: {self.series} 获取iso_log路径")
        try:
            mash_ = self.mash_httpd_path.strip().split("\n")
            if len(mash_) == 1:
                wget_remote_dirs(self.build_logger, mash_[0].strip() + "/repodata",
                                 self.build_log + os.sep + "mash/repodata")
            else:
                for i, repo in enumerate(mash_):
                    wget_remote_dirs(self.build_logger, repo.strip() + "/repodata",
                                     self.build_log + os.sep + f"mash/repodata-{i}")
        except Exception as e:
            self.build_logger.error(f"错误信息： {e}")

        if not self.mash_httpd_path and self.mash_log:
            # mash失败时覆盖build log
            download_file(self.mash_log, dir_=self.build_log, logger=self.build_logger)
            delete_dirs(f"{self.build_log}/build-{self.task_id[0:4]}.log", self.build_logger)
            move_dirs(f"{self.build_log}/{self.mash_log_name}",
                      f"{self.build_log}/build-{self.task_id[0:4]}.log")
        if os.path.exists(self.build_log) and len(os.listdir(self.build_log)) > 0:
            iso_log = f"{self.build_log}/build-{self.task_id[0:4]}.log"
            return iso_log.replace(BUILD_PATH, '')
        else:
            raise RuntimeError("日志初始化失败。")

    def check_rpm(self):
        """
        检查iso内包是否含有rhel字样
        检查是否包含黑名单包
        """
        packages_path = f"{self.build_mockroot}/root/buildiso/Packages"
        package_file = ""
        black_exit_rpms = []
        for f in os.listdir(self.build_isos):
            if f.lower().endswith(f"-{self.target_arch}-packages.txt"):
                package_file = f"{self.build_isos}/{f}"
                break

        self.build_logger.info(f"{self.series} Package列表为{package_file}")
        if self.params.get('mash_blacklist_path'):
            download_file(self.params.get('mash_blacklist_path'), dir_=self.build_cfg_dir, logger=self.build_logger)
            mash_blacklist = f"{self.build_cfg_dir}/{url_filename(self.params.get('mash_blacklist_path'))}"
            black_exit_rpms = check_rpm_name_blacklist(package_file, mash_blacklist, self.build_logger)
        if self.params.get("check_blacklist", True) and len(black_exit_rpms):
            self.build_logger.info(f"【Step-10/11】: 黑名单软件包为 {black_exit_rpms} ")
            raise BuildException("含有黑名单软件")
        sensitive_exit_rpms = check_rpm_name_sensitive(package_file, SENSITIVE_KEYWORDS, self.build_logger)
        if self.params.get("check_sensitive", True) and len(sensitive_exit_rpms):
            self.build_logger.info(f"【Step-10/11】: 敏感软件包为 {sensitive_exit_rpms} ")
            self.tags.append("含有敏感软件")

        for root, dirs, files in os.walk(packages_path):
            for f in files:
                file_name = os.path.join(root, f)
                if not file_name.endswith(".rpm") or not read_rpm_header(file_name):
                    raise BuildException(f"软件包{file_name}不可用，无法读取Header信息。")
        self.build_logger.info(f"{self.series} 软件包名称黑名单、敏感词、是否是正确软件包 校验通过")

    def checksum_iso(self):
        """05-生成iso的md5值和sha256值"""
        isos_dir = self.build_isos
        iso_name = self.iso_name
        cmd1 = f"cd {isos_dir}; isohybrid -u {iso_name}" if self.target_arch == "x86_64" else f"echo '当前架构 {self.target_arch} 不架构支持isohybrid' "
        cmd2 = f"cd {isos_dir}; implantisomd5 --force {iso_name}"
        cmd3 = f"cd {isos_dir}; checkisomd5 {iso_name}"
        cmd4 = f"cd {isos_dir}; sha256sum {iso_name} > {iso_name}.sha256sum"
        index = 0
        for cmd in [cmd1, cmd2, cmd3, cmd4]:
            ok = run_command(cmd, self.build_logger, f"ISO校验失败: {cmd}")
            self.build_logger.info(f"【CMD】ISO集成后处理工作\t命令:{cmd}\t状态:{ok}")
            if index != 0 and ok != 0:
                raise BuildException(f"ISO校验失败: {cmd}")

        iso_sha256 = f"{isos_dir}/{iso_name}.sha256sum"
        if os.path.isfile(iso_sha256):
            sha256_str = open(iso_sha256, encoding="utf-8").read()
            if sha256_str:
                self._update_status("ISO校验完成", self.process, None)
                return sha256_str.split(" ")[0]
            else:
                raise BuildException("iso校验失败")
        else:
            raise BuildException(f"iso校验失败,无sha256文件：{iso_sha256}")

    def create_package_list(self, package_dir, pkgs_list):
        """创建iso内packages列表"""
        into_chroot_env(self.build_mockroot)
        self._update_status(f"{self.series}创建iso内packages列表", self.process, None)
        args = rf"""find {package_dir} |grep "\.rpm$"|xargs rpm -qp --qf %{{N}}-%{{V}}-%{{R}}.%{{ARCH}}.rpm\\n """ \
               + f""" | sort > {pkgs_list}"""
        ok = run_command(args, error_message="创建packages-list失败")
        exit_chroot_env()
        self.command_logger.info(f'【CMD】创建iso内packages列表\t命令:{args}\t状态:{ok}')
        self.pkg_list = pkgs_list

    def create_srcpackage_list(self, package_dir):
        """创建iso内packages列表"""
        into_chroot_env(self.build_mockroot)
        self._update_status(f"{self.series}创建iso内src_packages列表", self.process, None)
        args = rf"""find {package_dir} |grep "\.rpm$"|xargs rpm -qpi |grep "Source RPM" | awk '{{print $4}}' """ \
               + f""" | sort | uniq > {self.src_pkgs_list}"""
        run_command(args, error_message="创建packages-list失败")
        exit_chroot_env()

    def create_package_sum(self, package_dir, pkgsum):
        """创建iso内packages-sha256sum列表"""
        into_chroot_env(self.build_mockroot)
        md5_args = f"sha256sum `find {package_dir} |grep rpm` > {pkgsum}"
        run_command(md5_args, error_message="创建sha256sum-list失败")
        exit_chroot_env()

    def create_env_package_list(self):
        """创建iso内packages-sha256sum列表"""
        self.generate_build_env_info()
        env_pkg_args = f"rpm -qa >>  {self.build_env}"
        run_command(env_pkg_args, self.build_logger, "查询宿主机环境软件包失败")

    def gen_suffix_sqlite_fp(self, repo_url):
        """
        根据仓库的路径，不带repodata那一级别，获取 primary.sqlite.xx 的压缩后缀
        Args:
            repo_url: xx/

        Returns:
            xz | bz2 | gz2
        """
        suffix = ""
        repo_url = repo_url.replace(FILE_SCHEMA, '') + REPODATA_PATH
        if repo_url.startswith("http"):
            response = send_request(repo_url, verify=False)
            url = ""
            if response.status_code == 200:
                url = re.compile(URL_REPODATA_SQLITE).findall(response.text)
            assert url
            suffix = url[0].split(".")[-1]
            repo_url += url[0]
        elif os.path.exists(repo_url):
            for fn in os.listdir(repo_url):
                if fn.find("primary.sqlite") >= 0:
                    suffix = fn.split(".")[-1]
                    repo_url = repo_url.replace(FILE_SCHEMA, '') + fn
                    break
        else:
            self.build_logger.error(
                f"获取primary.sqlite的压缩后缀失败，协议不被支持。 repo_url: {repo_url} {os.path.isdir(repo_url)}")
        return suffix, repo_url

    def create_repo_package_list(self, repo_url, file_path):
        self.build_logger.info(f"通过repo：{repo_url}, 生成pkglsit：{file_path}")
        try:
            suffix, _ = self.gen_suffix_sqlite_fp(repo_url)
            if not suffix:
                raise BuildException(f"repo_url ： {repo_url} 没有db文件")
            self.compress_sqlite_name = self.compress_sqlite_name + "." + suffix
            self.build_logger.info(f"数据库位置是：{self.compress_sqlite_name}")
            yum_package_sum = self.get_package_list_and_sum(repo_url, suffix)

            if yum_package_sum:
                with open(file_path, "w") as txt:
                    txt.write(f"yum源地址为：{repo_url}\n")
                    for pak in yum_package_sum.keys():
                        txt.write(f"{pak}\t{yum_package_sum.get(pak)}\n")
            else:
                self.build_logger.warning("yum软件包记录文件生成失败。")
        except Exception as e:
            traceback.print_exc()
            self.build_logger.error(f"创建yum包列表失败，失败原因为: {e}， repo_url ： {repo_url}")

    def create_iso_package_list(self, package_url):
        """创建iso内packages列表"""
        self._update_status("创建iso pkg list", self.process, None)
        self.create_repo_package_list(package_url, self.iso_pkgs_list)

    def create_yum_package_list(self, yum_url):
        """创建iso内packages列表"""
        self._update_status("创建yum pkg list", self.process, None)
        self.create_repo_package_list(yum_url, self.yum_pkgs_list)

    def create_mash_package_list(self):
        """
        创建mash源packages列表
        需要传入mash源地址
        """
        self._update_status("创建mash源package列表", self.process, None)
        mash_database_url = self.build_log + os.sep + "mash"
        self.create_repo_package_list(mash_database_url, self.mash_pkgs_list)

    def gen_sqlite_file(self, repo_path: str, suffix="bz2"):
        """

        Args:
            repo_path:
            suffix:

        Returns:

        """
        _, sqlite_fp = self.gen_suffix_sqlite_fp(repo_path)
        self.build_logger.info(f"获取软件包sum的repo是：{repo_path}, SQLITE: {sqlite_fp}")
        delete_dirs(self.compress_sqlite_name)
        delete_dirs(self.decompress_sqlite_name)
        try:
            if sqlite_fp.startswith("http"):
                r = send_request(sqlite_fp, verify=False)
                if r.status_code == 200:
                    open(self.compress_sqlite_name, "wb").write(r.content)
                else:
                    self.build_logger.info("repo数据库下载失败")
            elif repo_path.startswith(BUILD_PATH):
                self.compress_sqlite_name = sqlite_fp
            else:
                raise BuildException(f"repo_path:  {repo_path} 的协议不被支持")
        except Exception as e:
            traceback.print_exc()
            raise ConnectionError(f"下载源数据库失败.Msg:{e}。Url : {repo_path}")
        if os.path.isfile(self.compress_sqlite_name):
            if suffix == "bz2":
                with bz2.BZ2File(self.compress_sqlite_name) as fr, open(self.decompress_sqlite_name, "wb") as fw:
                    shutil.copyfileobj(fr, fw)
            else:
                with lzma.open(self.compress_sqlite_name, 'rb') as input_file:
                    try:
                        with open(self.decompress_sqlite_name, 'wb') as output_file:
                            shutil.copyfileobj(input_file, output_file)
                            self.build_logger.info(f"DB文件解压成功：{self.decompress_sqlite_name}")
                    except lzma.LZMAError as e:
                        os.remove(self.decompress_sqlite_name)
                        self.build_logger.error(f"SQLite的压缩格式「{_}」不被支持：「{e}」")
        else:
            self.build_logger.error(
                f"primary.sqlite文件 「{self.compress_sqlite_name}」不存在 : {os.path.isfile(self.compress_sqlite_name)}")

    def get_package_list_and_sum(self, repo_path: str, suffix="bz2") -> dict:
        """
        根据传入的primary.sqlite.bz2提取出对应源的package列表,md5值
        return 包列表与对应md5的字典
        """
        self.gen_sqlite_file(repo_path, suffix)
        pkg_sum = {}
        cs = conn = None
        try:
            if not os.path.isfile(self.decompress_sqlite_name):
                return {}
            conn = sqlite3.connect(self.decompress_sqlite_name)
            cs = conn.cursor()
            cs.execute("SELECT pkgId,name,location_href FROM packages")
            for row in cs.fetchall():
                pkg_sum[row[2]] = row[0]
            return pkg_sum

        except Exception as e:
            if cs:
                cs.close()
            if conn:
                conn.close()
            raise ConnectionError(f"数据库链接失败！{e} 。 {self.decompress_sqlite_name}")

    def clean_mock_env(self):
        if self.params.get("clean_env", 0):
            """06-清理mock构建环境"""
            self.process = 90
            delete_dirs(f"/etc/mock/{self.build_mocktag}", self.build_logger)
            self._update_status("清理mock构建环境", self.process, None)
            delete_dirs(f"/var/lib/mock/{self.build_mocktag}", self.build_logger)
            delete_dirs(f"/var/lib/mock/{self.build_mocktag}-bootstrap", self.build_logger)

    def clean_build_dir(self):
        """07-清理系统构建环境"""
        self._update_status(f"clean {self.build_path}", self.process, None)
        if os.path.isdir(self.build_path):
            shutil.rmtree(self.build_path)

    def fix_mock_env(self):
        # 修复lorax写pkglists时，遇到软件包文件名含中文问题,非3.6版本没此问题吗。。。。
        process = subprocess.Popen(PYTHON_MINOR_CMD, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   cwd='/usr/bin/')
        out = process.stdout.readline()
        minor = out.decode(encoding='utf-8', errors='ignore') if isinstance(out, bytes) else str(out)
        if not minor:
            raise RuntimeError("无法获取mock内 python版本")
        fp = f"/usr/lib/python3.{minor.strip()}/site-packages/pylorax/treebuilder.py"
        if os.path.isfile(fp):
            code = open(fp, "r", encoding="utf-8").read()
            str_old = """with open(joinpaths(pkglistdir, pkgobj.name), "w") as fobj:"""
            str_new = """with open(joinpaths(pkglistdir, pkgobj.name), "w", encoding="utf-8") as fobj: # edit by kylin """
            code = code.replace(str_old, str_new)
            open(fp, "w", encoding="utf-8").write(code)
            print("修复lorax写pkglists带中文问题。")

    def prep_create_iso(self):
        """构建过程准备工作，函数入口，根据类多次继承"""
        self.build_logger.info(f"【Step-02/11】: {self.series} 构建过程准备工作")
        self.build_logger.info("准备ISO集成环境")
        if self.init_mock_env():
            # 输出lorax版本
            try:
                self.build_logger.info(f"Mock（{self.mock_cfg_file}）环境初始化成功，检查lorax、pungi是否安装。")
                into_chroot_env(self.build_mockroot)
                _, lorax_v = run_command_with_return("rpm -qa |grep lorax")
                _, pungi_v = run_command_with_return("rpm -qa |grep pungi")
                _, oemaker_v = run_command_with_return("rpm -qa |grep oemaker")
                # mock环境修改
                self.fix_mock_env()
                exit_chroot_env()
                self.command_logger.info(f'【INFO】版本检查:lorax版本{lorax_v}，pungi版本{pungi_v}')
                self.build_logger.info(
                    f"\nlorax version:\n{lorax_v}\npungi version:\n{pungi_v}\noemaker version:{oemaker_v}\n")
                self.build_logger.info("ISO集成环境构建成功。")
            except Exception as e:
                traceback.print_exc()
                self.build_logger.info(f"ISO集成环境构建失败，原因是{e}")
                raise AssertionError(f"ISO集成环境构建失败，原因是{e}")
        else:
            raise AssertionError("Mock环境初始化失败")

    def generate_build_env_info(self):
        """ 记录一些额外信息 ipAddr, 磁盘占有率信息， cpu使用率信息， 机器时间， 系统信息 """
        file_write(self.build_env, "\n编译环境如下：\n")
        content = ""
        content += "ipAddr : " + os.getenv("IP", "localhost") + "\n"
        content += "date : " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())) + "\n"
        content += "systemInformation : " + os.popen('uname -a').read() + "\n"
        content += "cpuInformation : \n" + os.popen('lscpu').read() + "\n"
        file_write(self.build_env, content)

    def check_ks_and_comps(self):
        """检查comps里面的包是否都在ks文件内"""
        self.build_logger.info("校验comps所需软件包是否都在ks文件内")
        comps_pak_set = get_comps_list(self.comps_file_path)
        comps_pak_set = {x for x in comps_pak_set if x is not None}
        ks_pak_set = get_ks_list(self.ks_file_path)
        ks_pak_set = {x for x in ks_pak_set if x is not None}
        if all([ks_pak_set, comps_pak_set]):
            more = "\n".join(comps_pak_set - ks_pak_set)
            if not more:
                self.build_logger.info("comps所需软件包都在ks文件内")
            else:
                self.build_logger.error(f"comps所需软件包不在ks文件内，请检查：\n{more}")
                open(self.build_warn_file, "a", encoding="utf-8").write(f"comps软件包不在ks文件的有：{more}\n")
                open(self.build_warn_file, "a", encoding="utf-8").write(">>>" * 20)
        else:
            if not ks_pak_set:
                self.build_logger.error("ks文件不存在，请检查。")
                open(self.build_warn_file, "a", encoding="utf-8").write("ks文件不存在，请检查。\n")
                open(self.build_warn_file, "a", encoding="utf-8").write(">>>" * 20)
            else:
                self.build_logger.error("comps文件不存在，请检查。")
                open(self.build_warn_file, "a", encoding="utf-8").write("comps文件不存在，请检查。\n")
                open(self.build_warn_file, "a", encoding="utf-8").write(">>>" * 20)

    def check_ks_and_package(self):
        """检查ks文件和packages列表是否一致 """
        if all([os.path.isfile(self.ks_file_path),
                os.path.isfile(self.build_isos + os.sep + os.path.basename(self.pkg_list))]):
            file_ = open(self.ks_file_path, "r")
            ks_list = file_.read().split("\n")[2:]
            ks_list = list(filter(lambda x: len(x), ks_list))[:-1]
            ks_list = set(ks_list)
            file_.close()

            file_ = open(self.build_isos + os.sep + os.path.basename(self.pkg_list), "r")
            pkgs_list = file_.read().split("\n")
            pkgs_list = list(filter(lambda x: len(x), pkgs_list))
            pkgs_list = list(map(lambda x: common_split_filename(x)[0], pkgs_list))
            pkgs_list = set(pkgs_list)
            file_.close()
            if ks_list != pkgs_list:
                self.build_logger.error("KS文件和软件包列表校验【不】通过。")
                more = "\n".join(ks_list - pkgs_list)
                try:
                    open(self.build_warn_file, "a", encoding="utf-8").write(
                        f"\nKS文件比较软件包列表不一致，多了：\n{more}\n")
                    open(self.build_warn_file, "a", encoding="utf-8").write(">>>" * 20)
                except Exception as e:
                    self.build_logger.error(f"警告文件写入失败，具体信息：{e}")
                self.build_logger.error(f"KS多了：\n{more}")
                less = "\n".join(pkgs_list - ks_list)
                try:
                    open(self.build_warn_file, "a", encoding="utf-8").write(
                        f"\nKS文件比较软件包列表不一致，少了：\n{less}\n")
                    open(self.build_warn_file, "a", encoding="utf-8").write(">>>" * 20)
                except Exception as e:
                    self.build_logger.error(f"警告文件写入失败，具体信息：{e}")
                # self.build_logger.error(f"KS少了：\n{less}")
            else:
                self.build_logger.info("KS文件和软件包列表校验通过")

        else:
            self.build_logger.warning(
                f"ks:{self.ks_file_path}。pkg:{os.path.isfile(self.build_isos + os.sep + os.path.basename(self.pkg_list))}")
            self.build_logger.warning("ks文件或者软件包列表文件不存在，无法对包列表是否一致进行检测。")

    def copy_repodata(self):
        """
        将iso内的repodata数据复制到logs/repodata目录下
        Returns:
        """
        repodata_path = f"{self.build_mockroot}/root/buildiso/repodata"
        self.build_logger.info(
            f"{self.series} 收集repodata数据,源目录 {repodata_path} 存在：{os.path.isdir(repodata_path)}")
        if not os.path.exists(repodata_path):
            os.makedirs(repodata_path)
        if not os.path.exists(self.build_log + os.sep + 'repodata'):
            os.makedirs(self.build_log + os.sep + 'repodata')
        self.build_logger.info(
            f"{self.series} 收集repodata数据,目的目录 {self.build_log + os.sep}repodata 存在："
            f"{os.path.isdir(self.build_log + os.sep + 'repodata')}")
        if os.path.isdir(repodata_path):
            copy_dirs(f"{repodata_path}", self.build_log + os.sep + 'repodata', self.build_logger)

    def copy_productinfo(self):
        """
        将mock环境内的productinfo文件复制到配置文件目录，并重命名为productinfo.txt
        Returns:

        """
        copy_dirs(self.product_file, self.build_cfg_dir + "/productinfo.txt")

    def check_repo_dep(self):
        """
        校验 repodata 依赖是否满足
        Returns:
        """
        iso_err_msg = ISOErrorEnum.ISO_REPOCLOSURE
        fp_iso_repoclosure = self.build_log + os.sep + 'iso_repoclosure.txt'

        try:
            cmd3 = f'mock -n -r {self.build_mocktag} "dnf repoclosure --arch={self.target_arch} --arch=noarch --repofrompath=MashRepoDepCheck,{self.mash_httpd_path} --repo=MashRepoDepCheck --check=MashRepoDepCheck " ' \
                   f' --chroot --enable-network '
            cmd4 = f"su pungier -c '{cmd3}' "
            self.build_logger.info(f"执行命令：{cmd4}")
            res = rum_command_and_log(cmd4, self.build_log + os.sep + 'mash_repoclosure.txt', self.build_logger)
            self.command_logger.info(f'【CMD】检测Mash仓库是否缺失依赖\t命令:{cmd4}\t状态:{res}')
            if not res:
                self.tags.append(ISOErrorEnum.BASE_REPOCLOSURE)
        except Exception as e2:
            self.build_logger.error(f"Mash 检查 repodata 依赖满足情况 失败, {e2}")

        try:
            self.build_logger.info("ISO 检查 repodata 依赖情况")
            cmd = f'mock -n -r {self.build_mocktag} "dnf repoclosure --arch={self.target_arch} --arch=noarch --repofrompath=ISORepoDepCheck,file:///root/buildiso/ --repo=ISORepoDepCheck --check=ISORepoDepCheck" ' \
                  f' --chroot --enable-network '
            cmd = f"su pungier -c '{cmd}' "
            self.build_logger.info(f"执行命令：{cmd}")
            res = rum_command_and_log(cmd, fp_iso_repoclosure, self.build_logger)
            self.command_logger.info(f'【CMD】检测ISO是否缺失依赖\t命令:{cmd}\t状态:{res}')
            if not res:
                self.tags.append(iso_err_msg)
        except Exception as e1:
            self.tags.append(iso_err_msg)
            self.build_logger.error(f"{iso_err_msg}, {e1} " + "\n" + open(fp_iso_repoclosure, 'r').read())
            raise BuildException(iso_err_msg)

    def check_lorax_log(self):
        txt = open(f"{self.build_log}/lorax/pylorax.log").read()
        err_pkgs = set(list(re.findall(r"Error in .* in rpm package (.*)", txt)))
        if err_pkgs:
            self.tags.append(f"Lorax异常包: {','.join(err_pkgs)}")

    def get_nkvers_info(self):
        """
        获取系统的nkvers信息
        Returns:
        """
        try:
            self.build_logger.info(f"{self.series} 获取系统的nkvers信息")
            cmd1 = f'mock -n -r {self.build_mocktag} --shell "nkvers" '
            cmd1 = f"su pungier -c '{cmd1}' "
            run = run_command_with_return(cmd1, self.build_logger, "获取nkvers失败")
            if run[0]:
                self.nkvers = run[1].decode("utf-8")
                self.build_logger.info(f"nkvers信息是：\n{self.nkvers}")
        except Exception as e1:
            self.build_logger.error(f"获取系统nkvers信息失败, {e1}")

    def get_repo_create_time(self):
        """
        获取仓库创建时间
        """
        mash_log_file = f'{self.build_log}/mash-*.log'

        # 定义要查找的关键字
        keywords = ["Mash开始,Tag"]

        # 定义时间戳的正则表达式模式
        time_pattern = r'(\d{6} \d{2}:\d{2}:\d{2})'

        try:
            # 查找并处理所有匹配的日志文件
            for log_file in glob.glob(mash_log_file):
                with open(log_file, 'r') as file:
                    for line in file:
                        for keyword in keywords:
                            if line.find(keyword) >= 0:
                                time_stamp = extract_time_from_line(line, time_pattern)
                                if time_stamp:
                                    time_array = time.strptime("20" + time_stamp, "%Y%m%d %H:%M:%S")
                                    self.repo_create_time = time.strftime("%Y-%m-%d %H:%M:%S", time_array)
                                    self.build_logger.info(f"获取仓库创建时间是,{self.repo_create_time}")
                                    break
        except Exception as e1:
            traceback.print_exc()
            self.build_logger.error(f"获取仓库创建时间失败,{e1}")

    def copy_lorax_log(self):
        """
        将lorax目录下的 log、conf、txt 复制到logs/lorax目录下
        Returns:

        """
        lorax_path = f"{self.build_mockroot}/lorax"
        self.build_logger.info(f"{self.series} 收集lorax日志,源目录 {lorax_path} 存在：{os.path.isdir(lorax_path)}")
        if not os.path.isdir(self.build_log + os.sep + "lorax"):
            os.makedirs(self.build_log + os.sep + "lorax")
        self.build_logger.info(
            f"{self.series} 收集lorax日志,目的目录 {self.build_log + os.sep}lorax 存在："
            f"{os.path.isdir(self.build_log + os.sep + 'lorax')}")
        if os.path.isdir(lorax_path):
            copy_dirs(f"{lorax_path}", self.build_log + os.sep + 'lorax', self.build_logger)
            delete_dirs(self.build_log + os.sep + 'lorax/outfiles/', self.build_logger)

    def iso_file_check(self):
        """
        校验ISO文件是否符合要求
            不能包含debuginfo、debugsource、source软件包
            是否都签名
        Returns:

        """
        for fp, fn in get_file_list(self.build_isos):
            if fn.endswith(".rpm") and (
                    fn.find("-debuginfo-") >= 0 or fn.find("-debugsource-") >= 0 or fn.endswith(".src.rpm")):
                self.build_logger.warning(f"ISO文件中包含debuginfo、debugsource、source软件包，文件名：{fn}")
                open(self.build_warn_file, "a", encoding="utf-8").write(f"文件不应该存在：{fn}\n")
                open(self.build_warn_file, "a", encoding="utf-8").write(">>>" * 20)
            sig = get_rpm_sign(fn + os.sep + fp)
            if fn.endswith(".rpm") and sig.find(SIG_KEY) < 0:
                open(self.build_warn_file, "a", encoding="utf-8").write(f"软件包签名不对：{fn}\n")
                open(self.build_warn_file, "a", encoding="utf-8").write(">>>" * 20)

    def get_lorax_templates_sha256sum(self) -> str:
        if self.lorax_templates_url.startswith("http"):
            fp = self.build_cfg_dir + self.lorax_templates_url.split("/")[-1]
            v = get_file_sha256sum(fp)
            self.lorax_templates_sha256sum = v
            self.build_logger.info(f"获取lorax_templates_sha256sum的值：{v}")
            cmd = f"sha256sum {fp} > {fp}.sha256sum"
            run_command(cmd, self.build_logger, "lorax_templates_sha256sum文件创建失败！")
            return v
        else:
            self.build_logger.info(f"lorax_templates_sha256sum的值为空，因为不是url：{self.lorax_templates_url}")
            return ""

    def post_create_iso(self):
        """#11 构建过程完成后整理工作，函数入口，根据类多次继承"""
        iso_name = self.find_iso_name()
        iso_size = self.get_iso_size()
        sha256_value = self.checksum_iso()
        self.build_logger.info(f"【Step-11/11】: {self.series} 构建过程完成后的整理工作")
        self.check_ks_and_package()
        self.check_ks_and_comps()
        self.check_rpm()  # 对package进行检测
        if all([self.mock_cfg_file, self.build_cfg_dir]):
            self.build_logger.info(f"mock内的配置文件({self.mock_cfg_file})复制到build目录:{self.build_cfg_dir}")
            shutil.copy(self.mock_cfg_file, self.build_cfg_dir)
        else:
            self.build_logger.warning(f"Mock配置文件保存失败，请检查。 {self.mock_cfg_file} && {self.build_cfg_dir}")
        self.copy_lorax_log()
        self.check_lorax_log()
        self.copy_repodata()
        self.get_nkvers_info()
        self.copy_productinfo()
        self.get_repo_create_time()
        self.release_resource()
        self.clean_mock_env()
        self.get_lorax_templates_sha256sum()
        self.process = 100
        self.dracut = self.get_dracut_params()
        self._update_status("🎉🧨本次ISO集成构建工作完成🧨🎉", self.process, None)
        self.repos = get_repos_info_rpm(base_path=self.build_mockroot, pungi=False)
        return iso_name, iso_size, sha256_value, self.nkvers, self.tags, self.repos, self.lorax_templates_sha256sum, \
            self.repo_create_time, f'''{self.dracut}'''

    def create_manifest(self):
        """
        创建ISO的manifest文件
        Returns:

        """
        self.build_logger.info(f"创建ISO的manifest文件 {self.build_isos}/{self.iso_name}.manifest")
        cmd = f"isoinfo -R -f -l -i {self.build_isos}/{self.iso_name} | grep -v '/TRANS.TBL$' | sort >> {self.build_isos}/{self.iso_name}.manifest"
        run_command(cmd, self.build_logger, "manifest文件创建失败！")

    def download_post_action(self, u):
        # 下载 kylin-post-actions 文件
        self.build_logger.info("尝试下载 post-action 文件")

        post_files = ["/.kylin-post-actions-nochroot", "/.kylin-post-actions", "/.discinfo", "/.kyinfo"]
        for file in post_files:
            url = u.rstrip("/") + file
            if send_request(url, verify=False, method="HEAD").status_code == 200:
                ok = download_file(url, self.not_boot_file, logger=self.build_logger)
                if not ok:
                    raise RuntimeError(f"下载{file}文件失败")
                self.build_logger.info(f"下载{file}文件成功: {url}->{self.not_boot_file}")
            else:
                self.build_logger.debug(f"{file} 文件不存在")

        # 老V10 x86架构支持
        post_dir_files = ["/.post/fonts-gb18030.sh", "/.post/runatinstall", "/.post/runatroot"]
        for one in post_dir_files:
            url = u.rstrip("/") + one
            if send_request(url, verify=False, method="HEAD").status_code == 200:
                ok = download_file(u + one, self.not_boot_file + ".post/", logger=self.build_logger)
                if not ok:
                    raise RuntimeError(f"下载{one}文件失败")
                self.build_logger.info(f"下载{one}文件成功: {url} -> {self.not_boot_file}")
            else:
                self.build_logger.debug(f"{one} 文件不存在 {url}")

    def check_iso_file(self):
        """
        ISO集成后的自检
        Returns:

        """
        iso_path = os.path.join(self.build_isos + os.sep + self.iso_name)
        if os.path.isfile(iso_path):
            build_warn_info = []

            # 校验ISO文件是否是ISO格式文件
            cmd = f"isoinfo -d -i {iso_path} | grep ISO"
            if run_command(cmd, self.build_logger, error_message="") != 0:
                build_warn_info.append("ISO文件非ISO格式文件")
                self.tags.append("非ISO")

            if self.target_arch == "x86_64" and not is_isohybrid(iso_path):
                build_warn_info.append("x86 ISO未启用isohybrid！")
                self.tags.append("未启用isohybrid")
            if os.path.getsize(iso_path) < 500 * 1024 * 1024:  # 校验ISO大小是否超过500M
                build_warn_info.append("ISO文件大小小于500M")
                self.tags.append("大小异常")

            # 对于不符合的情况，写到WARNING文件中
            reason = "\n".join(build_warn_info)
            open(self.build_warn_file, "a", encoding="utf-8").write(f"{reason}\n")
            self.build_logger.info(f"ISO文件 {self.iso_name} 校验通过")
        else:
            self.build_logger.error(f"ISO文件：{self.iso_name} 不存在")

    def download_not_boot_file(self):
        """Step-5.5"""
        self.build_logger.info("开始下载 非启动文件")
        for u in self.params.get('not_boot_dir').split("\n"):
            if u and u.strip():
                wget_remote_dirs(self.build_logger, u, self.not_boot_file)
                self.download_post_action(u)
        copy_dirs(self.not_boot_file, f"{self.build_mockroot}{self.build_inmock}", logger_=self.build_logger)
        self.command_logger.info(
            f'【MOVE】将 {self.not_boot_file} 下的文件复制到 {f"{self.build_mockroot}{self.build_inmock}"}')
        self.check_addon_dep()

    def check_addon_dep(self):
        self.gen_addon_repodata()
        iso_err_msg = ISOErrorEnum.BASE_REPOCLOSURE
        fp_addon_repoclosure = self.build_log + os.sep + 'addon_repoclosure.txt'
        try:
            self.build_logger.info("ISO 检查 内软件包 依赖情况")
            cmd1 = f'mock -n -r {self.build_mocktag} "dnf repoclosure --arch={self.target_arch} --arch=noarch --repofrompath=AddonRepoDepCheck,file://{self.addon_repodata}  --repo=AddonRepoDepCheck --check=AddonRepoDepCheck" ' \
                   f' --chroot --enable-network '
            cmd2 = f"su pungier -c '{cmd1}' "
            self.build_logger.info(f"执行命令：{cmd2}")
            if not rum_command_and_log(cmd2, fp_addon_repoclosure, self.build_logger):
                self.tags.append(iso_err_msg)
        except Exception as e1:
            self.tags.append(iso_err_msg)
            self.build_logger.error(f"{iso_err_msg}, {e1} " + "\n" + open(fp_addon_repoclosure, 'r').read())

    def gen_addon_repodata(self):
        try:
            self.build_logger.info(f"【Step-5.5/11】: {self.series} createrepo创建 addon repo源")
            self.process = 60
            self._update_status(f"{self.series} createrepo创建addon repo源", self.process, None)
            into_chroot_env(self.build_mockroot)
            cmd = f'mkdir {self.addon_repodata} && cd {self.build_inmock} && createrepo -d -g "/root/{self.comps_file}" --outputdir {self.addon_repodata} {self.build_inmock}'
            ok = run_command(cmd, error_message=f"{self.series} createrepo失败")
            if ok != 0:
                raise RuntimeError(f"{self.series} [{self.task_id[:4]}] createrepo失败")
            exit_chroot_env()
            self._update_status("addon createrepo 检测完成！", self.process, None)
        except Exception as e:
            self.build_logger.error(f"【Step-5.5/11】: {self.series} createrepo创建addon repo源失败.{e}")

    def write_productinfo2file(self, product_file):
        """ #7 7/8/SP 系-生成.productinfo文件"""
        product_file = product_file or self.product_file
        self.process = 70
        self.build_logger.info(f"【Step-07/11】: {self.series} mock内生成产品信息文件")
        self._update_status(f"{self.series} mock内生成产品信息文件", self.process, None)
        info = self.params.get('product_info')

        # 客户端自定义
        if info:
            with open(product_file, 'w') as f:
                f.write(self.params.get('product_name'))
                f.write('\n')
                f.write(info)
                f.write(os.linesep)
        elif os.path.isfile(f"{self.build_mockroot}/etc/.productinfo"):
            # 读取kylin-release内productinfo
            shutil.copy(f"{self.build_mockroot}/etc/.productinfo", product_file)
            self.build_logger.info("==移动kylin-release的productinfo文件")
        else:
            # 客户端未定义且kylin-release也没有，自动生成
            info = '/'.join([self.params.get('release'), f"{self.params.get('target_arch')}-{self.params.get('build')}",
                             self.cur_day])
            with open(product_file, 'w') as f:
                f.write(self.params.get('product_name'))
                f.write('\n')
                f.write(info)
                f.write(os.linesep)

    def release_resource(self):
        """集成后释放资源"""
        for i in open("/proc/mounts", "r"):
            if i.find(self.build_mocktag) >= 0:
                mount_path = i.split(" ")[1]
                cmd = f"umount {mount_path}"
                ok, err = run_command_with_return(cmd)
                self.build_logger.info(f"集成后umount lorax资源：{ok} {err} ON {mount_path}")

    def insert_grub_ks_cmd(self, root_path):
        """插入ks文件自动安装指令"""
        install_ks_url = self.params.get("ks_install_url")
        if install_ks_url:
            self.build_logger.info(f"【无人值守】插入ks文件自动安装指令：{install_ks_url}")
            ks_name = "." + install_ks_url.split("/")[-1]
            wget.download(install_ks_url, out=root_path + os.sep + ks_name, bar=None)
            insert_res = insert_install_ks(root_path, ks_name, self.build_logger, self.params.get("target_arch"))
            if not insert_res:
                raise BuildException(f"根据{install_ks_url} 新增入grub文件失败")


def match_build_id(n):
    # build**
    match = re.findall(r"-(build\d+)-", n.lower())
    if not match:
        # alpha-**
        match = re.findall(r"-(alpha-?\d+)-", n.lower())
    return match[0] if match else ""


def extract_arch_from_path(path) -> str:
    """
     从路径中提取架构
    Args:
        ipaddress:路径 例如：/opt/integration_iso_files/pungi-kylin/Kylin-Server-11-1215_1455-83.97/compose/Server/sw_64/iso/xxxxxx.iso
    Returns: 架构 例如：sw_64

    """
    path_obj = Path(path)
    parts = path_obj.parts
    result = ""
    arch_map = {
        "ARM64": "aarch64",
        "X86": "x86_64",
        "Loongarch64": "loongarch64",
    }
    arch_list = ["aarch64", "x86_64", "loongarch64", "sw_64", "ARM64", "X86", "Loongarch64"]
    for i, part in enumerate(parts):
        for arch in arch_list:
            if arch in part:
                result = arch
                break
        if result:
            break
    if not result:
        result = find_arch_by_name(path)
    if result in arch_map:
        return arch_map[result]
    return result


def iso_upload(params, work_dir, pattern, task_id, pungi_koji,
               upload_result_url="/iso-manager/server-api/iso-manager/isos"):
    iso_filepaths = []
    files = get_file_list(work_dir, exclude_keywords=['net', 'boot', 'source'])
    server_api = upload_result_url.split('api')[0]
    for fp, file in files:
        if file.endswith(".iso"):
            iso_filepaths.append(fp + os.sep + file)
    if not iso_filepaths:
        data = {
            **params,
            "task_id": task_id,
            "task_status": states.FAILURE,
            "ipaddress": HOST_IP,
            "isoname": "",
            "isosize": 0,
            "isolog": pungi_koji.path.log.topdir().replace(BUILD_PATH, '') if pungi_koji.path.log.topdir().startswith(
                BUILD_PATH) else pungi_koji.path.log.topdir(),
            'repo_path': pungi_koji.path.work.pkgset_repo(),
            "sha256": None,
            "err_msg": "",
            "md5": "",
            "work_dir": work_dir,
            "upload_result_url": upload_result_url,
            'is_pungi': True,
            "tag": pungi_koji.conf.get("pkgset_koji_tag"),
            "build_id": pungi_koji.build_id or match_build_id(pungi_koji.conf.get("image_name_format").get("^Server")),
            "repos": pungi_koji.repos,
            "dracut": pungi_koji.dracut
        }
        logger.info(f"回传数据：{data}")

        r = send_request(upload_result_url, data=data, method="POST")
        logger.info(f"{work_dir} 回传结果：{r.text}")
        return {'current': 100, 'total': 100, 'status': 'Task Failed!',
                'result': {"work_dir": work_dir, "msg": "没有ISO文件或者sha256文件"}}

    for iso_filepath in iso_filepaths:
        isoname = iso_filepath.replace(BUILD_PATH, '')
        isosize = get_file_size(iso_filepath)
        # 生成文件sha256信息
        generate_sha256sum(iso_filepath)
        # 生成repos信息
        arch = extract_arch_from_path(iso_filepath)
        pungi_koji.repos = get_repos_info_rpm(base_path=work_dir, pungi=True, arch=arch)
        # 生成dracut参数
        pungi_koji.dracut = get_drauct_augment_pungi(iso_filepath)
        # 生成镜像内软件包列表信息
        generate_packages_list(iso_filepath, arch)
        # 生成仓库生成时间
        repo_create_time = get_repo_create_time(iso_filepath)
        if os.path.isfile(iso_filepath) and os.path.isfile(iso_filepath + EXT_SHA256SUM):
            sha256 = open(iso_filepath + EXT_SHA256SUM).read().split(" ")[0]
            arch = get_base_arch(isoname)
            # ISO回传
            data = {
                **params,
                "task_id": task_id,
                "task_status": states.SUCCESS,
                "ipaddress": HOST_IP,
                "isoname": isoname,
                "mash_httpd": server_api + 'integration_iso_files' + isoname.split("Server/")[0] + f"Everything/{arch}/",
                "isosize": isosize,
                "isolog": isoname.split("compose")[0] + "logs/",
                "sha256": sha256,
                "err_msg": "",
                "md5": sha256,
                "work_dir": work_dir,
                "upload_result_url": upload_result_url,
                'is_pungi': True,
                'target_arch': arch,
                'tag': pungi_koji.conf.get('pkgset_koji_tag'),
                "csrf": uuid.uuid4().hex,
                "compose_type": pungi_koji.conf.get("compose_type"),
                "koji_ip": KOJI_SERVER_PORT[pungi_koji.conf.get("koji_profile").split("_")[-1]],
                "repos": pungi_koji.repos,
                "dracut": pungi_koji.dracut,
                "repo_create_time": repo_create_time
            }
            logger.info(f"回传数据：{data}")
            r = send_request(upload_result_url, method="POST", data=data)
            logger.info(f"ISO: {iso_filepath} 回传结果：{r.text}")
        else:
            print(f"没有ISO文件或者sha256文件，{iso_filepath} . {iso_filepath + EXT_SHA256SUM}")
            raise exceptions.Ignore(f"没有ISO文件或者sha256文件，{iso_filepath} . {iso_filepath + EXT_SHA256SUM}")


def generate_sha256sum(iso_filepath):
    cmd = f"sha256sum {iso_filepath} > {iso_filepath}.sha256sum"
    run_command(cmd)


def generate_packages_list(iso_filepath, arch):
    rpm_packages_file = iso_filepath.replace('.iso', f'-{arch}-packages.txt')
    srpm_packages_file = iso_filepath.replace('.iso', '-src_packages.txt')
    repodata_path = os.path.join(Path(iso_filepath).parent.parent, 'os')  # 寻找os文件路径

    if not os.path.exists(repodata_path):
        return False, 'repodata路径不存在'
    try:
        rim = load_repodata(repodata_path)
        rpms = rim.get_rpm_fullname_list_all()
        srpms = rim.get_srpm_fullname_list_all()
        if rpms:
            with open(rpm_packages_file, 'w') as f: f.write('\n'.join(rpms))
        if srpms:
            with open(srpm_packages_file, 'w') as f: f.write('\n'.join(srpms))
        return True, '软件包数据获取成功'
    except Exception as e:
        return False, e


def get_repo_create_time(iso_filepath):
    pungi_log = os.path.join(iso_filepath[:iso_filepath.find('compose')], 'logs/global/pungi.global.log')  # 寻找log文件路径
    repo_time = None
    with open(pungi_log, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if line.find('Getting koji event') > 0:  # 从log日志获取koji event时间
                repo_time = line.split(' ')[:2]
                repo_time = datetime.strptime(' '.join(repo_time), "%Y-%m-%d %H:%M:%S")
                break
        return repo_time


def get_drauct_augment_pungi(iso_filepath) -> str:
    """
    获取系统的drauct信息
    Returns:
    """
    initrd_file = "/images/pxeboot/initrd.img"
    temp_dir = tempfile.mkdtemp()
    cmd = ['isoinfo', '-i', iso_filepath, '-x', initrd_file]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            with open(f'{temp_dir}/initrd.img', 'wb') as f:
                f.write(result.stdout)
        initrd_fp = f'{temp_dir}/initrd.img'
        drauct = run_lsinitrd(initrd_fp)
        return drauct
    except Exception as e:
        return f"获取drauct消息失败,{str(e)}"
    finally:
        shutil.rmtree(temp_dir)


def get_data_from_build_cfg(_iso, WEB_URL, _logger=logger):
    """
    通过ISO，获取ISO的构建信息
    Args:
        _logger:
        WEB_URL:
        _iso:

    Returns:
        {
            "mash-repo"："",
            "release":"",
            "build":"",
            "yum_url":"",
        }
    """
    _build_info = {}
    try:
        work_dir = ROOT_PATH_ISO_PATH + _iso.isoname[:_iso.isoname.rfind("/") + 1]
        path_build_cfg = os.path.join(work_dir, "conf", "build.cfg.txt")
        if os.path.exists(path_build_cfg):
            _logger.info(f"配置文件: {str(path_build_cfg)}")
            with open(path_build_cfg, encoding="utf-8") as f:
                for line in f.readlines():
                    re_findall = re.findall(BUILD_PARAMS, line)
                    for re_find in re_findall:
                        if len(re_find) == 2:
                            _build_info[re_find[0].strip('\'",')] = re_find[1].strip('\'",')
        else:
            conf_file = ROOT_PATH_ISO_PATH + _iso.isoname.split("compose")[0] + "logs/global/config-copy/kylin.conf"
            if os.path.exists(conf_file):
                _logger.info(f"配置文件: {str(path_build_cfg)}")
                with open(path_build_cfg, encoding="utf-8") as f:
                    for line in f.readlines():
                        if line.startswith("#"):
                            continue
                        line = line.split("#")[0].strip()
                        re_findall = re.findall(BUILD_PARAMS, line)
                        for re_find in re_findall:
                            if len(re_find) == 2:
                                _build_info[re_find[0].strip()] = re_find[1].strip('\'", ')
                _build_info = {
                    "mash-repo": WEB_URL + "/compose" + _iso.isoname.split("Server")[0] + "Everything/",
                    "release": _build_info.get('release_short') + "-" + _build_info.get('release_version'),
                    "build": _build_info.get('release_type'),
                }
    except Exception as _e:
        _logger.error(f"从build_cfg文件获取数据失败, 原因: {str(_e)}")

    return _build_info


def get_kylin_repos_path(repos_path):
    for root, dirs, files in os.walk(repos_path):
        for file in files:
            if file.startswith('kylin-repos') and file.endswith('.rpm'):
                return os.path.join(root, file)


def get_repos_info_rpm(base_path, pungi, arch: str = "") -> str:
    """
    获取系统的repos信息
    Returns:
    """
    if pungi:
        repo_path = f"{base_path}/compose/Everything/{arch}/os/Packages"
    else:
        repo_path = f"{base_path}root/buildiso/Packages/"
    temp_dir = tempfile.mkdtemp()
    repos_contents = []
    kylin_repos_path = get_kylin_repos_path(repo_path)
    try:
        proc1 = subprocess.Popen(['rpm2cpio', kylin_repos_path], stdout=subprocess.PIPE)
        proc2 = subprocess.Popen(['cpio', '-idmv'], stdin=proc1.stdout, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, cwd=temp_dir)
        proc1.stdout.close()
        proc2.communicate()

        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    repos_contents.append(f.read())
        repos = "\n".join(repos_contents)
        return repos
    except Exception as e:
        return f"获取repos消息失败,{str(e)}"
    finally:
        shutil.rmtree(temp_dir)
