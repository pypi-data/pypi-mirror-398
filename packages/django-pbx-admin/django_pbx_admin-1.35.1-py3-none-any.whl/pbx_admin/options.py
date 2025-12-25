from __future__ import annotations

import itertools
from collections.abc import Callable
from contextlib import suppress
from typing import (
    Any,
    Generic,
    Optional,
    Sequence,
    Tuple,
    TypedDict,
    TypeVar,
    Union,
    cast,
)

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_permission_codename
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import (
    FieldDoesNotExist,
    ImproperlyConfigured,
    PermissionDenied,
)
from django.db.models import ForeignKey, Model, QuerySet
from django.db.models.fields import Field
from django.db.models.fields.reverse_related import ForeignObjectRel
from django.forms import (
    HiddenInput,
    ModelForm,
    inlineformset_factory,
    modelform_factory,
)
from django.forms.forms import BaseForm
from django.forms.formsets import BaseFormSet
from django.http import Http404
from django.urls import include, re_path, reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import View

from django_stubs_ext import StrOrPromise

from pbx_admin.conf import admin_settings
from pbx_admin.consts import DEFAULT_PAGE_TYPE
from pbx_admin.data import MenuItem
from pbx_admin.decorators import try_cached_as
from pbx_admin.forms import SearchForm
from pbx_admin.templatetags.admin_tags import humanize_number
from pbx_admin.utils import count_estimate
from pbx_admin.views import (
    AdminCreateView,
    AdminDeleteMultipleView,
    AdminDeleteView,
    AdminListView,
    AdminShowView,
    AdminUpdateView,
    CSVExportView,
)


class _OptionalFieldOpts(TypedDict, total=False):
    """
    django admin requires fields, but we give possibility to define formset,
    so fields are optional
    prefix is used by product-images.js
    """

    fields: Sequence[str | Sequence[str]]
    classes: Sequence[str]
    description: str
    prefix: str
    template_name: str
    formset: type[BaseFormSet]
    fieldsets: _ListOrTuple[tuple[Optional[StrOrPromise], dict]]
    html: str | Callable[..., str]
    nested_list: type[Model]
    nested_admin_class: type[ModelAdmin]
    nested_fields: tuple[str, ...]
    related_field: str
    section_id: str


class _FieldOpts(_OptionalFieldOpts, total=True):
    pass


# Workaround for mypy issue, a Sequence type should be preferred here.
# https://github.com/python/mypy/issues/8921
_T = TypeVar("_T")
_ListOrTuple = Union[Tuple[_T, ...], list[_T]]
_FieldsetSpec = _ListOrTuple[tuple[Optional[StrOrPromise], _FieldOpts]]

_Model = TypeVar("_Model", bound=Model)
_BaseForm = TypeVar("_BaseForm", bound=BaseForm)


