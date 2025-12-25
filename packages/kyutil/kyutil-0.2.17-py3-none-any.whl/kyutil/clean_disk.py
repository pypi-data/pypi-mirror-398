# -*- coding: UTF-8 -*-
""""""
import datetime
import os.path
import shutil
import socket
import time

from kyutil.config import BUILD_PATH, BUILD_PATH_LOGGER_FILE
from kyutil.log import zero_log

logger = zero_log(__file__, BUILD_PATH_LOGGER_FILE)


def is_dir(fn):
    return os.path.isdir(fn)


def get_dir_timestamp(dir_path):
    """
    获取目录最新文件的 创建时间
    Args:
        dir_path:目录

    Returns:

    """
    newest = (datetime.datetime.now() - datetime.timedelta(days=3650)).timestamp()
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        for fn in os.listdir(dir_path):
            try:
                fn = dir_path + os.sep + fn
                if is_dir(fn):
                    newest = max(os.path.getctime(fn), newest)
            except Exception as e:
                print("最新的文件获取失败：", e)
        return newest
    return datetime.datetime.now().timestamp()  # 如果路径不存在，返回当前时间


def get_percent_disk_used(dir_path):
    """返回dir_path所在的磁盘已经使用大小的百分比"""
    if not os.path.isdir(dir_path):
        return 0
    total_b, used_b, _ = shutil.disk_usage(dir_path)  # 查看磁盘的使用情况
    return used_b / total_b


def get_path_list_older(dir_path, timestamp=datetime.datetime.now().timestamp()):
    """返回一个目录下比给定时间戳早的目录路径"""
    path_list = map(lambda p: os.path.join(dir_path, p), os.listdir(dir_path))
    return [path_one for path_one in path_list if get_dir_timestamp(path_one) < timestamp and os.path.isdir(os.path.join(dir_path, path_one))]


def get_timestamp_by_day_delta(delta: int = 0):
    """例：输入-5,获取五天前的时间戳"""
    return (datetime.datetime.now() + datetime.timedelta(days=delta)).timestamp()


def remove_path(path):
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.islink(path):
        os.remove(path)


def remove_file(size_percent, time_day_delta, dir_root=BUILD_PATH + "downloaded", logger=logger):
    # 比对机器
    if os.path.isdir(dir_root):
        if size_percent > get_percent_disk_used(BUILD_PATH):
            path_file_list_older = get_path_list_older(BUILD_PATH + "downloaded", get_timestamp_by_day_delta(time_day_delta))
            if path_file_list_older:
                path_will_del = sorted(path_file_list_older, key=lambda x: get_dir_timestamp(x))[0]
                if os.path.exists(path_will_del) and os.path.isfile(path_will_del):
                    logger.info(f'删除文件：{path_will_del} : {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(get_dir_timestamp(path_will_del))))}')
                    remove_path(path_will_del)


def del_dir(dir_one, time_day_delta, white_list, logger=logger):
    logger.info(f"{dir_one} 所在磁盘到达最大占用，需要删除")
    path_list_older = get_path_list_older(dir_one, get_timestamp_by_day_delta(time_day_delta))
    if not path_list_older:
        print(f"{dir_one} 下 没有比较旧的 目录。。")
        return
    path_will_del = sorted(path_list_older, key=lambda x: get_dir_timestamp(x))[0]
    if os.path.exists(path_will_del) and os.path.isdir(path_will_del):
        logger.info(f'删除目录：{path_will_del} : {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(get_dir_timestamp(path_will_del))))}')
        if white_list:
            for i in white_list:
                if path_will_del.find(i) >= 0:
                    continue
                else:
                    remove_path(path_will_del)
        else:
            remove_path(path_will_del)
    else:
        print(f"不是目录:{path_will_del}")


def remove_dir_if_greater_than_size(dir_list: list, size_percent: float = 0.75, time_day_delta=-10, logger=logger, white_list=None):
    """
    功能：
        检测磁盘占用，若超过阈值，遍历给定目录，删除给定阈值之前最老的子目录
    参数：
        dir_list：目录列表
        size_percent：磁盘占用的百分比，当磁盘超过此阈值才进行删除
        time_day_delta：以天为单位的时间阈值，（eg. -10 代表十天前）
    """
    for _ in range(10):  # 设定上限，防止死循环
        for dir_one in dir_list:
            logger.info(f"{dir_one} 所在磁盘已用：{int(get_percent_disk_used(dir_one) * 100)}%")
            if not os.path.isdir(dir_one):
                continue
            if size_percent > get_percent_disk_used(dir_one):  # 还没有到达最大占用，不删除
                logger.info(f"{dir_one}还没有到达最大占用，不删除")
                continue
            del_dir(dir_one, time_day_delta, white_list)
            remove_file(size_percent, time_day_delta)


if __name__ == '__main__':
    dirs = ["/var/lib/mock", BUILD_PATH + "/mash"]
    if os.environ.get("TASK").find("build") >= 0:
        dirs.append(BUILD_PATH)
    try:
        print("apscheduler 开始 初始化 ------")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 2164))
    except socket.error:
        print("磁盘清理任务正在进行,跳过")
    else:
        remove_dir_if_greater_than_size(dirs, time_day_delta=-10, white_list=['mash_cache'])
