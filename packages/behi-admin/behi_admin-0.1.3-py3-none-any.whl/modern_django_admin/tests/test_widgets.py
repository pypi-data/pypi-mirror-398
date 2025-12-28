from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from modern_django_admin.widgets import (
    ModelCountWidget,
    QuickLinksWidget,
    RecentActionsWidget,
    WidgetRegistry,
)

User = get_user_model()


class WidgetRegistryTestCase(TestCase):
    def test_registry_registration(self):
        self.assertIn("count", WidgetRegistry.get_available_types())
        self.assertIn("recent_actions", WidgetRegistry.get_available_types())
        self.assertIn("quick_links", WidgetRegistry.get_available_types())

    def test_get_widget_class(self):
        widget_class = WidgetRegistry.get_widget_class("count")
        self.assertEqual(widget_class, ModelCountWidget)


class ModelCountWidgetTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        self.request = self.factory.get('/')
        self.request.user = self.user

    def test_model_count_widget_with_valid_config(self):
        from django.contrib import admin
        from modern_django_admin.admin import modern_admin_site

        if User not in modern_admin_site._registry:
            modern_admin_site.register(User, admin.ModelAdmin)

        config = {
            "app_label": "auth",
            "model_name": "user",
        }
        widget = ModelCountWidget(config)
        result = widget.render(self.request, modern_admin_site)

        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "count")
        self.assertIn("data", result)


class RecentActionsWidgetTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        self.request = self.factory.get('/')
        self.request.user = self.user

    def test_recent_actions_widget(self):
        from modern_django_admin.admin import modern_admin_site

        widget = RecentActionsWidget()
        result = widget.render(self.request, modern_admin_site)

        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "recent_actions")
        self.assertIn("data", result)
        self.assertIsInstance(result["data"], list)


class QuickLinksWidgetTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        self.request = self.factory.get('/')
        self.request.user = self.user

    def test_quick_links_widget(self):
        from modern_django_admin.admin import modern_admin_site

        config = {
            "links": [
                {"title": "Test Link", "url": "/test/", "icon": "🔗"},
            ]
        }
        widget = QuickLinksWidget(config)
        result = widget.render(self.request, modern_admin_site)

        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "quick_links")
        self.assertIn("data", result)
        self.assertEqual(len(result["data"]), 1)
