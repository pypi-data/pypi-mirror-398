from django.core.paginator import Page, Paginator
from django.utils.functional import cached_property

from django_stubs_ext import QuerySetAny

from pbx_admin.conf import admin_settings
from pbx_admin.utils import count_estimate


class EstimatedObjectsPagination(Paginator):
    def __init__(self, *args, **kwargs):
        self.use_estimated_count = kwargs.pop("use_estimated_count", False)
        super().__init__(*args, **kwargs)

    @cached_property
    def count(self):
        if self.use_estimated_count and isinstance(self.object_list, QuerySetAny):
            return count_estimate(
                self.object_list, precision=max(admin_settings.PAGINATION_CHOICES)
            )
        return super().count

    def _get_page(self, *args, **kwargs):
        return EstimatedObjectsPage(*args, **kwargs)


class EstimatedObjectsPage(Page):
    """
    Handle page pagination for estimated object count.
    """

    def has_next(self) -> bool:
        if not self.object_list:
            return False
        return super().has_next()
