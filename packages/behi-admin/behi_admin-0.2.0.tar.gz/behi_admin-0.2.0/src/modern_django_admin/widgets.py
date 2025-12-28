from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _


class Widget:
    widget_type = None
    default_config = {}

    def __init__(self, config=None):
        self.config = {**self.default_config, **(config or {})}

    def get_data(self, request, admin_site):
        raise NotImplementedError("Subclasses must implement get_data()")

    def render(self, request, admin_site):
        data = self.get_data(request, admin_site)
        if data is None:
            return None
        return {
            "type": self.widget_type,
            "title": self.config.get("title", ""),
            "data": data,
        }


class ModelCountWidget(Widget):
    widget_type = "count"
    default_config = {
        "app_label": None,
        "model_name": None,
        "title": None,
    }

    def get_data(self, request, admin_site):
        app_label = self.config.get("app_label")
        model_name = self.config.get("model_name")

        if not app_label or not model_name:
            raise ImproperlyConfigured("ModelCountWidget requires app_label and model_name")

        try:
            model = apps.get_model(app_label, model_name)
            if model is None:
                return None

            has_permission = False
            if model in admin_site._registry:
                model_admin = admin_site._registry[model]
                has_permission = model_admin.has_view_permission(request)
            else:
                has_permission = request.user.is_superuser or request.user.has_perm(f"{app_label}.view_{model_name}")

            if has_permission:
                count = model.objects.count()
                verbose_name_plural = model._meta.verbose_name_plural
                return {
                    "count": count,
                    "label": self.config.get("title") or verbose_name_plural,
                    "url": f"/admin/{app_label}/{model_name}/",
                }
        except (LookupError, AttributeError):
            pass

        return None


class RecentActionsWidget(Widget):
    widget_type = "recent_actions"
    default_config = {
        "limit": 10,
        "title": _("Recent Actions"),
    }

    def get_data(self, request, admin_site):
        from django.contrib.admin.models import LogEntry

        limit = self.config.get("limit", 10)
        actions = LogEntry.objects.select_related("user", "content_type").order_by("-action_time")[:limit]

        return [
            {
                "action_time": action.action_time.isoformat(),
                "user": action.user.get_full_name() or action.user.username,
                "content_type": action.content_type.model,
                "object_repr": action.object_repr,
                "action_flag": action.get_action_flag_display(),
                "change_message": action.change_message,
            }
            for action in actions
        ]


class QuickLinksWidget(Widget):
    widget_type = "quick_links"
    default_config = {
        "links": [],
        "title": _("Quick Links"),
    }

    def get_data(self, request, admin_site):
        links = self.config.get("links", [])
        return [
            {
                "title": link.get("title"),
                "url": link.get("url"),
                "icon": link.get("icon", ""),
            }
            for link in links
        ]


class WidgetRegistry:
    _registry = {}

    @classmethod
    def register(cls, widget_class):
        if not issubclass(widget_class, Widget):
            raise TypeError("Widget must be a subclass of Widget")
        cls._registry[widget_class.widget_type] = widget_class
        return widget_class

    @classmethod
    def get_widget_class(cls, widget_type):
        return cls._registry.get(widget_type)

    @classmethod
    def get_available_types(cls):
        return list(cls._registry.keys())


WidgetRegistry.register(ModelCountWidget)
WidgetRegistry.register(RecentActionsWidget)
WidgetRegistry.register(QuickLinksWidget)

