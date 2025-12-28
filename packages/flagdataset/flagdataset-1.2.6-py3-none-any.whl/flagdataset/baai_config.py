import time
import datetime
import os
import pathlib
import threading
import json

import jwt

from .helper import baai_requests as requests


HOME = pathlib.Path(os.path.expanduser("~")) / ".sdk_download"
HOME_CONFIG = HOME / "config.json"
HOME_CONFIG.parent.mkdir(parents=True, exist_ok=True)

REQUEST_HEADER = {
    "Accept-Language": "zh-CN",
    "Content-Type": "application/json",
}

# config attr
FLAG_DATASET_HOST = "host"
FLAG_DATASET_NETWORK = "network" # 网络
FLAG_DATASET_BANDWITH = "bandwith" # 带宽 TODO: 暂时未启用

FLAG_DATASET_AUTH_LOGIN_API = "auth_login_api"
FLAG_DATASET_SING_DOWNLOAD_API = "sign_download_api" # 文件签名
FLAG_DATASET_META_DOWNLOAD_API = "meta_download_api" # 文件meta信息
FLAG_DATASET_LOG_DOWNLOAD_API = "log_download_api" # 下载日志

# executor_worker_size
FLAG_DATASET_EXECUTOR_WORKER_SIZE = "executor_worker_size"
FLAG_DATASET_EXECUTOR_DOWN_SIZE = "executor_down_size"
FLAG_DATASET_EXECUTOR_MERGE_SIZE = "executor_merge_size"

# flag dataset default
FLAG_DATASET_DEFAULT_HOST = "http://internal-data.baai.ac.cn"
FLAG_DATASET_DEFAULT_AUTH_LOGIN_API = "api/user-srv/userAccessKey/v1/getAccessToken"
FLAG_DATASET_DEFAULT_SING_DOWNLOAD_API = "api/v5/storage-download/dataset/provider-storage/download/presign"
FLAG_DATASET_DEFAULT_META_DOWNLOAD_API = "api/v5/storage-download/dataset/provider-meta/datasets/%s"
FLAG_DATASET_DEFAULT_LOG_DOWNLOAD_API = "api/dataset/search/v5/updateDownloadNum"


class Application:
    _initialized: bool = False

    def __new__(cls, *args, **kwargs) -> "Application":
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
        return cls._instance # noqa

    def __init__(self):
        if not self._initialized:
            print(f"init Application: {datetime.datetime.now()}")
            # default
            self.root_path = HOME
            self.req_header = REQUEST_HEADER

            # env
            config_default = config_read()
            host = config_default.get(FLAG_DATASET_HOST, FLAG_DATASET_DEFAULT_HOST)

            self.req_host = host
            self.network = config_default.get(FLAG_DATASET_NETWORK)

            self.sign_download_api = config_default.get(FLAG_DATASET_SING_DOWNLOAD_API, FLAG_DATASET_DEFAULT_SING_DOWNLOAD_API)
            if not self.sign_download_api.startswith("http"):
                self.sign_download_api = f"{self.req_host}/{self.sign_download_api}"

            self.meta_download_api = config_default.get(FLAG_DATASET_META_DOWNLOAD_API, FLAG_DATASET_DEFAULT_META_DOWNLOAD_API)
            if not self.meta_download_api.startswith("http"):
                self.meta_download_api = f"{self.req_host}/{self.meta_download_api}"

            self.auth_login_api = config_default.get(FLAG_DATASET_AUTH_LOGIN_API, FLAG_DATASET_DEFAULT_AUTH_LOGIN_API)
            if not self.auth_login_api.startswith("http"):
                self.auth_login_api = f"{self.req_host}/{self.auth_login_api}"

            self.log_download_api = config_default.get(FLAG_DATASET_LOG_DOWNLOAD_API, FLAG_DATASET_DEFAULT_LOG_DOWNLOAD_API)
            if not self.log_download_api.startswith("http"):
                self.log_download_api = f"{self.req_host}/{self.log_download_api}"

            self.chunk_size = 1024 * 1024 * 5

            # login
            self._login_token = ""
            self._login_lock = threading.Lock()

            # size
            self.executor_worker_size = config_default.get(FLAG_DATASET_EXECUTOR_WORKER_SIZE, 100)
            self.executor_down_size = config_default.get(FLAG_DATASET_EXECUTOR_DOWN_SIZE, 20)
            self.executor_merge_size = config_default.get(FLAG_DATASET_EXECUTOR_MERGE_SIZE, 100)

            self.ak = config_default.get("ak")
            self.sk = config_default.get("sk")

            # initialized
            self._initialized = True

    def set_init_token(self, token):
        self._login_token = token

    def try_access_token(self):
        resp_login = requests.post(self.auth_login_api,json={"ak": self.ak, "sk": self.sk}, headers=self.req_header)
        token = resp_login.json().get("data").get("token")
        return token

    def retry_login_token(self):
        with self._login_lock:
            self._login_token = self.try_access_token()

    def try_login(self):
        if self._login_token == "":
            self.retry_login_token()
        decoded = jwt.decode(self._login_token, options={"verify_signature": False})
        exp = decoded.get("exp")
        if exp + 60 * 10 < int(time.time()):
            self.retry_login_token()
        return self._login_token

    def login_check(self) -> str:
        if self._login_token == "":
            return ""
        decoded = jwt.decode(self._login_token, options={"verify_signature": False})
        exp = decoded.get("exp")
        if exp + 60 * 10 >  int(time.time()):
            return self._login_token
        return ""


