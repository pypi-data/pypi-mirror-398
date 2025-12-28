import re
import pathlib
import logging

import psutil


from .baai_config import Application
from .helper.baai_dataset import save_remote_meta, read_remote_meta
from .helper.baai_read import read_base_meta, read_local_meta


logger = logging.getLogger(__name__)


def meta_download(cmd_args, cb=None):

    save_path = cmd_args.save_path
    meta_path = pathlib.Path(save_path) / "meta"

    config = Application()
    post_api = config.meta_download_api % cmd_args.dataset
    print(post_api)

    post_api = config.meta_download_api % "meta-down"
    offset, limit = 0, 10000


    while True:
        meta_part_path = meta_path / f"{cmd_args.dataset}_{offset}.bin"

        try:
            req_data = {"dataset_id": cmd_args.dataset, "prefix": cmd_args.prefix}
            resp_meta_ = read_remote_meta(f"{post_api}?offset={offset}&limit={limit}", json=req_data)
        except AssertionError as e:
            logger.error(e)
            break
        else:
            meta_data_part= resp_meta_.get("data").get("download_set")
            if len(meta_data_part) != 0:
                save_remote_meta(meta_part_path, meta_data_part)

                if cb:
                    cb(f"{cmd_args.dataset}_{offset}.bin")

            if resp_meta_.get("data").get("search_count") == 0:
                break
            offset = offset + limit



def meta_list(cmd_args):
    save_path = cmd_args.save_path
    meta_path = pathlib.Path(save_path) / "meta"

    grep = cmd_args.grep.replace("*", ".*").strip()
    re_grep = re.compile(rf"{grep}")

    list_bin = meta_path.glob("*.bin")
    read_count = 0
    for meta_bin in list_bin:
        rows = read_local_meta(meta_bin)
        for row in rows:
            name, size = row[0], row[1]
            if not re_grep.search(name):
                continue

            print(f"{read_count+1:<5} {size:10}  {name}")  # 右对齐，宽度10
            read_count += 1
            if read_count >=cmd_args.line:
                break


def meta_descript(cmd_args):

    save_path = cmd_args.save_path
    meta_path = pathlib.Path(save_path) / "meta"

    print(meta_path.absolute())
    print("---" * 20)

    meta_list = meta_path.glob("*.bin")
    meta_data = {}
    meta_size = {}
    for idx, meta_file in enumerate(meta_list):
        print(meta_file.__str__())
        base_rows = read_base_meta(meta_file)
        for base_row in base_rows:
            _, size, extn =base_row
            meta_data.setdefault(extn, 0)
            meta_data.update({extn: meta_data.get(extn) + 1})

            meta_size.setdefault(extn, 0)
            meta_size.update({extn: meta_size.get(extn) + int(size)})
    print("---" * 20)

    meta_set = sorted(list(meta_data.items()), key=lambda x: x[1], reverse=True)
    for meta_item in meta_set:
        type_size_desc = psutil._common.bytes2human(meta_size[meta_item[0]])
        print(f"{meta_item[0]:25}  {meta_item[1]:>5} {meta_size[meta_item[0]]:>20} {type_size_desc}")
