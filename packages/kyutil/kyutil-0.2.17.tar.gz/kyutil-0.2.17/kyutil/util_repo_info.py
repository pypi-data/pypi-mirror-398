# -*- coding: UTF-8 -*-
import bz2
import fnmatch
import glob
import gzip
import logging
import lzma
import os
import pickle
import re
import shutil
import sqlite3
import time
import uuid
import xml.dom.minidom
from contextlib import closing
from xml.dom.minidom import parse

import urllib3

from kyutil.file import ensure_dir
from kyutil.http_util import send_request
from kyutil.reg_exp import HTML_URL

urllib3.disable_warnings()

HTML_PARSER = "html.parser"
REPODATA = "repodata"
ROOT_PATH_ISO_PATH = os.getenv("ISO_PATH") or "/opt/integration_iso_files/"
TMP_PATH = os.getenv("ISO_PATH", ROOT_PATH_ISO_PATH + "tmp/")


def get_dir_list(url_link):
    if os.path.exists(url_link):
        return glob.glob(os.path.join(url_link, "*"))
    else:
        res = send_request(url_link, verify=False)
        if res.status_code != 200:
            return []
        return re.findall(HTML_URL, res.text)[1:]


def get_primary_sqlite_link(url_link):
    """给定一个repodata的url，获取里面primary的sqlite链接（要么xz，要么bz2，要么gz,有且仅有一个）"""
    pattern_primary_sqlite = r".*-primary\.sqlite\.(xz|bz2|gz)"
    for file_name in get_dir_list(url_link):
        if re.match(pattern_primary_sqlite, file_name):
            if os.path.exists(file_name):  # 判断是否存在，如果是以目录的形式，则不需要增加前缀
                return file_name
            return os.path.join(url_link, file_name)
    return ""


def get_primary_xml_link(url_link):
    """给定一个repodata的url，获取里面primary的xml链接（要么xz，要么bz2，要么gz,有且仅有一个）"""
    pattern_primary_sqlite = r".*-primary\.xml\.(xz|bz2|gz)"
    for file_name in get_dir_list(url_link):
        if re.match(pattern_primary_sqlite, file_name):
            return os.path.join(url_link, file_name)
    return ""


def get_link_repo_map(base_url, date_str):
    get_version = get_arch = get_dir_list
    version_list = get_version(f"{base_url}{date_str}")
    link_map = {}
    for version in version_list:
        arch_list = get_arch(f"{base_url}{date_str}/{version}")
        for arch in arch_list:
            link_map['#'.join([version, arch]).replace('/', '')] = f"{base_url}{date_str}/{version}{arch}".rstrip('/')
    return link_map


def dir_init(file_path_all):
    file_path_all = os.path.dirname(file_path_all)
    if not os.path.exists(file_path_all):
        logging.info(f"初始化文件夹：{file_path_all}")
        os.makedirs(file_path_all)


def download(file_url, save_path_dir=TMP_PATH, verbose=True):
    if file_url == "":
        logging.error("!!! 下载地址不能为空")
        return ""
    file_name = os.path.basename(file_url)
    file_path = os.path.join(save_path_dir, file_name)
    dir_init(file_path)
    try:
        with open(file_path, 'wb') as f:
            with closing(send_request(file_url, stream=True, verify=False)) as response:
                chunk_size = 1024  # 单次请求最大值
                data_count = 0
                for data in response.iter_content(chunk_size=chunk_size):
                    f.write(data)
                    data_count = data_count + len(data)
        if verbose:
            logging.info("下载完成：" + str(file_name))
        return file_path
    except Exception as e:
        if verbose:
            logging.error("下载失败：" + str(file_name) + str(e))
        return ""


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
    save_path = save_path or file_path_gz.rstrip(".gz")
    with gzip.GzipFile(file_path_gz) as f_gz:
        with open(save_path, "wb+") as f:
            f.write(f_gz.read())
    return save_path


def extract_file(file_path, save_path=None):
    """
    解压压缩文件，如果没有指定目录，默认去掉压缩后缀的文件即为目录。
    Args:
        file_path:
        save_path:

    Returns:

    """
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


def get_sqlite_from_repodata(link_repodata, save_path=TMP_PATH):
    if os.path.exists(link_repodata):  # link_repodata 有可能是文件目录
        file_path_zip = get_primary_sqlite_link(link_repodata)
    else:
        link_sqlite = get_primary_sqlite_link(link_repodata)
        ensure_dir(save_path)
        file_path_zip = download(link_sqlite, save_path)
    if not os.path.exists(file_path_zip):
        raise RuntimeError("repodata地址可能存在问题，下载sqlite文件失败")
    file_path_sqlite = extract_file(file_path_zip)
    return file_path_sqlite