class ModelAdmin:
    model: type[Model] | None = None
    queryset: QuerySet | None = None

    # parent-children relation
    parent: type[ModelAdmin] | None = None
    parent_field: str | None = None
    is_inner: bool = False

    # url pattern
    namespace: str | None = None
    pk_url_kwarg: str | None = None
    slug_url_kwarg: str | None = None
    slug_url_pattern: str | None = None
    slug_field: str | None = None

    # add/edit view
    form_class: type[BaseForm] = ModelForm
    fields: tuple[str, ...] = ()
    fieldsets: _FieldsetSpec = ()

    # add/edit view actions
    success_url: StrOrPromise | Callable[..., Any] | None = None
    cancel_url: StrOrPromise | Callable[..., Any] | None = None
    no_cancel: bool = False

    # list view
    search_form_class: type[BaseForm] | None = None
    list_display: tuple[str, ...] = ("id",)
    list_ordering: tuple[str, ...] | None = None
    list_editable: tuple[str, ...] = ()
    editable_view_name: str = ""
    csv_export_fields: tuple[str, ...] | None = None  # fields for csv export

    # add & duplicate modals
    add_modal_fields: tuple[str, ...] = ()
    add_modal_form_attrs: dict[str, str] = {}
    duplicate_modal_fields: tuple[str, ...] = ()
    duplicate_async: bool = False

    # templates
    list_template_name: str = "pbx_admin/list.html"
    add_template_name: str | None = None
    edit_template_name: str = "pbx_admin/edit.html"

    # view classes
    list_view_class: type[View] | None = AdminListView
    add_view_class: type[View] | None = AdminCreateView
    edit_view_class: type[View] | None = AdminUpdateView
    show_view_class: type[View] | None = AdminShowView
    delete_view_class: type[View] | None = AdminDeleteView
    delete_multiple_view_class: type[View] | None = AdminDeleteMultipleView
    csv_export_view_class: type[View] | None = CSVExportView
    csv_import_view_class: type[View] | None = None
    csv_template_export_view_class: type[View] | None = None
    csv_template_import_view_class: type[View] | None = None

    # Duplicate, Export & Import View Class have to implemented separately
    duplicate_view_class: type[View] | None = None
    serialize_view_class: type[View] | None = None

    # other
    only_menu_actions = False
    use_estimated_count = False
    csv_export_button_data_action: str = "link-submit"

    def __init__(self, model, admin_site, *args, parent=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.model = model
        if self.queryset is None:
            self.queryset = self.model.objects.all()
        self.opts = self.model._meta
        self.admin_site = admin_site
        self.children = []

        if self.namespace is None:
            self.namespace = self.opts.model_name

        if parent:
            self.parent = parent
            self.parent.children.append(self)
            parent_model = self.parent.model._meta.concrete_model
            parent_fields = [
                field
                for field in self.model._meta.fields
                if isinstance(field, ForeignKey) and field.related_model == parent_model
            ]
            if parent_fields:
                self.parent_field = parent_fields[0]

        if self.add_template_name is None:
            self.add_template_name = self.edit_template_name

        self._init_url_kwarg()
        self._init_fields()
        self._init_forms()
        self._init_formsets()

    def __str__(self):
        return "%s.%s" % (self.model._meta.app_label, self.__class__.__name__)

    def _init_url_kwarg(self):
        # urls init
        if not self.pk_url_kwarg and not self.slug_url_kwarg:
            self.pk_url_kwarg = "pk"
            parent = self.parent
            while parent:
                self.pk_url_kwarg = "sub_" + self.pk_url_kwarg
                parent = parent.parent

        if self.slug_url_kwarg is not None and self.slug_field is None:
            self.slug_field = self.slug_url_kwarg

        self.url_kwarg = self.pk_url_kwarg or self.slug_url_kwarg

    def _init_fields(self):
        if self.fields and self.fieldsets:
            raise ImproperlyConfigured(
                "Specifying both 'fields' and 'fieldsets' is not permitted."
            )
        elif self.fieldsets:
            self.fields = self._get_fields_from_fieldsets(self.fieldsets)
        elif self.fields:
            self.fieldsets = ((None, {"fields": self.fields}),)
        elif hasattr(self.form_class, "Meta") and hasattr(self.form_class.Meta, "fields"):
            # if fields and fieldsets are not defined,
            # use all form fields by defining __all__
            # this allows to include also dynamically generated forms
            # e.g. for EditorStep & EditorComponent
            self.fields = self.form_class.Meta.fields
            self.fieldsets = ((None, {"fields": "__all__"}),)

    def _init_forms(self):
        if self.form_class is None:
            self.form_class = ModelForm

        try:
            fields = self.form_class.Meta.fields
        except AttributeError:
            fields = self.fields

        p_field = self.parent_field
        if p_field and p_field.name not in fields:
            try:
                widgets = self.form_class.Meta.widgets.copy()
            except AttributeError:
                widgets = {}
            widgets[p_field.name] = HiddenInput
            fields = (p_field.name,) + tuple(fields)
            self.form_class = modelform_factory(
                self.model,
                form=self.form_class,
                fields=(p_field.name,) + tuple(fields),
                widgets=widgets,
            )
        else:
            self.form_class = modelform_factory(self.model, form=self.form_class, fields=fields)

        if not self.search_form_class:
            model_fields = {f.name for f in self.model._meta.fields}
            self.search_form_class = modelform_factory(
                self.model,
                form=SearchForm,
                fields=[f for f in self.list_display if f in model_fields],
            )

        if not self.csv_export_fields:
            self.csv_export_fields = (
                self.form_class.Meta.fields if self.form_class else self.fields
            )
            if not any(field in self.csv_export_fields for field in ("id", "pk")):
                self.csv_export_fields = ("id",) + tuple(self.csv_export_fields)

    def _init_formsets(self):
        self.formsets = {}
        formset_id = 0
        for _title, fieldset in self.fieldsets:
            if "formset" in fieldset:
                formset = fieldset["formset"]
                fieldset.setdefault("prefix", f"formset-{formset_id}")

                fieldsets = fieldset.get("fieldsets")
                if fieldsets:
                    fields = self._get_fields_from_fieldsets(fieldsets)
                    form = modelform_factory(formset.model, form=formset.form, fields=fields)
                    formset = inlineformset_factory(
                        self.model, formset.model, form=form, formset=formset
                    )

                self.formsets[fieldset["prefix"]] = formset
                formset_id += 1

    def _get_fields_from_fieldsets(self, fieldsets):
        return tuple(
            itertools.chain(*(fieldset.get("fields", ()) for title, fieldset in fieldsets))
        )

    def get_list_display(self, *args, **kwargs) -> list[RenderField]:
        return [
            RenderField(
                field_name=field_name, admin=self, editable=field_name in self.list_editable
            )
            for field_name in self.list_display
        ]

    def get_object_url_pattern(self):
        if self.pk_url_kwarg is not None:
            return rf"(?P<{self.pk_url_kwarg}>\d+)"
        if self.slug_url_kwarg is not None:
            return rf"(?P<{self.slug_url_kwarg}>{self.slug_url_pattern})"

    def build_url(self, name, **kwargs):
        namespace_list = [self.namespace]
        parent = self.parent
        while parent:
            namespace_list = [parent.namespace] + namespace_list
            parent = parent.parent
        namespace = ":".join([self.admin_site.name] + namespace_list)
        return reverse(f"{namespace}:{name}", kwargs=kwargs)

    def list_url(self, **kwargs):
        return self.build_url("list", **kwargs)

    def add_url(self, **kwargs):
        return self.build_url("add", **kwargs)

    def edit_url(self, **kwargs):
        return self.build_url("edit", **kwargs)

    def delete_url(self, **kwargs):
        return self.build_url("delete", **kwargs)

    def show_url(self, **kwargs):
        return self.build_url("show", **kwargs)

    @property
    def can_duplicate(self):
        return self.duplicate_view_class and hasattr(self.model, "duplicate")

    @property
    def hide_from_index(self):
        return self.parent or self.is_inner

    def get_urlpatterns(self):
        urlpatterns = []

        if self.list_view_class:
            urlpatterns.append(re_path(r"^$", self.list_view, name="list"))

        obj_pattern = self.get_object_url_pattern()

        if self.delete_view_class:
            urlpatterns.append(
                re_path(rf"^{obj_pattern}/delete/$", self.delete_view, name="delete")
            )
        if self.delete_multiple_view_class:
            urlpatterns.append(
                re_path(r"^delete/$", self.delete_multiple_view, name="delete-multiple")
            )

        if self.add_view_class:
            urlpatterns.append(re_path(r"^add/$", self.add_view, name="add"))
        if self.edit_view_class:
            urlpatterns.append(
                re_path(
                    rf"^{obj_pattern}/$" if obj_pattern else r"$", self.edit_view, name="edit"
                )
            )

        if self.show_view_class:
            urlpatterns.append(
                re_path(
                    rf"^{obj_pattern}/show/$" if obj_pattern else r"^show/$",
                    self.show_view,
                    name="show",
                )
            )

        if self.can_duplicate:
            urlpatterns.append(
                re_path(rf"^{obj_pattern}/duplicate/$", self.duplicate_view, name="duplicate")
            )

        if self.csv_export_view_class:
            urlpatterns.append(
                re_path(r"^export-to-csv", self.csv_export_view, name="csv-export")
            )

        if self.csv_import_view_class:
            urlpatterns.append(
                re_path(r"^import-from-csv", self.csv_import_view, name="csv-import")
            )

        if self.csv_template_export_view_class:
            urlpatterns.append(
                re_path(
                    r"^export-template-to-csv",
                    self.csv_template_export_view,
                    name="csv-template-export",
                )
            )

        if self.csv_template_import_view_class:
            urlpatterns.append(
                re_path(
                    r"^import-template-from-csv",
                    self.import_from_csv_view,
                    name="csv-template-import",
                )
            )

        if self.serialize_view_class:
            urlpatterns.append(re_path(r"^export/$", self.export_view, name="export"))

        for admin in self.children:
            urlpatterns += admin.get_urls()

        return urlpatterns

    def get_urls(self):
        urlpatterns = (self.get_urlpatterns(), "pbx_admin")

        if self.parent:
            prefix = r"{}/{}/".format(self.parent.get_object_url_pattern(), self.namespace)
        else:
            prefix = r"^{}/".format(self.namespace)

        return [re_path(prefix, include(urlpatterns, namespace=self.namespace))]

    def _get_default_view_kwargs(self):
        return {"admin": self, "model": self.model}

    def _get_single_object_view_kwargs(self):
        kwargs = self._get_default_view_kwargs()
        kwargs.update(
            {
                "pk_url_kwarg": self.pk_url_kwarg,
                "slug_url_kwarg": self.slug_url_kwarg,
                "slug_field": self.slug_field,
                "success_url": self.success_url,
                "cancel_url": self.cancel_url,
            }
        )
        return kwargs

    def list_view(self, request, *args, **kwargs):
        view_kwargs = self._get_default_view_kwargs()
        return self.list_view_class.as_view(
            form_class=self.search_form_class,
            list_display=self.list_display,
            ordering=self.list_ordering or self.list_display,
            template_name=self.list_template_name,
            **view_kwargs,
        )(request, *args, **kwargs)

    def add_view(self, request, *args, **kwargs):
        view_kwargs = self._get_single_object_view_kwargs()
        return self.add_view_class.as_view(
            form_class=self.form_class,
            template_name=self.add_template_name,
            no_cancel=self.no_cancel,
            **view_kwargs,
        )(request, *args, **kwargs)

    def edit_view(self, request, *args, **kwargs):
        view_kwargs = self._get_single_object_view_kwargs()
        return self.edit_view_class.as_view(
            form_class=self.form_class,
            template_name=self.edit_template_name,
            no_cancel=self.no_cancel,
            **view_kwargs,
        )(request, *args, **kwargs)

    def delete_view(self, request, *args, **kwargs):
        view_kwargs = self._get_single_object_view_kwargs()
        return self.delete_view_class.as_view(**view_kwargs)(request, *args, **kwargs)

    def delete_multiple_view(self, request, *args, **kwargs):
        view_kwargs = self._get_default_view_kwargs()
        return self.delete_multiple_view_class.as_view(**view_kwargs)(request, *args, **kwargs)

    def duplicate_view(self, request, *args, **kwargs):
        return self.duplicate_view_class.as_view(
            admin=self,
            model=self.model,
            pk_url_kwarg=self.pk_url_kwarg,
            slug_url_kwarg=self.slug_url_kwarg,
            slug_field=self.slug_field,
            async_=self.duplicate_async,
        )(request, *args, **kwargs)

    def export_view(self, request, *args, **kwargs):
        view_kwargs = self._get_default_view_kwargs()
        return self.serialize_view_class.as_view(**view_kwargs)(request, *args, **kwargs)

    def show_view(self, request, *args, **kwargs):
        view_kwargs = self._get_single_object_view_kwargs()
        return self.show_view_class.as_view(
            form_class=self.form_class,
            template_name=self.edit_template_name,
            no_cancel=self.no_cancel,
            **view_kwargs,
        )(request, *args, **kwargs)

    def csv_export_view(self, request, *args, **kwargs):
        view_kwargs = self._get_default_view_kwargs()
        return self.csv_export_view_class.as_view(
            csv_export_fields=self.csv_export_fields, **view_kwargs
        )(request, *args, **kwargs)

    def csv_import_view(self, request, *args, **kwargs):
        view_kwargs = self._get_default_view_kwargs()
        return self.csv_import_view_class.as_view(**view_kwargs)(request, *args, **kwargs)

    def csv_template_export_view(self, request, *args, **kwargs):
        view_kwargs = self._get_default_view_kwargs()
        return self.csv_template_export_view_class.as_view(**view_kwargs)(
            request, *args, **kwargs
        )

    def import_from_csv_view(self, request, *args, **kwargs):
        view_kwargs = self._get_default_view_kwargs()
        return self.csv_template_import_view_class.as_view(
            ordering=self.list_ordering or self.list_display, **view_kwargs
        )(request, *args, **kwargs)

    @property
    def csv_template_export_title(self) -> str:
        if self.model is None:
            raise ImproperlyConfigured("ModelAdmin has no model.")
        return f"Export CSV template for {self.model._meta.verbose_name} upload"

    @property
    def csv_import_title(self) -> str:
        if self.model is None:
            raise ImproperlyConfigured("ModelAdmin has no model.")
        return f"Import {self.model._meta.verbose_name} from CSV template"

    def get_queryset(self, request, **kwargs):
        if self.parent_field:
            parent_obj = self.parent.get_object(request, **kwargs)
            return self.queryset.filter(**{self.parent_field.name: parent_obj})
        return self.queryset

    def get_object(self, request, **kwargs):
        if self.url_kwarg not in kwargs:
            return None

        queryset = self.get_queryset(request, **kwargs)

        # Next, try looking up by primary key.
        pk = kwargs.get(self.pk_url_kwarg)
        if pk is not None:
            queryset = queryset.filter(pk=pk)

        # Next, try looking up by slug.
        slug = kwargs.get(self.slug_url_kwarg)
        if slug is not None and pk is None:
            queryset = queryset.filter(**{self.slug_field: slug})

        try:
            # Get the single item from the filtered queryset
            obj = queryset.get()
        except queryset.model.DoesNotExist as e:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": self.opts.verbose_name}
            ) from e
        return obj

    def get_initial(self, request, **kwargs):
        if self.parent_field:
            parent_obj = self.parent.get_object(request, **kwargs)
            return {self.parent_field.name: parent_obj}
        return {}

    def get_initial_object(self, request, **kwargs):
        """
        Return initial object passed to the form in add view.
        Django initializes this as Model() if instance is None,
        we're changing this behavior to assign parent object to instance.
        This way, we don't have to override Form.save() to assign it
        nor define extra form input for it.
        """
        instance = self.model()
        if self.parent_field:
            p_obj = self.parent.get_object(request, **kwargs)
            setattr(instance, self.parent_field.name, p_obj)
        return instance

    def delete(self, obj):
        obj.delete()

    def dispatch(self, view):
        if True not in self.get_model_perms(view.request).values():
            raise PermissionDenied()

    def get_breadcrumbs(self, request, obj=None, **kwargs):
        # filter out only parents pk_url_kwargs from kwargs
        list_kwargs = {}
        p = self.parent
        while p:
            list_kwargs[p.pk_url_kwarg] = kwargs.get(p.pk_url_kwarg)
            p = p.parent

        qs = self.queryset

        if self.parent_field:
            p_obj = self.parent.get_object(request, **list_kwargs)
            qs = qs.filter(**self.parent_field.get_forward_related_filter(p_obj))
            breadcrumbs = self.parent.get_breadcrumbs(request, p_obj, **list_kwargs)
        else:
            breadcrumbs = []

        objects_count = self._get_objects_count(qs)

        breadcrumbs += [
            (
                f"{self.model._meta.verbose_name_plural} ({humanize_number(objects_count)})",
                self.list_url(**list_kwargs),
            )
        ]

        if obj and obj.pk:
            breadcrumb_url = (
                self.edit_url if self.has_change_permission(request, obj=obj) else self.show_url
            )
            breadcrumbs += [(getattr(obj, "name", str(obj)), breadcrumb_url(**kwargs))]
        elif obj:
            breadcrumbs += [(_("New %s") % self.opts.verbose_name, self.add_url(**kwargs))]

        return breadcrumbs

    def get_cancel_url(self, view):
        pass

    def get_cancel_button_attrs(self, view) -> dict[str, Any]:
        return {}

    def get_success_url(self, view):
        pass

    def get_context_data(self, request, **kwargs):
        return {
            "page_title": self.get_page_title(request, **kwargs),
            "page_type": self.get_page_type(**kwargs),
        }

    def get_form_class(self, view):
        return self.form_class

    def get_form_kwargs(self, view):
        kwargs = {}
        if hasattr(self, "request") and hasattr(self.request, "csp_nonce"):
            kwargs.update({"csp_nonce": self.request.csp_nonce})
        return kwargs

    def get_formset_kwargs(self, view):
        return {}

    def get_search_form(self, view, form):
        return form

    def get_add_modal_form(self, view, **form_kwargs):
        if self.add_modal_fields:
            return modelform_factory(self.model, form=ModelForm, fields=self.add_modal_fields)(
                **form_kwargs
            )

    def get_duplicate_modal_form(self, view, **form_kwargs):
        if self.duplicate_modal_fields:
            return modelform_factory(
                self.model, form=ModelForm, fields=self.duplicate_modal_fields
            )(**form_kwargs)

    def get_add_model_form_kwargs(self, **kwargs) -> dict[str, Any]:
        return {}

    def get_duplicate_model_form_kwargs(self, **kwargs) -> dict[str, Any]:
        return {}

    def get_fieldsets(self, form=None):
        return self.fieldsets

    def get_formsets(self, obj=None):
        return self.formsets

    def get_menu_items(self, request, **kwargs):
        menu_items = []
        for admin in self.children:
            if admin.has_view_permission(request):
                list_url = ""
                if self.url_kwarg in kwargs:
                    list_url = admin.list_url(**kwargs)
                item_extra_html = admin.get_menu_item_extra_html(**kwargs) or ""
                item = MenuItem(list_url, admin.opts.verbose_name_plural, item_extra_html)
                menu_items.append(item)

        if menu_items:
            if self.url_kwarg in kwargs:
                main_url = (
                    self.edit_url(**kwargs)
                    if self.has_change_permission(request)
                    else self.show_url(**kwargs)
                )
            else:
                main_url = self.add_url(**kwargs)
            item_extra_html = self.get_menu_item_extra_html(**kwargs) or ""
            item = MenuItem(main_url, _("Main"), item_extra_html)
            menu_items = [item] + menu_items

        return menu_items

    def get_menu_item_extra_html(self, **kwargs):
        return None

    def get_list_actions(self, request, obj):
        obj_id = getattr(obj, self.slug_field or "id")
        actions = []
        if self.has_change_permission(request, obj):
            actions.append({"icon": "pencil", "label": _("Edit"), "url": f"{obj_id}/"})
        if self.has_view_permission(request, obj):
            actions.append({"icon": "eye", "label": _("Show"), "url": f"{obj_id}/show"})
        if self.can_duplicate and self.has_duplicate_permission(request, obj):
            action = {"icon": "copy", "label": _("Duplicate")}
            if self.duplicate_modal_fields:
                action["url"] = "#"
                action["attrs"] = {
                    "data-toggle": "modal",
                    "data-target": "#duplicate-modal",
                    "data-id": obj_id,
                }
            else:
                action["url"] = f"{obj_id}/duplicate/"
            actions.append(action)
        if self.has_export_permission(request):
            actions.append(
                {
                    "icon": "download",
                    "label": _("Export portable package"),
                    "url": f"export/?ids={obj_id}",
                    "attrs": {
                        "data-mixpanel-enabled": True,
                        "data-mixpanel-event-name": "export_portable_package",
                        "data-mixpanel-extra-prop-model-name": self.opts.verbose_name,
                        "data-mixpanel-extra-prop-event-object": getattr(obj, "name", obj_id),
                    },
                }
            )
        if self.has_delete_permission(request, obj):
            actions.append(
                {
                    "icon": "trash",
                    "label": _("Delete"),
                    "url": f"{obj_id}/delete/",
                    "attrs": {
                        "class": " modal-confirm-click",
                        "data-modal-type": "confirm-deletion",
                        "data-modal-number": "1",
                        "data-modal-title-1": _("Confirm deletion"),
                        "data-modal-body-1": _('Delete %s "%s"?')
                        % (self.opts.verbose_name, obj),
                    },
                }
            )
        return actions

    def get_model_perms(self, request):
        return {
            "add": self.has_add_permission(request),
            "change": self.has_change_permission(request),
            "delete": self.has_delete_permission(request),
            "duplicate": self.has_duplicate_permission(request),
            "view": self.has_view_permission(request),
        }

    def has_add_permission(self, request):
        opts = self.opts
        codename = get_permission_codename("add", opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename))

    def has_change_permission(self, request, obj=None):
        opts = self.opts
        codename = get_permission_codename("change", opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename))

    def has_delete_permission(self, request, obj=None):
        opts = self.opts
        codename = get_permission_codename("delete", opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename))

    def has_view_permission(self, request, obj=None):
        if self.has_change_permission(request, obj):
            return True
        opts = self.opts
        codename = get_permission_codename("view", opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename))

    def has_module_permission(self, request):
        return request.user.has_module_perms(self.opts.app_label)

    def has_duplicate_permission(self, request, obj=None):
        return self.has_change_permission(request, obj=obj)

    def has_import_permission(self, request, obj=None):
        return self.serialize_view_class is not None

    def has_export_permission(self, request, obj=None):
        return self.serialize_view_class is not None

    def get_page_title(self, request, **kwargs):
        title = ""
        if self.model:
            model_title = self.model._meta.verbose_name.title()
            if self.url_kwarg in kwargs:
                obj = self.get_object(request, **kwargs)
                title = "{} - {} | ".format(getattr(obj, "name", str(obj)), model_title)
            else:
                title = "{} list | ".format(model_title)

        return _("{}Printbox Dashboard {}".format(title, settings.PRINTBOX_SITE_NAME))

    def get_page_type(self, **kwargs) -> str:
        if self.model:
            verbose_name = self.model._meta.verbose_name or ""
            page_type = verbose_name.title()

            if self.url_kwarg not in kwargs:
                page_type += " list"

            return page_type

        return DEFAULT_PAGE_TYPE

    def handle_async_task_ready(self, request, task):
        if task.successful():
            messages.success(request, "Operation completed successfully.")
        elif task.failed():
            messages.error(request, "Operation failed.")

    @try_cached_as
    def _get_objects_count(self, queryset: QuerySet) -> int:
        if self.use_estimated_count:
            return count_estimate(queryset, precision=max(admin_settings.PAGINATION_CHOICES))
        return queryset.count()

    def _get_header_field_attrs(self, field_name: str) -> dict[str, str] | None:
        return None


