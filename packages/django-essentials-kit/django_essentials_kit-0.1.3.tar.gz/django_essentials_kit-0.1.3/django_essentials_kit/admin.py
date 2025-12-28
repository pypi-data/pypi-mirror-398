from typing import TypeVar

from django.db.models import ImageField, Model
from django.utils.safestring import mark_safe

__all__ = ["MediaFancybox", "get_fancybox_image"]

M = TypeVar("M", bound=Model)
IMAGE_FIELD = TypeVar("IMAGE_FIELD", bound=ImageField)


class MediaFancybox:
    js = (
        "https://code.jquery.com/jquery-latest.min.js",
        "https://ajax.googleapis.com/ajax/libs/jqueryui/1.8.24/jquery-ui.min.js",
        "https://cdn.jsdelivr.net/gh/fancyapps/fancybox@3.5.7/dist/jquery.fancybox.min.js",
    )
    css = {"screen": ("https://cdn.jsdelivr.net/gh/fancyapps/fancybox@3.5.7/dist/jquery.fancybox.min.css",)}


@mark_safe
def get_fancybox_image(
    obj: M,
    field: str,
    w: int = 40,
    h: int = 40,
    data_name="images",
    preview_field: str | None = None,
) -> str:
    value: IMAGE_FIELD = getattr(obj, field, None)
    if not value:
        return "-"

    preview: IMAGE_FIELD | None = getattr(obj, preview_field, value)
    if not isinstance(preview, ImageField):
        preview = value

    try:
        return (
            f"<a data-fancybox='{data_name}' href='{value.url}'><img src='{preview.url}' width='{w}' height='{h}'></a>"
        )
    except Exception:
        return "-"
