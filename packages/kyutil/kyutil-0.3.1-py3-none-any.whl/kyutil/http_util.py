# -*- coding: UTF-8 -*-
from urllib.parse import urlparse

import requests
import urllib3

from kyutil.config import BUILD_PATH_LOGGER_FILE
from kyutil.log import zero_log

urllib3.disable_warnings()
logger = zero_log(__file__, BUILD_PATH_LOGGER_FILE)


def send_request(url, **kwargs):
    method = str(kwargs["method"]).lower() if "method" in kwargs.keys() else "get"
    data = kwargs["data"] if "data" in kwargs.keys() else None
    headers = kwargs["headers"] if "headers" in kwargs.keys() else None
    cookies = kwargs["cookies"] if "cookies" in kwargs.keys() else None
    proxies = kwargs["proxies"] if "proxies" in kwargs.keys() else None
    timeout = kwargs["timeout"] if "timeout" in kwargs.keys() else None
    verify = kwargs["verify"] if "verify" in kwargs.keys() else False
    json_ = kwargs["json"] if "json" in kwargs.keys() else None
    allow_redirects = kwargs["allow_redirects"] if "allow_redirects" in kwargs.keys() else True
    if method.lower() not in ["get", "post", "head", "delete", "put", "options", 'patch']:
        raise ValueError("method must in [get, post, head, delete, put, options, patch]")
    func = getattr(requests, method.lower())
    resp = func(url, data=data, headers=headers, cookies=cookies, proxies=proxies,
                timeout=timeout, verify=verify, allow_redirects=allow_redirects, json=json_)
    return resp


def is_url(url):
    try:
        r = urlparse(url)
        return all([r.scheme, r.netloc])
    except ValueError:
        return


def result_post_server(_url, _data, logger_=logger):
    """回传数据至服务端，10次连接尝试"""
    for _ in range(10):
        try:
            r = send_request(url=str(_url), method="POST", data=_data, verify=False, timeout=600)
            logger_.info(f"ISO回传成功，状态：{r.status_code}，数据：{_data}")
            return True
        except requests.exceptions.ConnectTimeout:
            logger_.info(f"ISO回传失败，数据  ===== ：{_data}")
            return False
