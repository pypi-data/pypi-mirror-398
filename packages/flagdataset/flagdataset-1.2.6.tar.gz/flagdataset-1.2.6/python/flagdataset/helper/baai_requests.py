import time
import logging

import requests
import psutil

logger = logging.getLogger(__name__)


# requests wrapper

def post(*args, **kwargs):
    for retry in range(1, 4):
        try:
            resp = requests.post(*args, **kwargs)
        except requests.ReadTimeout as e:
            logger.error(e)
            time.sleep(2 * retry)
            continue
        except Exception as e:
            logger.info(e)
            break
        else:
            if resp.status_code != 200:
                logger.error("request: %s, %s, status: %s", args, kwargs, resp.status_code)
            return resp

    raise AssertionError("与服务器连接超时")

def get(*args, **kwargs):
    start = time.time()

    for retry in range(1, 4):
        try:
            resp = requests.get(*args, **kwargs)
        except requests.ReadTimeout as e:
            logger.error(e)
            time.sleep(2 * retry)
            continue
        except Exception as e:
            logger.info("error: %s, args: %s, kwargs: %s", e, args, kwargs)
            break
        else:
            content_length = resp.headers.get("Content-Length")
            speed_compute = psutil._common.bytes2human(int(int(content_length) / (time.time() - start)))

            logger.info(f"request, %s,%.2fs, %s/s", content_length, time.time() - start, speed_compute)
            return resp

    raise AssertionError("与服务器连接超时")


def head(*args, **kwargs):
    return requests.head(*args, **kwargs)