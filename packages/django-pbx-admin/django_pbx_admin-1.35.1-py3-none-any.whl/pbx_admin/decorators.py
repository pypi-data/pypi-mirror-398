from typing import Any, Callable, TypeVar, cast

from django.core.exceptions import ImproperlyConfigured
from django.db.models import QuerySet

T = TypeVar("T", bound=Callable[[Any, QuerySet], int])


def register(*models, **kwargs):
    from pbx_admin.options import ModelAdmin
    from pbx_admin.sites import AdminSite, site

    def _model_admin_wrapper(admin_class):
        if not models:
            raise ValueError("At least one model must be passed to register.")

        admin_site = kwargs.pop("site", site)

        if not isinstance(admin_site, AdminSite):
            raise ValueError("site must subclass AdminSite")

        if not issubclass(admin_class, ModelAdmin):
            raise ValueError("Wrapped class must subclass ModelAdmin.")

        admin_site.register(models, admin_class=admin_class, **kwargs)

        return admin_class

    return _model_admin_wrapper


def try_cached_as(func: T) -> T:
    def wrapper(obj: Any, queryset: QuerySet) -> int:
        try:
            cached_qs = queryset.cache()  # type: ignore[attr-defined]
            return func(obj, cached_qs)
        except (AttributeError, ImproperlyConfigured):
            return func(obj, queryset)

    return cast(T, wrapper)
