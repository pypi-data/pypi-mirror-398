from lazysdk import lazyrequests
from lazysdk import lazybase64
from lazysdk import lazytime


def make_auth(
        keyid,
        secret_key
):
    """
    生成校验字符串
    :param keyid:
    :param secret_key:
    :return:
    """
    authorization = f"{keyid}:{secret_key}"
    return f"Basic {lazybase64.lazy_b64encode(authorization)}"


def apps(
        organization_id,
        keyid,
        secret_key,
        timeout: int = 10
):
    """
    获取app列表
    https://services.docs.unity.com/advertise/v1/index.html#section/Get-Started/First-Call:-List-Apps
    :param organization_id:
    :param keyid:
    :param secret_key:
    :param timeout:
    :return:
    """
    url = f"https://services.api.unity.com/advertise/v1/organizations/{organization_id}/apps"
    headers = {"Authorization": make_auth(keyid=keyid, secret_key=secret_key)}
    return lazyrequests.lazy_requests(
        method="GET",
        url=url,
        headers=headers,
        timeout=timeout,
    )


def list_campaigns(
        organization_id,
        app_id,
        keyid,
        secret_key,
        timeout: int = 10
):
    """
    获取Campaigns列表
    https://services.docs.unity.com/advertise/v1/index.html#tag/Campaigns
    :param organization_id:
    :param app_id:
    :param keyid:
    :param secret_key:
    :return:
    """
    url = f"https://services.api.unity.com/advertise/v1/organizations/{organization_id}/apps/{app_id}/campaigns"
    headers = {"Authorization": make_auth(keyid=keyid, secret_key=secret_key)}
    return lazyrequests.lazy_requests(
        method="GET",
        url=url,
        headers=headers,
        timeout=timeout,
    )


def get_campaign(
        organization_id,
        app_id,
        campaign_id,
        keyid,
        secret_key,
        include_fields: list = None,
        timeout: int = 10
):
    """
    获取Campaign信息
    https://services.docs.unity.com/advertise/v1/index.html#tag/Campaigns/operation/advertise_getCampaign
    :param organization_id:
    :param app_id:
    :param campaign_id:
    :param keyid:
    :param secret_key:
    :param include_fields: ["cpiBids", "sourceBids", "roasBids", "retentionBids", "eventOptimizationBids", "budget"]
    :return:
    """
    default_include_fields = ["cpiBids", "sourceBids", "roasBids", "retentionBids", "eventOptimizationBids", "budget"]
    url = f"https://services.api.unity.com/advertise/v1/organizations/{organization_id}/apps/{app_id}/campaigns/{campaign_id}"
    headers = {"Authorization": make_auth(keyid=keyid, secret_key=secret_key)}
    if include_fields:
        pass
    else:
        include_fields = default_include_fields
    params_list = list()
    for each in include_fields:
        params_list.append(f"includeFields={each}")
    params_str = "&".join(params_list)
    return lazyrequests.lazy_requests(
        method="GET",
        url=f"{url}?{params_str}",
        headers=headers,
        timeout=timeout,
    )


def get_budget(
        organization_id,
        app_id,
        campaign_id,
        keyid,
        secret_key,
        timeout: int = 10
):
    """
    获取 Campaign budget
    https://services.docs.unity.com/advertise/v1/index.html#tag/Campaigns/operation/advertise_getCampaignBudget
    :param organization_id:
    :param app_id:
    :param campaign_id:
    :param keyid:
    :param secret_key:
    :return:
    """
    url = f"https://services.api.unity.com/advertise/v1/organizations/{organization_id}/apps/{app_id}/campaigns/{campaign_id}/budget"
    headers = {"Authorization": make_auth(keyid=keyid, secret_key=secret_key)}
    return lazyrequests.lazy_requests(
        method="GET",
        url=url,
        headers=headers,
        timeout=timeout,
    )


def get_targeting_options(
        organization_id,
        app_id,
        campaign_id,
        keyid,
        secret_key,
        timeout: int = 10
):
    """
    Get targeting options
    https://services.docs.unity.com/advertise/v1/index.html#tag/Campaigns/operation/advertise_getTargeting
    :param organization_id:
    :param app_id:
    :param campaign_id:
    :param keyid:
    :param secret_key:
    :return:
    """
    url = f"https://services.api.unity.com/advertise/v1/organizations/{organization_id}/apps/{app_id}/campaigns/{campaign_id}/targeting"
    headers = {"Authorization": make_auth(keyid=keyid, secret_key=secret_key)}
    return lazyrequests.lazy_requests(
        method="GET",
        url=url,
        headers=headers,
        timeout=timeout,
    )


