from django.urls import path
from django.contrib import admin
from modern_django_admin.admin import modern_admin_site

urlpatterns = [
    path("admin/", modern_admin_site.urls),
]

