from django.conf import settings
from django.utils.translation import get_language


def get_density():
    return getattr(settings, "MODERN_ADMIN_DENSITY", "comfortable")


def get_rtl_direction():
    force_rtl = getattr(settings, "MODERN_ADMIN_RTL_FORCE", None)
    if force_rtl is not None:
        return "rtl" if force_rtl else "ltr"

    language = get_language()
    rtl_languages = ["ar", "fa", "he", "ur"]
    if language and len(language) >= 2:
        lang_code = language[:2].lower()
        return "rtl" if lang_code in rtl_languages else "ltr"

    return "ltr"


def get_theme_mode():
    return getattr(settings, "MODERN_ADMIN_DEFAULT_THEME", "light")


def get_primary_color():
    return getattr(settings, "MODERN_ADMIN_PRIMARY_COLOR", "#2563eb")


def get_accent_color():
    return getattr(settings, "MODERN_ADMIN_ACCENT_COLOR", "#10b981")


def get_brand_logo():
    return getattr(settings, "MODERN_ADMIN_BRAND_LOGO", None)


def get_favicon():
    return getattr(settings, "MODERN_ADMIN_FAVICON", None)


def is_dark_mode_enabled():
    return getattr(settings, "MODERN_ADMIN_ENABLE_DARK_MODE", True)


def get_extra_css():
    return getattr(settings, "MODERN_ADMIN_EXTRA_CSS", [])


def get_extra_js():
    return getattr(settings, "MODERN_ADMIN_EXTRA_JS", [])