def get_primary_xml_from_repodata(link_repodata, save_path=TMP_PATH):
    link_primary_xml = get_primary_xml_link(link_repodata)
    ensure_dir(save_path)
    file_path_zip = download(link_primary_xml, save_path)
    if not os.path.exists(file_path_zip):
        raise RuntimeError("repodata地址可能存在问题，下载sqlite文件失败")
    file_path_xml = extract_file(file_path_zip)
    return file_path_xml


def get_primary_xml_from_local_repodata(link_repodata):
    link_primary_xml = get_primary_xml_link(link_repodata)
    if not os.path.exists(link_primary_xml):
        raise RuntimeError("repodata地址异常")
    file_path_xml = extract_file(link_primary_xml)
    return file_path_xml


def get_modules_yaml_link(url_link):
    """给定一个repodata的url，获取里面modules.yaml文件的链接（要么xz，要么bz2，要么gz,有且仅有一个）"""
    pattern_modules_yaml = r".*-modules\.yaml\.(xz|bz2|gz)"
    for file_name in get_dir_list(url_link):
        if re.match(pattern_modules_yaml, file_name):
            return os.path.join(url_link, file_name)
    return ""


def get_db(sql_path):
    return sqlite3.connect(sql_path)


def deal_select(sql, sql_path, db_conn=None):
    if db_conn is None:
        db_conn = get_db(sql_path)
    cursor = db_conn.cursor()
    cursor.execute(sql)
    rs = cursor.fetchall()
    return rs


def get_href_from_xml_file(file_path_xml):
    dom_tree = xml.dom.minidom.parse(file_path_xml)
    collection = dom_tree.documentElement
    for c in collection.getElementsByTagName("data"):
        if c.getAttribute("type") == "primary_db":
            return os.path.basename(c.getElementsByTagName("location")[0].getAttribute("href"))


def get_repo_info_sqlite(link_repo, save_path):
    link_repo = link_repo.rstrip('/')
    link_repodata_xml = link_repo + f"/{REPODATA}/repomd.xml"
    file_path_xml = download(link_repodata_xml, save_path)
    link_repodata_sqlite_bz2 = link_repo + f"/{REPODATA}/" + get_href_from_xml_file(file_path_xml)
    file_path_sqlite_bz2 = download(link_repodata_sqlite_bz2, save_path)
    file_path_sqlite = extract_file_from_bz2(file_path_sqlite_bz2)
    repo_info = {
        "link_repo": link_repo,
        "link_repodata_xml": link_repodata_xml,
        "link_repodata_sqlite_bz2": link_repodata_sqlite_bz2,
        "file_path_xml": file_path_xml,
        "file_path_sqlite_bz2": file_path_sqlite_bz2,
        "file_path_sqlite": file_path_sqlite
    }
    return repo_info


def get_repo_data(base_url, date_str, save_path):
    link_repo_map = get_link_repo_map(base_url, date_str)
    repo_info_map = {}
    for tag, link_repo in link_repo_map.items():
        repo_info_map[tag] = get_repo_info_sqlite(link_repo, save_path)
    return repo_info_map


def repo_info_map_save(repo_info_map, save_path):
    with open(save_path, 'wb') as f:
        pickle.dump(repo_info_map, f)


def repo_info_map_load(save_path):
    with open(save_path, 'rb') as f:
        repo_info_map = pickle.load(f)
        return repo_info_map


def rpm_filter(rpm_name, _rpm_name):
    *_rpm_name_list, _, _ = _rpm_name.split('-')
    _rpm_name = '-'.join(_rpm_name_list)
    if '*' in rpm_name:
        return fnmatch.fnmatch(_rpm_name, rpm_name)
    return rpm_name == _rpm_name


def search_rpm_from_sqlite(rpm_name, file_path_sqlite):
    sql_str = "select distinct rpm_sourcerpm from packages"
    group_all = [g_o[0] for g_o in deal_select(sql_str, file_path_sqlite)]
    rpm_all = [_rpm_name for _rpm_name in group_all if rpm_filter(rpm_name, _rpm_name.rstrip(".src.rpm"))]
    return rpm_all


def search_rpm_bin_from_sqlite(rpm_name, file_path_sqlite):
    sql_str = f"select * from packages WHERE name like %{rpm_name}%"
    group_all = [g_o[2] for g_o in deal_select(sql_str, file_path_sqlite)]
    return group_all


def search_rpm_info_from_sqlite(file_path_sqlite):
    sql_str = "select * from packages"
    return deal_select(sql_str, file_path_sqlite)


