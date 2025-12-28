from django.test import TestCase, override_settings

from modern_django_admin.conf import (
    get_rtl_direction,
    get_theme_mode,
    get_primary_color,
    get_accent_color,
    is_dark_mode_enabled,
)


class ConfTestCase(TestCase):
    def test_get_rtl_direction_default(self):
        direction = get_rtl_direction()
        self.assertIn(direction, ['ltr', 'rtl'])

    @override_settings(MODERN_ADMIN_RTL_FORCE=True)
    def test_get_rtl_direction_forced(self):
        direction = get_rtl_direction()
        self.assertEqual(direction, 'rtl')

    @override_settings(MODERN_ADMIN_RTL_FORCE=False)
    def test_get_rtl_direction_forced_ltr(self):
        direction = get_rtl_direction()
        self.assertEqual(direction, 'ltr')

    def test_get_theme_mode_default(self):
        mode = get_theme_mode()
        self.assertIn(mode, ['light', 'dark', 'system'])

    @override_settings(MODERN_ADMIN_DEFAULT_THEME='dark')
    def test_get_theme_mode_custom(self):
        mode = get_theme_mode()
        self.assertEqual(mode, 'dark')

    def test_get_primary_color_default(self):
        color = get_primary_color()
        self.assertIsInstance(color, str)
        self.assertTrue(color.startswith('#'))

    @override_settings(MODERN_ADMIN_PRIMARY_COLOR='#ff0000')
    def test_get_primary_color_custom(self):
        color = get_primary_color()
        self.assertEqual(color, '#ff0000')

    def test_get_accent_color_default(self):
        color = get_accent_color()
        self.assertIsInstance(color, str)
        self.assertTrue(color.startswith('#'))

    def test_is_dark_mode_enabled_default(self):
        enabled = is_dark_mode_enabled()
        self.assertIsInstance(enabled, bool)

