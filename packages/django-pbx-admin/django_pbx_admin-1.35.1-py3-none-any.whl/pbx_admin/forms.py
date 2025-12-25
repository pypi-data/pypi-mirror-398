import logging

from django import forms

log = logging.getLogger(__name__)


class SearchForm(forms.ModelForm):
    json_fields: dict[str, str] = {}
    annotated_fields: dict[str, str] = {}

    def __init__(self, *args, **kwargs):
        if "csp_nonce" in kwargs:
            kwargs.pop("csp_nonce")
        super().__init__(*args, **kwargs)
        for fname in self.fields:
            self.fields[fname].required = False
            self.fields[fname].initial = None
            if isinstance(self.fields[fname], forms.BooleanField):
                self.fields[fname] = forms.NullBooleanField(
                    label=self.fields[fname].label, required=False
                )

    def get_filters(self):
        filters = {}
        if self.is_valid():
            for f in self.fields:
                val = self.cleaned_data.get(f)
                if val is not None and val != "":
                    filters[self._get_lookup(f)] = val
        return filters

    def _get_lookup(self, field_name: str) -> str:
        extra_fields = self.json_fields | self.annotated_fields
        if field_name in extra_fields:
            return f"{extra_fields[field_name]}__icontains"

        field = self.fields.get(field_name)

        if isinstance(field, forms.UUIDField):
            # optimization: do simple lookup on UUID field
            # otherwise it is treated as a CharField and adds icontains
            # which is expensive on huge tables such as Project
            return field_name

        if isinstance(field, forms.CharField):
            return f"{field_name}__icontains"

        return field_name

    def _get_validation_exclusions(self):
        # ignore uuid in validation to allow filtering using modelform
        return super()._get_validation_exclusions() + ["uuid"]

    def _post_clean(self):
        # _post_clean validates model instance - we don't need it since there
        # is no instance in search_form
        pass
