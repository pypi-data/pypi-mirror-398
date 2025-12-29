# 微盛，企业管家 https://platform.wshoto.com
from lazysdk import lazyrequests
import copy


default_headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, zstd",
        "Accept-Language": "en-US,en;q=0.5",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Host": "platform.wshoto.com",
        "Origin": "https://platform.wshoto.com",
        "Pragma": "no-cache",
        "Referer": "https://platform.wshoto.com/index/dashboard",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "TE": "trailers",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:139.0) Gecko/20100101 Firefox/139.0",
        "x-admin-header": "1",
        "x-clientType-header": "pc",
        "x-header-host": "platform.wshoto.com",
    }


def dashboard(
        authorization: str
):
    url = "https://platform.wshoto.com/bff/index/private/pc/dashboard?saMode=SECRET"
    headers = copy.deepcopy(default_headers)
    headers["Authorization"] = authorization
    return lazyrequests.lazy_requests(
        method="POST",
        url=url,
        headers=headers
    )


def material_package(
        authorization: str,
        search_package_name: str = ""
):
    """
    【内容中心】/【组合素材】/【配置素材合集】/查询
    :param authorization:
    :param search_package_name: 被查询的素材合集名称
    :return:
    """
    url = "https://platform.wshoto.com/bff/content/private/pc/material/package/packageQuery"
    headers = copy.deepcopy(default_headers)
    headers["Authorization"] = authorization
    data = {
        "pageSize": 1000,
        "pageIndex": 1,
        "searchPackageName": search_package_name,
        "isManager": 1,
        "isContainsNoUse": True,
        "isContainsStop": True,
        "businessType": 14,
        "isShowRecommend": True,
        "isScope": False
    }
    return lazyrequests.lazy_requests(
        method="POST",
        url=url,
        headers=headers,
        json=data
    )


def create_material_package(
        authorization: str,
        name: str
):
    """
    【内容中心】/【组合素材】/【配置素材合集】/【+添加素材合集】
    :param authorization:
    :param name: 素材合集名称
    :return: {"code":"00000","msg":"OK","data":{"id":"2000222213115036674"}}
    """
    url = "https://platform.wshoto.com/bff/content/private/pc/materialCategory/create"
    headers = copy.deepcopy(default_headers)
    headers["Authorization"] = authorization
    data = {
        "name": name,
        "businessType":14,
        "editStatus":0
    }
    return lazyrequests.lazy_requests(
        method="POST",
        url=url,
        headers=headers,
        json=data
    )


class WshotoCrawler:
    def __init__(
            self,
            authorization: str,
            headers: dict = None,
    ):
        if headers is None:
            headers = default_headers
        self.authorization = authorization
        self.headers = headers
        self.headers["Authorization"] = authorization

    def upload_file(
            self,
            file_path: str,
    ):
        """
        上传文件
        :param file_path: 文件路径
        :return:
        """
        url = "https://platform.wshoto.com/bff/content/private/pc/file/upload"
        headers = copy.deepcopy(self.headers)

        # 以二进制模式打开图片文件
        with open(file_path, 'rb') as f:
            files = {'file': (file_path, f, 'multipart/form-data')}
            return lazyrequests.lazy_requests(
                method="POST",
                url=url,
                headers=headers,
                files=files
            )