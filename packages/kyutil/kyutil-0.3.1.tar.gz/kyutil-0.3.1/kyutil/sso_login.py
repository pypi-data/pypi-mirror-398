#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：ctdy
@File    ：auto_sso.py
@IDE     ：PyCharm
@Author  ：xuyong@kylinos.cn
@Date    ：2025/6/5 上午11:34
@Desc    ：说明：
"""

import argparse
import base64
import os

import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding

PUBLIC_KEY_STRING = 'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAqEyOop2t43djjFC8Qg1Q+TN7HEj3zvrLrJgNhl799Ye8pK7++Vg9rLisi3xzFuwNooEzhJ/DcXazw9YCalLP+HgFplfrjUt5s7YJPshDGyW4qXnf2XLHc1YtRzPmd6FXN2IVQ866dd3S4KU3Sj8F9+JlyxaKXl8ZFhmUx1aejC0Porql0WoWLW9hsvRcMt+NUUQFTFL3F5LxQ9rZPVFZ/Qk9+lzvvU5zpsOwwk1T8pFoMwp9lFzgODIZ4awx+aPgOKHIta3hH93pdqxPvpBekL7XMZ/lSDBYV6npbTnY/6rVBX4cpAoqfmC9KbsIb19/MdxdqP5RO64XZsH5gGUfmQIDAQAB'
LOGIN_URL = 'https://sso.kylinos.cn/oauth2/token?grant_type=password&response_type=code'


def sso_password_encryption(public_key_string, raw_password: str):
    """
    KylinSSO Password Encryption Method
    :param str public_key_string: public key pem file.
    :param int raw_password: prepare encrypt password.
    :returns str password: encryption password or raises exception
    """
    try:
        public_key_string = public_key_string.replace("\r\n", "")
        public_key_bytes = base64.b64decode(public_key_string)
        public_key = serialization.load_der_public_key(
            public_key_bytes,
            backend=default_backend()
        )
        cipher_text = public_key.encrypt(
            str(raw_password).encode('utf-8'),
            padding.PKCS1v15()
        )
        return cipher_text.hex()
    except Exception as e:
        raise Exception(e)


def parse_args():
    parser = argparse.ArgumentParser(description="Kylin SSO 登录并获取访问令牌，用于调用受保护资源。")
    parser.add_argument('--username', '-u', required=True, help='SSO登录用户名')
    parser.add_argument('--password', '-p', required=True, help='SSO登录密码')
    parser.add_argument('--url', '-l', required=True, help='要下载的目标URL')
    parser.add_argument('--dest', '-d', required=False, help='下载到目录，默认当前目录')
    return parser.parse_args()


def gen_token(username, password, client_id="", client_secret=""):
    encrypted_password = sso_password_encryption(PUBLIC_KEY_STRING, password)
    data = {
        'username': username,
        'password': encrypted_password,
        'client_id': client_id,
        'client_secret': client_secret,
    }

    res = requests.post(LOGIN_URL, json=data)
    return res.json()['data']['tokenInfo']['access_token']


def download_sso_iso(token, url, dest=os.getcwd()):
    cmd = None
    if url and token:
        cmd = f'wget -P {dest} --header="Authorization: {token}" "{url}"'
    if cmd:
        print("开始下载：" + cmd)
        os.system(cmd)
    else:
        print("请检查参数")


def main():
    args = parse_args()
    at = gen_token(args.username, args.password, os.getenv("CLIENT_ID"), os.getenv("CLIENT_SECRET"))
    download_sso_iso(at, args.url, args.dest)


if __name__ == '__main__':
    main()
