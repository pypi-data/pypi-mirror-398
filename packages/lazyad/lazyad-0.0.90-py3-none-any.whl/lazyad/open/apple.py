from lazysdk import lazyrequests
import showlog


def lookup(
        _id: int = None,
        track_id: int = None,
        bundle_id: str = None,
        country: str = None,
        timeout: int = 5
):
    """
    获取app信息/开发者信息
    :param _id: app id/开发者id
    :param track_id:
    :param bundle_id:
    :param country:
    :param timeout:
    :return:
    """
    params = dict()
    url = "https://itunes.apple.com/lookup"
    if country:
        params['country'] = country

    if _id is not None:
        params["id"] = _id
    if track_id is not None:
        params["id"] = track_id
        # url = f"https://itunes.apple.com/lookup?id={track_id}"
    if bundle_id is not None:
        params["bundleId"] = bundle_id
        # url = f"https://itunes.apple.com/lookup?bundleId={bundle_id}"
    return lazyrequests.lazy_requests(
        method="GET",
        url=url,
        params=params,
        timeout=timeout
    )


def lookup_auto(
        input_str: str
):
    """
    输入待查询的字符串，自动处理查询结果
    :param input_str:
    :return:
    """
    bundle_id = None
    track_id = None
    if input_str.startswith("id") and input_str[2:].isdigit():
        # 以id开头，后续为数字的格式，判断为track_id
        showlog.info(f"输入 [{input_str}] 类型为 [id+track_id]")
        track_id = input_str[2:]
    elif input_str.startswith("tempBundleId"):
        showlog.info(f"输入 [{input_str}] 类型为 [tempBundleId]")
        bundle_id = input_str
    elif input_str.isdigit():  # 全部为数字
        showlog.info(f"输入 [{input_str}] 类型为 [track_id]")
        track_id = input_str
    else:
        showlog.info(f"输入 [{input_str}] 类型为 [bundle_id]")
        bundle_id = input_str

    if track_id:
        if isinstance(track_id, str):
            return {"track_id": track_id, "lookup_res": lookup(track_id=int(track_id))}
        elif isinstance(track_id, int):
            return {"track_id": track_id, "lookup_res": lookup(track_id=track_id)}
        else:
            return None
    elif bundle_id:
        return {"bundle_id": bundle_id, "lookup_res": lookup(bundle_id=bundle_id)}
    else:
        return None
