# -*- coding: UTF-8 -*-
import os

from kyutil.config import APACHE_READ_MODEL
from kyutil.file import ensure_dir

chroot_fd = -1


def into_chroot_env(chroot_path):
    """
    函数功能：进入chroot状态
    函数参数：chroot_path - chroot的目录
    函数返回值：无
    """
    global chroot_fd
    if chroot_fd == -1:
        try:
            chroot_fd = os.open("/", os.O_PATH)
            os.chdir(chroot_path)
            os.chroot(".")
            os.listdir(".")
        except Exception as e:
            print(f"chroot失败：{e}")


def exit_chroot_env():
    """
    函数功能：退出chroot状态
    函数参数：无
    函数返回值：无
    """
    global chroot_fd
    if chroot_fd > 0:
        os.chdir(chroot_fd)
        os.chroot(".")
        os.close(chroot_fd)
        chroot_fd = -1


def get_mock_template(tag):
    if str(tag).startswith("ns6"):
        return "mock_ns6.cfg"
    elif str(tag).startswith("v11"):
        return "mock_ns11.cfg"
    return "mock_ns7_plus.cfg"


def generate_mock_config(params, mock_tag, _logger, config_root_dir):
    """
    mock通用配置文件设置
    os.path.abspath(__file__)
    """
    # 输出测试
    fn = get_mock_template(mock_tag)
    fp = f"{config_root_dir}{fn}"
    if os.path.isfile(fp):
        content = open(fp, encoding="utf-8").read()
        content = content.replace("{Packages}", "yum" if params.get('series_version') == '7' else "dnf")
        content = content.replace("{arch}", params.get('target_arch'))
        content = content.replace("{root}", mock_tag)
        content = content.replace("{yum_url}", params.get('yum_url'))
        if params.get('yum_url').find("kojifiles/repos") < 0:
            content = content.replace('#{yum_url_in_koji}', '')
    else:
        _logger.error(f"未找到mock模版配置文件: {fp}. {os.path.isfile(fp)}")
        raise FileNotFoundError(f"未找到mock模版配置文件: {fp}, {os.path.isfile(fp)}")
    mock_cfile = f"/etc/mock/{mock_tag}.cfg"
    ensure_dir(mock_cfile)
    with open(mock_cfile, 'w', APACHE_READ_MODEL) as f:
        f.writelines(content)
    os.chmod(mock_cfile, APACHE_READ_MODEL)
    _logger.info("生成Mock配置文件 " + mock_cfile)
    return mock_cfile
