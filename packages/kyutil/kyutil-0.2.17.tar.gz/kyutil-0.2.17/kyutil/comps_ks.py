#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：kyutil 
@File    ：comps_ks.py
@IDE     ：PyCharm 
@Author  ：xuyong@kylinos.cn
@Date    ：2025/5/22 下午4:01 
@Desc    ：说明：
"""
import os
import shutil
from tempfile import TemporaryDirectory
from xml.etree import ElementTree as Et

from logzero import logger

from kyutil.base import BaseService
from kyutil.config import ROOT_PATH_ISO_PATH
from kyutil.file import un_gz
from kyutil.rpm_operation import mount_iso, unmount


class CompsKs(BaseService):
    # comps
    XML_SUFFIX = ".xml"
    XML_GZ_SUFFIX = ".xml.gz"
    REPODATA_PATH = "repodata"
    COMPS_XML_SUFFIX = "-comps.xml"
    COMPS_XML_PREFIX = "comps-"

    # comps 解析
    LANG_NAMESPACE_KEY = "{http://www.w3.org/XML/1998/namespace}lang"
    ZH_CH = "zh_CN"

    # ks
    PACKAGES_PATH = "Packages"
    KS_HEAD = 'repo --name= --baseurl=""'
    KS_PACKAGES = "%packages"
    KS_END = "%end"
    KS_SUFFIX = ".ks"

    def __init__(self, _logger=logger, **kwargs):
        super().__init__(**kwargs)
        self.logger = _logger

    def check_comps_file_content(self, comps_path):
        """校验comps文件内容
        """
        if not os.path.exists(comps_path):
            return False, "comps文件不存在"

        try:
            tree = Et.parse(comps_path)
            xml_root = tree.getroot()
            if not xml_root:
                return False, "comps文件不合规：不存在根节点"

            root_compliance, root_err_msg = self.check_comps_root(xml_root)
            group_compliance, group_err_msgs = self.check_comps_groups(xml_root)
            env_compliance, env_err_msgs = self.check_comps_environments(xml_root)
            if not all([root_compliance, group_compliance, env_compliance]):
                err_info = "comps文件不合规："
                if root_err_msg:
                    err_info += root_err_msg + "；"
                if group_err_msgs:
                    err_info += "分组错误：" + " ，".join(group_err_msgs) + "；"
                if env_err_msgs:
                    err_info += "环境错误： " + " ，".join(env_err_msgs) + "；"
                return False, err_info

            return True, "符合规范"
        except Et.ParseError as e:
            self.logger.error("comps文件不符合xml文件格式，解析失败 %s" % e)
            return False, "comps文件不合规： 不符合xml文件格式"

    @staticmethod
    def check_comps_root(root):
        """校验comps根节点内容
        """
        if root.tag != "comps":
            return False, "根节点不是comps"

        return True, ""

    @staticmethod
    def check_comps_groups(root):
        """
        校验comps文件的组元素
        校验规则内容如下:
            1. 是否包含重复组id, 重复不合规
            2. 组元素内元素是否正确， 包含元素： id， name， description， 其中packagelist存在空情况
        """
        groups = root.findall("group")
        if not groups:
            return False, "不存在元素 group"

        compliance_flag = True
        err_msgs = []
        group_ids = []
        for group in groups:
            group_id = group.find("id").text
            if group_id in group_ids:
                compliance_flag = False
                err_msgs.append("组 %s 重复" % group_id)

            group_ids.append(group_id)
            if not group_id:
                compliance_flag = False
                err_msgs.append("组name为 %s 的组内缺失必要元素 id" % group.find("name").text)

            if not group.findall("name"):
                compliance_flag = False
                err_msgs.append("组id为 %s 的组内缺失必要元素 name" % group_id)

            if not group.findall("description"):
                compliance_flag = False
                err_msgs.append("组id为 %s 的组内缺失必要元素 description" % group_id)

            if not group.find("packagelist"):
                compliance_flag = False
                err_msgs.append("组id为 %s 的组内缺失必要元素 packagelist，或者packagelist为空" % group_id)

        return compliance_flag, err_msgs

    @staticmethod
    def check_comps_environments(root):
        """
        校验comps文件的环境元素
        校验规则内容如下:
            1. 是否包含重复id, 重复不合规
            2. 环境元素内元素是否正确， 包含元素： id， name， description， 其中packagelist存在空情况
        """
        envs = root.findall("environment")
        if not envs:
            return False, "不存在元素 environment"

        compliance_flag = True
        err_msgs = []
        env_ids = []
        for env in envs:
            env_id = env.find("id").text
            if env_id in env_ids:
                compliance_flag = False
                err_msgs.append("环境 %s 重复" % env_id)

            env_ids.append(env_id)
            if not env_id:
                compliance_flag = False
                err_msgs.append("环境name为 %s 的环境内缺失必要元素 id" % env.find("name").text)

            if not env.findall("name"):
                compliance_flag = False
                err_msgs.append("环境id为 %s 的环境内缺失必要元素 name" % env_id)

            if not env.findall("description"):
                compliance_flag = False
                err_msgs.append("环境id为 %s 的环境内缺失必要元素 description" % env_id)

            if not env.find("grouplist"):
                compliance_flag = False
                err_msgs.append("环境id为 %s 的环境内缺失必要元素 grouplist" % env_id)

            if not env.find("optionlist"):
                compliance_flag = False
                err_msgs.append("环境id为 %s 的环境内缺失必要元素 optionlist" % env_id)

        return compliance_flag, err_msgs

    def check_whether_comps_by_the_content(self, f: str) -> bool:
        """解析xml文件，根据根节点tag是否为comps判断为compose文件
        """
        try:
            tree = Et.parse(f)
            root = tree.getroot()
            if root.tag == "comps":
                return True
            else:
                return False
        except Exception as e:
            self.logger.error("comps xml解析失败 %s" % e)
            return False

    def get_iso_path_by_iso_id(self, iso_id):
        """获取ISO文件存储绝对路径
        """
        filters = [self.model.id == iso_id]
        iso_mod = self.model.query.filter(*filters).one_or_none()
        if not iso_mod:
            return None

        iso_path = os.path.join(ROOT_PATH_ISO_PATH, iso_mod.isoname.strip("/"))
        self.logger.debug("根据iso_id: %s, 查询到ISO 的存储路径为: %s" % (iso_id, iso_path))

        return iso_path

    def get_iso_compose_file(self, iso_dir):
        # TODO: 是否符合要求
        for fp, _, fns in os.walk(iso_dir):
            for fn in fns:
                if fn.endswith(self.COMPS_XML_SUFFIX) or fn.startswith(self.COMPS_XML_PREFIX):
                    xml_file = os.path.join(iso_dir, fn)
                    if not os.path.exists(xml_file):
                        return os.path.join(iso_dir, "conf", fn)
                    self.logger.debug("ISO同目录comps文件为 %s " % xml_file)
                    break

    def get_iso_comps_env_group_by_iso_id(self, iso_id):
        """
        根据iso_id 获取iso内的环境分组信息
        """
        iso = self.get(iso_id)
        iso_path = ROOT_PATH_ISO_PATH + iso.isoname
        if not iso_path or not os.path.exists(iso_path):
            self.logger.error("iso %s 不存在。" % iso_id)
            return None

        iso_dir = os.path.dirname(iso_path)
        xml_file = self.get_iso_compose_file(iso_dir)

        if not xml_file or not os.path.exists(xml_file):
            self.logger.debug("ISO %s 下无comps文件" % iso_dir)
            exit_comps = self.traverse_iso_repodata_folder_to_get_comps(iso_path)
            if exit_comps:
                xml_file = iso_path.replace(".iso", self.COMPS_XML_SUFFIX)
            else:
                self.logger.error("遍历ISO %s repodata文件夹未找到comps文件")
                return None

        return self.parse_compose_xml(xml_file)

    @staticmethod
    def get_uservisible_group(group_info: dict):
        """
        根据所有得分组信息，获取所有分组中用户可见得分组， 字段uservisible  == "true"
        @param group_info:
        {
            "container-management": {
                "id": "container-management",
                "name": "Container Management",
                "name_zh_cn": "容器管理",
                "description_zh_cn": "用于管理 Linux 容器的工具。",
                "default": "true",
                "uservisible": "true"
            }, ......
        }
        @return:
        {
            "container-management": {
                "id": "container-management",
                "name": "Container Management",
                "name_zh_cn": "容器管理",
                "description_zh_cn": "用于管理 Linux 容器的工具。",
                "default": "true",
                "uservisible": "true"
            }, ......
        }
        """
        uservisiable_group = {}
        for g_id, g_info in group_info.items():
            if g_info.get("uservisible") == "true":
                uservisiable_group[g_id] = g_info
        return uservisiable_group

    def parse_compose_xml(self, xml_fp):
        """解析comps文件，返回ISO安装界面所示的 环境 - 分组 列表
        """
        if not os.path.exists(xml_fp):
            return None

        tree = Et.parse(xml_fp)
        root = tree.getroot()

        all_group = self.parse_xml_get_all_group(root)  # 解析获取xml内得所有分组
        visible_group = self.get_uservisible_group(all_group)  # 解析获取所有分组内 用户可见得分组
        env_group_info = self.parse_comps_get_env_group(root, all_group, visible_group)  # 解析comps中的环境-分组（包含可见分组）信息

        return env_group_info

    def parse_xml_get_all_group(self, xml_root):
        """
         解析comps xml文件，获取其中的可见分组
        @param xml_root: "ElementTree解析 getroot 获取的root根节点"
        @return:
        {
            "container-management": {
                "id": "container-management",
                "name": "Container Management",
                "name_zh_cn": "容器管理",
                "description_zh_cn": "用于管理 Linux 容器的工具。",
                "default": "true",
                "uservisible": "true"
            }, ......
        }
        """
        all_group_dict = {}
        for group in xml_root.findall("group"):
            group_id = group.find("id").text
            all_group_dict.setdefault(group_id, {})
            all_group_dict[group_id]["id"] = group_id
            for child in group:
                if child.tag == "name" and not child.attrib:
                    all_group_dict[group_id]["name"] = child.text

                # name 中文 中文描述
                if child.tag == ["description", "name"] and child.attrib.get(self.LANG_NAMESPACE_KEY) == self.ZH_CH:
                    all_group_dict[group_id]["description_zh_cn"] = child.text

                if child.tag in ["default", 'uservisible']:
                    all_group_dict[group_id][child.tag] = child.text

        return all_group_dict

    def parse_env_dict_group(self, child, all_groups, env_dict, env_id):

        if child.tag == "grouplist":
            for g_id in child.findall("groupid"):
                if not all_groups.get(g_id.text):
                    # comps 内无此分组，不展示
                    continue
                env_dict[env_id]["necessary_groups"].append(all_groups.get(g_id.text))

    def parse_env_dict_option(self, child, all_groups, visiable_groups, env_dict=None, env_id=None):
        if child.tag == "optionlist":
            optional_groups = []
            for g_id in child.findall("groupid"):
                if not all_groups.get(g_id.text):
                    # comps 内无此分组，不展示
                    continue
                optional_groups.append(all_groups.get(g_id.text))
            # 添加用户可见分组
            optional_groups.extend(visiable_groups.values())
            env_dict[env_id]["optional_groups"] = [dict(t) for t in set([tuple(d.items()) for d in optional_groups])]

    def parse_comps_get_env_group(self, xml_root, all_groups, visiable_groups):
        """

        @param xml_root:    "ElementTree解析 getroot 获取的root根节点"
        @param all_groups:   comps内得所有分组
        @param visiable_groups:     comps内可见分组
        @return:
        {
            "minimal-environment": {
            "necessary_groups": [
                {
                    "id": "core",
                    "name": "Core",
                    "name_zh_cn": "核心",
                    "description_zh_cn": "最小安装。",
                    "default": "true",
                    "uservisible": "false"
                }
            ],
            "optional_groups": [
                {
                    "id": "graphical-admin-tools",
                    "name": "Graphical Administration Tools",
                    "name_zh_cn": "图形管理工具",
                    "description_zh_cn": "用于管理系统各个方面的图形系统管理工具。",
                    "default": "true",
                    "uservisible": "true"
                }, .....  ],
            "name": "Minimal Install",
            "name_zh_cn": "最小安装",
            "description_zh_cn": "基本功能。"
            }, ......
        }
        """
        env_dict = {}
        for env in xml_root.findall("environment"):
            env_id = env.find("id").text
            env_dict.setdefault(env_id, {})
            for child in env:
                # name 非中文
                if child.tag == "name" and not child.attrib:
                    env_dict[env_id]["name"] = child.text

                # name 中文
                if child.tag == "name" and child.attrib.get(self.LANG_NAMESPACE_KEY) == self.ZH_CH:
                    env_dict[env_id]["name_zh_cn"] = child.text

                # 中文描述
                if child.tag == "description" and child.attrib.get(self.LANG_NAMESPACE_KEY) == self.ZH_CH:
                    env_dict[env_id]["description_zh_cn"] = child.text

                # 环境中必装分组
                env_dict[env_id].setdefault("necessary_groups", [])
                self.parse_env_dict_group(child, all_groups, env_dict, env_id)

                # 环境中可选分组
                env_dict[env_id].setdefault("optional_groups", [])
                self.parse_env_dict_option(child, all_groups, visiable_groups, env_dict, env_id)

        return env_dict

    def traverse_iso_repodata_folder_to_get_comps(self, abs_iso_path):
        """遍历ISO内的repodata文件夹，获取comps文件，以ISO名称-comps.xml，备份到ISO存储的同级目录下
        """
        if not os.path.exists(abs_iso_path):
            return None

        iso_name = os.path.basename(abs_iso_path)  # ISO名称
        abs_iso_dir = os.path.dirname(abs_iso_path)  # ISO存储路径
        mount_dir = mount_iso(abs_iso_path)
        md_repo_path = os.path.join(mount_dir, self.REPODATA_PATH)

        exit_comps = False  # 是否存在comps文件

        if not os.path.exists(md_repo_path):
            self.logger.error("ISO挂载失败，repodata源路径: %s 不存在" % md_repo_path)
            return exit_comps

        try:
            with TemporaryDirectory(dir="/tmp/") as tmp_dir:
                # ISO内的所有xml.gz 文件 copy到临时目录
                for f in os.listdir(md_repo_path):
                    if f.endswith(self.XML_GZ_SUFFIX):
                        src_file = os.path.join(md_repo_path, f)
                        dst_file = os.path.join(tmp_dir, f)
                        shutil.copy(src_file, dst_file)

                # 解压、判断 临时目录内的xml 文件是否根节点未comps
                for f in os.listdir(tmp_dir):
                    file = os.path.join(tmp_dir, f)
                    xml_file = file.replace(self.XML_GZ_SUFFIX, self.XML_SUFFIX)
                    if not un_gz(file, xml_file):
                        self.logger.error("解压缩xml文件 %s -> %s 失败" % (file, xml_file))
                        continue

                    is_comps = self.check_whether_comps_by_the_content(xml_file)
                    if is_comps:
                        # 备份到ISO存储路径下，以ISO名称-comps.xml存储
                        exit_comps = True
                        comps_file = os.path.join(abs_iso_dir, iso_name.replace(".iso", self.COMPS_XML_SUFFIX))
                        shutil.copy(xml_file, comps_file)
                        self.logger.debug("comps文件： %s -> %s 成功" % (xml_file, abs_iso_dir))
                        break

            return exit_comps

        except IOError as e:
            self.logger.error("复制ISO内的repodata 源错误，原因: %s" % e)
        finally:
            unmount(mount_dir)

        return exit_comps
