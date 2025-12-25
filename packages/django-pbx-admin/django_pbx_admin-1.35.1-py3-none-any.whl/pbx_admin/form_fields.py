import datetime
from typing import Optional

from django.core.exceptions import ValidationError
from django.forms.fields import DateTimeField, MultiValueField

from pbx_admin.widgets import DateTimePickerWidget, DateTimeRangePickerWidget


class DateTimePickerField(DateTimeField):
    widget = DateTimePickerWidget


class DateTimeRangePickerField(MultiValueField):
    widget = DateTimeRangePickerWidget

    def __init__(self, *args, **kwargs):
        fields = (DateTimePickerField(required=False), DateTimePickerField(required=False))
        super().__init__(fields, *args, **kwargs, require_all_fields=False)

    def compress(self, data_list: list[datetime.datetime]) -> Optional[list[datetime.datetime]]:
        if not data_list:
            return None

        begin_date, end_date = data_list
        if all(data_list) and begin_date > end_date:
            raise ValidationError("Invalid date range", "invalid-date-range")

        return data_list