class RenderField(Generic[_Model]):
    def __init__(self, field_name: str, admin: ModelAdmin, editable: bool = False):
        self.field_name: str = field_name
        self.admin: ModelAdmin = admin
        self.model_field: Field | ForeignObjectRel | GenericForeignKey | None = None
        self.admin_field: Callable[[Any], str] | None = getattr(
            self.admin, self.field_name, None
        )
        self.editable = editable
        model = self.admin.model

        with suppress(FieldDoesNotExist, AttributeError):
            if model is not None:
                self.model_field = model._meta.get_field(self.field_name)

    def get_value(self, obj: _Model):
        if field := self.admin_field:
            return field(obj) if callable(field) else field
        return getattr(obj, self.field_name)

    def get_field_ordering(self) -> StrOrPromise:
        if self.admin_field and hasattr(self.admin_field, "order_field"):
            return cast(StrOrPromise, self.admin_field.order_field)

        if self.model_field:
            return self.model_field.name

        return ""

    def get_label(self, form: _BaseForm | None = None) -> StrOrPromise:
        if self.admin_field and hasattr(self.admin_field, "label"):
            return cast(StrOrPromise, self.admin_field.label)

        form_field = form.fields.get(self.field_name) if form else None

        if form_field:
            return cast(StrOrPromise, form_field.label)

        if self.model_field and hasattr(self.model_field, "verbose_name"):
            return self.model_field.verbose_name

        return self.field_name

    def get_tooltip(self, obj: _Model) -> StrOrPromise | None:
        if (field := self.admin_field) and hasattr(field, "tooltip"):
            _tooltip = field.tooltip
            return cast(StrOrPromise, _tooltip(obj) if callable(_tooltip) else _tooltip)
        return None

    def __repr__(self):
        return f"{self.__class__.__name__} {self.field_name}"