class Progress:
    _initialized: bool = False

    def __new__(cls, *args, **kwargs) -> "Application":
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
        return cls._instance # noqa

    def __init__(self):
        if not self._initialized:
            self._lock = threading.Lock()

            self.require_count = 0 # 需要下载的数量
            self.require_size = 0 # 需要下载的大小

            self.download_count = 0 # 下载数量
            self.download_size = 0 # 下载大小

            self.download_submit_count = 0 # 提交下载数量
            self.required_part_count = 0 # 分片统计数量
            self.download_part_count = 0 # 下载分片数量

            self.required_merged_count = 0
            self.download_merged_count = 0


            # 失败数量
            self.fail_count = 0

            self._initialized = True

    def add_require_count(self, count):
        with self._lock:
            self.require_count += count

    def add_require_size(self, size):
        with self._lock:
            self.require_size += size

    def add_download_count(self, count):
        with self._lock:
            self.download_count += count

    def add_download_size(self, size):
        with self._lock:
            self.download_size += size

    def add_fail_count(self, count):
        with self._lock:
            self.fail_count += count

    def add_download_submit_count(self, count):
        with self._lock:
            self.download_submit_count += count

    def add_download_part_count(self, count):
        with self._lock:
            self.download_part_count += count

    def add_required_part_count(self, count):
        with self._lock:
            self.required_part_count += count

    def add_required_merged_count(self, count):
        with self._lock:
            self.required_merged_count += count

    def add_download_merged_count(self, count):
        with self._lock:
            self.download_merged_count += count

def config_update(config_data):
    try:
        with open(HOME_CONFIG, 'r') as f:
            config_default = json.load(f)
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        config_default = {}
    config_default.update(config_data)

    try:
        with open(HOME_CONFIG, 'w') as f:
            json.dump(config_default, f, indent=4)
    except Exception as e:
        print(f"保存配置文件时出错: {e}")

def config_read():
    try:
        with open(HOME_CONFIG, 'r') as f:
            config_default = json.load(f)
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        config_default = {}
    return config_default

def print_config():
    try:
        with open(HOME_CONFIG, 'r') as f:
            config_default = json.load(f)
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        config_default = {}

    for k, v in config_default.items():
        if k in ["sk", "ak"]:
            continue
        print(f"{k}: {v}")
    print("")
