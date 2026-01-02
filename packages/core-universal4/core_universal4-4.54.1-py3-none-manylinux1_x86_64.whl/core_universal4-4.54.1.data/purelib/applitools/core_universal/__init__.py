from __future__ import absolute_import

import os


def _version(package_name):
    try:  # assume python>=3.9
        from importlib.metadata import version

        return version(package_name)
    except ImportError:  # older python
        from pkg_resources import get_distribution

        return get_distribution(package_name).version


__version__ = _version("core-universal4")


def _str2bool(v):
    return None if v is None else v.lower() in ("yes", "true", "t", "1")


DEBUG = _str2bool(os.getenv("APPLITOOLS_UNIVERSAL_DEBUG", None))


def get_instance(mask_log=None):
    from . import instance

    return instance.create_or_get_instance(debug=DEBUG, mask_log=mask_log)


__all__ = ("get_instance",)
