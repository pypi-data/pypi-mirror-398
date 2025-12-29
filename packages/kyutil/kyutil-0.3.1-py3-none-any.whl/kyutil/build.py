# -*- coding: UTF-8 -*-
"""
@Project ：kyutil 
@File    ：build.py
@IDE     ：PyCharm 
@Author  ：xuyong@kylinos.cn
@Date    ：2025/3/27 下午11:05 
@Desc    ：说明：
"""
import time
import traceback

from celery import states
from celery.result import AsyncResult

from kyutil.base import strip_dict
from kyutil.config import APACHE_READ_MODEL, BUILD_PATH, BUILD_PATH_LOGGER_FILE
from kyutil.date_utils import get_today
from kyutil.file import recursive_chmod
from kyutil.log import zero_log
from kyutil.shell import start_httpd
from kyutil.url import url_reachable

logger = zero_log(__file__, BUILD_PATH_LOGGER_FILE)


def update_state(*args, **kwargs):
    print(args)
    print(kwargs)


def _params_check_base(params):
    """base参数校验"""
    _params = params
    _params_core_keys = ['series_version', 'koji_ip', 'target_arch', 'yum_url', 'lorax_templates_url']
    for key in _params_core_keys:
        if not _params.get(key):
            raise ValueError(f"核心参数{key}未定义")
    _params_dict = {
        'series_version': _params.get('series_version'),
        'koji_ip': _params.get('koji_ip'),
        'tag': _params.get('tag'),
        'target_arch': _params.get('target_arch'),
        'yum_url': _params.get('yum_url'),
        'deps': _params.get("deps"),
        'lorax_templates_url': _params.get("lorax_templates_url")
    }
    if _params.get('series_version') == '7':
        _params_check_p7(_params, _params_dict)
    elif _params.get('series_version') == '8' or _params.get('series_version') == 'SP*':
        _params_dict = _params_check_p8(_params, _params_dict)
    else:
        _params_dict = _params_check_p8(_params, _params_dict)
    _params_check_build(_params, _params_dict)

    return strip_dict(_params_dict)


def _params_check_p7(_params, params_dict):
    """7系参数校验"""
    _params_7 = ['product_name', 'release', 'build', 'volid', 'replace_comps']
    for key in _params_7:
        if not _params.get(key):
            raise ValueError(f"7系构建参数{key}未定义")
    _params_dict_7 = {
        'product_name': _params.get('product_name'),
        'release': _params.get('release'),
        'build': _params.get('build'),
        'bugzilla_url': _params.get('bugzilla_url') if _params.get('bugzilla_url') else "https://bugzilla.kylinos.cn",
        'volid': _params.get('volid'),
        'iso_name': _params.get('iso_name'),
        'product_info': _params.get('product_info'),
        'release_path': _params.get('release_path'),
        'replace_comps': _params.get('replace_comps') if _params.get('replace_comps') else False,
    }
    params_dict.update(_params_dict_7)
    return params_dict


def _params_check_p8(_params, params_dict):
    """8系参数校验"""
    _params_8 = ['product_name', 'version', 'release', 'build', 'volid', ]
    for key in _params_8:
        if not _params.get(key):
            raise ValueError(f"8系构建参数{key}未定义")
    _params_dict_8 = {
        'product_name': _params.get('product_name'),
        'version': _params.get('version'),
        'release': _params.get('release'),
        'build': _params.get('build'),
        'bugzilla_url': _params.get('bugzilla_url') if _params.get('bugzilla_url') else "https://bugzilla.kylinos.cn",
        'volid': _params.get('volid'),
        'variant': _params.get('variant') if _params.get('variant') else '',
        'iso_name': _params.get('iso_name'),
        'product_info': _params.get('product_info'),
        'release_path': _params.get('release_path'),
    }
    params_dict.update(_params_dict_8)
    return params_dict


