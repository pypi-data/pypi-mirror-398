from lazysdk import lazyrequests
from lazysdk import lazytime
import showlog
import hashlib
import time


def convert_data2dict(data):
    data_lines = data.split("\n")
    res = list()
    if len(data_lines) == 1:
        return
    else:
        dict_key_line = data_lines[0]
        dict_keys = dict_key_line.split("\t")
        dict_value_lines = data_lines[1: -1]
        for each_line in dict_value_lines:
            each_line_values = each_line.split("\t")
            temp_dict = dict(zip(dict_keys, each_line_values))
            res.append(temp_dict)
    return res


def convert_format(data):
    data_list = convert_data2dict(data=data)
    for each in data_list:
        # each["Offer_Id"] = each["Offer Id"]
        each["Date"] = f'{each["Date"][0:4]}-{each["Date"][4:6]}-{each["Date"][6:8]}'  # 日期
        each["Impression"] = eval(each["Impression"])
        each["Click"] = eval(each["Click"])
        each["Conversion"] = eval(each["Conversion"])
        each["Ecpm"] = eval(each["Ecpm"])
        each["Cpc"] = eval(each["Cpc"])
        each["Ctr"] = eval(each["Ctr"])
        each["Cvr"] = eval(each["Cvr"])
        each["Ivr"] = eval(each["Ivr"])
        each["Spend"] = eval(each["Spend"])
    return data_list


def make_token(api_key):
    """
    生成token算法，使用时生成
    参考：https://adv.mintegral.com/doc/cn/guide/introduction/token.html
    :param api_key:
    :return:
    """
    timestamp = int(time.time())

    # 计算时间戳的MD5哈希值
    timestamp_md5 = hashlib.md5(str(timestamp).encode()).hexdigest()

    # 将API密钥与时间戳的MD5哈希值连接，并计算最终的MD5哈希值
    token = hashlib.md5((api_key + timestamp_md5).encode()).hexdigest()
    return {"timestamp": timestamp, "token": token}


def get_report(
        api_key: str,
        access_key: str,
        timezone: str = "+8",
        start_date: str = None,
        end_date: str = None,
        time_granularity: str = "daily",
        req_type: int = 1,
        dimension_option: list = None
):
    """
    广告投放报表_进阶版
    https://adv.mintegral.com/doc/cn/guide/report/advancedPerformanceReport.html

    {'code': 201, 'msg': 'Successful reception'}
    200 => 生成数据完成，可使用 type=2 获取数据。
    201 => 接收请求成功，等待生成数据。
    202 => 数据正在生成中。
    10000 => 参数错误或权限缺失。

    :param api_key:
    :param access_key:
    :param timezone: 时区
    :param start_date: 开始日期
    :param end_date: 结束日期
    :param time_granularity:
    :return:
    """
    url = "https://ss-api.mintegral.com/api/v2/reports/data"
    token_info = make_token(api_key=api_key)
    params = {"access-key": access_key}
    params.update(token_info)

    if timezone:
        params["timezone"] = timezone
    if not start_date:
        start_date = lazytime.get_date_string(days=-1)
    if not end_date:
        end_date = lazytime.get_date_string(days=0)
    params["start_time"] = start_date
    params["end_time"] = end_date
    params["time_granularity"] = time_granularity
    params["type"] = req_type
    if not dimension_option:
        params["dimension_option"] = "Offer"
    else:
        params["dimension_option"] = ",".join(dimension_option)
    if req_type == 1:
        return lazyrequests.lazy_requests(
            method="GET",
            url=url,
            params=params
        )
    elif req_type == 2:
        return lazyrequests.lazy_requests(
            method="GET",
            url=url,
            params=params,
            return_json=False
        )


