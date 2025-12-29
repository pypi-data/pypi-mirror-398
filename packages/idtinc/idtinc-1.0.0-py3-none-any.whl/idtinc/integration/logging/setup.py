def get_setup_logging():
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "colored": {
                "()": "idtinc.integration.logging.formatters.ColoredFormatter",
            },
            "server": {
                "()": "idtinc.integration.logging.formatters.ServerLogFormatter",
            },
            "request": {
                "()": "idtinc.integration.logging.formatters.RequestLogFormatter",
            },
            "response": {
                "()": "idtinc.integration.logging.formatters.ResponseLogFormatter",
            },
            "exception": {
                "()": "idtinc.integration.logging.formatters.ExceptionLogFormatter",
            },
        },
        "filters": {
            "require_debug_false": {
                "()": "idtinc.integration.logging.formatters.RequireDebugFalse",
            },
            "require_debug_true": {
                "()": "idtinc.integration.logging.formatters.RequireDebugTrue",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "colored",
                "stream": "ext://sys.stdout",
                "filters": ["require_debug_true"],
            },
            "server_console": {
                "class": "logging.StreamHandler",
                "formatter": "server",
                "stream": "ext://sys.stdout",
                "filters": ["require_debug_true"],
            },
            "request_console": {
                "class": "logging.StreamHandler",
                "formatter": "request",
                "stream": "ext://sys.stdout",
                "filters": ["require_debug_true"],
            },
            "response_console": {
                "class": "logging.StreamHandler",
                "formatter": "response",
                "stream": "ext://sys.stdout",
                "filters": ["require_debug_true"],
            },
            "exception_console": {
                "class": "logging.StreamHandler",
                "formatter": "exception",
                "stream": "ext://sys.stdout",
                "filters": ["require_debug_true"],
            },
        },
        "loggers": {
            "django": {
                "handlers": ["console"],
                "level": "CRITICAL",
                "propagate": False,
            },
            "django.server": {
                "handlers": ["server_console"],
                "level": "CRITICAL",
                "propagate": False,
            },
            "daphne": {
                "handlers": ["server_console"],
                "level": "CRITICAL",
                "propagate": False,
            },
            "request": {
                "handlers": ["request_console"],
                "level": "INFO",
                "propagate": False,
            },
            "response": {
                "handlers": ["response_console"],
                "level": "INFO",
                "propagate": False,
            },
            "exception": {
                "handlers": ["exception_console"],
                "level": "ERROR",
                "propagate": False,
            },
            "utils.helpers": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
        "root": {
            "handlers": ["console"],
            "level": "CRITICAL",
        },
    }