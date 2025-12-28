# Django Essentials

Essential utilities for Django that make common tasks easier and more efficient.

## Features

- **Admin Utilities**: Enhanced admin interface components including FancyBox image display
- **Model Utilities**: Helper functions for common model operations

## Installation

```bash
pip install django-essentials-kit
```

## Quick Start

### Admin Utilities

The library provides `MediaFancybox` class and `get_fancybox_image` function for enhanced image display in Django admin:

```python
from django.contrib import admin
from django_essentials_kit.admin import MediaFancybox, get_fancybox_image
from .models import YourModel

@admin.register(YourModel)
class YourModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'image_preview']

    class Media(MediaFancybox):
        ...

    def image_preview(self, obj) -> SafeString:
        return get_fancybox_image(obj, 'image_field', w=60, h=60)
```

### Model Utilities

Use `get_object_or_none` for safe object retrieval:

```python
from django_essentials_kit.utils import get_object_or_none

from .models import YourModel

# Instead of try/except blocks
obj = get_object_or_none(YourModel, pk=1)
if obj:
    ...  # Do something with obj
```

## Requirements

- Python 3.8+
- Django 3.2+

## License

MIT License - see LICENSE file for details.
