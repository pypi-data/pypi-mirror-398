import logging

from django.shortcuts import redirect
from django.utils import translation
from django.utils.deprecation import MiddlewareMixin

from idtinc.core.message import Msg
from idtinc.core.status import HttpStatus

from .response import JsonAPIResponse

request_logger = logging.getLogger("request")
response_logger = logging.getLogger("response")


class ExceptionMiddleware(MiddlewareMixin):
    EXCLUDED_PATHS = [
        "/favicon.ico",
        "/robots.txt",
        "/manifest.json",
        "/apple-touch-icon.png",
        "/admin/",
        "/media/",
        "/static/",
        "/staticfiles/",
        "/swagger",
        "/redoc",
    ]

    def should_log_request(self, request):
        path = request.path.rstrip("/")
        excluded_paths = [p.rstrip("/") for p in self.EXCLUDED_PATHS]

        if path in excluded_paths:
            return False

        for excluded_path in self.EXCLUDED_PATHS:
            if excluded_path.endswith("/") and path.startswith(excluded_path.rstrip("/")):
                return False

        return True

    def process_request(self, request):
        from django.conf import settings
        if self.should_log_request(request) and settings.DEBUG:
            request_logger.info(f"{request.path} [{request.method}]")
        return None

    def process_response(self, request, response):
        response_data = getattr(response, "data", {}) or {}
        status_code = getattr(response, "status_code", HttpStatus.INTERNAL_SERVER_ERROR.value)

        if isinstance(response_data, dict) and response_data.get("status"):
            status_code = response_data.get("status")

        if request.path == "/admin":
            return redirect("/admin/")

        if not self.should_log_request(request):
            return response

        if response.status_code == HttpStatus.NOT_FOUND.value:
            if self.should_log_request(request):
                response_logger.warning(f"{request.path} [{HttpStatus.NOT_FOUND}]")
            return JsonAPIResponse(status=HttpStatus.NOT_FOUND, message=Msg.NOT_FOUND)

        if HttpStatus.is_server_error(response.status_code):
            if self.should_log_request(request):
                response_logger.error(f"InternalServerError {status_code}: Internal Server Error")
        elif self.should_log_request(request):
            response_logger.warning(f"{request.path} [{status_code}]")

        return response


class CustomLocaleMiddleware(MiddlewareMixin):

    def __init__(self, get_response=None):
        from django.conf import settings

        self.ALLOWED_LANGUAGES = [l[0] for l in getattr(settings, "LANGUAGES", [])]
        self.DEFAULT_LANGUAGE = getattr(settings, "LANGUAGE_CODE", "vi")
        
        super().__init__(get_response)

    def is_valid_language(self, lang):
        return lang in self.ALLOWED_LANGUAGES

    def get_language_from_request(self, request):
        lang_param = request.GET.get("lang")
        if lang_param and self.is_valid_language(lang_param):
            return lang_param

        accept_language = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
        if accept_language and self.is_valid_language(accept_language):
            return accept_language

        return self.DEFAULT_LANGUAGE

    def process_request(self, request):
        language = self.get_language_from_request(request)

        if not self.is_valid_language(language):
            language = self.DEFAULT_LANGUAGE

        translation.activate(language)

        request.LANGUAGE_CODE = language
        request.META["HTTP_ACCEPT_LANGUAGE"] = language

        if request.path.startswith("/swagger"):
            request.META["HTTP_ACCEPT_LANGUAGE"] = language

        return None

    def process_response(self, request, response):
        if hasattr(request, "LANGUAGE_CODE"):
            response["Content-Language"] = request.LANGUAGE_CODE

        return response
