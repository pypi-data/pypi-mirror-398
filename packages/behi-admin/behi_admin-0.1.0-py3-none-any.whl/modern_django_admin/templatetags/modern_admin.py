from django import template
from django.conf import settings
from modern_django_admin.conf import (
    get_rtl_direction,
    get_theme_mode,
    get_primary_color,
    get_accent_color,
    get_brand_logo,
    get_favicon,
    is_dark_mode_enabled,
    get_extra_css,
    get_extra_js,
)

register = template.Library()


@register.simple_tag
def get_rtl_direction():
    return get_rtl_direction()


@register.simple_tag
def get_theme_mode():
    return get_theme_mode()


@register.simple_tag
def get_primary_color():
    return get_primary_color()


@register.simple_tag
def get_accent_color():
    return get_accent_color()


@register.simple_tag
def get_brand_logo():
    return get_brand_logo()


@register.simple_tag
def get_favicon():
    return get_favicon()


@register.simple_tag
def is_dark_mode_enabled():
    return is_dark_mode_enabled()


@register.simple_tag
def get_extra_css():
    return get_extra_css()


@register.simple_tag
def get_extra_js():
    return get_extra_js()

