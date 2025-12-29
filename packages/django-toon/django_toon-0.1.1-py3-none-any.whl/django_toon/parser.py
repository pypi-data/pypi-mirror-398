from rest_framework.parsers import BaseParser, JSONParser
from toon.decoder import decode

class DynamicParser(BaseParser):
    """
    A dynamic parser that chooses between JSON and Toon decoding
    based on the `Content-Type` header of the incoming request.

    Behavior:
        - If the `Content-Type` header is 'application/x-toon', the request body
          will be decoded using the Toon format.
        - Otherwise, the body will be parsed as standard JSON.

    Attributes:
        media_type (str): Wildcard media type to accept any request type.
        format (None): Format name is not fixed since it can be JSON or Toon.

    Methods:
        parse(stream, media_type=None, parser_context=None):
            Reads the request body and parses it into a Python data structure.
            Returns a dict or list.
    """

    media_type = "*/*"
    format = None

    def parse(self, stream, media_type=None, parser_context=None):
        content_type = (
            parser_context["request"].content_type if parser_context else None
        )
        if content_type == "application/x-toon":
            return decode(stream.read())
        # default JSON
        return JSONParser().parse(stream, media_type, parser_context)


class ToonParser(BaseParser):
    """
    A parser that decodes request bodies in the Toon format.

    Designed for use with Django REST Framework to parse requests
    with 'application/x-toon' Content-Type.

    Attributes:
        media_type (str): The media type this parser accepts ('application/x-toon').

    Methods:
        parse(stream, media_type=None, parser_context=None):
            Reads the request body and decodes it using Toon.
            Returns a Python object (dict, list, etc.).
            Raises ValueError if the decoding fails.
    """

    media_type = "application/x-toon"

    def parse(self, stream, media_type=None, parser_context=None):
        raw_data = stream.read()

        try:
            data = decode(raw_data)
        except Exception as e:
            raise ValueError(f"Invalid Toon data: {e}")

        return data
