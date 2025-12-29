from lazysdk import lazyrequests
from lazysdk import lazytime
from urllib import parse
import copy
import re


default_headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Host": "business.oceanengine.com",
        "Origin": "https://business.oceanengine.com",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "TE": "trailers",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0"
    }
default_timeout = 10


def get_token_from_cookie(
        cookie: str
):
    """
    从cookie中提取token
    :param cookie:
    :return:
    """
    cookie = parse.unquote(cookie.replace('+', '%20'))  # 处理解码
    find_csrf_token = re.findall(r'csrftoken=(.*?);', cookie, re.S)
    if find_csrf_token:
        csrf_token = find_csrf_token[0]
        return csrf_token
    else:
        return None


def get_account_list(
        cookie: str,
        csrf_token: str = None,
        page: int = 1,
        page_size: int = 10,
        timeout: int = default_timeout,
        start_date: str = None,
        end_date: str = None,
        order_field: str = 'stat_cost',
        order_type: int = 1
):
    """
    主账号获取账户列表信息
    【账户】-【巨量广告】-【升级版】-【账户】
    :param cookie:
    :param csrf_token:
    :param page: 页码，默认为1
    :param page_size: 每页数量，默认为10，可选10，20，50，100
    :param timeout: 超时时间，单位为秒，默认为5
    :param start_date: 开始日期，默认为当日0点，例如：2022-03-21
    :param end_date: 结束日期，默认为次日0点，例如：2022-03-22
    :param order_field: 排序列，默认为stat_cost，默认按照消耗排序
    :param order_type: 排序方式：0:升序，1:降序；默认为1，降序
    """
    url = "https://business.oceanengine.com/nbs/api/bm/promotion/ad/get_account_list"
    # ------------------ 标准过程 ------------------
    if not csrf_token:
        csrf_token = get_token_from_cookie(cookie=cookie)
    temp_headers = copy.deepcopy(default_headers)
    temp_headers["Cookie"] = cookie
    if csrf_token:
        temp_headers["x-csrftoken"] = csrf_token
    # ------------------ 标准过程 ------------------

    if start_date:
        start_time = lazytime.get_date2timestamp(date=start_date)
    else:
        start_time = lazytime.get_date2timestamp(date=lazytime.get_date_string(-1))

    if end_date:
        end_time = lazytime.get_date2timestamp(date=end_date) + 86400
    else:
        end_time = lazytime.get_date2timestamp(date=lazytime.get_date_string(0))

    data = {
        "offset": page,
        "limit": page_size,
        "order_type": order_type,
        "order_field": order_field,
        "fields": [
            "convert_cnt",
            "conversion_cost",
            "conversion_rate",
            "deep_convert_cnt",
            "deep_convert_cost",
            "deep_convert_rate",
            "stat_cost",
            "show_cnt",
            "cpm_platform",
            "click_cnt",
            "ctr",
            "cpc_platform"
        ],
        "cascade_metrics": [
            "advertiser_followed",
            "advertiser_name",
            "advertiser_id",
            "advertiser_status",
            "advertiser_budget",
            "advertiser_remark",  # 账户备注
            "advertiser_balance",
            "advertiser_valid_balance"
        ],
        "filter": {
            "group": {

            },
            "advertiser": {

            },
            "campaign": {

            },
            "ad": {

            },
            "project": {

            },
            "promotion": {

            },
            "search": {
                "keyword": "",
                "searchType": 0,
                "queryType": "phrase"
            },
            "pricingCategory": [
                2
            ]
        },
        "account_type": 0,
        "platform_version": "2.0",
        "start_time": str(start_time),
        "end_time": str(end_time)
    }
    return lazyrequests.lazy_requests(
        method='POST',
        url=url,
        headers=temp_headers,
        json=data,
        timeout=timeout,
        return_json=True
    )
