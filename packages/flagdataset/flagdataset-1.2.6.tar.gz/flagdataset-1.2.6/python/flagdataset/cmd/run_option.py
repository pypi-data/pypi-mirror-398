import os
import pathlib
import argparse
import traceback

from ..baai_config import config_read

from ..helper.baai_update import run_update
from ..helper.baai_print import print_figlet
from ..baai_config import print_config, HOME
from ..helper.baai_logger import logger_init


def runcmd_option():
    from . import argument
    from ..baai_environment import setup_network

    print_figlet()

    root_parser = argparse.ArgumentParser(add_help=False)
    root_parser.add_argument('-t', '--save-path', type=str, default=".", help='保存路径(默认当前文件夹)')
    root_parser.add_argument('-j', '--jobs-down', type=int, default=os.cpu_count()*2+1, help='jobs')
    root_parser.add_argument('-b', '--bandwidth', type=int, default=100, help='带宽')
    root_parser.add_argument("--proxy", type=str, help='代理')

    argument.setup_parser(root_parser)


    # flagdataset
    parser = argparse.ArgumentParser(prog='flagdataset', description="flagdataset 命令行工具: bf")
    subparsers = parser.add_subparsers(dest='command')


    auth_parser = subparsers.add_parser('auth', help='认证相关命令')
    auth_subparsers = auth_parser.add_subparsers(dest='auth_command')

    # auth login 子命令
    login_parser = auth_subparsers.add_parser('login', help='登录数据平台')
    login_parser.set_defaults(func=auth_login)

    # down
    down_parser = subparsers.add_parser('download', help='下载数据', parents=[root_parser])
    down_parser.add_argument('-d', '--dataset', type=str, help='数据集ID')
    down_parser.add_argument('-p', '--prefix', type=str, help='指定目录')
    down_parser.add_argument('-k', '--key', type=str, help='指定文件')
    down_parser.set_defaults(func=download)

    # meta
    meta_parser = subparsers.add_parser('meta', help='下载meta信息')
    meta_subparsers = meta_parser.add_subparsers(dest='meta_cmd')

    meta_down_parser = meta_subparsers.add_parser('down', help='下载数据集描述信息', parents=[root_parser])
    meta_down_parser.add_argument('--dataset', type=str, help='下载的数据集')
    meta_down_parser.add_argument('-p', '--prefix', type=str, default="",  help='指定下载目录')
    meta_down_parser.set_defaults(func=meta_down)

    meta_desc_parse = meta_subparsers.add_parser('desc', help='查看数据集描述信息', parents=[root_parser])
    meta_desc_parse.set_defaults(func=meta_desc)

    meta_list_parse = meta_subparsers.add_parser('list', help='查看数据集列表', parents=[root_parser])
    meta_list_parse.add_argument('--grep', type=str, default="*", help='grep')
    meta_list_parse.add_argument('--line', type=int, default=100, help='line')
    meta_list_parse.set_defaults(func=meta_list_grep)


    # 解析命令行参数
    cmd_args = parser.parse_args()

    # 设置网络
    setup_network(cmd_args)
    run_update(cmd_args)

    # logger
    if hasattr(cmd_args, 'save_path'):
        logger_init(pathlib.Path(cmd_args.save_path)/"log")
    else:
        home_loggr = pathlib.Path(HOME) / "logs"
        home_loggr.mkdir(parents=True, exist_ok=True)
        logger_init(home_loggr)

    if hasattr(cmd_args, 'func'):
        try:
            cmd_args.func(cmd_args)
        except Exception: # noqa
            pass
        except KeyboardInterrupt:
            print()
            pass
    else:
        parser.print_help()


def auth_login(cmd_args):
    from ..helper.baai_login import auth_user_login

    config_default = config_read()

    ak = input(f"请输入ak[{config_default.get('ak', '-')}]: ") or config_default.get("ak")
    sk = input(f"请输入sk[{config_default.get('sk', '-')}]: ") or config_default.get("sk")

    try:
        resp_data = auth_user_login(ak, sk)
    except AssertionError as e:
        print(e)


