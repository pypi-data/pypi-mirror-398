import logging
from typing import Any, Type, TypeVar

from django.db.models import Model

__all__ = ["get_object_or_none"]

M = TypeVar("M", bound=Model)

logger = logging.getLogger("django.essentials")


def get_object_or_none(model: Type[M], *args: Any, **kwargs: Any) -> M | None:
    try:
        return model.objects.get(*args, **kwargs)
    except model.DoesNotExist:
        logger.warning(f"{model.__name__}.get({args}, {kwargs}) — object not found")

        return None

    except Exception as e:
        logger.exception(f"Error occurred while retrieving {model.__name__} with args={args}, kwargs={kwargs}")

        raise e