def get_rpm_info_header_from_sqlite(file_path_sqlite):
    sql_str = 'SELECT sql FROM sqlite_master WHERE type="table" AND name="packages"'
    try:
        result = deal_select(sql_str, file_path_sqlite)
        column_names = result[0][0].split('(')[1].split(')')[0].split(',')
        column_names = [c.strip().split()[0] for c in column_names]
        return column_names
    except Exception as e:
        print("查询sqlite表列字段名称出错，原因：", e)
        return []


def get_str4provides_or_require(info_list):
    map_cmp_flag = {"LT": "<", "GT": ">", "LE": "<=", "GE": ">=", "EQ": "=", "NE": "!="}
    str_cmp = map_cmp_flag.get(info_list[1], "")
    str_evr = '-'.join([y for y in map(lambda x: x or "", info_list[2:5]) if y != ""])
    return ' '.join([x for x in [info_list[0], str_cmp, str_evr] if x != ""])


def get_str4provides_or_require_from_dict(info_map):
    map_cmp_flag = {"LT": "<", "GT": ">", "LE": "<=", "GE": ">=", "EQ": "=", "NE": "!="}
    str_cmp = map_cmp_flag.get(info_map.get("flags", ""), "")
    evr_list = [info_map.get("epoch", ""), info_map.get("ver", ""), info_map.get("rel", "")]
    str_evr = '-'.join([y for y in map(lambda x: x or "", evr_list) if y != ""])
    return ' '.join([x for x in [info_map.get("name", ""), str_cmp, str_evr] if x != ""])


def get_rpm_info_one4item_data_try(node_sub):
    try:
        return {node_sub.nodeName: node_sub.childNodes[0].data}
    except IndexError:
        return {}


def get_rpm_info_one4item_attr_try(node_sub):
    try:
        return dict(node_sub.attributes.items())
    except Exception as e:
        print(f"属性不存在：{e}")
        return {}


def child_node(node_sub_sub):
    _ = []
    for sub_item in node_sub_sub.childNodes:
        parse_sub = get_rpm_info_one4item_attr_try(sub_item)
        if len(parse_sub) == 0:
            continue
        _.append(get_str4provides_or_require_from_dict(parse_sub))
    return _


def get_rps(node_sub):
    list_requires, list_provides, src_name = [], [], ""

    for node_sub_sub in node_sub.childNodes:
        if node_sub_sub.nodeName == "rpm:requires":
            list_requires.append(child_node(node_sub_sub))
        elif node_sub_sub.nodeName == "rpm:provides":
            list_provides.append(child_node(node_sub_sub))
        elif node_sub_sub.nodeName == "rpm:sourcerpm":
            src_name = get_rpm_info_one4item_data_try(node_sub_sub).get("rpm:sourcerpm")
    return list_requires, list_provides, src_name


def get_rpm_info_one4requires_provides_etc_try(node_sub):
    if node_sub.nodeName != "format":
        return {}
    try:
        list_requires, list_provides, src_name = get_rps(node_sub)
        return {"requires": list_requires, "provides": list_provides, "src_name": src_name}
    except Exception as e:
        print(f"get_rpm_info_one4requires_provides_etc_try ERR: {e}")
        return {}


def get_rpm_info_one(pkg_node):
    """从xml中获取rpm_info"""
    rpm_info = {}
    for node_sub in pkg_node.childNodes:
        rpm_info.update(get_rpm_info_one4item_data_try(node_sub))
        rpm_info.update(get_rpm_info_one4item_attr_try(node_sub))
        rpm_info.update(get_rpm_info_one4requires_provides_etc_try(node_sub))
        rpm_info["filepath"] = rpm_info.get("href")
    return rpm_info


def get_rpm_info_from_xml(file_path_xml):
    """从xml文件中获取rpm_info列表"""
    logging.info(">>> 正在解析xml文件")
    rpm_info_list = []
    dom_tree = parse(file_path_xml)
    collection = dom_tree.documentElement
    pkg_list = collection.getElementsByTagName("package")
    for pkg_one in pkg_list:
        rpm_info_one = get_rpm_info_one(pkg_one)
        rpm_info_list.append(rpm_info_one)
    return rpm_info_list


def search_rpm_provides_from_sqlite(file_path_sqlite):
    logging.info(">>> 从sqlite中获取provides映射")
    rpm_pkg_key2provides_map = {}
    try:
        sql_str = "select * from provides"
        for info_one in deal_select(sql_str, file_path_sqlite):
            pkg_key = info_one[5]
            info_str = get_str4provides_or_require(info_one)
            rpm_pkg_key2provides_map[pkg_key] = rpm_pkg_key2provides_map.get(pkg_key, []) + [info_str]
    except Exception as e:
        logging.error("error in get_single_package_source_info.search_rpm_provides_from_sqlite" + str(e))
    return rpm_pkg_key2provides_map


