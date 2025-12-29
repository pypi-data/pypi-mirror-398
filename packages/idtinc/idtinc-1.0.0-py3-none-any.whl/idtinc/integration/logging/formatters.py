import logging
import sys
import traceback


def get_project_name():
    from django.conf import settings

    project_name = "Application"

    if hasattr(settings, "SERVER_ORIGIN"):
        project_name = settings.SERVER_ORIGIN
    elif hasattr(settings, "BASE_DIR"):
        project_name = settings.BASE_DIR.name
    
    return project_name

_COLORS = {
    "info": "\033[32m",
    "debug": "\033[36m",
    "warning": "\033[33m",
    "error": "\033[31m",
    "critical": "\033[35m",
    "RESET": "\033[0m",
}


class BaseColoredFormatter(logging.Formatter):
    def __init__(self, use_colors=True):
        super().__init__()
        self.use_colors = use_colors and sys.stdout.isatty()

    def _get_colored_level(self, level_name):
        level = level_name.lower()
        if self.use_colors and level in _COLORS:
            return f"{_COLORS[level]}{level[0]}{_COLORS['RESET']}"
        return level[0]


class ColoredFormatter(BaseColoredFormatter):
    def format(self, record):
        colored_level = self._get_colored_level(record.levelname)
        return f"[{colored_level}] {get_project_name()}: {record.getMessage()}"


class ExceptionLogFormatter(BaseColoredFormatter):
    def format(self, record):
        colored_level = self._get_colored_level(record.levelname)

        message = record.getMessage()
        if getattr(record, "error", False):
            prefix = f"{_COLORS['error']}error{_COLORS['RESET']}"

        if record.exc_info:
            _tracebacks = traceback.format_exception(*record.exc_info)
            _traceback_str = " ".join(_tracebacks)
            if self.use_colors:
                _traceback_str = f"{_COLORS['error']}{_traceback_str}{_COLORS['RESET']}"
            message = f"{message} → {prefix}\n{_traceback_str}"
        return f"[{colored_level}] {get_project_name()}: {message}"


class RequestLogFormatter(BaseColoredFormatter):
    def format(self, record):
        colored_level = self._get_colored_level(record.levelname)
        prefix = "request"
        if self.use_colors:
            prefix = f"{_COLORS['info']}request{_COLORS['RESET']}"

        return f"[{colored_level}] {get_project_name()}: {record.getMessage()} → {prefix}"


class ResponseLogFormatter(BaseColoredFormatter):
    def format(self, record):
        colored_level = self._get_colored_level(record.levelname)

        prefix = "response"
        if self.use_colors:
            prefix = f"{_COLORS['debug']}response{_COLORS['RESET']}"

        return f"[{colored_level}] {get_project_name()}: {record.getMessage()} → {prefix}"


class ServerLogFormatter(BaseColoredFormatter):
    def format(self, record):
        colored_level = self._get_colored_level(record.levelname)

        message = record.getMessage()

        if "Starting" in message or "Listening" in message:
            if self.use_colors:
                message = f"{_COLORS['info']}{message}{_COLORS['RESET']}"
        elif "HTTP" in message or "support" in message:
            if self.use_colors:
                message = f"{_COLORS['debug']}{message}{_COLORS['RESET']}"
        elif "Configuring" in message:
            if self.use_colors:
                message = f"{_COLORS['warning']}{message}{_COLORS['RESET']}"

        return f"[{colored_level}] {get_project_name()}: {message}"


class RequireDebugTrue(logging.Filter):
    def filter(self, record):
        from django.conf import settings
        return getattr(settings, "ENV", "development") == "development"


class RequireDebugFalse(logging.Filter):
    def filter(self, record):
        from django.conf import settings
        return getattr(settings, "ENV", "development") == "production"
