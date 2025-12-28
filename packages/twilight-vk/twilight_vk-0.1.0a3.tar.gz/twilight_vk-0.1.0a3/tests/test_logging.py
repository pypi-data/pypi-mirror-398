from twilight_vk.logger.darky_logger import DarkyLogger
from twilight_vk.logger.formatters import (
    DarkyConsoleFormatter,
    DarkyFileFormatter
)

CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "file": {
            "()": DarkyFileFormatter,
            "fmt": "%(name)s | %(asctime)s | %(levelname)s | %(message)s"
        },
        "console": {
            "()": DarkyConsoleFormatter,
            "fmt": "%(name)s | %(asctime)s | %(levelname)s | %(message)s",
            "colored": True
        }
    },
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INIT",
            "formatter": "file",
            "filename": "tests/test_logging.log",
            "encoding": "utf8",
            "backupCount": 1
        },
        "console": {
            "class": "logging.StreamHandler",
            "level": "INIT",
            "formatter": "console"
        }
    },
    "loggers": {
        "test": {
            "handlers": ["console", "file"],
            "level": "INIT",
            "propagate": True
        }
    }
}

def test_logging(caplog):

    print()
    logger = DarkyLogger("test", CONFIG, silent=True)

    for level in [logger.initdebug, logger.note, logger.subdebug, logger.debug, logger.info, logger.warning, logger.error]:
        level(f"Mlem")
        level("{'key': 123}, {'access_token': 'abc'}, {\"access_token\": \"abc\"}")
        level(f"https://mlem.api/mlem?access_token=123")
        level(f"https://mlem.api/mlem?access_token=123&abs=True")
    logger.mlem("Mlem")
    try:
        raise Exception
    except Exception as ex:
        logger.critical(f"We got an error! Mlem", exc_info=True)
    
    for record in caplog.records:
        if record.message not in ["ANSI support initiated!", "DarkyLogger initiated"]:
            if record.levelname in ["INIT", "SUBDEBUG", "DEBUG", "INFO", "ERROR"]:
                assert record.message in ["Mlem",
                                          "{'key': 123}, {'access_token': 'abc'}, {\"access_token\": \"abc\"}",
                                          "https://mlem.api/mlem?access_token=123",
                                          "https://mlem.api/mlem?access_token=123&abs=True"]
            elif record.levelname == "WARNING":
                assert record.message in ["'DarkyLogger' has no attribute 'mlem'. \"INFO\" is used instead.",
                                          "Mlem",
                                          "{'key': 123}, {'access_token': 'abc'}, {\"access_token\": \"abc\"}",
                                          "https://mlem.api/mlem?access_token=123",
                                          "https://mlem.api/mlem?access_token=123&abs=True"]
            elif record.levelname == "CRITICAL":
                assert record.message == "We got an error! Mlem"