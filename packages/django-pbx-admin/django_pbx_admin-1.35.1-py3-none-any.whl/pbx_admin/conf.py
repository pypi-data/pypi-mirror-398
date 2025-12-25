from __future__ import absolute_import

from collections.abc import Callable

from django.conf import settings
from django.utils.module_loading import import_string

from pbx_admin.handlers import default_protected_error_handler


class Settings:
    """
    Shadow Django's settings with a little logic
    """

    @property
    def PROTECTED_ERROR_HANDLER(self):
        handler = getattr(
            settings, "PBX_ADMIN_PROTECTED_ERROR_HANDLER", default_protected_error_handler
        )
        if isinstance(handler, Callable) or handler is None:
            return handler
        return import_string(handler)

    @property
    def ITEMS_PER_PAGE(self):
        return getattr(settings, "PBX_ADMIN_ITEMS_PER_PAGE", 50)

    @property
    def ADJACENT_PAGES(self):
        return getattr(settings, "PBX_ADMIN_ADJACENT_PAGES", 2)

    @property
    def PAGINATION_CHOICES(self):
        return getattr(settings, "PBX_ADMIN_PAGINATION_CHOICES", [20, 50, 100, 200, 500, 1000])


admin_settings = Settings()
