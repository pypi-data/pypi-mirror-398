import json
from copy import deepcopy

import zbToolLib as zb


def getSign(post: dict):
    """
    获取H5 Api POST请求的标识码
    :param post: 请求数据字典
    :return: 处理后的标识
    """
    sign = ""
    for k in sorted(list(post.keys())):
        sign += f"{k}={post[k]}&"
    sign += "mc#h5page#web"
    from hashlib import md5
    sign = md5(sign.encode("utf-8")).hexdigest()
    return sign


def processPostData(post: dict):
    """
    处理H5 Api POST请求的数据
    :param post: 请求数据字典
    :return: 处理后的请求数据字典
    """
    result = deepcopy(post)
    result["sign"] = getSign(post)
    return result


def H5ApiPost(url: str, post: dict):
    """
    中国版H5 Api POST请求
    :param url: Api地址，仅需填写https://g79apigatewayobt.nie.netease.com/h5后面的部分。
    :param post: 请求数据字典，不需要添加sign标识
    :return: 请求结果requests Response对象
    """
    if not url.startswith("https://g79apigatewayobt.nie.netease.com/h5"):
        url = "https://g79apigatewayobt.nie.netease.com/h5" + url
    result = zb.postUrl(url, json=processPostData(post))
    return result


def getItemDetail(item_id: str | int, channel_id: int = 5):
    """
    获取组件详情
    :param item_id: 组件id
    :param channel_id: 渠道id，默认为5
    :return: 请求结果
    """
    if not isinstance(item_id, str):
        item_id = str(item_id)
    return json.loads(H5ApiPost("/pe-item-detail-v2", {"item_id": item_id, "channel_id": channel_id}).text)


def getUserDetail(user_id: str | int):
    """
    获取用户详情
    :param user_id: 用户id
    :return: 请求结果
    """
    if not isinstance(user_id, str):
        user_id = str(user_id)
    return json.loads(H5ApiPost("/user-detail/query/other", {"user_id": user_id}).text)


def getUserComment(item_id: str | int, length: int = 10, sort_type: int = 1, order: int = 0):
    """
    获取指定组件的用户评论
    :param item_id: 组件id
    :param length: 评论数量
    :param sort_type: 排序方式
    :param order: 排序顺序
    :return: 请求结果
    """
    if not isinstance(item_id, str):
        item_id = str(item_id)
    return json.loads(H5ApiPost("/pe-user-comment", {"item_id": item_id, "length": length, "sort_type": sort_type, "order": order}).text)


def getDownloadInfo(item_id: str | int):
    """
    获取组件下载信息
    :param item_id: 组件id
    :return: 请求结果
    """
    if not isinstance(item_id, str):
        item_id = str(item_id)
    return json.loads(H5ApiPost("/pe-download-item/get-download-info", {"item_id": item_id}).text)


def getDeveloperInfo(developer_id: str | int):
    """
    获取开发者信息
    :param developer_id:
    :return:
    """
    if not isinstance(developer_id, str):
        developer_id = str(developer_id)
    return json.loads(H5ApiPost("/pe-developer-homepage/load_developer_homepage/get/", {"id": developer_id}).text)
