# -*- coding: UTF-8 -*-
from kyutil.config import BUILD_PATH
from kyutil.file import ensure_dir
from kyutil.koji_tools import compare
from kyutil.repomd import RepoMD
from kyutil.sheeter import SpreadSheet


def save_xlsx(repo_senior_url, repo_junior_url, final_dict, repo_senior_newest, repo_junior_newest, task_id):
    tmp_sheet = SpreadSheet()
    # 添加表格以及表头
    for index, sheet_name in enumerate(['同版本软件包', '降级版本软件包', '升级版本软件包', '新增软件包', '删除软件包']):
        tmp_sheet.add_sheet(sheet_name, index)
        tmp_sheet.append(sheet_name, [f"repo1：{repo_senior_url}\n  repo2：{repo_junior_url}"])
        tmp_sheet.merge_col(sheet_name, ((1, 1), (3, 1)))
        tmp_sheet.append(sheet_name, ["SRPM包名", "repo1内包版本", "repo2内包版本"])

    for pkg, source_pkg in final_dict.items():
        if pkg in repo_junior_newest.keys():
            if source_pkg.get('pkg_handle_flag') == 'NOT_CHANGED':
                tmp_sheet.append('同版本软件包', [pkg, str(repo_senior_newest[pkg]), str(repo_junior_newest[pkg])])
            elif source_pkg.get('pkg_handle_flag') == 'VERSION_UPGRADE' or source_pkg.get('pkg_handle_flag') == 'RELEASE_UPGRADE':
                tmp_sheet.append('升级版本软件包', [pkg, str(repo_senior_newest[pkg]), str(repo_junior_newest[pkg])])
            elif source_pkg.get('pkg_handle_flag') == 'VERSION_DOWNGRADE' or source_pkg.get('pkg_handle_flag') == 'RELEASE_DOWNGRADE':
                tmp_sheet.append('降级版本软件包', [pkg, str(repo_senior_newest[pkg]), str(repo_junior_newest[pkg])])
            elif source_pkg.get('pkg_handle_flag') == 'DEPRECATED':
                tmp_sheet.append('删除软件包', [pkg, '', str(repo_junior_newest[pkg])])
        elif source_pkg.get('pkg_handle_flag') == 'ADD':
            tmp_sheet.append('新增软件包', [pkg, str(repo_senior_newest[pkg]), ''])
    ensure_dir(f"{BUILD_PATH}/repos_compare/")
    sp = f"{BUILD_PATH}/repos_compare/repo-{task_id[:4]}"
    tmp_sheet.save_workbook(sp)
    return sp


def comp_repo_repo(repo_senior_url: str, repo_junior_url: str, task_id):
    """repo对比功能测试V1.0"""
    repo_senior = RepoMD(repo_senior_url)
    repo_junior = RepoMD(repo_junior_url)
    repo_senior_newest = repo_senior.newest_pkgs_group
    repo_junior_newest = repo_junior.newest_pkgs_group
    if not repo_junior_newest:
        raise RuntimeError("Repo_junior_newest not exists.")
    compare(repo_senior_newest, repo_junior_newest)

    final_dict = {}
    for pkg, source_pkg in repo_senior_newest.items():
        final_dict[pkg] = source_pkg.all_info
    for pkg, source_pkg in repo_junior_newest.items():
        if source_pkg.pkg_handle_flag == 'DEPRECATED':
            final_dict[pkg] = source_pkg.all_info
    return save_xlsx(repo_senior_url, repo_junior_url, final_dict, repo_senior_newest, repo_junior_newest, task_id)
