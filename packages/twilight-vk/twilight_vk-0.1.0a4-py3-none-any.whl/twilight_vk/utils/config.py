from ..logger.formatters import (
    DarkyConsoleFormatter,
    DarkyFileFormatter,
    UvicornAccessFormatter
)

class CONFIG:

    class FRAMEWORK:
        version = "0.1.0-alpha4"
        developer = "darky_wings"
    
    class VK_API:
        url = "https://api.vk.ru"
        version = "5.199"
        wait = 25

    class API:
        host = "0.0.0.0"
        port = 8000
        title = "Twilight API Swagger"
        description = "Welcome to the Twilight API Swagger!"
        version = "0.0.1"
        prefix = "/api/v1"

    LOGGER = {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "file": {
                        "()": DarkyFileFormatter,
                        "fmt": "%(name)s | %(asctime)s | %(levelname)s | %(message)s"
                    },
                    "console": {
                        "()": DarkyConsoleFormatter,
                        "fmt": "%(name)s | %(asctime)s | %(levelname)s | %(message)s",
                        "colored": True,
                        "color_core_name": True
                    },
                    "uvicorn_access_console": {
                        "()": UvicornAccessFormatter,
                        "fmt": "%(name)s | %(asctime)s | %(levelname)s | %(client_addr)s - \"%(request_line)s\" %(status_code)s",
                        "colored": True
                    }
                },
                "handlers": {
                    "file": {
                        "level": "INIT",
                        "class": "logging.handlers.RotatingFileHandler",
                        "formatter": "file",
                        "filename": "twilight_vk.log",
                        "backupCount": 3,
                        "encoding": "utf-8"
                    },
                    "console": {
                        "level": "INFO",
                        "class": "logging.StreamHandler",
                        "formatter": "console"
                    },
                    "uvicorn_access_console": {
                        "level": "INIT",
                        "class": "logging.StreamHandler",
                        "formatter": "uvicorn_access_console"
                    }
                },
                "loggers": {
                    "twilight-api": {
                        "handlers": ["console", "file"],
                        "level": "INIT",
                        "propagate": True
                    },
                    "uvicorn.access": {
                        "handlers": ["uvicorn_access_console", "file"],
                        "level": "INIT",
                        "propagate": True
                    },
                    "uvicorn.error": {
                        "handlers": ["uvicorn_access_console", "file"],
                        "level": "WARNING",
                        "propagate": True
                    },
                    "twi-api-fw": {
                        "handlers": ["console", "file"],
                        "level": "INIT",
                        "propagate": True
                    },
                    "twi-api-vkapi": {
                        "handlers": ["console", "file"],
                        "level": "INIT",
                        "propagate": True
                    },
                    "twilight-vk": {
                        "handlers": ["console", "file"],
                        "level": "INIT",
                        "propagate": True
                    },
                    "botslongpoll": {
                        "handlers": ["console", "file"],
                        "level": "INIT",
                        "propagate": True
                    },
                    "vk-methods": {
                        "handlers": ["console", "file"],
                        "level": "INIT",
                        "propagate": True
                    },
                    "http-validator": {
                        "handlers": ["console", "file"],
                        "level": "INIT",
                        "propagate": True
                    },
                    "event-validator": {
                        "handlers": ["console", "file"],
                        "level": "INIT",
                        "propagate": True
                    },
                    "event-router": {
                        "handlers": ["console", "file"],
                        "level": "INIT",
                        "propagate": True
                    },
                    "event-handler": {
                        "handlers": ["console", "file"],
                        "level": "INIT",
                        "propagate": True
                    },
                    "rule-handler": {
                        "handlers": ["console", "file"],
                        "level": "INIT",
                        "propagate": True
                    },
                    "loop-manager": {
                        "handlers": ["console", "file"],
                        "level": "INIT",
                        "propagate": True
                    },
                    "asyncio": {
                        "handlers": ["console", "file"],
                        "level": "INFO",
                        "propagate": True
                    }
                }
            }