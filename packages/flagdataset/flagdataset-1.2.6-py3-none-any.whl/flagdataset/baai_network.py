import logging

import requests

from .baai_config import config_update



logger = logging.getLogger(__name__)


def network_config():
    try:
        private = "https://baai-datasets.ks3-cn-beijing-internal.ksyuncs.com/public/internal/speed/readme.md"
        requests.get(private, timeout=1)
    except requests.exceptions.ReadTimeout:
        network = "public"
    except Exception as e:
        logger.error("network_config, err: %s, set public network", e)
        network = "public"
    else:
        network = "private"

    config_data = {
        "network": network,
    }
    config_update(config_data)
