from django_filters import filterset
from drf_yasg import openapi

__all__ = ["SerializerViewSetMixin", "generate_filter_parameters"]


class SerializerViewSetMixin:
    serializer_class_map = {
        # "create": None,
        # "list": None,
        # "retrieve": None,
        # "update": None,
        # "partial_update": None,
    }

    def get_serializer_class(self):
        serializer = self.serializer_class_map.get(self.action, None)
        self.serializer_class = serializer or self.serializer_class

        return self.serializer_class


def generate_filter_parameters(filter_set_class, ordering_fields: list[str] = None) -> list:
    parameters = []

    for name, kind in filter_set_class.base_filters.items():
        param_type = openapi.TYPE_STRING
        param_format = None

        if isinstance(kind, filterset.NumberFilter):
            param_type = openapi.TYPE_NUMBER

        elif isinstance(kind, filterset.DateFilter) or isinstance(kind, filterset.DateTimeFilter):
            param_type = openapi.TYPE_STRING
            param_format = openapi.FORMAT_DATE

        elif isinstance(kind, filterset.BooleanFilter):
            param_type = openapi.TYPE_BOOLEAN

        parameter = openapi.Parameter(name, openapi.IN_QUERY, f"Filter by {name}", type=param_type, format=param_format)
        parameters.append(parameter)

    if ordering_fields:
        description = f"Sort by any of the following fields: {', '.join(ordering_fields)}."
        parameter = openapi.Parameter("ordering", openapi.IN_QUERY, description, type=openapi.TYPE_STRING)
        parameters.append(parameter)

    return parameters
