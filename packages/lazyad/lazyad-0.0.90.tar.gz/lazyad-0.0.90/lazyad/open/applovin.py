from lazysdk import lazyrequests


def campaigns(token: str):
    """
    获取所有的campaign
    """
    url = "https://o.applovin.com/campaign_management/v1/campaigns"
    return lazyrequests.lazy_requests(
        method="GET",
        url=url,
        headers={"Authorization": token},
        timeout=60
    )


def campaign_targets(
        token: str,
        campaign_id: str
):
    """
    获取所有的campaign的目标信息
    """
    url = f"https://o.applovin.com/campaign_management/v1/campaign_targets/{campaign_id}"
    return lazyrequests.lazy_requests(
        method="GET",
        url=url,
        headers={"Authorization": token},
        timeout=60
    )

