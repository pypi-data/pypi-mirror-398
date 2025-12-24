import hashlib
import time
import zbToolLib as zb

def decryptUrl(url: str):
    """
    解密来自g79.gdl.netease.com的链接
    :param url: 链接
    :return: 带有key1和key2的链接
    """
    if "?" in url:
        url = url.split("?")[0]
    expiration_time_hex = hex(int(time.time()) + 60 * 60 * 24 * 365)[2:]
    return f"{url}?key1={hashlib.md5(("mEE7Cot48r9j2AvEL2N6jpXEc" + zb.getUrlPath(url) + expiration_time_hex).encode()).hexdigest()}&key2={expiration_time_hex}"
