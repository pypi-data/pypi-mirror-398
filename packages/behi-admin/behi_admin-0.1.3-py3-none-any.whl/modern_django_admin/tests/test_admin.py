from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from modern_django_admin.admin import ModernAdminSite

User = get_user_model()


class ModernAdminSiteTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        self.client.login(username='testuser', password='testpass123')
        self.admin_site = ModernAdminSite()

    def test_admin_site_initialization(self):
        self.assertIsInstance(self.admin_site, ModernAdminSite)
        self.assertEqual(self.admin_site.name, "modern_admin")

    def test_admin_index_view(self):
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)

    def test_global_search_view(self):
        response = self.client.get('/admin/global-search/?q=test')
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.json())

    def test_dashboard_data_view(self):
        response = self.client.get('/admin/dashboard-data/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('widgets', data)
        self.assertIn('recent_actions', data)


class AdminSiteIntegrationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        self.client.login(username='testuser', password='testpass123')

    def test_admin_login_required(self):
        self.client.logout()
        response = self.client.get('/admin/')
        self.assertRedirects(response, '/admin/login/?next=/admin/')

    def test_global_search_permission_check(self):
        self.client.logout()
        response = self.client.get('/admin/global-search/?q=test')
        self.assertRedirects(response, '/admin/login/?next=/admin/global-search/')

