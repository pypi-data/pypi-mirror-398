# -*- coding: UTF-8 -*-
from kyutil.util_rpm_info import compare_evr_by_shell


def add_and_remove(_set0: list, _set1: list):
    set_minus = lambda set0, set1: list(set(set0) - set(set1))
    _0_add = set_minus(_set0, _set1)
    _0_rmv = set_minus(_set1, _set0)
    return [_0_add, _0_rmv]


def up_down_grade(_repo0: dict, _repo1: dict, _repo0_1_add: list):
    _repo0_extra = list(set(_repo0.keys()) - set(_repo0_1_add))

    for pkg in _repo0_extra:
        left_pkg = _repo0[pkg]
        right_pkg = _repo1[pkg]

        if left_pkg < right_pkg:
            left_pkg.set_pkg_handle_flag('VERSION_DOWNGRADE')
        elif left_pkg > right_pkg:
            left_pkg.set_pkg_handle_flag('VERSION_UPGRADE')
        elif left_pkg <= right_pkg:
            left_pkg.set_pkg_handle_flag('RELEASE_DOWNGRADE')
        elif left_pkg >= right_pkg:
            left_pkg.set_pkg_handle_flag('RELEASE_UPGRADE')
        elif left_pkg == right_pkg:
            left_pkg.set_pkg_handle_flag('NOT_CHANGED')


def compare(coll_senior: dict, coll_junior: dict):
    added_pkg, deprecated_pkg = add_and_remove(coll_senior.keys(), coll_junior.keys())
    for pkg in added_pkg:
        coll_senior[pkg].set_pkg_handle_flag('ADD')
    for pkg in deprecated_pkg:
        coll_junior[pkg].set_pkg_handle_flag('DEPRECATED')
    up_down_grade(coll_senior, coll_junior, added_pkg)


def group_pkgs(pkgs: list) -> dict:
    tmp_dict = {}
    for pkg in pkgs:
        tmp_name = pkg.name
        if not tmp_dict.__contains__(tmp_name):
            tmp_dict[tmp_name] = []
        tmp_dict[tmp_name].append(pkg)
    for pkg, pkg_list in tmp_dict.items():
        max_index = max_version_index(pkg_list)
        if max_index:
            pkg_list[0], pkg_list[max_index] = pkg_list[max_index], pkg_list[0]
    return tmp_dict


def max_version_index(tmp_pkgs: list):
    max_index = 0
    for index, tmp in enumerate(tmp_pkgs):
        if (tmp.version == tmp_pkgs[max_index].version and
                compare_evr_by_shell(tmp.version + "-" + tmp.release, tmp_pkgs[max_index].version + "-" + tmp_pkgs[max_index].release)[0] == 11):
            max_index = index
    return max_index