def _params_check_build(_params, params_dict):
    """参数校验"""
    _params_build = ['ks_path', 'comps_path', 'not_boot_dir']
    for key in _params_build:
        if not _params.get(key):
            raise ValueError(f"非8系构建，但是参数{key}未定义")
    _params_dict_build = {
        'ks_path': _params.get('ks_path'),
        'comps_path': _params.get('comps_path'),
        'before_repo_package':
            _params.get('before_repo_package', ''),
        'after_repo_package':
            _params.get('after_repo_package', ''),
        'boot_dir': _params.get('boot_dir', ''),
        'not_boot_dir': _params.get('not_boot_dir', ''),
        'pungi_cmd': _params.get('pungi_cmd', ''),
        'lorax_cmd': _params.get('lorax_cmd', ''),
        'mkisofs_cmd': _params.get('mkisofs_cmd', ''),
        'pungi_url': _params.get('pungi_url', ''),
        'lorax_url': _params.get('lorax_url', ''),
        'ks_install_url': _params.get('ks_install_url', ''),
        'grub_url': _params.get('grub_url', ''),
        'treeinfo_url': _params.get('treeinfo_url', ''),
        'mash_blacklist_path': _params.get('mash_blacklist_path'),
        'strict_keys': _params.get('strict_keys'),
        'debuginfo': _params.get('debuginfo'),
        'debugsource': _params.get('debugsource'),
        'source': _params.get('source'),
        'deps': _params.get('deps'),
        'tags': _params.get('tags'),
        'base_iso_id': _params.get('base_iso_id', None),
        'base_iso_name': _params.get('base_iso_name', None)
    }
    params_dict.update(_params_dict_build)
    return params_dict


def check_mash_status(mash_ok_in, mash_task, logger=logger):
    err_msg = mash_log = mash_repo = ""
    if mash_task.info and isinstance(mash_task.info, dict):
        if mash_task.info.get('status') == states.FAILURE:
            mash_log = mash_task.info.get('mash_log')
        elif f"{mash_task.info.get('status')}" == "SUCCESS":
            mash_repo, mash_log, _ = mash_task.info.get('mash_httpd'), \
                mash_task.info.get('mash_log'), mash_task.info.get('mash_list')
            mash_repo = str(mash_repo.strip("[").strip("]").strip("{").strip("}"))
            for one in mash_repo.split("\n"):
                if not url_reachable(one, logger=logger):
                    logger.error(f"对应的mash执行失败，源地址不可用：[{one}]")
                    err_msg = f"mash执行失败，源地址不可用：[{one}]"
                    return False, err_msg, mash_log, mash_repo
            mash_ok_in = True
        else:
            err_msg = f"mash状态不对，[{mash_task.info}]"
            mash_ok_in = False
    return mash_ok_in, err_msg, mash_log, mash_repo


def mash_wait(params: dict, this_task_id="", logger=logger):
    """单目录监控返回方法"""
    mash_repo = mash_log = err_msg = mash_list = mash_sum = None
    # 等待对应的mash任务执行完成
    logger.debug(f"等待 mash_task[{params['mash_task_id']}]结果")
    while True:
        mash_task = AsyncResult(params['mash_task_id'])
        if f"{mash_task.status}" == "FAILURE":
            if mash_task.info and isinstance(mash_task.info, dict):
                mash_log = mash_task.info.get('mash_log')
            logger.error(f"mash任务失败，_id为{params['mash_task_id']}")
            mash_status = False
            break
        elif f"{mash_task.status}" == "SUCCESS":
            mash_status, err_msg, mash_log, mash_repo = check_mash_status(False, mash_task)
            break
        elif f"{mash_task.status}" == "REVOKED":
            if mash_task.info and isinstance(mash_task.info, dict):
                mash_log = mash_task.info.get('mash_log')
            logger.error(f"mash任务被取消，_id为{params['mash_task_id']}")
            mash_status = False
            break
        else:
            logger.debug(
                f"Task mash「{params['mash_task_id']}」's status is ：{mash_task.status}..... Wait 10s。Build Task ID: {this_task_id}")
            time.sleep(10)
    logger.debug("mash结果检测完成")
    return {"mash_ok": mash_status, "mash_repo": mash_repo,
            "mash_log": mash_log, "mash_list": mash_list, "mash_sum": mash_sum, "err_msg": err_msg}


