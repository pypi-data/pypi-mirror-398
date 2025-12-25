from __future__ import annotations

import csv
import json
import logging
import operator
import re
import typing
from typing import TypeVar
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.core.serializers import serialize
from django.db import IntegrityError, models
from django.db.models import ProtectedError
from django.db.models.manager import Manager
from django.forms.formsets import BaseFormSet
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.html import format_html, format_html_join
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.views.generic.edit import FormMixin

from celery.result import AsyncResult
from django_stubs_ext import QuerySetAny

from pbx_admin.conf import admin_settings
from pbx_admin.forms import SearchForm
from pbx_admin.utils import get_related_field
from pbx_admin.views.mixins import (
    AdminViewMixin,
    CSPViewMixin,
    FooterMixin,
    FormsetsMixin,
    ListSelectionMixin,
    PaginationMixin,
    PermissionMixin,
)

log = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from pbx_admin.options import RenderField

_M = TypeVar("_M", bound=models.Model)


class AdminListView(  # type: ignore
    CSPViewMixin,
    PaginationMixin,
    AdminViewMixin,
    FormMixin,
    FooterMixin,
    ListView,
):
    template_name = "pbx_admin/list.html"
    allow_empty = True
    form_class = SearchForm
    list_display = ("id",)

    def handle_async_task_ready(self, request, task):
        self.admin.handle_async_task_ready(request, task)

    def get(self, request, *args, **kwargs):
        url = self.admin.list_url(**kwargs)
        params = dict(request.GET.items())
        if response := self.handle_pagination(request, url):
            return response

        if task_id := request.GET.get("task"):
            task = AsyncResult(task_id)
            if task.ready():
                self.handle_async_task_ready(request, task)
                return HttpResponseRedirect(f"{url}?{urlencode(params)}")
        return super().get(request, *args, **kwargs, url=url)

    def get_form_class(self):
        return self.admin.search_form_class

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.GET:
            kwargs["data"] = self.request.GET
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        return self.admin.get_search_form(self, form)

    def get_template_names(self):
        return [
            "pbx_admin/{}_list.html".format(self.model._meta.model_name),
            self.template_name,
        ]

    def get_queryset(self, **kwargs):
        queryset = self.admin.get_queryset(self.request, **self.kwargs)

        form = self.get_form()
        if form and form.is_valid():
            queryset = queryset.filter(**form.get_filters())

        ordering = ()
        for field_name in self.get_ordering():
            try:
                get_related_field(self.model, field_name.lstrip("-"))
            except FieldDoesNotExist:
                if field_name.lstrip("-") in queryset.query.annotations:
                    ordering += (field_name,)
            else:
                ordering += (field_name,)
        return queryset.order_by(*ordering)

    def get_ordering(self):
        ordering = self.request.GET.get("o") or self.ordering
        if isinstance(ordering, str):
            ordering = (ordering,)

        # add default ordering if not in query params
        for field in self.ordering:
            if field.lstrip("-") not in ordering:
                ordering += (field,)

        return ordering

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.admin.parent:
            context["menu_items"] = self.admin.parent.get_menu_items(
                self.request, **self.kwargs
            )
        if self.form_class:
            context["form"] = self.get_form()

        context["add_form"] = self.admin.get_add_modal_form(
            self, **self.admin.get_add_model_form_kwargs(**self.kwargs)
        )
        context["duplicate_form"] = self.admin.get_duplicate_modal_form(
            self, **self.admin.get_duplicate_model_form_kwargs(**self.kwargs)
        )

        context["breadcrumbs"] = self.admin.get_breadcrumbs(self.request, **self.kwargs)
        fields_list = self.admin.get_list_display(**self.kwargs)
        context["fields_list"] = fields_list
        context["fields_search_list"] = [field.field_name for field in fields_list]

        context["header"] = self._get_context_header(fields_list)

        return context

    def _get_context_header(self, fields_list: list[RenderField]):
        header = []
        form = self.get_form()

        for field in fields_list:
            attrs = self._get_header_field_attrs(field.field_name)
            attrs = {} if attrs is None else {}

            order_field = field.get_field_ordering()
            order_param = self.request.GET.get("o", "")
            header.append(
                {
                    "name": field,
                    "label": field.get_label(form),
                    "is_ordered": order_param.lstrip("-") == order_field,
                    "order_field": order_field,
                    "order_desc": order_param == "-" + order_field,
                    "attrs": attrs,
                }
            )

        return header

    def _get_header_field_attrs(self, field_name: str) -> dict[str, str] | None:
        if self.admin:
            return self.admin._get_header_field_attrs(field_name)
        return None