def update_targeting_options(
        organization_id,
        app_id,
        campaign_id,
        keyid,
        secret_key,
        allow_list: list = None,
        block_list: list = None,
        iso_os_min: str = None,
        timeout: int = 10
):
    """
    Update targeting options
    https://services.docs.unity.com/advertise/v1/index.html#tag/Campaigns/operation/advertise_updateTargeting
    :param organization_id:
    :param app_id:
    :param campaign_id:
    :param keyid:
    :param secret_key:

    :param allow_list:
    :param block_list:
    :param iso_os_min:
    :return:
    """
    url = f"https://services.api.unity.com/advertise/v1/organizations/{organization_id}/apps/{app_id}/campaigns/{campaign_id}/targeting"
    headers = {"Authorization": make_auth(keyid=keyid, secret_key=secret_key)}
    data = {}
    if allow_list or block_list:
        data["appTargeting"] = {}
        if allow_list:
            data["appTargeting"]["allowList"] = allow_list
        if block_list:  # 黑名单
            data["appTargeting"]["blockList"] = block_list
    if iso_os_min:
        data["deviceTargeting"] = {}
        if iso_os_min:
            data["deviceTargeting"]["osMin"] = iso_os_min
    return lazyrequests.lazy_requests(
        method="PATCH",
        url=url,
        headers=headers,
        json=data,
        timeout=timeout,
    )


def reports(
        organization_id,
        keyid,
        secret_key,
        start: str,
        end: str,
        scale: str = "day",
        metrics: list = None,
        breakdowns: list = None,
        timeout: int = 60
):
    """
    https://services.docs.unity.com/statistics/index.html#tag/Acquisitions/operation/stats_acquisition
    :param metrics:
        starts
        views
        clicks
        installs
        spend
        cpi
        ctr
        cvr
        ecpm
        d0AdRevenue
        d1AdRevenue
        d3AdRevenue
        d7AdRevenue
        d14AdRevenue
        d0AdRevenueRoas
        d1AdRevenueRoas
        d3AdRevenueRoas
        d7AdRevenueRoas
        d14AdRevenueRoas
        d0IapRevenue
        d1IapRevenue
        d3IapRevenue
        d7IapRevenue
        d14IapRevenue
        d0IapRoas
        d1IapRoas
        d3IapRoas
        d7IapRoas
        d14IapRoas
        d0Purchases
        d1Purchases
        d3Purchases
        d7Purchases
        d14Purchases
        d0UniquePurchasers
        d1UniquePurchasers
        d3UniquePurchasers
        d7UniquePurchasers
        d14UniquePurchasers
        d0Retained
        d1Retained
        d3Retained
        d7Retained
        d14Retained
        d0RetentionRate
        d1RetentionRate
        d3RetentionRate
        d7RetentionRate
        d14RetentionRate
        d0TotalRoas
        d1TotalRoas
        d3TotalRoas
        d7TotalRoas
        d14TotalRoas
        d0LevelComplete
        d1LevelComplete
        d3LevelComplete
        d7LevelComplete
        d14LevelComplete
        d0CostPerLevelComplete
        d1CostPerLevelComplete
        d3CostPerLevelComplete
        d7CostPerLevelComplete
        d14CostPerLevelComplete
        d0LevelCompleteRate
        d1LevelCompleteRate
        d3LevelCompleteRate
        d7LevelCompleteRate
        d14LevelCompleteRate
    :param breakdowns:
        app,
        campaign,
        country,
        creativePack,
        creativePackType,
        osVersion,
        platform,
        sourceAppId,
        store,
        targetGame,
        eventType,
        eventName
    :return:
    """
    authorization = f"Basic {keyid}:{secret_key}"
    url = f"https://services.api.unity.com/advertise/stats/v2/organizations/{organization_id}/reports/acquisitions"
    params = {
        "scale": scale,  # "summary" "hour" "day" "week" "month"
        "format": "json"
    }

    if not metrics:
        metrics = [
            "spend"
        ]
    if not breakdowns:
        breakdowns = [
            "country"
        ]

    params["breakdowns"] = ",".join(breakdowns)
    params["metrics"] = ",".join(metrics)
    params["start"] = start
    params["end"] = end

    headers = {"Authorization": authorization}
    return lazyrequests.lazy_requests(
        method="GET",
        url=url,
        params=params,
        headers=headers,
        return_json=False,
        timeout=timeout
    )
