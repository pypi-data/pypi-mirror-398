import datetime
import json
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.forms import ModelForm, modelform_factory
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.test.utils import override_settings
from django.utils import timezone

from parameterized import parameterized

from pbx_admin.form_fields import DateTimeRangePickerField
from pbx_admin.templatetags.admin_tags import humanize_number
from pbx_admin.utils import is_from_trusted_network
from pbx_admin.views.base import AdminUpdateView
from pbx_admin.views.mixins import PaginationMixin
from pbx_admin.widgets import DateTimeRangePickerWidget


class AdminListViewTests(TestCase):
    def test_adjacent_pages(self):
        self.assertEqual(
            PaginationMixin._get_adjacent_pages(7, range(1, 12), 2), ([5, 6], [8, 9])
        )
        self.assertEqual(
            PaginationMixin._get_adjacent_pages(3, range(1, 7), 2), ([1, 2], [4, 5])
        )


class DateTimeRangePickerFieldTest(SimpleTestCase):
    def setUp(self) -> None:
        self.test_field = DateTimeRangePickerField()

    def test_valid_widget(self) -> None:
        self.assertIsInstance(self.test_field.widget, DateTimeRangePickerWidget)

    def test_valid_time_range(self) -> None:
        date_range = [
            timezone.now(),
            timezone.now() + datetime.timedelta(days=10),
        ]

        test_case = self.test_field.clean(date_range)

        self.assertEqual(date_range, test_case)

    def test_invalid_time_range(self) -> None:
        invalid_date_range = [
            timezone.now(),
            timezone.now() - datetime.timedelta(days=10),
        ]

        with self.assertRaisesMessage(ValidationError, "Invalid date range"):
            self.test_field.clean(invalid_date_range)


class TemplateTagsTests(TestCase):
    @parameterized.expand(
        (
            (0, "0"),
            (999, "999"),
            (1_000, "1K"),
            (99_999, "99K"),
            (100_000, "100K"),
            (324_324, "324K"),
            (1_000_000, "1M"),
            (1_888_000, "1.8M"),
        )
    )
    def test_humanize_number(self, num, expected):
        self.assertEqual(humanize_number(num), expected)


class NetworkTrustedTests(SimpleTestCase):
    def _create_request(self, ip):
        request = Mock()
        request.META = {"REMOTE_ADDR": ip}
        return request

    @override_settings(OAUTH_TRUSTED_IP_ADDRESSES=["192.168.1.100"])
    def test_individual_ip(self):
        self.assertTrue(is_from_trusted_network(self._create_request("192.168.1.100")))
        self.assertFalse(is_from_trusted_network(self._create_request("192.168.1.101")))

    @override_settings(OAUTH_TRUSTED_IP_ADDRESSES=["80.82.28.0/24"])
    def test_cidr_range(self):
        self.assertTrue(is_from_trusted_network(self._create_request("80.82.28.42")))
        self.assertFalse(is_from_trusted_network(self._create_request("80.82.29.1")))

    @override_settings(OAUTH_TRUSTED_IP_ADDRESSES=["192.168.1.100", "80.82.28.0/24"])
    def test_mixed(self):
        self.assertTrue(is_from_trusted_network(self._create_request("192.168.1.100")))
        self.assertTrue(is_from_trusted_network(self._create_request("80.82.28.42")))
        self.assertFalse(is_from_trusted_network(self._create_request("172.16.1.1")))

    @override_settings(OAUTH_TRUSTED_IP_ADDRESSES=["192.168.1.1"])
    def test_invalid(self):
        with self.assertLogs("pbx_admin.utils", level="WARNING") as cm:
            self.assertFalse(is_from_trusted_network(self._create_request("invalid")))
        self.assertIn("Invalid client IP address", cm.output[0])

    @override_settings(OAUTH_TRUSTED_IP_ADDRESSES=[])
    def test_empty_trusted_list(self):
        self.assertTrue(is_from_trusted_network(self._create_request("192.168.1.1")))

    @override_settings(OAUTH_TRUSTED_IP_ADDRESSES=["invalid", "192.168.1.100"])
    def test_invalid_trusted_range(self):
        with self.assertLogs("pbx_admin.utils", level="WARNING") as cm:
            self.assertTrue(is_from_trusted_network(self._create_request("192.168.1.100")))
        self.assertIn("Invalid trusted IP range", cm.output[0])

    @override_settings(OAUTH_TRUSTED_IP_ADDRESSES=["192.168.1.100", "10.0.0.0/8"])
    def test_forwarded_for_priority(self):
        request = Mock()
        request.META = {
            "HTTP_X_ORIGINAL_FORWARDED_FOR": "192.168.1.100",
            "HTTP_X_FORWARDED_FOR": "192.168.1.101",
            "REMOTE_ADDR": "192.168.1.102",
        }
        self.assertTrue(is_from_trusted_network(request))

        request.META = {
            "HTTP_X_FORWARDED_FOR": "10.0.0.5",
            "REMOTE_ADDR": "192.168.1.102",
        }
        self.assertTrue(is_from_trusted_network(request))

    @override_settings(OAUTH_TRUSTED_IP_ADDRESSES=["192.168.1.100"])
    def test_ip_list_first_item(self):
        request = Mock()
        request.META = {"HTTP_X_FORWARDED_FOR": "192.168.1.100, 192.168.1.101, 192.168.1.102"}
        self.assertTrue(is_from_trusted_network(request))

        request.META = {"HTTP_X_FORWARDED_FOR": "192.168.1.101, 192.168.1.100"}
        self.assertFalse(is_from_trusted_network(request))


class AdminUpdateViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.factory = RequestFactory()
        cls.user = User.objects.create(username="base_username")
        cls.user_form = modelform_factory(User, fields=["username"])

        cls.view = AdminUpdateView()
        cls.view.model = User
        cls.view.get_object = Mock(return_value=cls.user)
        cls.view.kwargs = {}
        cls.view.get_form_class = Mock(return_value=cls.user_form)
        cls.view.get_formsets = Mock(return_value=[])

    def setUp(self):
        super().setUp()
        self.mock_admin = Mock(
            opts=User._meta,
            parent_field=None,
            **{
                "get_form_class.return_value": ModelForm,
                "get_form_kwargs.return_value": {},
                "get_formset_kwargs.return_value": {},
                "get_fieldsets.return_value": [],
                "get_menu_items.return_value": [],
                "get_initial.return_value": {},
            },
        )

        self.view.admin = self.mock_admin

    def test_full_post_flow_updates_object_and_logs_old_fields(self):
        request = self.factory.post("/fake-url/", {"username": "new_username"})
        self.view.request = request

        def mock_form_valid_with_save(form, formsets=None):
            self.view.object = form.save()
            return HttpResponse()

        with (
            patch(
                "pbx_admin.views.base.AdminSingleObjectView.form_valid",
                side_effect=mock_form_valid_with_save,
            ),
            self.assertLogs("pbx_admin.views.base", level="INFO") as cm,
        ):
            self.view.post(request)

        log_message = cm.output[0]
        log_record = cm.records[0]
        old_object_fields = json.loads(log_record.old_object_fields)

        self.user.refresh_from_db()

        self.assertEqual(len(cm.output), 1)
        self.assertEqual("new_username", self.user.username)
        self.assertEqual("base_username", self.view.old_object_fields.get("username"))
        self.assertEqual("base_username", old_object_fields.get("username"))
        self.assertIn(f"Updated User {self.user.id}", log_message)
