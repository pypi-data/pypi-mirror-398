from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class SmokeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )

    def test_login_page(self):
        response = self.client.get('/admin/login/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'login')

    def test_index_page(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')

    def test_global_search_endpoint(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/admin/global-search/?q=test')
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.json())

    def test_dashboard_data_endpoint(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/admin/dashboard-data/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('widgets', response.json())

    def test_logout_redirect(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post('/admin/logout/')
        self.assertIn(response.status_code, [200, 302])

    def test_permission_required(self):
        response = self.client.get('/admin/')
        self.assertRedirects(response, '/admin/login/?next=/admin/')


