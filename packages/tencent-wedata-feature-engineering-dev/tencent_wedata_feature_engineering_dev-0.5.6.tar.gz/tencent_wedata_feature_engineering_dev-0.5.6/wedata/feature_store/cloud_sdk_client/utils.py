import os
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.profile.client_profile import ClientProfile


def get_client_profile() -> 'ClientProfile':
    """
    获取网络客户端配置
    """
    http_profile = HttpProfile()
    http_profile.protocol = "https"
    endpoint = os.getenv("TENCENT_CLOUD_SDK_ENDPOINT")
    if endpoint:
        http_profile.endpoint = endpoint
    else:
        http_profile.endpoint = "wedata.internal.tencentcloudapi.com"

    client_profile = ClientProfile()
    client_profile.httpProfile = http_profile
    return client_profile


def set_request_header(headers):
    """
    设置请求头
    """
    if headers is None:
        headers = {}
    if os.environ.get("IS_WEDATA_TEST"):
        headers["X-Qcloud-User-Id"] = os.environ.get("TEST_USER_ID")
    return headers


def is_mock() -> bool:
    """
    是否为模拟环境
    """
    return os.getenv("IS_MOCK_API") == "true"


def is_warning() -> bool:
    """
    是否展示警告环境
    """
    return os.getenv("IS_CLOUD_API_WARNING") == "true"

