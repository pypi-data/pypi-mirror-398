from __future__ import absolute_import

from .server import SDKServer

_instance = None


def create_or_get_instance(debug, mask_log):
    global _instance
    if _instance:
        return _instance
    _instance = SDKServer(debug, mask_log)
    return _instance
