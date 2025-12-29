from lazysdk import lazyrequests


def postback(
        callback: str,
        event_time: int,
        event_type: int,
        purchase_amount=None
):
    """
    快手回传
    :param callback:
    :param event_time: 时间戳，单位秒
    :param event_type:
    :param purchase_amount:
    :return:
    """
    # result=1上报成功
    params = {
        "event_type": event_type,
        "event_time": event_time,
    }
    if purchase_amount:
        params["purchase_amount"] = purchase_amount
    res = lazyrequests.lazy_requests(
        method="GET",
        url=callback,
        params=params
    )
    return res

