from pathlib import Path
from logging.config import dictConfig

def logger_init(logger_default_directory: Path):
    logger_default_directory.mkdir(parents=True, exist_ok=True)
    logger_default_path = logger_default_directory / "access.log"

    logger_default = {
        "version": 1,
        "disable_existing_loggers": False,  # 避免禁用第三方库日志
        "formatters": {
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - [Thread-%(thread)d] - %(message)s"
            },
            "simple": {
                "format": "%(name)s - %(levelname)s - %(message)s"
            }
        },
        "handlers": {
            "file": {
                "class": "logging.handlers.RotatingFileHandler", # 轮转文件
                "level": "INFO",
                "formatter": "detailed",
                "filename": logger_default_path.absolute().__str__(),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 100,      # 保留 5 个备份
                "encoding": "utf-8"
            },
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "simple"
            }
        },
        "loggers": {
            "root": {
                "level": "DEBUG",
                "handlers": ["file"],
                "propagate": False
            },
        }
    }
    dictConfig(logger_default)






