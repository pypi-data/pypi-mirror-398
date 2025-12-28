from .. import baai_config
from ..baai_config import config_update

def run_update(cmd_args):


    for_update = {}

    if hasattr(cmd_args, 'host') and cmd_args.host:
        for_update.setdefault(baai_config.FLAG_DATASET_HOST, cmd_args.host)

    # 同时下载文件数量
    if hasattr(cmd_args, 'workers_down') and cmd_args.workers_down:
        for_update.setdefault(baai_config.FLAG_DATASET_EXECUTOR_WORKER_SIZE, cmd_args.workers_down)

    # 下载器工作线程数
    if hasattr(cmd_args, 'jobs_down') and cmd_args.jobs_down:
        for_update.setdefault(baai_config.FLAG_DATASET_EXECUTOR_DOWN_SIZE, cmd_args.jobs_down)

    # 合并线程数
    if hasattr(cmd_args, 'merges_down') and cmd_args.merges_down:
        for_update.setdefault(baai_config.FLAG_DATASET_EXECUTOR_MERGE_SIZE, cmd_args.merges_down)

    # 签名接口
    if hasattr(cmd_args, 'sign_download_api') and  cmd_args.sign_download_api:
        for_update.setdefault(baai_config.FLAG_DATASET_DEFAULT_SING_DOWNLOAD_API, cmd_args.sign_download_api)

    # 元数据接口
    if hasattr(cmd_args, 'meta_download_api') and cmd_args.meta_download_api:
        for_update.setdefault(baai_config.FLAG_DATASET_DEFAULT_META_DOWNLOAD_API, cmd_args.meta_download_api)

    # 登录接口
    if hasattr(cmd_args, 'auth_login_api') and cmd_args.auth_login_api:
        for_update.setdefault(baai_config.FLAG_DATASET_DEFAULT_AUTH_LOGIN_API, cmd_args.auth_login_api)


    # 更新参数
    config_update(for_update)