class AdminSingleObjectView(AdminViewMixin, FormsetsMixin, SuccessMessageMixin, FooterMixin):
    template_name: str | None = "pbx_admin/edit.html"

    def get_initial(self):
        initial = self.initial.copy()
        initial.update(self.admin.get_initial(self.request, **self.kwargs))
        return initial

    def get_form_class(self):
        return self.admin.get_form_class(self)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(self.admin.get_form_kwargs(self))
        return kwargs

    def get_formset_kwargs(self):
        kwargs = super().get_formset_kwargs()
        kwargs.update(self.admin.get_formset_kwargs(self))
        return kwargs

    def get_fieldsets(self, form=None, formsets=None):
        if form is None:
            form = self.get_form()
        if formsets is None:
            formsets = self.get_formsets()

        formsets = {formset.prefix: formset for formset in formsets}
        fieldsets = []

        for title, fieldset in self.admin.get_fieldsets(form):
            fieldset = fieldset.copy()

            if "formset" in fieldset and fieldset["prefix"] in formsets:
                fieldset["formset"] = formsets[fieldset["prefix"]]

            elif "fields" in fieldset:
                fieldset["form"] = form
                if isinstance(fieldset["fields"], str) and fieldset["fields"] == "__all__":
                    fieldset["fields"] = form.fields

            fieldsets.append((title, fieldset))
        return fieldsets

    def get_context_data(self, **kwargs):
        form = kwargs.pop("form", self.get_form())
        formsets = kwargs.pop("formsets", self.get_formsets())

        context = super().get_context_data(**kwargs)

        fieldsets = self.get_fieldsets(form, formsets)
        context["fieldsets"] = fieldsets
        context["menu_items"] = self.admin.get_menu_items(self.request, **self.kwargs)

        # set extra parent field in context if not defined in any fieldset
        p_field = self.admin.parent_field
        if (
            p_field
            and p_field.name in form.fields
            and not any(
                p_field.name in fs["fields"] for name, fs in fieldsets if "fields" in fs
            )
        ):
            context["parent_field"] = form[p_field.name]

        # TODO: ustawiać enctype=multipart/form-data na podstawie poniższego
        # aktualnie sprawdzane jest jedynie form.is_multipart()
        # formularze overridują metodę is_multipart() jeśli jakiś formset
        # jest multipart
        # context['is_multipart'] = \
        #     form.is_multipart() or any(f.is_multipart() for f in formsets)

        return context


class AdminCreateView(AdminSingleObjectView, CreateView):
    success_message_template = _("%s was created successfully.")
    object = None  # noqa A003

    def get_formset_kwargs(self):
        kwargs = super().get_formset_kwargs()
        # TODO: get rid of get_initial_object, use initial data
        kwargs["instance"] = self.admin.get_initial_object(self.request, **self.kwargs)
        return kwargs

    def form_valid(self, form, formsets=None):
        handler = super().form_valid(form, formsets)
        log.info(
            "Created %s %s",
            self.model.__name__,
            self.object.id,
            extra={"request": self.request, "object": self.object},
        )
        return handler

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.admin.get_initial_object(self.request, **self.kwargs)
        context["breadcrumbs"] = self.admin.get_breadcrumbs(self.request, obj, **self.kwargs)
        return context

    def test_func(self):
        if not self.admin.has_add_permission(self.request):
            return False
        return super().test_func()


class AdminUpdateView(AdminSingleObjectView, UpdateView):
    success_message_template = _("%s was saved successfully.")
    formsets: dict[str, type[BaseFormSet]] = {}

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except ValidationError as e:
            raise Http404(e) from e

    def form_valid(self, form, formsets=None):
        handler = super().form_valid(form, formsets)

        log.info(
            "Updated %s %s",
            self.model.__name__,
            self.object.id,
            extra={
                "request": self.request,
                "object": self.object,
                "old_object_fields": json.dumps(self.old_object_fields),
            },
        )
        return handler

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = self.admin.get_breadcrumbs(
            self.request, self.object, **self.kwargs
        )
        return context

    def test_func(self):
        if not self.admin.has_change_permission(self.request):
            return False
        return super().test_func()

    def handle_no_permission(self):
        if self.admin.has_view_permission(self.request):
            return redirect(self.admin.show_url(**self.kwargs))
        return super().handle_no_permission()