def meta_down(cmd_args):
    try:
        from ..baai_meta import meta_download

        meta_download(cmd_args)
    except Exception as e:
        print(e)
        if not cmd_args.debug:
            return
        traceback.print_exc()


def meta_desc(cmd_args):
    from ..baai_meta import meta_descript

    print_config()
    meta_descript(cmd_args)


def meta_list_grep(cmd_args):
    from ..baai_meta import meta_list

    print_config()

    meta_list(cmd_args)


def download(cmd_args):
    from ..helper.baai_dataset import logger_download


    filter_args = cmd_args.prefix
    if not filter_args:
        filter_args = cmd_args.key
    if not filter_args:
        filter_args = "*"


    logger_download(cmd_args.dataset, 0, filter_args)
    if cmd_args.runtime == "rust":
        _download_with_ihttpd_runtime(cmd_args)
    else:
        _download_with_ks3util_runtime(cmd_args)

    logger_download(cmd_args.dataset, 1, filter_args)


def _download_with_ihttpd_runtime(cmd_args):
    try:
        try:
            from ihttpd import read # noqa
        except ImportError:
            print("请安装运行环境: pip install -U ihttpd")
            return

        from ..helper.baai_read import read_base_meta, read_local_meta
        from ..helper.baai_dataset import save_remote_meta, read_remote_meta

        from ..baai_meta import meta_download
        from ..baai_config import Application


        config = Application()

        use_path = pathlib.Path(".").absolute().__str__()
        presign = "http://internal-data.baai.ac.cn/api/v1/storage/sign/download/presign"
        network = config.network

        print("target: ", use_path)

        # 异步下载
        jobs_down = cmd_args.jobs_down
        read.multi_download(use_path, presign, network, cmd_args.bandwidth, jobs_down)

        save_path = cmd_args.save_path
        meta_path = pathlib.Path(save_path) / "meta"

        post_api = config.meta_download_api % "meta-down"
        offset, limit = 0, 10000

        try:
            read.push("---start---")
            while True:
                meta_name = f"{cmd_args.dataset}_{offset}.bin"
                next_name = f"{cmd_args.dataset}_{offset + limit}.bin"
                meta_part_path = meta_path / meta_name
                meta_next_path = meta_path / next_name

                if meta_next_path.exists():
                    offset = offset + limit
                    read.push(meta_name)
                    continue

                try:
                    req_data = {"dataset_id": cmd_args.dataset, "prefix": cmd_args.prefix}
                    resp_meta_ = read_remote_meta(f"{post_api}?offset={offset}&limit={limit}", json=req_data)
                except AssertionError as e:
                    print(e)
                    break
                else:
                    meta_data_part = resp_meta_.get("data").get("download_set")
                    if len(meta_data_part) != 0:
                        save_remote_meta(meta_part_path, meta_data_part)
                        read.push(meta_name)

                    if resp_meta_.get("data").get("search_count") == 0:
                        break
                    offset = offset + limit

        except Exception as e:
            print(e)
        finally:
            read.push("---end---")
        read.wait()

    except Exception as e:
        print(e)
        if not cmd_args.debug:
            return
        traceback.print_exc()


def _download_with_ks3util_runtime(cmd_args):
    from ..baai_config import Application

    config = Application()

    save_path = pathlib.Path(cmd_args.save_path)
    print(f"""data_path: {(save_path.absolute() / "data").__str__()}""")

    proxy = cmd_args.proxy
    if not proxy:
        proxy = None

    try:
        from flagdataset.core.baai_share_url import download_share

        save_path = save_path.__str__()
        dataset = cmd_args.dataset
        prefix = cmd_args.prefix
        key = cmd_args.key
        jobs_down = cmd_args.jobs_down
        debug = cmd_args.debug

        download_share(
            dataset,
            save_path,
            prefix,
            key,
            network=config.network,
            jobs_down=jobs_down,
            debug=debug,
            proxy=proxy
        )

    except Exception as e:
        print(e)
