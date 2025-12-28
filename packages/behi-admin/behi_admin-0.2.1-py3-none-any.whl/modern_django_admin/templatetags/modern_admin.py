from django import template

from modern_django_admin.conf import (
    get_rtl_direction as conf_get_rtl_direction,
    get_theme_mode as conf_get_theme_mode,
    get_primary_color as conf_get_primary_color,
    get_accent_color as conf_get_accent_color,
    get_brand_logo as conf_get_brand_logo,
    get_favicon as conf_get_favicon,
    is_dark_mode_enabled as conf_is_dark_mode_enabled,
    get_extra_css as conf_get_extra_css,
    get_extra_js as conf_get_extra_js,
)

register = template.Library()


@register.simple_tag
def get_rtl_direction():
    return conf_get_rtl_direction()


@register.simple_tag
def get_theme_mode():
    return conf_get_theme_mode()


@register.simple_tag
def get_primary_color():
    return conf_get_primary_color()


@register.simple_tag
def get_accent_color():
    return conf_get_accent_color()


@register.simple_tag
def get_brand_logo():
    return conf_get_brand_logo()


@register.simple_tag
def get_favicon():
    return conf_get_favicon()


@register.simple_tag
def is_dark_mode_enabled():
    return conf_is_dark_mode_enabled()


@register.simple_tag
def get_extra_css():
    return conf_get_extra_css()


@register.simple_tag
def get_extra_js():
    return conf_get_extra_js()


@register.simple_tag
def get_density():
    from modern_django_admin.conf import get_density
    return get_density()

