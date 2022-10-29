import time
import uuid
import string
import random
import hashlib
from typing import Dict

from .settings import *


def cookie_str2dict(cookie_string: str) -> Dict:
    cookie = cookie_string.replace(" ", "").split(";")
    cookies = {}
    for i in cookie:
        cookies[i.split("=")[0]] = i.split("=")[1]
    return cookies


# 获取请求Header里的DS 当web为true则生成网页端的DS
def get_ds(web: bool) -> str:
    if web:
        n = mihoyobbs_Salt_web
    else:
        n = mihoyobbs_Salt
    i = str(timestamp())
    r = random_text(6)
    c = md5("salt=" + n + "&t=" + i + "&r=" + r)
    return f"{i},{r},{c}"


# 获取请求Header里的DS(版本2) 这个版本ds之前见到都是查询接口里的
def get_ds2(q: str, b: str) -> str:
    n = mihoyobbs_Salt2
    i = str(timestamp())
    r = str(random.randint(100001, 200000))
    add = f'&b={b}&q={q}'
    c = md5("salt=" + n + "&t=" + i + "&r=" + r + add)
    return f"{i},{r},{c}"


# 生成一个device id
def get_device_id(cookie) -> str:
    return str(uuid.uuid3(uuid.NAMESPACE_URL, cookie)).replace(
        '-', '').upper()


# 时间戳
def timestamp() -> int:
    return int(time.time())


def random_text(num: int) -> str:
    return ''.join(random.sample(string.ascii_lowercase + string.digits, num))


def md5(text: str) -> str:
    md5 = hashlib.md5()
    md5.update(text.encode())
    return md5.hexdigest()
