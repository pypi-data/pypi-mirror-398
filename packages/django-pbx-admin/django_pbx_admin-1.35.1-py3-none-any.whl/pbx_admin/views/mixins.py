from __future__ import annotations

import json
import logging
import urllib
from contextlib import suppress
from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.core.serializers import serialize
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from django_stubs_ext import StrOrPromise

from pbx_admin.conf import admin_settings
from pbx_admin.paginator import EstimatedObjectsPagination

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from pbx_admin.options import ModelAdmin


class PermissionMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = reverse_lazy("pbx_admin:login")

    def test_func(self):
        return self.request.user.is_staff


class FooterMixin:
    """Changes success_url to object's edit url if
    there is _continue in post request.
    Otherwise redirects to attribute default_success_url
    Also adds cancel_url.
    """

    success_url: StrOrPromise | None = None
    cancel_url = None
    no_cancel = False
    admin: ModelAdmin | None = None

    def get_success_url(self):
        if self.request.POST.get("_continue"):
            kwargs = self.kwargs.copy()
            if self.admin.url_kwarg not in kwargs:
                obj = self.object or self.get_object()
                if self.admin.pk_url_kwarg is not None:
                    kwargs[self.admin.url_kwarg] = obj.pk
                if self.admin.slug_field is not None:
                    kwargs[self.admin.url_kwarg] = getattr(obj, self.admin.slug_field)
            return self.admin.edit_url(**kwargs)
        admin_url = self.admin.get_success_url(self)
        if admin_url:
            return admin_url
        if self.success_url:
            return self.success_url
        return self.get_default_url()

    def get_cancel_url(self):
        admin_url = self.admin.get_cancel_url(self)
        if admin_url:
            return admin_url
        if self.cancel_url:
            return self.cancel_url
        return self.get_default_url()

    def get_cancel_button_attrs(self) -> dict[str, Any]:
        if not self.admin:
            return {}
        return self.admin.get_cancel_button_attrs(self)

    def get_default_url(self):
        kwargs = self.kwargs.copy()
        kwargs.pop(self.admin.pk_url_kwarg, "")
        kwargs.pop(self.admin.slug_url_kwarg, "")
        return self.admin.list_url(**kwargs)


class MessagesMixin:
    """
    Handle messages from django messages framework. Divide messages into
    two groups: to be display as bar or as modal.
    """

    def _update_messages(self, context):
        messages_storage = messages.get_messages(self.request)
        context["bar_messages"] = []
        context["modal_messages"] = []
        for msg in messages_storage:
            msg.tags_set = set(msg.tags.split())
            if {"bar", "success"} & msg.tags_set:
                context["bar_messages"].append(msg)
            else:
                context["modal_messages"].append(msg)
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return self._update_messages(context)


class AdminViewMixin(PermissionMixin, MessagesMixin):
    admin: ModelAdmin | None = None

    success_message_template: StrOrPromise = "%s"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["admin"] = self.admin
        context["model"] = self.admin.model
        context["opts"] = self.admin.opts

        perms = self.admin.get_model_perms(self.request)
        context["model_perms"] = perms
        context["can_add"] = perms["add"] and bool(self.admin.add_view_class)
        context["can_change"] = perms["change"] and bool(self.admin.edit_view_class)
        context["can_delete"] = perms["delete"] and bool(self.admin.delete_view_class)
        context["can_duplicate"] = perms["duplicate"] and bool(self.admin.duplicate_view_class)
        context["can_export"] = bool(self.admin.serialize_view_class)
        context["can_import"] = bool(self.admin.serialize_view_class)

        context["action_name"] = self._get_action_name(self.request)

        context.update(self.admin.get_context_data(self.request, **self.kwargs))

        return context

    def dispatch(self, request, *args, **kwargs):
        try:
            self.admin.dispatch(self)
        except PermissionDenied:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get_success_message(self, cleaned_data):
        obj_name = self.admin.opts.verbose_name.capitalize()
        if "name" in cleaned_data:
            obj_name += ' "{}" '.format(cleaned_data["name"])
        return self.success_message_template % obj_name

    def _get_action_name(self, request) -> str:
        event_name = "".join(
            [
                f"_{letter.lower()}" if letter.isupper() else letter
                for letter in self.admin.model.__name__  # type: ignore[union-attr]
            ]
        ).lstrip("_")
        action_type = "added" if "/add/" in request.build_absolute_uri() else "edited"

        return f"{event_name}_{action_type}"


