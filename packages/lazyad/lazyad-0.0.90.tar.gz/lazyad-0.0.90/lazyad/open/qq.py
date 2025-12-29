from lazysdk import lazyrequests
import showlog

from lazysdk import lazytime
import json
import random
import copy
import time


"""
2024-04-11 全面升级至3.0版本 https://developers.e.qq.com/v3.0/docs/api
"""


def make_nonce():
    """
    参考示例代码的生成一个随机数
    :return:
    """
    return str(time.time()) + str(random.randint(0, 999999))


def oauth_token2(
        app_id,
        app_secret,
        redirect_uri,
        grant_type='authorization_code',
        auth_code=None,
        refresh_token=None,
):
    """
    OAuth 2.0 授权
    获取/刷新token
    相关文档：https://developers.e.qq.com/docs/start/authorization
    :param auth_code:
    :param app_id:
    :param app_secret:
    :param grant_type: 请求的类型，可选值：authorization_code（授权码方式获取 token）、refresh_token（刷新 token）
    :param refresh_token:
    :param redirect_uri:
    :return:
    """
    redirect_uri = f'{redirect_uri}?app_id={app_id}'

    url = 'https://api.e.qq.com/oauth/token'
    params = {
        'client_id': app_id,
        'client_secret': app_secret,
        'grant_type': grant_type
    }
    if auth_code:
        params['authorization_code'] = auth_code
    if refresh_token:
        params['refresh_token'] = refresh_token
    if redirect_uri:
        params['redirect_uri'] = redirect_uri

    for k in params:
        if type(params[k]) is not str:
            params[k] = json.dumps(params[k])

    return lazyrequests.lazy_requests(
        method="GET",
        url=url,
        params=params
    )


def oauth_token3(
        app_id,
        app_secret,
        redirect_uri=None,
        access_token=None,
        grant_type='authorization_code',
        auth_code=None,
        refresh_token=None,
):
    """
    获取/刷新token
    相关文档：https://developers.e.qq.com/v3.0/docs/api/oauth/token
    :param access_token:
    :param auth_code:
    :param app_id:
    :param app_secret:
    :param grant_type: 请求的类型，可选值：authorization_code（授权码方式获取 token）、refresh_token（刷新 token）
    :param refresh_token:
    :param redirect_uri: 回调地址
    :return:
    """
    params = {
        'client_id': app_id,
        'client_secret': app_secret,
        'grant_type': grant_type
    }
    if access_token:
        # OAuth 相关接口无需提供 access_token、timestamp、nonce 等通用请求参数。
        params['access_token'] = access_token
        params['timestamp'] = int(time.time())
        params['nonce'] = make_nonce()
        url = 'https://api.e.qq.com/v3.0/oauth/token'
    else:
        url = 'https://api.e.qq.com/oauth/token'
    if auth_code:
        params['authorization_code'] = auth_code
    if refresh_token:
        params['refresh_token'] = refresh_token
    if redirect_uri:
        redirect_uri = f'{redirect_uri}?app_id={app_id}'
        params['redirect_uri'] = redirect_uri

    return lazyrequests.lazy_requests(
        method="GET",
        url=url,
        params=params
    )


def get_organization_account_relation(
        access_token: str,
        account_id=None,
        cursor=None,
        page: int = 1,
        page_size: int = 100,
        pagination_mode: str = "PAGINATION_MODE_CURSOR"
):
    """
    版本：3.0
    获取子账号列表
    这里获取子账户主要使用这个方法
    https://developers.e.qq.com/v3.0/docs/api/organization_account_relation/get
    :param access_token:
    :param account_id:
    :param cursor:
    :param page:
    :param page_size: 最小值 1，最大值 100
    :param pagination_mode: 分页方式，注意，为PAGINATION_MODE_NORMAL时，不能获取大于1000条的记录
    :return:
    """
    url = 'https://api.e.qq.com/v3.0/organization_account_relation/get'
    params = {
        'access_token': access_token,
        'timestamp': int(time.time()),
        'nonce': make_nonce(),
        "pagination_mode": pagination_mode,
        "page_size": page_size
    }
    if pagination_mode == "PAGINATION_MODE_NORMAL":
        params["page"] = page
    elif pagination_mode == "PAGINATION_MODE_CURSOR":
        params["cursor"] = cursor
    else:
        showlog.warning("pagination_mode参数错误")
        return

    if account_id:
        params["account_id"] = account_id
    return lazyrequests.lazy_requests(
        method="GET",
        url=url,
        params=params
    )