def get_report_until_success(
        api_key: str,
        access_key: str,
        timezone: str = "+0",
        start_date: str = None,
        end_date: str = None,
        time_granularity: str = "daily",
        dimension_option: list = None
):
    """
        {'code': 201, 'msg': 'Successful reception'}
        200 => 生成数据完成，可使用 type=2 获取数据。
        201 => 接收请求成功，等待生成数据。
        202 => 数据正在生成中。
        10000 => 参数错误或权限缺失。
    """
    req_type = 1
    while True:
        res = get_report(
            api_key=api_key,
            access_key=access_key,
            req_type=req_type,
            dimension_option=dimension_option,
            start_date=start_date,
            end_date=end_date,
            time_granularity=time_granularity,
            timezone=timezone
        )
        if res["code"] == 201:
            showlog.info("接收请求成功，等待生成数据。")
            lazytime.count_down(5)
        elif res["code"] == 202:
            showlog.info("数据正在生成中。")
            lazytime.count_down(5)
        elif res["code"] == 200:
            showlog.info("生成数据完成，可使用 type=2 获取数据。")
            req_type = 2
            res = get_report(
                api_key=api_key,
                access_key=access_key,
                req_type=req_type,
                dimension_option=dimension_option,
                start_date=start_date,
                end_date=end_date,
                time_granularity=time_granularity,
                timezone=timezone
            )
            return convert_format(res.text)
        elif res["code"] == 10000:
            showlog.warning(res)
            return


def get_app_name(
        package_name: str,
        api_key: str,
        access_key: str
):
    """
    通过包名获取对应的 APP 名称
    https://adv.mintegral.com/doc/cn/guide/report/acquiringAppName.html
    :param api_key:
    :param access_key:
    :param package_name: 包名
    :return:
    """
    url = "https://ss-api.mintegral.com/api/open/v1/target-apps/app-name"
    token_info = make_token(api_key=api_key)
    params = {"access-key": access_key}
    params.update(token_info)

    params["package_name"] = package_name

    return lazyrequests.lazy_requests(
            method="POST",
            url=url,
            params=params,
            data={"package_name": package_name}
        )


def update_traffic(
        api_key: str,
        access_key: str,
        offer_id: int,
        option: str,
        mtg_ids: list = None,
):
    """
    更新流量投放状态;
    广告单元里需要优化的流量 mtgid。如果 mtgid 传空，则清空黑白名单。多个用,号分隔，最多 3000 个。
    https://adv.mintegral.com/doc/cn/guide/offer/updateTraffic.html
    :param api_key:
    :param access_key:
    :param offer_id: 广告单元 ID
    :param option:
        ENABLE:表示将某个 mtgid 添加进白名单或者将某个 mtgid 从黑名单剔除
        DISABLE:表示将某个 mtgid 添加进黑名单或者将某个 mtgid 从白名单剔除。
        ALLOW_ALL:表示恢复所有 App 的投放状态，取消黑白名单的设置。
    :param mtg_ids: 广告单元里需要优化的流量 mtgid。仅option 传 "ALLOW_ALL" 时，mtgid 可传空，如果 mtgid 传空，则清空黑白名单。多个用,号分隔，最多 3000 个。
注： 该接口采取全量更新方式，请提交完整的黑白名单设置。
    :return:
    """
    url = "https://ss-api.mintegral.com/api/open/v1/offer/target"
    token_info = make_token(api_key=api_key)
    params = {"access-key": access_key}
    params.update(token_info)
    mtg_ids_new = set(mtg_ids)  # 去重复
    mtgid = ",".join(mtg_ids_new)
    return lazyrequests.lazy_requests(
            method="PUT",
            url=url,
            params=params,
            data={
                "offer_id": offer_id,
                "option": option,
                "mtgid":  mtgid
            }
        )


def get_offer(
        api_key: str,
        access_key: str,
        page: int = 1,
        limit: int = 10,
        campaign_id: str = None,
        offer_id: str = None,
        package_name: str = None,
        ext_fields: list = None
):
    """
    获取广告单元列表
    https://adv.mintegral.com/doc/cn/guide/offer/getOffer.html
    :param api_key:
    :param access_key:
    :param page: 页数
    :param limit: 每页数量，最大值：50；大于 50 时，接口只返回 50 个
    :param campaign_id: 广告 ID，多个用,隔开
    :param offer_id: 广告单元 ID，多个用,隔开
    :param package_name: 包名，支持模糊查询
    :param ext_fields: 扩展查询,target_app:该字段用于屏蔽或者定向具体的应用
    :return:
    """
    url = "https://ss-api.mintegral.com/api/open/v1/offers"
    token_info = make_token(api_key=api_key)
    params = {"access-key": access_key}
    params.update(token_info)

    if page:
        params["page"] = page
    if limit:
        params["limit"] = limit
    if campaign_id:
        params["campaign_id"] = campaign_id
    if offer_id:
        params["offer_id"] = offer_id
    if package_name:
        params["package_name"] = package_name
    if ext_fields:
        params["ext_fields"] = ",".join(ext_fields)

    return lazyrequests.lazy_requests(
        method="GET",
        url=url,
        params=params
    )


