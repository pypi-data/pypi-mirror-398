# Behi Admin | بهی ادمین

<div align="center">

**یک پکیج مدرن و کامل برای Django Admin Panel با UI/UX حرفه‌ای**  
**A modern, responsive, RTL/LTR-ready Django Admin Panel with enhanced UI/UX**

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Django Version](https://img.shields.io/badge/django-3.2%2C%204.2%2C%205.0-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyPI](https://img.shields.io/pypi/v/behi-admin)](https://pypi.org/project/behi-admin/)
[![Demo](https://img.shields.io/badge/demo-GitHub%20Pages-blue)](https://yourusername.github.io/behi-admin/)

[English](#english) | [فارسی](#فارسی)

</div>

---

<div id="english"></div>

# English

## 📋 Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Documentation](#documentation)
- [Demo Project](#demo-project)
- [Compatibility](#compatibility)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

### 🎨 Modern UI/UX

- Minimal and professional design
- Fully responsive interface
- Complete support for mobile, tablet, and desktop
- Collapsible sidebar
- Smart navigation

### 🌐 RTL/LTR Support

- Automatic text direction detection based on language
- Full support for Persian and Arabic
- Manual direction setting (RTL Force)
- Appropriate fonts for different languages

### 🌙 Dark Mode

- Complete dark theme
- Automatic system theme detection
- Manual theme switching
- Settings saved in LocalStorage

### 🔍 Global Search

- Search across all registered models
- Respects access permissions
- Grouped results display
- Direct link to change page

### 📊 Customizable Dashboard

- Configurable widgets
- Recent actions display
- Statistical cards
- Quick links

### 🌍 Multi-language

- Support for 6 languages: English, Persian, Arabic, Spanish, Italian, German
- Easy to add new languages
- Uses Django i18n

### 🔒 Security

- Complete Django permission system preservation
- CSRF Protection
- Permission-aware search
- Controlled access

### ⚡ Performance

- Query optimization
- Lazy Loading
- Appropriate caching
- Smart pagination

## 📦 Installation

### Install from PyPI

```bash
pip install behi-admin
```

### Install from Source

```bash
git clone https://github.com/yourusername/behi-admin.git
cd behi-admin
pip install -e .
```

## 🚀 Quick Start

### 1. Add to INSTALLED_APPS

In your `settings.py`:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'modern_django_admin',
    # ... your other apps
]
```

### 2. Update URLs

In your `urls.py`:

```python
from django.urls import path
from modern_django_admin.admin import modern_admin_site

urlpatterns = [
    path('admin/', modern_admin_site.urls),
    # ... your other URLs
]
```

### 3. Register Your Models

Your models must be registered in Django Admin:

```python
from django.contrib import admin
from .models import MyModel

@admin.register(MyModel)
class MyModelAdmin(admin.ModelAdmin):
    list_display = ['field1', 'field2']
    search_fields = ['field1']
    list_filter = ['field2']
```

### 4. Run Migrations and Collect Static

```bash
python manage.py migrate
python manage.py collectstatic
```

### 5. Access Admin Panel

Open your browser and go to `http://127.0.0.1:8000/admin/`.

## ⚙️ Configuration

You can customize the admin panel by adding these settings to `settings.py`:

### Basic Settings

```python
MODERN_ADMIN_SITE_TITLE = "My Admin Panel"
MODERN_ADMIN_SITE_HEADER = "My Site Administration"
MODERN_ADMIN_INDEX_TITLE = "Welcome to My Admin"
```

### Visual Settings

```python
MODERN_ADMIN_BRAND_LOGO = "/static/logo.png"
MODERN_ADMIN_FAVICON = "/static/favicon.ico"
MODERN_ADMIN_PRIMARY_COLOR = "#2563eb"
MODERN_ADMIN_ACCENT_COLOR = "#10b981"
```

### Dark Mode

```python
MODERN_ADMIN_ENABLE_DARK_MODE = True
MODERN_ADMIN_DEFAULT_THEME = "light"  # or "dark" or "system"
```

### Global Search

```python
MODERN_ADMIN_GLOBAL_SEARCH_ENABLED = True
MODERN_ADMIN_GLOBAL_SEARCH_MODELS_WHITELIST = [
    "app1.Model1",
    "app2.Model2",
]
```

### Dashboard

```python
MODERN_ADMIN_DASHBOARD_WIDGETS = [
    {
        "type": "count",
        "app_label": "myapp",
        "model_name": "mymodel",
        "title": "Total Items",
    },
]
```

### RTL/LTR

```python
MODERN_ADMIN_RTL_FORCE = None  # None for auto-detect, True/False for forced
```

### Custom CSS/JS

```python
MODERN_ADMIN_EXTRA_CSS = [
    "/static/custom-admin.css",
]

MODERN_ADMIN_EXTRA_JS = [
    "/static/custom-admin.js",
]
```

## 📚 Documentation

### Django Admin Compatibility

This package is compatible with all Django Admin features:

- ✅ `list_display`
- ✅ `list_filter`
- ✅ `search_fields`
- ✅ `readonly_fields`
- ✅ `fieldsets`
- ✅ `inlines` (TabularInline, StackedInline)
- ✅ `actions`
- ✅ `autocomplete_fields`
- ✅ `date_hierarchy`
- ✅ `ordering`
- ✅ `list_editable`
- ✅ `raw_id_fields`
- ✅ And more...

### Customizing Templates

You can override package templates in your project:

```
your_project/
└── templates/
    └── admin/
        ├── base.html
        ├── index.html
        ├── change_list.html
        └── change_form.html
```

### Adding New Languages

1. Create a new directory in `locale/`
2. Add translation files
3. Compile: `python manage.py compilemessages`
4. Add language to `LANGUAGES` in settings

## 🎬 Demo & Live Examples

### 🚀 Live Demo

- **📱 GitHub Pages Demo**: [View Live Demo Page](https://yourusername.github.io/behi-admin/)
- **💻 Demo Project**: See `examples/demo_project/` for a complete working example with setup instructions
- **📦 PyPI Package**: [View on PyPI](https://pypi.org/project/behi-admin/)

### 📖 Demo Project

A complete sample project is available in `examples/demo_project/` which includes:

- Multiple models (Book, Author, Category, Review)
- Complete settings
- Usage of various Admin features

To run the demo:

```bash
cd examples/demo_project
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## 🔧 Compatibility

### Supported Versions

- **Django**: 3.2, 4.2, 5.0+
- **Python**: 3.9, 3.10, 3.11, 3.12

### Browsers

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## 🛠️ Development

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Linting

```bash
ruff check src/
ruff format src/
```

### Build Package

```bash
python -m build
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 Testing Checklist

Before using in production:

- [ ] Test on Django 3.2, 4.2, 5.0
- [ ] Test on Python 3.9+
- [ ] Test RTL (Persian/Arabic)
- [ ] Test Dark Mode
- [ ] Test Global Search
- [ ] Test Dashboard Widgets
- [ ] Test on mobile
- [ ] Test performance
- [ ] Test security

## 🐛 Bug Reports

If you find a bug, please open an Issue on GitHub.

## 💡 Ideas and Suggestions

If you have ideas or suggestions, we'd love to hear them!

## 📄 License

This project is released under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Thanks to everyone who contributed to building this project.

## 🔗 Useful Links

- [Django Documentation](https://docs.djangoproject.com/)
- [Django Admin Documentation](https://docs.djangoproject.com/en/stable/ref/contrib/admin/)
- [Issue Tracker](https://github.com/yourusername/behi-admin/issues)
- [Changelog](CHANGELOG.md)

---

<div id="فارسی"></div>

# فارسی

## 📋 فهرست مطالب

- [ویژگی‌ها](#ویژگی‌ها-1)
- [نصب](#نصب)
- [راه‌اندازی سریع](#راه‌اندازی-سریع)
- [پیکربندی](#پیکربندی)
- [مستندات کامل](#مستندات-کامل)
- [نمونه پروژه](#نمونه-پروژه)
- [سازگاری](#سازگاری)
- [مشارکت](#مشارکت)
- [مجوز](#مجوز)

## ✨ ویژگی‌ها

### 🎨 رابط کاربری مدرن

- طراحی مینیمال و حرفه‌ای
- رابط کاربری کاملاً واکنش‌گرا (Responsive)
- پشتیبانی کامل از موبایل، تبلت و دسکتاپ
- Sidebar قابل جمع‌شدن
- Navigation هوشمند

### 🌐 پشتیبانی RTL/LTR

- تشخیص خودکار جهت متن بر اساس زبان
- پشتیبانی کامل از فارسی و عربی
- قابلیت تنظیم دستی جهت (RTL Force)
- فونت‌های مناسب برای زبان‌های مختلف

### 🌙 حالت تاریک (Dark Mode)

- حالت تاریک کامل
- تشخیص خودکار تم سیستم
- امکان تغییر دستی تم
- ذخیره تنظیمات در LocalStorage

### 🔍 جستجوی سراسری

- جستجو در تمام مدل‌های ثبت‌شده
- احترام به مجوزهای دسترسی
- نمایش نتایج گروه‌بندی شده
- لینک مستقیم به صفحه تغییر

### 📊 داشبورد سفارشی

- ویجت‌های قابل تنظیم
- نمایش آخرین فعالیت‌ها
- کارت‌های آماری
- لینک‌های سریع

### 🌍 چندزبانه

- پشتیبانی از 6 زبان: انگلیسی، فارسی، عربی، اسپانیایی، ایتالیایی، آلمانی
- امکان افزودن زبان‌های جدید
- استفاده از Django i18n

### 🔒 امنیت

- حفظ کامل سیستم مجوزهای Django
- CSRF Protection
- Permission-aware search
- دسترسی کنترل شده

### ⚡ عملکرد

- بهینه‌سازی Query ها
- Lazy Loading
- Cache مناسب
- Pagination هوشمند

## 📦 نصب

### نصب از PyPI

```bash
pip install behi-admin
```

### نصب از منبع

```bash
git clone https://github.com/yourusername/behi-admin.git
cd behi-admin
pip install -e .
```

## 🚀 راه‌اندازی سریع

### 1. افزودن به INSTALLED_APPS

در فایل `settings.py`:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'modern_django_admin',
    # سایر اپلیکیشن‌های شما
]
```

### 2. تنظیم URLs

در فایل `urls.py`:

```python
from django.urls import path
from modern_django_admin.admin import modern_admin_site

urlpatterns = [
    path('admin/', modern_admin_site.urls),
    # سایر URL های شما
]
```

### 3. ثبت مدل‌ها

مدل‌های شما باید در Django Admin ثبت شوند:

```python
from django.contrib import admin
from .models import MyModel

@admin.register(MyModel)
class MyModelAdmin(admin.ModelAdmin):
    list_display = ['field1', 'field2']
    search_fields = ['field1']
    list_filter = ['field2']
```

### 4. اجرای Migration و Collect Static

```bash
python manage.py migrate
python manage.py collectstatic
```

### 5. دسترسی به پنل ادمین

مرورگر خود را باز کنید و به `http://127.0.0.1:8000/admin/` بروید.

## ⚙️ پیکربندی

می‌توانید با افزودن تنظیمات زیر به `settings.py` پنل ادمین را شخصی‌سازی کنید:

### تنظیمات اصلی

```python
MODERN_ADMIN_SITE_TITLE = "پنل مدیریت"
MODERN_ADMIN_SITE_HEADER = "مدیریت سایت"
MODERN_ADMIN_INDEX_TITLE = "خوش آمدید به پنل مدیریت"
```

### تنظیمات بصری

```python
MODERN_ADMIN_BRAND_LOGO = "/static/logo.png"
MODERN_ADMIN_FAVICON = "/static/favicon.ico"
MODERN_ADMIN_PRIMARY_COLOR = "#2563eb"
MODERN_ADMIN_ACCENT_COLOR = "#10b981"
```

### حالت تاریک

```python
MODERN_ADMIN_ENABLE_DARK_MODE = True
MODERN_ADMIN_DEFAULT_THEME = "light"  # یا "dark" یا "system"
```

### جستجوی سراسری

```python
MODERN_ADMIN_GLOBAL_SEARCH_ENABLED = True
MODERN_ADMIN_GLOBAL_SEARCH_MODELS_WHITELIST = [
    "app1.Model1",
    "app2.Model2",
]
```

### داشبورد

```python
MODERN_ADMIN_DASHBOARD_WIDGETS = [
    {
        "type": "count",
        "app_label": "myapp",
        "model_name": "mymodel",
        "title": "تعداد آیتم‌ها",
    },
]
```

### RTL/LTR

```python
MODERN_ADMIN_RTL_FORCE = None  # None برای تشخیص خودکار، True/False برای اجباری
```

### CSS/JS سفارشی

```python
MODERN_ADMIN_EXTRA_CSS = [
    "/static/custom-admin.css",
]

MODERN_ADMIN_EXTRA_JS = [
    "/static/custom-admin.js",
]
```

## 📚 مستندات کامل

### سازگاری با Django Admin

این پکیج با تمام ویژگی‌های Django Admin سازگار است:

- ✅ `list_display`
- ✅ `list_filter`
- ✅ `search_fields`
- ✅ `readonly_fields`
- ✅ `fieldsets`
- ✅ `inlines` (TabularInline, StackedInline)
- ✅ `actions`
- ✅ `autocomplete_fields`
- ✅ `date_hierarchy`
- ✅ `ordering`
- ✅ `list_editable`
- ✅ `raw_id_fields`
- ✅ و سایر ویژگی‌ها

### شخصی‌سازی Template ها

می‌توانید template های پکیج را در پروژه خود override کنید:

```
your_project/
└── templates/
    └── admin/
        ├── base.html
        ├── index.html
        ├── change_list.html
        └── change_form.html
```

### افزودن زبان جدید

1. فایل `.po` جدید در `locale/` ایجاد کنید
2. ترجمه‌ها را اضافه کنید
3. فایل را compile کنید: `python manage.py compilemessages`
4. زبان را به `LANGUAGES` در settings اضافه کنید

## 🎬 Demo و نمونه‌های زنده

### 🚀 Demo زنده

- **📱 GitHub Pages Demo**: [مشاهده صفحه Demo](https://yourusername.github.io/behi-admin/)
- **💻 پروژه نمونه**: `examples/demo_project/` را برای یک نمونه کامل با راهنمای نصب ببینید
- **📦 پکیج PyPI**: [مشاهده در PyPI](https://pypi.org/project/behi-admin/)

### 📖 نمونه پروژه

یک پروژه نمونه کامل در `examples/demo_project/` موجود است که شامل:

- چندین مدل (Book, Author, Category, Review)
- تنظیمات کامل
- استفاده از ویژگی‌های مختلف Admin

برای اجرای نمونه:

```bash
cd examples/demo_project
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## 🔧 سازگاری

### نسخه‌های پشتیبانی شده

- **Django**: 3.2, 4.2, 5.0+
- **Python**: 3.9, 3.10, 3.11, 3.12

### مرورگرها

- Chrome (آخرین نسخه)
- Firefox (آخرین نسخه)
- Safari (آخرین نسخه)
- Edge (آخرین نسخه)

## 🛠️ توسعه

### نصب وابستگی‌های توسعه

```bash
pip install -e ".[dev]"
```

### اجرای تست‌ها

```bash
pytest
```

### Linting

```bash
ruff check src/
ruff format src/
```

### ساخت بسته

```bash
python -m build
```

## 🤝 مشارکت

مشارکت‌های شما خوش آمدید! لطفاً:

1. Fork کنید
2. یک branch جدید ایجاد کنید (`git checkout -b feature/amazing-feature`)
3. تغییرات را commit کنید (`git commit -m 'Add amazing feature'`)
4. به branch push کنید (`git push origin feature/amazing-feature`)
5. یک Pull Request باز کنید

## 📝 چک‌لیست تست

قبل از استفاده در production:

- [ ] تست روی Django 3.2, 4.2, 5.0
- [ ] تست روی Python 3.9+
- [ ] تست RTL (فارسی/عربی)
- [ ] تست Dark Mode
- [ ] تست Global Search
- [ ] تست Dashboard Widgets
- [ ] تست روی موبایل
- [ ] تست Performance
- [ ] تست Security

## 🐛 گزارش باگ

اگر مشکلی پیدا کردید، لطفاً یک Issue در GitHub باز کنید.

## 💡 ایده‌ها و پیشنهادات

اگر ایده یا پیشنهادی دارید، خوشحال می‌شویم که بشنویم!

## 📄 مجوز

این پروژه تحت مجوز MIT منتشر شده است. برای جزئیات بیشتر فایل [LICENSE](LICENSE) را ببینید.

## 🙏 تشکر

از تمام کسانی که در ساخت این پروژه مشارکت کرده‌اند تشکر می‌کنیم.

## 🔗 لینک‌های مفید

- [Django Documentation](https://docs.djangoproject.com/)
- [Django Admin Documentation](https://docs.djangoproject.com/en/stable/ref/contrib/admin/)
- [Issue Tracker](https://github.com/yourusername/behi-admin/issues)
- [Changelog](CHANGELOG.md)

---

<div align="center">

ساخته شده با ❤️ برای جامعه Django  
Made with ❤️ for the Django Community

</div>
