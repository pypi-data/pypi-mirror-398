#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：kyutil 
@File    ：build_ns8.py
@IDE     ：PyCharm 
@Author  ：xuyong@kylinos.cn
@Date    ：2025/3/27 下午11:25 
@Desc    ：说明：
"""
import os
import subprocess

from kyutil.build_base import ReleaseOSBase
from kyutil.config import FILE_SCHEMA, PYTHON_MINOR_CMD
from kyutil.download import wget_remote_dirs
from kyutil.file import copy_dirs, delete_dirs, file_str_switch, move_dirs
from kyutil.file_compare import run_lsinitrd, find_initrd_img
from kyutil.mock import into_chroot_env, exit_chroot_env
from kyutil.shell import run_command


class ReleaseOSEl8(ReleaseOSBase):
    """8系集成构建类"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.series = "el8"
        # 基类初始化
        # 8系构建过程目录
        # 通用iso输出名称
        self.iso_name = self.params.get('iso_name') if self.params.get('iso_name') else \
            f"{self.params.get('release')}-{self.params.get('target_arch')}" \
            f"-{self.params.get('build')}-{self.cur_day}.iso"
        self.scripts = []

    def mount_proc_system(self):
        self.build_logger.info(f"{self.series} 尝试挂载proc")
        into_chroot_env(self.build_mockroot)
        run_command("mount -t proc proc /proc", error_message=f"{self.series} 挂载proc失败")
        exit_chroot_env()

    def umount_proc_system(self):
        self.build_logger.info(f"{self.series} 尝试卸载proc")
        into_chroot_env(self.build_mockroot)
        run_command("umount /proc", error_message=f"{self.series} 卸载proc失败")
        exit_chroot_env()

    def mock_pungi_gather(self):
        """#3 8系-pungi-gather收集包"""
        ###  解决pungi不支持https源问题
        self.build_logger.info(f"【Step-02.5/11】: {self.series} 修改pungi-gather源码")
        new_str = '            module_hotfixes=True,\nsslverify=False,\n'
        old_str = "            module_hotfixes=True,"
        into_chroot_env(self.build_mockroot)
        process = subprocess.Popen(PYTHON_MINOR_CMD, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   cwd='/usr/bin/')
        out = process.stdout.readline()
        minor = out.decode(encoding='utf-8', errors='ignore') if isinstance(out, bytes) else str(out)
        if not minor:
            raise RuntimeError("无法获取mock内 python版本")
        dnf_wrapper = f"/usr/lib/python3.{minor.strip()}/site-packages/pungi/dnf_wrapper.py"
        if os.path.exists(dnf_wrapper):
            file_str_switch(dnf_wrapper, old_str, new_str, _logger=self.command_logger, reason='修复pungi不支持ssl问题')
        exit_chroot_env()
        self.build_logger.info(f"修复pungi-gather  {dnf_wrapper}  SSL问题")
        self.build_logger.info(f"【Step-03/11】: {self.series} pungi-gather收集包")
        self.build_logger.info(f"{self.series}执行pungi命令，从mash下载软件包到Packages目录")
        self.process = 40
        _dep = "" if str(self.params.get('deps')) == "True" else '--nodeps'
        _source = '--exclude-source' if self.params.get('source') != 'True' else ''
        _debug = '--exclude-debug'
        self._update_status(f"{self.series}默认mock内执行pungi-gather-收集包", self.process, None)
        self._update_status("ks文件修改repo地址", self.process, None)
        for i, repo in enumerate(self.mash_httpd_path.strip().split("\n")):
            new_str = f"repo --name={self.params.get('tag').replace('/', '_')}-{i} --baseurl={repo}\n%packages\n"
            file_str_switch(f"{self.build_cfg_dir}/{self.ks_file}", "%packages", new_str, reason="KS文件配置仓库地址")

        # 复制进mock环境内
        copy_dirs(f"{self.build_cfg_dir}/{self.ks_file}", f"{self.build_mockroot}/root/{self.ks_file}",
                  self.build_logger)
        # chroot执行
        into_chroot_env(self.build_mockroot)
        cmd1 = f"pungi-gather --config /root/{self.ks_file} --download-to {self.build_inmock}/Packages " \
               f"--arch {self.params.get('target_arch')} {_source} {_debug} {_dep}"
        ok = run_command(cmd1, error_message=f"{self.series} pungi-gather失败")
        self.command_logger.info(f'【CMD】pungi-gather拉包\t命令:{cmd1}\t状态:{ok}')
        if ok != 0:
            raise RuntimeError(f"{self.series} [{self.task_id[:4]}] pungi-gather失败")
        else:
            self.process = 45
            self._update_status("pungi-gather成功", self.process, None)
        exit_chroot_env()

    def mock_create_repo(self):
        """#4 8系-createrepo创建本地源"""
        self.build_logger.info(f"【Step-04/11】: {self.series} createrepo创建本地源")
        self.process = 50
        self._update_status(f"{self.series} mock内执行createrepo-创建源", self.process, None)
        if self.params.get('before_repo_package'):
            wget_remote_dirs(self.build_logger, self.params.get('before_repo_package'), self.before_repo_package)
            copy_dirs(self.before_repo_package, f"{self.build_mockroot}{self.build_inmock}/Packages", self.build_logger)
        copy_dirs(f"{self.build_cfg_dir}/{self.comps_file}", f"{self.build_mockroot}/root/{self.comps_file}",
                  self.build_logger)
        if os.path.isfile(f"{self.build_mockroot}/root/{self.comps_file}"):
            self.build_logger.info(
                f"{self.series} comps文件移动到了mock环境里:{self.build_mockroot}/root/{self.comps_file}")
        else:
            self.build_logger.error(
                f"{self.series} comps文件没有移动到了mock环境里:{self.build_mockroot}/root/{self.comps_file}")
            raise RuntimeError("comps文件没有移动到了mock环境里")
        into_chroot_env(self.build_mockroot)
        cmd = f'cd /root/buildiso/ && createrepo -d -g /root/{self.comps_file} /root/buildiso'
        ok = run_command(cmd, error_message=f"{self.series} createrepo失败")
        self.command_logger.error(f'【CMD】制作镜像内repo\t命令:{cmd}\t状态:{ok}')
        if ok != 0:
            raise RuntimeError(f"{self.series} [{self.task_id[:4]}] createrepo失败")
        exit_chroot_env()
        self._update_status("createrepo后文件下载，并复制", self.process, None)
        if self.params.get('after_repo_package'):
            wget_remote_dirs(self.build_logger, self.params.get('after_repo_package'), self.after_repo_package)
            copy_dirs(self.after_repo_package, f"{self.build_mockroot}{self.build_inmock}/Packages", self.build_logger)
            self.command_logger.info(
                f'【MOVE】将 {self.after_repo_package} 下的文件复制到 {f"{self.build_mockroot}{self.build_inmock}/Packages"} ')
        self.check_repo_dep()
        self.generate_rpmgraph()

    def gen_lorax_source_cmd(self):
        cmd = ''
        for _, repo in enumerate(self.mash_httpd_path.split("\n")):
            cmd += f"-s \'{repo}\' "
        return cmd

    def get_lorax_cmd(self):
        """获取lorax对应版本命令格式"""
        product = self.params.get('product_name')
        version = self.params.get('version')
        release = self.params.get('release')
        volid = self.params.get('volid')
        variant = f"-t \'{self.params.get('variant')}\'" if self.params.get('variant') else ""
        if self.params.get('lorax_cmd'):
            lorax_cmd = f"cd {self.build_inmock}/lorax; {self.params.get('lorax_cmd')}"
        elif self.params.get('tag') == "v10-2203sp2-hpc":
            lorax_cmd = f"cd {self.build_inmock}/lorax; lorax -p \'{product}\' -v \'{version}\' -r \'{release}\' " \
                        f"--force --rootfs-size=5 --isfinal --nomacboot  -t   \'Server\'  --volid=\'{volid}\' {variant} " + \
                        f"{self.gen_lorax_source_cmd()} " \
                        f"{self.build_inmock}/lorax/outfiles --noverifyssl "
        else:
            lorax_cmd = f"cd {self.build_inmock}/lorax; lorax -p \'{product}\' -v \'{version}\' -r \'{release}\' " \
                        f"--force --rootfs-size=5 --isfinal --nomacboot  --volid=\'{volid}\' {variant} " \
                        f"{self.gen_lorax_source_cmd()} " \
                        f"{self.build_inmock}/lorax/outfiles --noverifyssl "
        return lorax_cmd

    def fix_process_file(self):
        """#6 8系 - 定制修改lorax启动文件 TODO:test"""
        self.build_logger.info(f"【Step-06/11】: {self.series} 定制修改lorax结果")
        cmd = f'mock -n -r {self.build_mocktag} "cp -a {self.build_inmock}/lorax/outfiles/. {self.build_inmock}"' \
              f' --chroot'
        _cmd = f"su - {self.user} <<EOF\n {cmd} \nEOF"
        self._update_status(f"{self.series}mock内 lorax 结果文件复制到 buildiso目录", self.process, None)
        run_command(_cmd, self.build_logger, "移动启动文件失败")
        # self.insert_grub_ks_cmd(self.build_mockroot + self.build_inmock)
        self.build_logger.info("将lorax结果备份到 " + f"/{self.build_mockroot}/lorax")
        move_dirs(f"{self.build_mockroot}{self.build_inmock}/lorax", f"/{self.build_mockroot}/lorax")
        delete_dirs(f"{self.build_mockroot}{self.build_inmock}/lorax", self.build_logger)
        delete_dirs(f"{self.build_mockroot}{self.build_inmock}/GBL", self.build_logger)

    def write_productinfo(self):
        """ #7 8系-生成.productinfo文件"""
        self.product_file = f"{self.build_mockroot}{self.build_inmock}/.productinfo"
        self.write_productinfo2file(self.product_file)

    def mkisofs_iso_file(self):
        """ #8
        函数功能：8系-mkisofs集成iso文件
        默认未开启参数：-input-charset utf-8
        已支持arch：aarch64、mips64el、loongarch64
        """
        self.iso_file_check()
        self.build_logger.info(f"【Step-08/11】: {self.series} mock内执行mkisofs集成ISO")
        self.process = 80
        self._update_status(f"{self.series} mock内执行mkisofs集成ISO", self.process, None)

        delete_dirs(f"{self.build_mockroot}{self.build_inmock}/lorax", self.build_logger)

        if self.params.get('mkisofs_cmd'):
            cmd = 'mock -n -r %s "cd %s;' % (self.build_mocktag, self.build_inmock) \
                  + self.params.get('mkisofs_cmd') + '" --chroot'
        else:
            if self.params.get('target_arch') == 'x86_64':
                cmd = 'mock -n -r %s "cd %s; mkdir -p /root/isos/logs && mkisofs -log-file %s -joliet-long -v -U -J -R -T -V \'%s\' \
                       -m repoview -m boot.iso -b isolinux/isolinux.bin -c isolinux/boot.cat \
                       -no-emul-boot -boot-load-size 4 -boot-info-table -eltorito-alt-boot \
                       -e images/efiboot.img -no-emul-boot -o /root/isos/%s . ; cd /root/isos ;" --chroot' % (
                    self.build_mocktag, self.build_inmock, "/root/isos/logs/mkisofs.log", self.params.get('volid'),
                    self.iso_name)
            else:
                cmd = 'mock -n -r %s "cd %s; mkdir -p /root/isos/logs && mkisofs -log-file %s -joliet-long -v -U -J -R -T -V \'%s\' \
                -m repoview -m boot.iso -eltorito-alt-boot \
                -e images/efiboot.img -no-emul-boot -o /root/isos/%s . " --chroot' % (
                    self.build_mocktag, self.build_inmock, "/root/isos/logs/mkisofs.log", self.params.get('volid'),
                    self.iso_name)
        _cmd = f"su - {self.user} <<EOF\n {cmd} \nEOF"
        ok = run_command(_cmd, self.build_logger, "集成iso文件(mkisofs)失败")
        self.command_logger.info(f'【CMD】mkiso封装iso\t命令:{cmd}\t状态:{ok}')
        if ok != 0:
            raise RuntimeError(f"{self.series} [{self.task_id[:4]}] 集成iso文件(mkisofs)失败")
        return self.iso_name

    def create_package_files(self):
        """
        #9 ISO集成后的操作
        Returns:

        """
        self.build_logger.info(f"【Step-09/11】: {self.series} mock内生成packages列表和sha256sum列表")
        self._update_status(f"{self.series} mock内生成packages列表和sha256sum列表", self.process, None)
        package_dir = self.build_inmock + "/Packages"
        pkgs_list = f"{self.isos_inmock}/%s" % '-'.join(
            [self.params.get('release', "").replace(" ", '-'), self.params.get('target_arch'), 'packages.txt'])
        self.create_package_list(package_dir, pkgs_list)
        self.create_srcpackage_list(package_dir)
        self.create_iso_package_list(f"{FILE_SCHEMA}{self.build_mockroot + self.build_inmock}")
        self.create_yum_package_list(self.yum_url)
        self.create_mash_package_list()
        self.create_env_package_list()

    # 备份及检查工作
    def copy_iso(self):
        """#10 8系拷贝iso文件步骤"""
        self.build_logger.info(f"【Step-10/11】: {self.series} mock内生成packages列表和sha256sum列表")
        self.process = 90
        self._update_status(f"{self.series} Mock内拷贝ISO文件至构建目录", self.process, None)
        isos_dir = f"{self.build_mockroot}{self.isos_inmock}"
        self.copy_iso_to_dir(isos_dir)
        self.create_manifest()

    def script_before_mkisofs(self):
        self.process = 85
        # 获取目录下所有文件
        self.scripts = os.listdir(self.scripts_dir)
        # 遍历每个文件
        for script in self.scripts:
            # 判断文件是否以".sh"结尾
            if script.endswith(".sh"):
                # 记录执行日志
                self.build_logger.info(f"【Step-11/11】: {self.series} 执行前 {script} 脚本")
                # 更新执行状态
                self._update_status(f"{self.series} 执行前 {script} 脚本", self.process, None)
                # 构建脚本路径
                script_path = f"{self.scripts_dir}/{script}"
                # 调用子进程执行脚本
                os.system(f'cd {self.build_mockroot + self.build_inmock} && sh {script_path}')

    def get_dracut_params(self):
        try:
            initrd_path = find_initrd_img(self.build_mockroot)
            if not initrd_path:
                self.build_logger.error("未找到initrd.img文件")
                return False, '未找到initrd.img文件'
            dracut_params = run_lsinitrd(initrd_path)
            return True, dracut_params
        except Exception as e:
            return False, f"{e}"
