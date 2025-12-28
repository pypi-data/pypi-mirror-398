import logging


from ..baai_config import Application
from ..helper import baai_requests as requests



logger = logging.getLogger(__name__)


def get_share_url(dataset_id: str):
    config = Application()

    user_login_token = config.try_login()
    req_headers = {
        "Authorization": f"Bearer {user_login_token}",
    }
    req_headers.update(config.req_header)

    req_sign_json = { # noqa
        "dataset_id": dataset_id,
    }

    api = "api/v5/storage-download/dataset/provider-meta/datasets/share-url"
    try:
        resp_share_url = requests.post(config.req_host + "/" + api, headers=req_headers, json=req_sign_json)
        resp_data  = resp_share_url.json()
        assert resp_share_url.status_code == 200, f"status: {resp_share_url.status_code}"
        assert resp_data.get("code") == 0, resp_data.get("message")
    except Exception as e:
        logger.error(e)
        raise  Exception("share_download, err: %s" % e)

    resp_share_data = resp_data.get("data")
    download_sign = resp_share_data.get("download_sign")
    download_code = resp_share_data.get("download_code")
    dataset_prefix = resp_share_data.get("dataset_prefix")

    return download_sign, download_code, dataset_prefix



def download_share(
        dataset,
        save_path,
        prefix=None,
        key=None,
        network=None,
        jobs_down=4,
        debug=False,
        proxy=None
):
    import pathlib

    from baai_flagdataset_ks3util import multi_download

    save_path = pathlib.Path(save_path)
    save_path.mkdir(parents=True, exist_ok=True)

    share_url, download_code, dataset_prefix = get_share_url(dataset)

    use_loc = save_path / "data"
    share_prefix = None

    if prefix:
        share_prefix = f"{dataset_prefix}/{prefix.strip('/')}/"
        use_loc = use_loc / share_prefix.rstrip("/").__str__()

    share_key = None
    if not share_prefix and key:
        share_key = f"{dataset_prefix}/{key.strip('/')}"
        use_loc = (use_loc / share_key.rstrip("/")).parent

    use_loc.mkdir(parents=True, exist_ok=True)

    multi_download(
        use_loc.__str__(),
        network,
        jobs_down,
        share_url,
        download_code,
        prefix=share_prefix,
        key=share_key,
        debug=debug,
        proxy=proxy
    )
