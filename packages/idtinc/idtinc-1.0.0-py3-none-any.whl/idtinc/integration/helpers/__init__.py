from .query import *
from .string import *
from .timezone import *
from .zns import *


def get_client_ip(request):
    ip_address = request.META.get("HTTP_CF_CONNECTING_IP")
    if ip_address:
        return ip_address

    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(",")[0].strip()
    else:
        ip_address = request.META.get("REMOTE_ADDR")
    return ip_address
