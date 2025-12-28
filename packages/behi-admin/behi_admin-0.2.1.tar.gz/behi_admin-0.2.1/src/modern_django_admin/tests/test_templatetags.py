from django.template import Context, Template
from django.test import TestCase


class TemplateTagsTestCase(TestCase):
    def test_get_rtl_direction_tag(self):
        template = Template('{% load modern_admin %}{% get_rtl_direction as direction %}{{ direction }}')
        context = Context({})
        result = template.render(context)
        self.assertIn(result.strip(), ['ltr', 'rtl'])

    def test_get_theme_mode_tag(self):
        template = Template('{% load modern_admin %}{% get_theme_mode as theme %}{{ theme }}')
        context = Context({})
        result = template.render(context)
        self.assertIn(result.strip(), ['light', 'dark', 'system'])

    def test_get_primary_color_tag(self):
        template = Template('{% load modern_admin %}{% get_primary_color as color %}{{ color }}')
        context = Context({})
        result = template.render(context)
        self.assertTrue(result.strip().startswith('#'))

