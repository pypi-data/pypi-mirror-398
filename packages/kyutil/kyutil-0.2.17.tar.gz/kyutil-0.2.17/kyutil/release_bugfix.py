# -*- coding: UTF-8 -*-
"""
@Project ：kyutil 
@File    ：bugfix.py
@IDE     ：PyCharm 
@Author  ：xuyong@kylinos.cn
@Date    ：2025/3/17 下午3:04 
@Desc    ：说明：
"""
import os

import yaml

from kyutil.mock import into_chroot_env, exit_chroot_env
from kyutil.shell import run_command, run_get_str


class ReleaseBugfix:

    def import_capser_sp(self):
        """sp1-aarch64-外部引入capser文件, 建议脚本化"""
        if self.params.get('target_arch') == 'aarch64' \
                and os.path.exists(f"{self.build_mockroot}{self.build_inmock}/capser"):
            self._update_status("v10sp-aarch64-引入capser文件夹SP", 60, None)
            into_chroot_env(self.build_mockroot)
            # 兼容ft2000plus版本
            cmd1 = "mkdir %s/kernel && cp -a %s/Packages/kernel-core* %s/kernel" % (
                self.build_inmock, self.build_inmock, self.build_inmock)
            cmd2 = "cd %s/kernel && rpm2cpio kernel-core*|cpio -ivd" % self.build_inmock
            cmd3 = "cp -a %s/kernel/boot/uImage* %s/casper/uImage-ft2000plus" % (self.build_inmock, self.build_inmock)
            cmd4 = "cp -a %s/kernel/boot/uImage* %s/casper/uImage" % (self.build_inmock, self.build_inmock)
            cmd5 = "cp -a %s/kernel/boot/dtb* %s/casper/" % (self.build_inmock, self.build_inmock)
            cmd6 = "rm -rf %s/kernel" % self.build_inmock
            for cmd in [cmd1, cmd2, cmd3, cmd4, cmd5, cmd6]:
                ok = run_command(cmd, error_message="修正 casper/Image文件失败")
                if ok != 0:
                    raise RuntimeError(f"{self.series} [{self.task_id[:4]}] 修正 casper/Image文件失败")
            # 兼容ft1500版本的特殊处理
            cmd7 = "mkdir -p %s/casper/ft1500 && cp -a %s/images/pxeboot/initrd.img %s/casper/ft1500" % (
                self.build_inmock, self.build_inmock, self.build_inmock)
            cmd8 = "cd %s/casper/ft1500 && xzcat -d initrd.img | cpio -iduvm 2>&1 >/dev/null" % self.build_inmock
            cmd9 = "rm -rf %s/casper/ft1500/initrd.img" % self.build_inmock
            cmd10 = "mv -f %s/repo_bak.sh  %s/casper/ft1500/lib/dracut/hooks/cmdline/27-parse-anaconda-repo.sh" % (
                self.build_inmock, self.build_inmock)
            cmd11 = "find %s/casper/ft1500 | cpio -oH newc | xz --check=crc32 -9 > %s/casper/initrd.img" % (
                self.build_inmock, self.build_inmock)
            cmd12 = "rm -rf %s/casper/ft1500" % self.build_inmock
            for cmd in [cmd7, cmd8, cmd9, cmd10, cmd11, cmd12]:
                ok = run_command(cmd, error_message="修正casper/ft1500文件失败")
                if ok != 0:
                    raise RuntimeError(f"{self.series} [{self.task_id[:4]}] 修正casper/ft1500文件失败")
            exit_chroot_env()

    def cut_initrd(self, config_fp):  # f"{SOURCE_PATH}/src/build/mips/mips_initrd.yaml"
        """mips64el-裁剪initrd中kernel组件"""
        self._update_status("Mips-裁剪initrdSP", 60, None)
        if self.params.get('target_arch') == 'mips64el':
            # 读取mips配置文件
            if os.path.isfile(config_fp):
                conf_files = open(config_fp).read()
                conf = yaml.load(conf_files, Loader=yaml.FullLoader)
            else:
                self._update_status("未处理定制化文件,因为没有找到配置文件", self.process, None)
                return
            # 获取kernel版本
            into_chroot_env(self.build_mockroot)
            _cmd1 = "ls %s/Packages/ |grep kernel-4" % self.build_inmock
            kernel = (run_get_str(_cmd1, "kernel-4").replace(".rpm", "")).split('-')
            kernel_version = '%s-%s' % (kernel[-2], kernel[-1])
            # 获取处理路径
            mips_kernel_dir = conf.get('mips_kernel_dir')
            mips_kernel_files = conf.get('mips_kernel_files')
            mips_other_files = conf.get('mips_other_files')
            cmd0 = "rm -rf %s/kylin-logo %s/capser %s/repo_bak.sh" % (
                self.build_inmock, self.build_inmock, self.build_inmock)
            # 裁剪initrd.img以适配mips64el固件
            cmd1 = "mkdir %s/initrd && cp -a %s/images/pxeboot/initrd.img %s/initrd" % (
                self.build_inmock, self.build_inmock, self.build_inmock)
            cmd2 = "cd %s/initrd && xzcat -d initrd.img | cpio -iduvm 2>&1 >/dev/null" % self.build_inmock
            cmd3 = "rm -rf %s/initrd/initrd.img" % self.build_inmock
            for cmd in [cmd0, cmd1, cmd2, cmd3]:
                run_command(cmd, error_message="删除定制化文件失败")
            for mips_kernel_file in mips_kernel_files:
                _cmd4 = "rm -rf %s/initrd/%s" % (
                    self.build_inmock, os.path.join(mips_kernel_dir, kernel_version, mips_kernel_file))
                run_command(_cmd4, error_message="删除kernel文件失败")
            for mips_other_file in mips_other_files:
                _cmd5 = "rm -rf %s/initrd/%s" % (self.build_inmock, mips_other_file)
                run_command(_cmd5, error_message="删除other文件失败")
            cmd6 = "find %s/initrd | cpio -oH newc | xz --check=crc32 -9 > %s/images/pxeboot/initrd.img" % (
                self.build_inmock, self.build_inmock)
            cmd7 = "rm -rf %s/initrd" % self.build_inmock
            for cmd in [cmd6, cmd7]:
                run_command(cmd, error_message="删除定制化文件失败")
            exit_chroot_env()
