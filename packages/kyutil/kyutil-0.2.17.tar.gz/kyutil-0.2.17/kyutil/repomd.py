# -*- coding: UTF-8 -*-
import bz2
import gzip
import lzma
import os
import uuid
from datetime import datetime
from html import unescape
from io import BytesIO, TextIOWrapper

from defusedxml import ElementTree

from kyutil.config import REPODATA_PATH
from kyutil.http_util import send_request
from kyutil.koji_tools import group_pkgs
from kyutil.source_pkg import SourcePackage


class RepoMD(object):
    __slots__ = ['_repo_url', '_ns', 'common_field', 'rpm_field', 'pkgs', '_requester', 'pkg_index', 'pkg_source']

    def __init__(self, _base_url_: str) -> None:
        """
        Create a repo object that contains all package information
        Args:
            _base_url_ (str): The Base address's directory that must contains /repodata/ directory
                              For example: https://mirrors.bfsu.edu.cn/centos/7/os/x86_64/
        """
        self._repo_url = _base_url_
        if _base_url_.endswith('/'):
            self._repo_url = _base_url_[:-1]
        self._ns = {
            'common': '{http://linux.duke.edu/metadata/common}',
            'repo': '{http://linux.duke.edu/metadata/repo}',
            'rpm': '{http://linux.duke.edu/metadata/rpm}',
            'other': '{http://linux.duke.edu/metadata/other}'
        }
        self.common_field = [
            # name attribute should always be put in the frontmost
            'name', 'version', 'arch', 'summary', 'description', 'location', 'format', 'checksum'
        ]
        self.rpm_field = [
            'license', 'vendor', 'sourcerpm'
        ]
        self.pkg_index = -1
        self.pkg_source = []
        self.pkgs = []
        self._set_pkgs_info()

    def __len__(self):
        return len(self.pkgs)

    def __getitem__(self, index) -> SourcePackage:
        return self.pkgs[index]

    def __iter__(self):
        return self.pkgs.__iter__()

    def __next__(self) -> SourcePackage:
        self.pkg_index += 1
        if self.pkg_index == self.__len__():
            raise StopIteration
        return self.pkgs[self.pkg_index]

    def _http_or_not(self, _uri_: str):
        if _uri_.startswith('http'):
            return True
        return False

    def _unzip_online(self, _prim_xml_url_: str):
        if self._http_or_not(_prim_xml_url_):
            _response_ = send_request(_prim_xml_url_, verify=False)
            if _prim_xml_url_.endswith('gz'):
                with BytesIO(_response_.content) as compressed:
                    with gzip.GzipFile(fileobj=compressed) as uncompressed:
                        with TextIOWrapper(uncompressed, encoding='UTF-8') as xml_tree:
                            return xml_tree.read()
            elif _prim_xml_url_.endswith('xz'):
                uncompressed = lzma.decompress(_response_.content)
                xml_tree = str(uncompressed, encoding='UTF-8')
                return xml_tree

            elif _prim_xml_url_.endswith('bz2'):
                tmp_file = f"./{uuid.uuid4().hex}.bz2"
                open(tmp_file, "wb").write(_response_.content)
                with bz2.BZ2File(tmp_file) as fr:
                    os.remove(tmp_file)
                    return fr.read()
            else:
                print(f"不支持的压缩类型：{_prim_xml_url_}")
                raise RuntimeError(f"不支持的压缩类型：{_prim_xml_url_}")
        else:
            if _prim_xml_url_.endswith('xz'):
                with lzma.open(_prim_xml_url_, 'rb') as de_prim_file:
                    return de_prim_file.read()
            elif _prim_xml_url_.endswith('gz'):
                with gzip.open(_prim_xml_url_, 'rb') as de_prim_file:
                    return de_prim_file.read()

    def _load_repomd_xml(self):
        xml_path = self._repo_url + f'{REPODATA_PATH}repomd.xml'
        if self._http_or_not(xml_path):
            xml_str = send_request(xml_path, verify=False).text
        else:
            with open(xml_path, 'r', encoding='UTF-8') as xml_file:
                xml_str = xml_file.read()
        xml_tree = ElementTree.fromstring(xml_str)
        return [node.attrib.get('href') for node in xml_tree.iter(f"{self._ns['repo']}location")]

    def _primary_url(self):
        repodata_list = self._load_repomd_xml()
        for name in repodata_list:
            if '-primary.xml.gz' in name or '-primary.xml.xz' in name or '-primary.xml.bz2' in name:
                return self._repo_url + '/' + name

    def _other_url(self):
        repodata_list = self._load_repomd_xml()
        for name in repodata_list:
            if '-other.xml.gz' in name or '-other.xml.xz' in name or '-other.xml.bz2' in name:
                return self._repo_url + '/' + name

    def _repo_changelog(self):
        other_xml_url = self._other_url()
        if not other_xml_url:
            print("没有 other url")
            return {}
        pkg_changelog_info = {}
        unziped_xml = ElementTree.fromstring(self._unzip_online(other_xml_url))
        for node in unziped_xml.iter(f"{self._ns['other']}package"):
            tmp_changelog = ''
            changelog_tmp = node.findall(f"{self._ns['other']}changelog")
            for log in changelog_tmp:
                author = unescape(log.attrib.get('author'))
                timestamp = int(log.attrib.get('date'))
                date_changelog = datetime.fromtimestamp(timestamp).strftime('%a %b %d %y')
                tmp_changelog += f"* {date_changelog} {author}\n{log.text}\n\n"
            pkg_changelog_info[node.attrib.get('pkgid')] = tmp_changelog
        return pkg_changelog_info

    def _parse_node(self, node) -> dict:
        tmp_dict = {}
        for common in self.common_field:
            if common == 'location':
                tmp_dict[common] = node.find(f"{self._ns['common']}{common}").attrib.get('href')
                continue
            if common == 'version':
                tmp_attr = node.find(f"{self._ns['common']}{common}")
                tmp_dict['nvr'] = f"{tmp_dict['name']}-{tmp_attr.attrib.get('ver')}-{tmp_attr.attrib.get('rel')}"
                continue
            if common == 'format':
                rpm_format = node.find(f"{self._ns['common']}{common}")
                for _rpm_tag in self.rpm_field:
                    tmp_dict[_rpm_tag] = rpm_format.find(f"{self._ns['rpm']}{_rpm_tag}").text
                continue
            tmp_dict[common] = node.find(f"{self._ns['common']}{common}").text
        if tmp_dict['arch'] == 'src':
            tmp_dict['sourcerpm'] = tmp_dict['location'].rsplit('/')[-1]
        return tmp_dict

    def _set_pkgs(self, pkgs_set: dict):
        for pkg, tmp_pkg_set in pkgs_set.items():
            tmp_pkg = SourcePackage(pkg)
            tmp_pkg.set_changelog(tmp_pkg_set[0]['changelog'])
            tmp_pkg.set_vendor(tmp_pkg_set[0]['vendor'])
            tmp_pkg.set_license(tmp_pkg_set[0]['license'])
            tmp_pkg.set_location(f"{self._repo_url}/{tmp_pkg_set[0]['location']}")
            tmp_description = {}
            tmp_summary = {}
            for tmp_info in tmp_pkg_set:
                tmp_pkg.set_built_rpms(tmp_info['nvr'])
                tmp_description[tmp_info['nvr']] = tmp_info['description']
                tmp_summary[tmp_info['nvr']] = tmp_info['summary']
            tmp_pkg.set_description(tmp_description)
            tmp_pkg.set_summary(tmp_summary)
            self.pkgs.append(tmp_pkg)
            self.pkg_source.append(pkg)

    def _set_pkgs_info(self) -> list:
        changelog_info = self._repo_changelog()
        prim_xml_url = self._primary_url()
        if not prim_xml_url:
            print("没有prim url")
            return []
        unziped_xml = ElementTree.fromstring(self._unzip_online(prim_xml_url))
        tmp_pkgs_set = {}
        for node in unziped_xml.iter(f"{self._ns['common']}package"):
            node_dict = self._parse_node(node)
            node_dict['changelog'] = changelog_info[node_dict['checksum']]
            if not tmp_pkgs_set.__contains__(node_dict['sourcerpm']):
                tmp_pkgs_set[node_dict['sourcerpm']] = []
            tmp_pkgs_set[node_dict['sourcerpm']].append(node_dict)
        self._set_pkgs(tmp_pkgs_set)

    @property
    def source_pkgs(self) -> list:
        return self.pkg_source

    @property
    def pkgs_group(self) -> dict:
        return group_pkgs(self.pkgs)

    @property
    def newest_pkgs_group(self) -> dict:
        return {pkg: group[0] for pkg, group in self.pkgs_group.items()}
