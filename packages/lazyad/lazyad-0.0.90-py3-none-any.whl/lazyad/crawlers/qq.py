from lazysdk import lazyrequests
from lazysdk import lazytime
import copy


default_headers = {
        "Host": "ad.qq.com",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "TE": "trailers"
    }  # 默认的header


def new_account_list(
        cookie: str,
        user_id: int,
        business_id: int,
        start_date: str = None,
        end_date: str = None,
        page: int = 1,
        page_size: int = 20,
        account_id: int = None,  # 支持按户id搜索
        account_status: int = 1,
        sort_seq: str = None,
        sort_field: str = None,
        platform_type: int = 1
):
    """
    概览-账户 页面按照消耗降序排序的数据
    :param cookie:
    :param user_id: 登录用户的id
    :param business_id: 大户id
    :param start_date:
    :param end_date:
    :param page:
    :param page_size:
    :param account_id: 子户id
    :param account_status: 账户状态
        1：有效
        2：待审核
        3：审核不通过
        4：封停
        21：临时冻结
    :return:
    """
    if not start_date:
        start_date = lazytime.get_date_string(days=-1)
    if not end_date:
        end_date = lazytime.get_date_string(days=-1)
    url = "https://ad.qq.com/tap/v1/account_daily_report/new_account_list?unicode=1&post_format=json"
    temp_headers = copy.deepcopy(default_headers)
    temp_headers["Cookie"] = cookie
    data = {
        "new_source": 1,
        "user_id": user_id,
        "page": page,
        "page_size": page_size,
        "need_sync": True,
        "sync_param_ready": True,
        "business_id_list": [
            business_id
        ],
        "dynamic_field_list": [
            "corporation_name",
            "corporation_alias",
            "rule_target_enable",
            "derive_status",
            "comment",  # 标签
            "cost"  # 消耗
        ],
        "time_line": "REQUEST_TIME",
        "start_date_millons": lazytime.get_date2timestamp(date=start_date) * 1000,  # 开始时间的时间戳
        "end_date_millons": lazytime.get_date2timestamp(date=end_date) * 1000,  # 结束时间的时间戳
        "account_status": account_status,
        "platform_type": platform_type,
        "use_top_sort": True,
        "filter_empty_data": 0
    }
    if account_id:
        data["account_id"] = [account_id]
    if sort_seq:
        data["sort_seq"] = sort_seq  # desc:降序排序，会自动过滤0数据
    if sort_field:
        data["sort_field"] = sort_field  # cost:按照消耗排序
    return lazyrequests.lazy_requests(
        method="POST",
        url=url,
        headers=temp_headers,
        json=data
    )


def account_list_v30(
        cookie: str,
        user_id: int,
        business_id: int,
        start_date: str = None,
        end_date: str = None,
        page: int = 1,
        page_size: int = 20,
        account_id: int = None,  # 支持按户id搜索
        account_status: int = 1,
        sort_seq: str = None,
        sort_field: str = None,
        platform_type: int = 1
):
    """
    概览-账户 ADQ3.0账户列表
    :param cookie:
    :param user_id: 登录用户的id
    :param business_id: 大户id
    :param start_date:
    :param end_date:
    :param page:
    :param page_size:
    :param account_id: 子户id
    :param account_status: 账户状态
        1：有效
        2：待审核
        3：审核不通过
        4：封停
        21：临时冻结
    :return:
    """
    if not start_date:
        start_date = lazytime.get_date_string(days=-1)
    if not end_date:
        end_date = lazytime.get_date_string(days=-1)
    url = "https://ad.qq.com/tap/v1/account_daily_report/new_account_list?unicode=1&post_format=json"
    temp_headers = copy.deepcopy(default_headers)
    temp_headers["Cookie"] = cookie
    data = {
        "new_source": 1,
        "user_id": user_id,
        "page": page,
        "page_size": page_size,
        "need_sync": True,
        "sync_param_ready": True,
        "business_id_list": [
            business_id
        ],
        "dynamic_field_list": [
            "corporation_name",
            "corporation_alias",
            "rule_target_enable",
            "derive_status",
            "comment",  # 标签
            "cost"  # 消耗
        ],
        "time_line": "REQUEST_TIME",
        "start_date_millons": lazytime.get_date2timestamp(date=start_date) * 1000,  # 开始时间的时间戳
        "end_date_millons": lazytime.get_date2timestamp(date=end_date) * 1000,  # 结束时间的时间戳
        "account_status": account_status,
        "platform_type": platform_type,
        "use_top_sort": True,
        "filter_empty_data": 0
    }
    if account_id:
        data["account_id"] = [account_id]
    if sort_seq:
        data["sort_seq"] = sort_seq  # desc:降序排序，会自动过滤0数据
    if sort_field:
        data["sort_field"] = sort_field  # cost:按照消耗排序
    return lazyrequests.lazy_requests(
        method="POST",
        url=url,
        headers=temp_headers,
        json=data
    )
