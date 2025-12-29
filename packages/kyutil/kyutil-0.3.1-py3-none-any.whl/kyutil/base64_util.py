# -*- coding: UTF-8 -*-
import base64


def pwd_b64decode(base64_str: str) -> str:
    return base64.b64decode(bytes(base64_str, 'utf-8')).decode()