def search_rpm_requires_from_sqlite(file_path_sqlite):
    logging.info(">>> 从sqlite中获取requires映射")
    rpm_pkg_key2requires_map = {}
    try:
        sql_str = "select * from requires"
        for info_one in deal_select(sql_str, file_path_sqlite):
            pkg_key = info_one[5]
            info_str = get_str4provides_or_require(info_one)
            rpm_pkg_key2requires_map[pkg_key] = rpm_pkg_key2requires_map.get(pkg_key, []) + [info_str]
    except Exception as e:
        logging.error("error in get_single_package_source_info.search_rpm_require_from_sqlite" + str(e))
    return rpm_pkg_key2requires_map


def search_rpm_version(rpm_name, repo_info_map):
    rpm_repo_info = {}
    for tag, repo_info in repo_info_map.items():
        rpm_repo_info[tag] = search_rpm_from_sqlite(rpm_name, repo_info.get("file_path_sqlite"))
    return rpm_repo_info


def main(keyword="*"):
    date_str = time.strftime("%Y%m%d")
    temp_file_path = TMP_PATH + f"temp4rpm_test_parse_{uuid.uuid4().hex[:4]}"
    repo_info_map = get_repo_data("", date_str=date_str, save_path=temp_file_path)
    repo_info_map_save(repo_info_map, save_path=os.path.join(temp_file_path, "dir_map"))
    repo_info_map = repo_info_map_load(save_path=os.path.join(temp_file_path, "dir_map"))
    logging.info("\n" + '-' * 100 + '\n')
    for k, v in search_rpm_version(keyword, repo_info_map).items():
        if len(v) > 0:
            logging.info(k, ":\n\t", '、'.join(v))


def find_sub_repo(url="", map_name2link=None):
    def get_map_name2url4a(_link):
        from bs4 import BeautifulSoup
        r = send_request(_link, verify=False)
        soup = BeautifulSoup(r.text, HTML_PARSER)
        _name_href_map = {}
        soup_a_list = soup.find_all("a")
        for soup_a in soup_a_list:
            if '..' in soup_a.string:
                continue
            _name_href_map[soup_a.string] = _link.rstrip('/') + '/' + soup_a.get("href")
        return _name_href_map

    if not any([url, map_name2link]):
        return []
    candidate_link_repodata = []
    map_name2link = map_name2link or get_map_name2url4a(url)
    if f"{REPODATA}/" in map_name2link:
        return [map_name2link[f"{REPODATA}/"]]  # repodata同一层级或更下一般不会再有repodata
    for name, link in map_name2link.items():
        if name.endswith('/'):  # 文件
            candidate_link_repodata += find_sub_repo(map_name2link=get_map_name2url4a(link))
    if url:
        candidate_link_repodata = [link.replace(f"{REPODATA}/", "") for link in candidate_link_repodata]
        candidate_link_repodata = [{"name": link.replace(url, ""), "url": link} for link in candidate_link_repodata]
    return candidate_link_repodata


def _link2file(r, f_o, _logger):
    file_path_link = os.path.join(r, f_o)
    if file_path_link.endswith("_bak"):
        return
    if not os.path.islink(file_path_link):
        return
    file_path = os.readlink(file_path_link)
    if not os.path.exists(file_path_link):
        _logger.error(f"链接文件[{file_path_link}]的指向[{file_path}]不存在")
        return
    if not os.path.isabs(file_path):  # 如果链接使用的是相对路径，则将其以当前路径为基础转换为绝对路径
        file_path = os.path.abspath(os.path.join(os.path.dirname(file_path_link), os.readlink(file_path_link)))
    if not os.path.exists(file_path_link) or not os.path.exists(file_path):  # 冗余判断
        _logger.error(f"链接文件[{file_path_link}]的指向[{file_path}]不存在")
        return
    return file_path, file_path_link


def convert_link2file(dir_path, _logger=logging):
    """ 给定一个目录，遍历所有文件，将链接文件转换成其所指向的文件"""
    for r, d, f in os.walk(dir_path):
        for f_o in f:
            lf = _link2file(r, f_o, _logger)
            if lf:
                file_path, file_path_link = lf
                # 当链接文件指向的文件确认存在后，先将链接文件修改名字，将原来的文件复制过来，复制成功之后，删除链接文件
                _logger.debug(f"复制文件[{file_path}]到[{file_path_link}]")
                shutil.move(file_path_link, file_path_link + "_bak")
                shutil.copy(file_path, file_path_link)
                os.remove(file_path_link + "_bak")
