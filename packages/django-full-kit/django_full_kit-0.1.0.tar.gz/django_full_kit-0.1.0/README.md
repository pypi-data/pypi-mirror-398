# Django Full Kit

A reusable Django package providing ready-to-use models, admin configurations, and utilities for common project needs such as users and articles.Powered by developlab

---

## Features

* **UserProfile**: Optional extension for Django's `AUTH_USER_MODEL`.
* **Article model**: Generic content model for blogs, news, or docs.
* **Admin ready**: Preconfigured admin for users and articles.
* **Utilities**: Helper functions for safer attribute access and common tasks.
* **TimeStampedModel**: Base abstract model with `created_at` and `updated_at`.

---

## Installation

```bash
pip install django-full-kit
```

---

## Usage

Add the app to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    "full_kit",
]
```

Run migrations for the included models:

```bash
python manage.py makemigrations
python manage.py migrate
```

Import models where needed:

```python
from django_full_kit.models import Article, UserProfile
```

Register in admin (optional if using default registration):

```python
from django.contrib import admin
import django_full_kit.admin
```

---

## Testing

Install test dependencies:

```bash
pip install .[dev]
```

Run tests with pytest:

```bash
pytest
```

---

## License

[MIT](LICENSE)