def get_advertiser_daily_budget(
        access_token: str,
        account_id
):
    """
    版本：3.0
    获取广告账户日预算
    https://developers.e.qq.com/v3.0/docs/api/advertiser_daily_budget/get
    :param access_token:
    :param account_id:
    :return:

    应答示例
    {
        "code": 0,
        "message": "",
        "message_cn": "",
        "data": {
            "account_id": "<ACCOUNT_ID>",
            "daily_budget": 20000,
            "min_daily_budget": 10000
        }
    }
    """
    url = 'https://api.e.qq.com/v3.0/advertiser_daily_budget/get'
    params = {
        'access_token': access_token,
        'timestamp': int(time.time()),
        'nonce': make_nonce(),

        "account_id": account_id,
        "fields": [
            "account_id",
            "daily_budget"
        ]
    }
    return lazyrequests.lazy_requests(
        method="GET",
        url=url,
        params=params
    )


def update_daily_budget(
        access_token: str,
        account_id: int = None,
        daily_budget: int = None,
        update_daily_budget_spec: list = None
):
    """
    版本：3.0
    批量修改广告主日限额
    https://developers.e.qq.com/v3.0/docs/api/advertiser/update_daily_budget
    :param access_token:
    :param account_id:
    :param daily_budget: 账户预算，单位为分
    :param update_daily_budget_spec: 任务列表，[{"account_id":"aaa","daily_budget": 100},{"account_id":"bbb","daily_budget": 100}]
    :return:

    应答示例
    {
        "code": 0,
        "message": "",
        "message_cn": "",
        "data": {
            "list": [
                {
                    "code": 0,
                    "message": "",
                    "message_cn": "",
                    "account_id": "<ACCOUNT_ID>"
                }
            ],
            "fail_id_list": []
        }
    }
    """
    url = 'https://api.e.qq.com/v3.0/advertiser/update_daily_budget'
    params = {
        'access_token': access_token,
        'timestamp': int(time.time()),
        'nonce': make_nonce()
    }
    data = dict()
    if update_daily_budget_spec:
        data["update_daily_budget_spec"] = update_daily_budget_spec
    else:
        data["update_daily_budget_spec"] = [
            {
                "account_id": account_id,
                "daily_budget": daily_budget
            }
        ]
    return lazyrequests.lazy_requests(
        method="POST",
        url=url,
        params=params,
        json=data
    )


