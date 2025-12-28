import logging
import pathlib

import csv


from flagdataset.baai_config import Application, Progress
from flagdataset.helper import baai_requests as requests


logger = logging.getLogger(__name__)

application = Application()
progress = Progress()


# --------- remote meta -----------
def read_remote_meta(request_api, json=None, **kwargs): # noqa
    config = Application()

    user_login_token = config.try_login()
    req_headers = {
        "Authorization": f"Bearer {user_login_token}",
    }
    req_headers.update(config.req_header)

    try:
        resp = requests.post(request_api, json=json, headers=req_headers)
        if resp.status_code == 401:
            raise AssertionError("请重新登录")
        assert resp.status_code == 200, f"status_code: {resp.status_code}"
        assert resp.json().get("code") == 0, resp.json().get("message")
        data_meta = resp.json()
        return data_meta
    except AssertionError as e:
        logger.info(f"read_remote_meta, {request_api}, {e}")
        raise AssertionError(f"{e}")


def save_remote_meta(meta_path: pathlib.Path, meta_data):
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    with meta_path.open("w", newline='') as fwriter:  # 添加newline参数
        fieldnames = ["download_sign", "download_size", "download_extn"]
        csv_writer = csv.DictWriter(fwriter, fieldnames=fieldnames)
        csv_writer.writeheader()
        for row in meta_data:
            row_write = {}
            for field in fieldnames:
                row_v = row.get(field, "")
                if not row_v:
                    if field == "download_size":
                        row_v = 0
                    logger.error(f"save_meta: {field} is empty, {row}")

                row_write[field] = row_v
            csv_writer.writerow(row_write)


# --------- auth login -----------
def executor_user_signin():
    config = Application()

    resp = requests.post(config.auth_login_api, headers=config.req_header, json={"ak": config.ak, "sk": config.sk})
    assert resp.status_code == 200, resp.status_code
    assert resp.json().get("code") == 0, resp.text
    config.set_init_token(resp.json().get("data").get("token"))


# --------- logger_download -----------
def logger_download(dataset_id: str, status: int=1, search: str="/"):
    config = Application()

    user_login_token = config.try_login()
    req_headers = {
        "Authorization": f"Bearer {user_login_token}",
    }
    req_headers.update(config.req_header)
    data = {"datasetId": dataset_id, "status": status, "filePath": search or "/"}
    try:
        resp = requests.post(config.log_download_api, headers=req_headers, json=data, timeout=2)
    except Exception as e:
        print(e)
        logger.error(f"logger_download,  {e}")
    else:
        logger.info(f"logger_download, {resp.status_code}, {resp.text}")
