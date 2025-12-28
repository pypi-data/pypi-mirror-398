import logging

import requests

from flagdataset.baai_config import Application, config_update


logger = logging.getLogger(__name__)


def auth_user_login(ak, sk):
    """auth_user_login
    api = "http://120.92.19.30:30880/userAccessKey/v1/getAccessToken"
    """

    conf = Application()
    resp = requests.post(conf.auth_login_api, headers=conf.req_header, json={"ak": ak, "sk": sk})
    if resp.status_code != 200:
        logger.error(f"status: {resp.status_code} {conf.auth_login_api}")

    assert resp.status_code == 200, f"status: {resp.status_code}"
    assert resp.json().get("code") == 0, resp.text

    config_update({"ak": ak, "sk": sk})
    print("登录成功")
    conf._login_token = resp.json().get("data").get("token")