class DevelopersEQQ:
    def __init__(
            self,
            access_token,
            user_token=None,
    ):
        self.access_token = access_token
        self.user_token = user_token

    def get_daily_reports(
            self,
            account_id,
            level: str,
            page: int = 1,
            page_size: int = 100,
            start_date: str = None,
            end_date: str = None,
            fields: list = None,
            group_by: list = None,
            filtering: list = None
    ):
        """
        数据洞察-广告数据洞察-获取日报表
        https://developers.e.qq.com/v3.0/docs/api/daily_reports/get
        :param account_id:
        :param level: 获取报表类型级别，当查询业务单元的报表时,level 只支持组件层级，枚举详情：https://developers.e.qq.com/v3.0/docs/enums#api_report_daily_level
        :param page:
        :param page_size:
        :param start_date:
        :param end_date:
        :param fields:
        :param group_by:
        :param filtering:
        :return:
        """
        url = 'https://api.e.qq.com/v3.0/daily_reports/get'

        if not start_date:
            start_date = lazytime.get_date_string(days=0)
        if not end_date:
            end_date = lazytime.get_date_string(days=0)
        if not fields:
            fields = [
                "account_id",
                "date",
                "cost"
            ]
        if not group_by:
            group_by = ["date"]
        parameters = {
            'access_token': self.access_token,
            'timestamp': int(time.time()),
            'nonce': str(time.time()) + str(random.randint(0, 999999)),

            "account_id": account_id,
            "level": level,
            "time_line": "REQUEST_TIME",
            "date_range": {
                "start_date": start_date,
                "end_date": end_date
            },
            "group_by": group_by,  # 聚合参数
            "order_by": [
                {
                    "sort_field": "cost",  # 排序字段
                    "sort_type": "DESCENDING"  # 排序方式:ASCENDING(升序)/DESCENDING(降序)
                }
            ],  # 排序字段
            "page": page,
            "page_size": page_size,
            "fields": fields  # 指定返回的字段列表，必需写，不写不返回数据，具体能写哪些，看文档
        }
        if filtering:
            parameters["filtering"] = filtering

        for k in parameters:
            if type(parameters[k]) is not str:
                parameters[k] = json.dumps(parameters[k])

        return lazyrequests.lazy_requests(
            method="GET",
            url=url,
            params=parameters,
        )

    def get_daily_reports_day_all(
            self,
            account_id,
            level: str,
            cost_min: int = None,
            start_date: str = None,
            end_date: str = None,
            fields: list = None,
            group_by: list = None,
    ):
        """
        开发文档：https://developers.e.qq.com/v3.0/docs/api/daily_reports/get
        :param level: 获取报表类型级别，当查询业务单元的报表时,level 只支持组件层级，枚举详情：https://developers.e.qq.com/v3.0/docs/enums#api_report_daily_level

        """
        task_data = list()
        if not fields:
            fields = [
                "date",  # 日期
                "account_id",  # 账号ID
                "cost",  # 花费，单位分
                "thousand_display_price",  # 千次展现均价，单位分
                "valid_click_count",  # 点击次数
                "conversions_count",  # 目标转化量
                "from_follow_uv",  # 公众号关注人数
                "dynamic_creative_id",  # 创意id
                "dynamic_creative_name",
                "scan_follow_user_count",  # 加企业微信客服人数。添加企微客服人数
                "cpc",  # 点击均价
                "scan_follow_user_cost",  # 加企业微信客服成本（人数）
                "income_val_1",  # 激活首日广告变现金额
            ]
        if not group_by:
            group_by = ["date", "dynamic_creative_id"]
        page = 1
        while True:
            showlog.info(f"正在采集第 {page} 页的数据...")
            response = self.get_daily_reports(
                account_id=account_id,
                level=level,
                fields=fields,
                group_by=group_by,
                page=page,
                start_date=start_date,
                end_date=end_date
            )
            if response.get('code') == 0:
                response_data = response.get('data')
                if response_data:
                    # print(response_data)
                    response_data_list = response_data.get('list')
                    page_info = response_data.get('page_info')
                    total_page = page_info.get('total_page')

                    if response_data_list:
                        showlog.info(f'获取到 {len(response_data_list)} 条记录...')
                        for each_data in response_data_list:
                            each_data_cost = each_data['cost'] / 100
                            each_data['cost'] = each_data_cost
                            each_data['thousand_display_price'] = each_data.get("thousand_display_price", 0) / 100
                            if each_data_cost >= cost_min or cost_min is None:
                                # print(each_data)
                                each_data["access_token"] = self.access_token
                                conversions_count = each_data.get('conversions_count', 0)  # 目标转化量
                                from_follow_uv = each_data.get('from_follow_uv', 0)  # 公众号关注人数
                                scan_follow_user_count = each_data.get('scan_follow_user_count', 0)  # 加企业微信客服人数
                                fans_add = conversions_count + from_follow_uv + scan_follow_user_count  # 进粉数
                                each_data["fans_add"] = fans_add
                                task_data.append(copy.deepcopy(each_data))
                            else:
                                continue
                    else:
                        showlog.warning(f'无数据，response: {response}')
                    if page >= total_page:
                        showlog.info("已采集到最后一页")
                        break
                    else:
                        page += 1
                else:
                    showlog.warning(f'response: {response}')
                    break
            else:
                showlog.warning(f'response: {response}')
                break
        return task_data

    def adgroups_get(
            self,
            account_id,
            page: int = 1,
            page_size: int = 100,
            fields: list = None,
            filtering: list = None,
            is_deleted: bool = False,
            pagination_mode: str = None,
            cursor: str = None
    ):
        """
        展示广告管理-广告-获取广告
        https://developers.e.qq.com/v3.0/docs/api/adgroups/get
        :param account_id:
        :param page:
        :param page_size:
        :param is_deleted: 是否已删除，true：是，false：否
        :param fields: 指定返回的字段列表
        :param pagination_mode: 分页方式，默认使用 PAGINATION_MODE_NORMAL，详见：https://developers.e.qq.com/v3.0/docs/enums#api_pagination_mode
        :param cursor: 游标值，游标翻页模式(PAGINATION_MODE_CURSOR)使用，第一次拉取无需填写、后续拉取传递上一次返回的 cursor 数值

        :param filtering:

        :return:
        """
        url = 'https://api.e.qq.com/v3.0/adgroups/get'
        if not fields:
            fields = [
                "account_id",
                "system_status",
                "configured_status"
            ]

        parameters = {
            'access_token': self.access_token,
            'timestamp': int(time.time()),
            'nonce': str(time.time()) + str(random.randint(0, 999999)),

            "account_id": account_id,
            "page": page,
            "page_size": page_size,
            "is_deleted": is_deleted,
            "fields": fields,  # 指定返回的字段列表，必需写，不写不返回数据，具体能写哪些，看文档

        }
        if pagination_mode is not None:
            parameters["pagination_mode"] = pagination_mode
        if cursor is not None:
            parameters["cursor"] = cursor
        if filtering:
            parameters["filtering"] = filtering

        for k in parameters:
            if type(parameters[k]) is not str:
                parameters[k] = json.dumps(parameters[k])

        return lazyrequests.lazy_requests(
            method="GET",
            url=url,
            params=parameters,
        )

    def adgroups_update(
            self,
            account_id,
            adgroup_id,
            configured_status: str = None,
            user_token: str = None,
    ):
        """
        展示广告管理-广告-更新广告
        https://developers.e.qq.com/v3.0/docs/api/adgroups/update
        :param account_id: [必填]
        :param adgroup_id: [必填]
        :param configured_status: 客户设置的状态，ADX 程序化广告不可填写提交，可选值：{ AD_STATUS_NORMAL, AD_STATUS_SUSPEND }

        :return:
        """
        url = 'https://api.e.qq.com/v3.0/adgroups/update'

        parameters = {
            'access_token': self.access_token,
            'timestamp': int(time.time()),
            'nonce': str(time.time()) + str(random.randint(0, 999999)),
        }
        if user_token is not None:
            parameters["user_token"] = user_token
        else:
            parameters["user_token"] = self.user_token

        data = {
            "account_id": account_id,
            "adgroup_id": adgroup_id,
        }
        if configured_status is not None:
            data["configured_status"] = configured_status

        for k in parameters:
            if type(parameters[k]) is not str:
                parameters[k] = json.dumps(parameters[k])

        return lazyrequests.lazy_requests(
            method="POST",
            url=url,
            params=parameters,
            json=data
        )

    def dynamic_creatives_get(
            self,
            account_id,
            page: int = 1,
            page_size: int = 100,
            fields: list = None,
            filtering: list = None,
            is_deleted: bool = False,
            pagination_mode: str = None,
            cursor: str = None
    ):
        """
        展示广告管理-创意-获取创意
        https://developers.e.qq.com/v3.0/docs/api/dynamic_creatives/get
        :param account_id:
        :param page:
        :param page_size:
        :param is_deleted: 是否已删除，true：是，false：否
        :param fields: 指定返回的字段列表
        :param pagination_mode: 分页方式，默认使用 PAGINATION_MODE_NORMAL，详见：https://developers.e.qq.com/v3.0/docs/enums#api_pagination_mode
        :param cursor: 游标值，游标翻页模式(PAGINATION_MODE_CURSOR)使用，第一次拉取无需填写、后续拉取传递上一次返回的 cursor 数值

        :param filtering:

        :return:
        """
        url = 'https://api.e.qq.com/v3.0/dynamic_creatives/get'
        method = "GET"

        if not fields:
            fields = [
                "account_id",
                "dynamic_creative_id",
                "dynamic_creative_name",
                "configured_status",
                "is_deleted"
            ]

        parameters = {
            'access_token': self.access_token,
            'timestamp': int(time.time()),
            'nonce': str(time.time()) + str(random.randint(0, 999999)),

            "account_id": account_id,
            "page": page,
            "page_size": page_size,
            "is_deleted": is_deleted,
            "fields": fields,  # 指定返回的字段列表，必需写，不写不返回数据，具体能写哪些，看文档

        }
        if pagination_mode is not None:
            parameters["pagination_mode"] = pagination_mode
        if cursor is not None:
            parameters["cursor"] = cursor
        if filtering:
            parameters["filtering"] = filtering

        for k in parameters:
            if type(parameters[k]) is not str:
                parameters[k] = json.dumps(parameters[k])

        return lazyrequests.lazy_requests(
            method=method,
            url=url,
            params=parameters,
        )

    def dynamic_creatives_update(
            self,
            account_id,
            dynamic_creative_id,
            configured_status: str = None,
            user_token: str = None,
    ):
        """
        展示广告管理-创意-更新创意
        https://developers.e.qq.com/v3.0/docs/api/dynamic_creatives/update
        :param account_id: [必填]
        :param dynamic_creative_id: [必填]
        :param configured_status: 客户设置的状态，ADX 程序化广告不可填写提交，可选值：{ AD_STATUS_NORMAL, AD_STATUS_SUSPEND }

        :return:
        """
        url = 'https://api.e.qq.com/v3.0/dynamic_creatives/update'
        method = "POST"

        parameters = {
            'access_token': self.access_token,
            'timestamp': int(time.time()),
            'nonce': str(time.time()) + str(random.randint(0, 999999)),
        }
        if user_token is not None:
            parameters["user_token"] = user_token
        else:
            parameters["user_token"] = self.user_token

        data = {
            "account_id": account_id,
            "dynamic_creative_id": dynamic_creative_id,
        }
        if configured_status is not None:
            data["configured_status"] = configured_status

        for k in parameters:
            if type(parameters[k]) is not str:
                parameters[k] = json.dumps(parameters[k])

        return lazyrequests.lazy_requests(
            method=method,
            url=url,
            params=parameters,
            json=data
        )
