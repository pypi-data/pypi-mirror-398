#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
@File ：install_ks.py
"""
import re

from logzero import logger


def get_grub_label(root_path: str, _logger=logger):
    """根据grub文件获取标签"""
    with open(root_path + "/EFI/BOOT/grub.cfg", "r+") as f_grub:
        grub_content = f_grub.read()
        # 获取标签
        l_abel = re.findall(r"inst.stage2=hd:LABEL=(.+) ", grub_content)
        if not l_abel:
            _logger.error(f"匹配grub文件标签失败,匹配格式为：inst.stage2=hd:LABEL=(.+) ")
            return False, ""
        return True, l_abel[0]


def insert_ks_cmd(file_content: str, key_word: str, insert_label: str):
    """向grub文件中插入ks相关命令"""
    post = file_content.find(key_word)
    if post != -1:
        # 插入ks启动文件命令
        file_content = (
                file_content[: post + len(key_word)]
                + insert_label
                + file_content[post + len(key_word):]
        )
        return file_content
    else:
        return None


def insert_install_ks(root_path: str, ks_file: str, _logger=logger, arch="x86_64"):
    """
    对EFI/BOOT/grub.cfg 或者 isolinux/isolinux.cfg 添加 指定ks文件 安装命令
    x86 会对boot 和 isolinux中的进行修改，arm 仅仅修改boot中的
    """
    try:
        bool_flag, label = get_grub_label(root_path, _logger)
        if not bool_flag:
            _logger.error(f"匹配grub文件标签失败,匹配格式为：search --no-floppy --set=root -l '(.+)'")
            return False
        _logger.info(f"标签是： {label}")
        insert_label = f" inst.ks=hd:LABEL={label}:/{ks_file}"
        _logger.info(f"新增入grub文件init语句为： {insert_label}")
        # 文件路径及匹配内容
        tu_relation_efi = (
            root_path + "/EFI/BOOT/grub.cfg",
            f" /images/pxeboot/vmlinuz inst.stage2=hd:LABEL={label}",
        )
        tu_relation_isolinux = (
            root_path + "/isolinux/isolinux.cfg",
            f"append initrd=initrd.img inst.stage2=hd:LABEL={label}",
        )
        # x86仅修改两个
        if arch.find("x86") >= 0:
            l_insert = [tu_relation_efi, tu_relation_isolinux]
        else:
            l_insert = [tu_relation_efi]
        for tu_re in l_insert:
            _logger.info(f"新增文件：{tu_re[0]}, 查找内容为：{tu_re[1]}")
            with open(tu_re[0], "r+") as f_grub:
                grub_content = f_grub.read()
                grub_content = insert_ks_cmd(grub_content, tu_re[1], insert_label)
                if not grub_content:
                    _logger.error(f"新增ks命令失败，关键字：{tu_re[1]}，插入内容：{insert_label}")
                    return False
                f_grub.seek(0)
                f_grub.write(grub_content)
        return True
    except FileNotFoundError as f_e:
        _logger.error(f"需要替换的grub.cfg 文件未找到 : {f_e}")
        return False
