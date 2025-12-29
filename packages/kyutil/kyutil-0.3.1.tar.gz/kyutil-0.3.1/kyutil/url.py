# -*- coding: UTF-8 -*-
"""
@File    ：url.py
"""
import os
import re

import requests
import urllib3
from bs4 import BeautifulSoup

from kyutil.config import BUILD_PATH_LOGGER_FILE
from kyutil.http_util import send_request
from kyutil.log import zero_log

logger = zero_log(__file__, BUILD_PATH_LOGGER_FILE)
urllib3.disable_warnings()


def url_reachable(url, logger=logger):
    """判断url是否可达"""
    if url and url.startswith("http"):
        try:
            r = send_request(url, verify=False, method="HEAD", timeout=7)
            logger.info(f"URL可达性检测状态码：{r.status_code}")
            return r.status_code < 400
        except Exception as e:
            logger.warning(f"URL {url} 不可达, {e}")
            return False


def url_filename(url_):
    if not url_:
        return ""
    return os.path.basename(url_)


def fetch_log_files(url, prefix="build", suffix='log'):
    # 发送GET请求获取页面内容
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve page, status code: {response.status_code}, URL: {url}")
        return []

    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(response.text, 'html.parser')

    # 查找所有的链接
    links = soup.find_all('a')
    # 定义正则表达式模式
    pattern = re.compile(fr'^{prefix}.*\.{suffix}$')

    # 过滤出符合模式的链接
    build_log_files = [link.get('href') for link in links if pattern.match(link.get('href', ''))]

    return build_log_files[0] if build_log_files else ''
