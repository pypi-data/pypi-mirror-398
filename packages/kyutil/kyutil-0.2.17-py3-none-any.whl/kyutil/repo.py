# -*- coding: UTF-8 -*-
import bz2
import gzip
import lzma
import os
import re
import shutil
from xml.dom.minidom import parse

from kyutil.config import ROOT_PATH_TMP


def extract_file_from_bz2(file_path_bz2, save_path=None):
    f_bz2 = bz2.open(file_path_bz2, 'r')
    save_path = save_path or file_path_bz2.rstrip(".bz2")
    with open(save_path, 'wb') as f:
        f.write(f_bz2.read())
    f_bz2.close()
    return save_path


def extract_file_from_xz(file_path_xz, save_path=None):
    save_path = save_path or file_path_xz.rstrip(".xz")
    with lzma.open(file_path_xz, 'rb') as f_xz:
        with open(save_path, 'wb') as f:
            shutil.copyfileobj(f_xz, f)
    return save_path


def extract_file_from_gz(file_path_gz, save_path=None):
    save_path = os.path.join(save_path, os.path.basename(file_path_gz).rstrip(".gz"))
    with gzip.GzipFile(file_path_gz) as f_gz:
        with open(save_path, "wb+") as f:
            f.write(f_gz.read())
    return save_path


def extract_file(file_path, save_path=None):
    if not os.path.exists(file_path):
        return f"error in extract_file, {file_path} not exists"
    if file_path.endswith(".bz2"):
        return extract_file_from_bz2(file_path, save_path)
    elif file_path.endswith(".xz"):
        return extract_file_from_xz(file_path, save_path)
    elif file_path.endswith(".gz"):
        return extract_file_from_gz(file_path, save_path)
    else:
        return RuntimeError("error in extract_file, not endswith bz2|xz|gz")


class IsoRepo(object):
    def __init__(self, mountpoint):
        self.mountpoint = mountpoint
        self.local_repodata = self.get_local_repodata_path()
        self.rpm_infos = self.get_rpm_infos()

    def get_local_repodata_path(self):
        link_repodata = self.mountpoint if "repodata" in self.mountpoint else self.mountpoint + "/repodata/"
        if os.path.exists(link_repodata):  # link_repodata 有可能是文件目录
            file_path_zip = self.get_primary_sqlite_link(link_repodata)
        else:
            file_path_zip = ''
        if not os.path.exists(file_path_zip):
            raise RuntimeError("repodata地址可能存在问题，下载sqlite文件失败")
        file_path_sqlite = extract_file(file_path_zip, ROOT_PATH_TMP)
        return file_path_sqlite

    @staticmethod
    def get_primary_sqlite_link(link_repodata):
        pattern_primary_sqlite = r".*-primary\.xml\.(xz|bz2|gz)"
        for file_name in os.listdir(link_repodata):
            if re.match(pattern_primary_sqlite, file_name):
                return os.path.join(link_repodata, file_name)
        return ""

    def get_rpm_infos(self):
        if not self.local_repodata:
            return []
        print(">>> 正在解析xml文件")
        rpm_info_list = []
        dom_tree = parse(self.local_repodata)
        collection = dom_tree.documentElement
        pkg_list = collection.getElementsByTagName("package")
        for pkg_one in pkg_list:
            rpm_info_one = get_rpm_info_one(pkg_one)
            rpm_info_list.append(rpm_info_one)
        return rpm_info_list

    def get_rpm_names(self):
        return [os.path.basename(x.get('href')) for x in self.rpm_infos]


def get_rpm_info_one4item_data_try(node_sub):
    try:
        return {node_sub.nodeName: node_sub.childNodes[0].data}
    except Exception as e:
        print(e)
        return {}


def get_rpm_info_one4item_attr_try(node_sub):
    try:
        return dict(node_sub.attributes.items())
    except Exception as e:
        print(e)
        return {}


def get_rpm_info_one(pkg_node):
    rpm_info = {}
    for node_sub in pkg_node.childNodes:
        rpm_info.update(get_rpm_info_one4item_data_try(node_sub))
        rpm_info.update(get_rpm_info_one4item_attr_try(node_sub))
        rpm_info["filepath"] = rpm_info.get("href")
    return rpm_info