def get_offer_all(
        api_key: str,
        access_key: str
):
    """
    获取广告单元列表
    :param api_key:
    :param access_key:
    :return:
    """
    page = 1
    limit = 10
    offers = list()
    while True:
        showlog.info(f"正在获取第 {page} 页的数据...")
        temp_res = get_offer(
            page=page,
            limit=limit,
            api_key=api_key,
            access_key=access_key
        )
        if temp_res["code"] == 200:
            data = temp_res["data"]
            if not data:
                break
            else:
                data_list = data["list"]
                if data_list:
                    offers.extend(data_list)
                    page += 1
                    continue
                else:
                    break
        else:
            showlog.warning(temp_res)
            break
    return offers


def update_budget(
        api_key: str,
        access_key: str,
        offer_id: int,
        option: str,
        mtg_ids: list = None,
):
    """
    更新预算
    广告单元里需要优化的流量 mtgid。如果 mtgid 传空，则清空黑白名单。多个用,号分隔，最多 3000 个。
    https://adv.mintegral.com/doc/cn/guide/offer/updateBudget.html
    :param api_key:
    :param access_key:
    :param offer_id: 广告单元 ID
    :param option:
        ENABLE:表示将某个 mtgid 添加进白名单或者将某个 mtgid 从黑名单剔除
        DISABLE:表示将某个 mtgid 添加进黑名单或者将某个 mtgid 从白名单剔除。
        ALLOW_ALL:表示恢复所有 App 的投放状态，取消黑白名单的设置。
    :param mtg_ids: 广告单元里需要优化的流量 mtgid。仅option 传 "ALLOW_ALL" 时，mtgid 可传空，如果 mtgid 传空，则清空黑白名单。多个用,号分隔，最多 3000 个。
注： 该接口采取全量更新方式，请提交完整的黑白名单设置。
    :return:
    """
    url = "https://ss-api.mintegral.com/api/open/v1/offer/budget"
    token_info = make_token(api_key=api_key)
    params = {"access-key": access_key}
    params.update(token_info)

    mtgid = ",".join(mtg_ids)
    return lazyrequests.lazy_requests(
            method="PUT",
            url=url,
            params=params,
            data={
                "offer_id": offer_id,
                "option": option,
                "mtgid":  mtgid
            }
        )


def get_campaign(
        api_key: str,
        access_key: str,
        page: int = 1,
        limit: int = 50
):
    """
    获取广告
    https://adv.mintegral.com/doc/cn/guide/campaign/getCampaign.html
    :param api_key:
    :param access_key:
    :param page:
    :param limit:
    :return:
    """
    url = "https://ss-api.mintegral.com/api/open/v1/campaign"
    token_info = make_token(api_key=api_key)
    params = {"access-key": access_key}
    params.update(token_info)
    params["page"] = page
    params["limit"] = limit
    return lazyrequests.lazy_requests(
            method="GET",
            url=url,
            params=params
        )


def get_account_balance(
        api_key: str,
        access_key: str,
):
    """
    获取账户余额（含有账户id信息）
    https://adv.mintegral.com/doc/cn/guide/account/getAccountBalance.html
    :param api_key:
    :param access_key:
    :return:
    """
    token_info = make_token(api_key=api_key)
    params = {"access-key": access_key}
    params.update(token_info)
    url = "https://ss-api.mintegral.com/api/open/v1/account/balance"
    return lazyrequests.lazy_requests(
        method="GET",
        url=url,
        params=params
    )