class AdminDeleteView(  # type: ignore[misc]
    AdminViewMixin, SuccessMessageMixin, FooterMixin, DeleteView
):
    success_url: str | None = None
    success_message_template = _("%s was deleted successfully.")
    query_pk_and_slug = True

    def get(self, request, *args, **kwargs):
        raise Http404()

    def test_func(self):
        if not self.admin.has_delete_permission(self.request):
            return False
        return super().test_func()

    def get_queryset(self):
        return self.admin.get_queryset(self.request, **self.kwargs)

    def form_valid(self, form):
        obj = self.get_object()
        # After delete obj does not have the id
        obj_id = obj.id
        serialized_object = serialize("json", [obj])

        try:
            self.admin.delete(obj)

        except ProtectedError as e:
            handler = admin_settings.PROTECTED_ERROR_HANDLER
            level, message = handler(e, obj)

        except IntegrityError as e:
            level = messages.ERROR
            message = str(e)

        else:
            log.info(
                "Deleted %s %s",
                self.model.__name__,
                obj_id,
                extra={"request": self.request, "serialized_object": serialized_object},
            )
            level = messages.SUCCESS
            message = self.success_message % {"name": obj}

        messages.add_message(self.request, level, message)
        return HttpResponseRedirect(self.get_success_url())


class AdminShowView(AdminUpdateView):
    http_method_names = ["get", "head", "trace"]
    read_only = True

    def get_form(self, form_class=None):
        form = super().get_form(form_class=form_class)
        for field in form.fields.values():
            field.disabled = True
            field.widget.attrs["disabled"] = True
        return form

    def get_formsets(self):
        formsets = super().get_formsets()
        for formset in formsets:
            for form in formset.forms:
                for field in form.fields.values():
                    field.disabled = True
                    field.widget.attrs["disabled"] = True
        return formsets

    def test_func(self):
        if self.admin.has_view_permission(self.request):
            return True


class AdminDeleteMultipleView(
    AdminViewMixin, SuccessMessageMixin, FooterMixin, ListSelectionMixin, View
):
    success_message_template = _("%s were deleted successfully.")
    model = None

    def get(self, request, *args, **kwargs):
        raise Http404()

    def test_func(self):
        if not self.admin.has_delete_permission(self.request):
            return False
        return super().test_func()

    def post(self, request, *args, **kwargs):
        queryset = self.get_filtered_queryset(request)
        success = []
        errors = []

        for obj in queryset:
            serialized_object = serialize("json", [obj])
            obj_id = obj.id
            try:
                self.admin.delete(obj)

            except ProtectedError as e:
                handler = admin_settings.PROTECTED_ERROR_HANDLER
                handler(e, obj)
                errors.append(
                    (
                        obj,
                        format_html(
                            "it is used in: <ul>{}</ul>",
                            format_html_join(
                                "",
                                '<li>{} "{}", id: {}</li>',
                                (
                                    (
                                        protected_obj._meta.verbose_name,
                                        protected_obj,
                                        protected_obj.pk,
                                    )
                                    for protected_obj in e.protected_objects
                                ),
                            ),
                        ),
                    )
                )

            except IntegrityError as e:
                errors.append((obj, str(e)))

            else:
                log.info(
                    "Deleted %s %s",
                    self.model.__name__,
                    obj_id,
                    extra={"request": request, "serialized_object": serialized_object},
                )
                success.append(obj)

        message = format_html(
            "<p>{} {} have been deleted.</p>",
            len(success),
            self.model._meta.verbose_name_plural,
        )

        if errors:
            message += format_html(
                "<p>{}</p><ul>{}</ul>",
                format_html("There have been {} deletion problems", len(errors)),
                format_html_join(
                    "",
                    '<li>{} "{}" could not be deleted because {}</li>',
                    ((obj._meta.verbose_name, obj, exc) for obj, exc in errors),
                ),
            )

        level = messages.ERROR if errors else messages.SUCCESS
        messages.add_message(request, level, message)
        return HttpResponseRedirect(self.get_success_url())


class CSVExportView(PermissionMixin, ListSelectionMixin, View):
    csv_export_fields = None
    model = None
    admin = None

    def post(self, request, *args, **kwargs):
        queryset = self.get_filtered_queryset(request)
        if queryset.exists():
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="{}.csv"'.format(
                self.admin.opts.verbose_name_plural
            )
            cw = csv.writer(response)

            header = []
            for field in self.csv_export_fields:
                try:
                    model_field = get_related_field(self.model, field)
                    title = model_field.verbose_name
                except FieldDoesNotExist:
                    title = None
                header.append(title or re.sub(r"_+", r" ", str(field)))
            cw.writerow(header)

            for obj in queryset:
                data = []
                for field in self.csv_export_fields:
                    field = field.replace("shinar_", "").replace("__", ".")
                    try:
                        value = operator.attrgetter(field)(obj)
                    except AttributeError:
                        value = None

                    if isinstance(value, Manager):
                        value = value.all()
                    if isinstance(value, QuerySetAny):
                        value = ", ".join([str(o) for o in value])

                    data.append(value)
                cw.writerow(data)
            return response
        else:
            messages.info(request, _("No objects selected."))
            return HttpResponseRedirect(self.admin.list_url(**kwargs))