def create_iso_process(**kwargs):
    """集成构建流程方法定义"""
    mash_result = kwargs.get("mash")
    update_state = kwargs.get("state")
    run_params = kwargs.get("params")
    request_id = kwargs.get("id")
    rs = kwargs.get("build")
    nkvers = None
    repos = None
    repo_create_time = None
    dracut_augment = None
    iso_log = iso_size = sha256_value = iso_name = err_msg = lorax_templates_sha256sum = None
    logger.info(f"参数：params = {run_params}")
    logger.info(f"参数：id = {request_id}")
    logger.info(f"参数：mash = {mash_result}")
    logger.info(f"实例：build = {type(rs).__name__}")
    tags = kwargs.get("tags", [])
    try:
        # 检查mash
        rs.check_mash(**kwargs.get("mash"))
        iso_log = rs.check_iso_log()  # 1
        rs.mock_pungi_gather()  # 3
        rs.mock_create_repo()  # 4
        rs.mock_pungi_lorax()  # 5
        rs.download_not_boot_file()  # 4.5 - 5.5
        rs.fix_process_file()  # 6
        rs.write_productinfo()  # 7
        rs.script_before_mkisofs()
        rs.mkisofs_iso_file()  # 8
        rs.create_package_files()  # 9
        rs.copy_iso()  # 10
        iso_name, iso_size, sha256_value, nkvers, tags, repos, lorax_templates_sha256sum, repo_create_time, dracut_augment = rs.post_create_iso()  # 11
        recursive_chmod(kwargs.get("build_root_path") + get_today(ts=time.time(), fmt='%Y%m%d'), APACHE_READ_MODEL)
        start_httpd()
    except Exception as e:
        err_msg = str(e)
        tags.append(err_msg)
        update_state(state=states.FAILURE)
        traceback.print_exc()
        logger.info(f"ISO构建主任务执行失败，ERRMSG:[{err_msg}]")

    return {
        "rs": rs,
        'tags': tags,
        "nkvers": nkvers,
        "err_msg": err_msg,
        "iso_log": iso_log,
        "iso_size": iso_size,
        "iso_name": iso_name,
        "md5": sha256_value,
        "sha256_value": sha256_value,
        "lorax_templates_sha256sum": lorax_templates_sha256sum,
        "repos": repos,
        "dracut_augment": dracut_augment,
        "repo_create_time": repo_create_time
    }


def create_iso_process_before_mash_result(release_class, **kwargs):
    """集成构建流程方法定义"""
    update_state = kwargs.get("state")
    run_params = kwargs.get("params")
    request_id = kwargs.get("id")
    cur_day = kwargs.get("cur_day")
    rs = None
    try:
        rs = release_class(state=update_state, params=run_params, id=request_id, cur_day=cur_day)
        rs.init_run_env_base()
        rs.prep_create_iso()
    except Exception as e:
        err_msg = str(e)
        update_state(state=states.FAILURE)
        traceback.print_exc()
        logger.info(f"ISO环境构建有误，ERRMSG:[{err_msg}]")
        return False, rs
    return True, rs


def build_iso(build, iso_return_before_mash, _params, mash_result_dict, update_state, run_params, self, iso_return, cur_day, build_root_path=BUILD_PATH):
    # mash，mock都成功，
    if iso_return_before_mash:
        logger.info("mash任务成功，mock成功，启动ISO主构建过程")
        logger.info(f"mash结果：{mash_result_dict}")
        _params['mash_httpd'] = mash_result_dict.get('mash_httpd', mash_result_dict.get('mash_repo'))
        iso_return = create_iso_process(
            build_root_path=build_root_path,
            state=update_state,
            params=run_params,
            id=self.request.id,
            mash=mash_result_dict,
            build=build,
            cur_day=cur_day
        )
        logger.debug(f"ISO主构建完成，ISO名称是：{iso_return.get('iso_name')}")
        logger.info("ISO构建主任务执行完成，进行数据回传")
        task_state = states.SUCCESS if iso_return.get('iso_name') else states.FAILURE
    # mash成功， mock失败
    else:
        logger.error("mash成功，mock环境初始化失败")
        task_state = states.FAILURE
        update_state(state=states.FAILURE)
        iso_return['err_msg'] = "mash成功，mock环境初始化失败"

    return task_state, iso_return
