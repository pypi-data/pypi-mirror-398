# -*- coding: UTF-8 -*-
import re
import subprocess

from packaging import version
from packaging.version import InvalidVersion

from kyutil.reg_exp import RPMS_END, RPM_NVR, MBS_FLAG
from kyutil.rpms import get_nvr


def version_compare_gt(v1, v2):
    try:
        if version.parse(v1) > version.parse(v2):
            return 1
        elif version.parse(v1) < version.parse(v2):
            return -1
        return 0
    except InvalidVersion:
        s = subprocess.run(["rpmdev-vercmp", v1, v2])
        # 大于
        if s.returncode == 11:
            return 1
        # 小于
        elif s.returncode == 12:
            return -1
        # 相等
        return 0


misc_kicker = re.compile(RPMS_END)
dist_re = re.compile(RPM_NVR)
mbs_flag = re.compile(MBS_FLAG)


class SourcePackage:
    """RPM package class
    Returns:_type_: RPM class
    """
    __slots__ = '_pkg_info'

    def __init__(self, _nvrdo_: str = 'tmp-pkg-0.0.0-0.tmp8.src.rpm') -> None:
        self._pkg_info = {
            'name': '',
            'version': '',
            'release': '',
            'dist': '',
            'other_info': '',
            'pkg_type': '',
            'origin_info': '',
            'changelog': '',
            'tags': '',
            'koji_complete_time': '',
            'built_rpms': [],
            'buildID': '',
            'license': '',
            'vendor': '',
            'location': '',
            'description': {},
            'summary': {},
            'pkg_handle_flag': 'UNDEFINED'
        }
        self.set_pkg_info(_nvrdo_)

    def split_nvrdo(self, _nvrdo_: str):
        misc_match = misc_kicker.match(_nvrdo_)
        _TYPE_NORMAL = 'normal'
        if misc_match:
            _nvrd_, *misc = misc_match.groups()
            _pkg_suffix = ''.join(misc)
        else:
            _nvrd_ = _nvrdo_
            _pkg_suffix = ''
        _name, _version, _release_dist = get_nvr(_nvrd_)
        # Already known error release format
        if '%' in _release_dist:
            _release, _dist = _release_dist.rsplit('%', 1)
            return _name, _version, _release, '%' + _dist, _pkg_suffix, _TYPE_NORMAL
        # mbs match
        mbs_match = mbs_flag.match(_release_dist)
        if mbs_match:
            return _name, _version, mbs_match.group(1), mbs_match.group(2), _pkg_suffix, "mbs"
        # normal match
        dist_match = dist_re.match(_release_dist)
        if dist_match:
            _release, *_dist = dist_match.groups()
            return _name, _version, _release, ''.join([tmp for tmp in _dist if tmp]), _pkg_suffix, _TYPE_NORMAL
        return _name, _version, _release_dist, '', _pkg_suffix, _TYPE_NORMAL

    def set_pkg_info(self, _nvrdo: str):
        name, v, release, dist, other, pkg_type = self.split_nvrdo(_nvrdo)
        self._pkg_info['name'] = name
        self._pkg_info['version'] = v
        self._pkg_info['release'] = release
        self._pkg_info['dist'] = dist
        self._pkg_info['other_info'] = other
        self._pkg_info['pkg_type'] = pkg_type
        self._pkg_info['origin_info'] = _nvrdo

    def set_changelog(self, _changelog: str):
        self._pkg_info['changelog'] = _changelog

    def set_built_rpms(self, _rpm_name):
        self._pkg_info['built_rpms'].append(_rpm_name)

    def set_description(self, _desc: dict):
        self._pkg_info['description'] = _desc

    def set_summary(self, _summary: dict):
        self._pkg_info['summary'] = _summary

    def set_vendor(self, _vendor: str):
        self._pkg_info['vendor'] = _vendor

    def set_license(self, _license: str):
        self._pkg_info['license'] = _license

    def set_location(self, _location: str):
        self._pkg_info['location'] = _location

    def set_pkg_handle_flag(self, _flag_: str):
        self._pkg_info['pkg_handle_flag'] = _flag_

    def __repr__(self) -> str:
        return self._pkg_info['origin_info']

    def __lt__(self, __o) -> bool:
        return version_compare_gt(self.nvrdo, __o.nvrdo) == -1

    def __gt__(self, __o) -> bool:
        return version_compare_gt(self.nvrdo, __o.nvrdo) == 1

    def __le__(self, __o) -> bool:
        return version_compare_gt(self.nvrdo, __o.nvrdo) == -1 and self.nv == __o.nv

    def __ge__(self, __o) -> bool:
        return version_compare_gt(self.nvrdo, __o.nvrdo) == 1 and self.nv == __o.nv

    def __eq__(self, __o) -> bool:
        return self.nvrdo == __o.nvrdo

    def __ne__(self, __o) -> bool:
        return self.nvrdo != __o.nvrdo

    @property
    def all_info(self):
        return self._pkg_info

    @property
    def name(self):
        return self._pkg_info['name']

    @property
    def version(self):
        return self._pkg_info['version']

    @property
    def release(self):
        return self._pkg_info['release']

    @property
    def dist(self):
        return self._pkg_info['dist']

    @property
    def nv(self):
        return '-'.join([self.name, self.version])

    @property
    def nr(self):
        return '-'.join([self.name, '0.0.0', self.release])

    @property
    def nvr(self):
        return '-'.join([self.nv, self.release])

    @property
    def nvrd(self):
        return self.nvr + self.dist

    @property
    def other_info(self):
        return self._pkg_info['other_info']

    @property
    def nvrdo(self):
        return self.nvrd + self.other_info

    @property
    def pkg_type(self):
        return self._pkg_info['pkg_type']

    @property
    def origin_info(self):
        return self._pkg_info['origin_info']

    @property
    def changelog(self):
        return self._pkg_info['changelog']

    @property
    def checksum(self):
        return self._pkg_info['checksum']

    @property
    def tag(self):
        return self._pkg_info['tag']

    @property
    def koji_complete_time(self):
        return self._pkg_info['koji_complete_time']

    @property
    def built_rpms(self):
        return self._pkg_info['built_rpms']

    @property
    def buildid(self):
        return self._pkg_info['buildID']

    @property
    def pkg_handle_flag(self):
        return self._pkg_info['pkg_handle_flag']

    @property
    def vendor(self):
        return self._pkg_info['vendor']