class FormsetsMixin:
    _old_object_fields: dict | None

    def get_formset_kwargs(self):
        kwargs = {}
        if hasattr(self, "object"):
            kwargs["instance"] = self.object
        if self.request.method in ("POST", "PUT"):
            kwargs.update({"data": self.request.POST, "files": self.request.FILES})
        return kwargs

    def get_formsets(self):
        formsets = self.admin.get_formsets(getattr(self, "object", None))
        return [
            formset(prefix=prefix, **self.get_formset_kwargs())
            for prefix, formset in formsets.items()
        ]

    def post(self, request: HttpRequest, *args: str, **kwargs: str) -> HttpResponse:
        with suppress(AttributeError):
            self.object = self.get_object()  # type: ignore[attr-defined]

        self.old_object_fields = self.object_fields

        form = self.get_form()  # type: ignore[attr-defined]
        formsets = self.get_formsets()

        if form.is_valid() and all(formset.is_valid() for formset in formsets):
            return self.form_valid(form, formsets)  # type: ignore[no-any-return]
        return self.form_invalid(form, formsets)  # type: ignore[no-any-return]

    def form_valid(self, form, formsets=None):
        handler = super().form_valid(form)

        if formsets:
            for formset in formsets:
                if hasattr(self, "object"):
                    formset.instance = self.object
                formset.save()

        return handler

    def form_invalid(self, form, formsets=None):
        context = self.get_context_data(form=form, formsets=formsets)
        return self.render_to_response(context)

    @property
    def object_fields(self) -> dict:
        if not hasattr(self, "object") or self.object is None:
            return {}

        try:
            serialized_data = serialize("json", [self.object])
            return json.loads(serialized_data)[0]["fields"]  # type: ignore[no-any-return]
        except json.JSONDecodeError:
            log.exception(
                "Failed to serialize %s %s",
                self.model.__name__,  # type: ignore[attr-defined]
                self.object.id,
            )
            return {}

    @property
    def old_object_fields(self) -> dict:
        if self._old_object_fields is None:
            log.warning(
                "Failed to retrieve old object fields for %s %s",
                self.model.__name__,  # type: ignore[attr-defined]
                getattr(self.object, "id", "unknown"),
            )
            return {}
        return self._old_object_fields

    @old_object_fields.setter
    def old_object_fields(self, value: dict) -> None:
        self._old_object_fields = value


class ListSelectionMixin:
    def get_filtered_queryset(self, request):
        ids = request.POST.get("ids", "")
        queryset = self.admin.get_queryset(self.request, **self.kwargs)

        if ids == "all":
            params = request.POST.get("search_params", "")
            form_class = self.admin.search_form_class
            form = form_class(
                data={k: v[0] for k, v in urllib.parse.parse_qs(params[1:]).items()}
            )
            if form.is_valid():
                return queryset.filter(**form.get_filters())
        elif ids:
            return queryset.filter(pk__in=ids.split(","))

        return queryset.none()


class PaginationMixin:
    per_page_key = "per-page"
    set_per_page_key = "set-per-page"
    per_page_session_key = "ITEMS_PER_PAGE"
    paginate_by = admin_settings.ITEMS_PER_PAGE
    paginator_class = EstimatedObjectsPagination

    def handle_pagination(self, request, url):
        params = dict(self.request.GET.items())
        set_per_page = params.pop(self.set_per_page_key, None)
        per_page = params.pop(self.per_page_key, None)

        validated_set_per_page = self._validate_per_page(request, set_per_page)
        per_page = self._validate_per_page(request, per_page)

        if validated_set_per_page:
            request.session[self.per_page_session_key] = validated_set_per_page
            params[self.per_page_key] = validated_set_per_page
            params.pop("page", None)
            return HttpResponseRedirect(f"{url}?{urlencode(params)}")

        if per_page is None:
            per_page = request.session.get(self.per_page_session_key, self.paginate_by)
            params[self.per_page_key] = per_page
            params.pop("page", None)
            return HttpResponseRedirect(f"{url}?{urlencode(params)}")

        if set_per_page is not None:
            return HttpResponseRedirect(f"{url}?{urlencode(params)}")

        self.paginate_by = per_page

    def _validate_per_page(self, request, per_page):
        if per_page is None:
            return
        try:
            per_page = int(per_page)
        except ValueError:
            messages.error(request, _("Please use dropdown on the bottom of the page"))
            return
        if per_page not in admin_settings.PAGINATION_CHOICES:
            messages.error(request, _("Please use dropdown on the bottom of the page"))
            return
        return per_page

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data()
        adjacent_pages = admin_settings.ADJACENT_PAGES

        page = context.get("page_obj", kwargs.get("page"))

        context.update(
            {
                "page_obj": page,
                "paginator": page.paginator,
                "is_paginated": page.has_other_pages,
                "pagination_choices": admin_settings.PAGINATION_CHOICES,
                "params_for_page": self._get_context_params_for_page(),
                "filter_params": self._get_context_params_for_page(with_sorting=False),
            }
        )
        if not page.has_other_pages():
            return context
        context["adjacent_pages_before"], context["adjacent_pages_after"] = (
            self._get_adjacent_pages(page.number, page.paginator.page_range, adjacent_pages)
        )
        return context

    def get_paginate_by(self, queryset=None):
        return int(
            self.request.GET.get(self.per_page_key)
            or self.request.session.get(self.per_page_session_key)
            or self.paginate_by
        )

    def get_paginator(self, *args, **kwargs):
        paginator = self.paginator_class(
            *args, **kwargs, use_estimated_count=self.admin.use_estimated_count
        )
        return paginator

    @staticmethod
    def _get_adjacent_pages(current_page, page_range, adjacent_count):
        adj_pages_before = list(
            range(max(page_range[0], current_page - adjacent_count), current_page)
        )
        adj_pages_after = list(
            range(current_page + 1, min(current_page + adjacent_count + 1, page_range[-1]))
        )
        return adj_pages_before, adj_pages_after

    def _get_context_params_for_page(self, with_sorting=True):
        params = dict(self.request.GET.items())
        params.pop("page", None)
        if not with_sorting:
            params.pop("o", None)
        return f"{urlencode(params)}&page=" if params else "page="


class CSPViewMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request, "csp_nonce"):
            kwargs.update({"csp_nonce": self.request.csp_nonce})
        return kwargs
