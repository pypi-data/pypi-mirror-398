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


def modern_admin_context(request):
    return {
        "modern_admin_direction": get_rtl_direction(),
        "modern_admin_theme": get_theme_mode(),
        "modern_admin_primary_color": get_primary_color(),
        "modern_admin_accent_color": get_accent_color(),
        "modern_admin_brand_logo": get_brand_logo(),
        "modern_admin_favicon": get_favicon(),
        "modern_admin_dark_mode_enabled": is_dark_mode_enabled(),
        "modern_admin_extra_css": get_extra_css(),
        "modern_admin_extra_js": get_extra_js(),
    }

