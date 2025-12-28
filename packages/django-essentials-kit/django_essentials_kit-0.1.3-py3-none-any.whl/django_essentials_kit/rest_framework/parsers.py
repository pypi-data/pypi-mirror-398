import logging
from json import JSONDecodeError

from rest_framework.exceptions import ParseError
from rest_framework.parsers import BaseParser, DataAndFiles
from rest_framework.utils import json

from django.conf import settings
from django.http.multipartparser import MultiPartParser as DjangoMultiPartParser
from django.http.multipartparser import MultiPartParserError

__all__ = ["JsonMultiPartParser"]

logger = logging.getLogger("django.request")


class JsonMultiPartParser(BaseParser):
    media_type = "multipart/form-data"

    def parse(self, stream, media_type=None, parser_context=None):
        request = (parser_context or {}).get("request")

        meta = request.META.copy()
        meta["CONTENT_TYPE"] = media_type

        encoding = parser_context.get("encoding", settings.DEFAULT_CHARSET)

        try:
            parser = DjangoMultiPartParser(meta, stream, request.upload_handlers, encoding)
            data, files = parser.parse()

            for key in data.keys():
                try:
                    data[key] = json.loads(data[key])
                except (JSONDecodeError, TypeError) as e:
                    ...

            return DataAndFiles(data, files)

        except MultiPartParserError as e:
            logger.exception("Error occurred while parsing multipart form")

            raise ParseError("Error occurred while parsing multipart form")
