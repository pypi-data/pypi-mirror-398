from rest_framework.renderers import BaseRenderer, JSONRenderer
from toon.encoder import encode


class DynamicRenderer(BaseRenderer):
    """
    A dynamic renderer that chooses between JSON and Toon serialization
    based on the `Accept` header of the incoming request.

    Behavior:
        - If the `Accept` header includes 'application/x-toon', the data
          will be serialized using the Toon format.
        - Otherwise, the data will be serialized as standard JSON.

    Attributes:
        media_type (str): Wildcard media type to accept any request type.
        format (None): Format name is not fixed since it can be JSON or Toon.

    Methods:
        render(data, accepted_media_type=None, renderer_context=None):
            Serializes the given Python data to the requested format.
    """

    media_type = "*/*"
    format = None

    def render(self, data, accepted_media_type=None, renderer_context=None):
        request = renderer_context.get("request") if renderer_context else None
        if request:
            accept = request.headers.get("Accept", "application/json")
            if "application/x-toon" in accept:
                return encode(data)
        # default JSON
        return JSONRenderer().render(data, accepted_media_type, renderer_context)


class ToonRenderer(BaseRenderer):
    """
    A renderer that serializes Python data structures into the Toon format.

    Designed for use with Django REST Framework to output responses in
    the custom 'application/x-toon' media type.

    Attributes:
        media_type (str): The media type this renderer produces ('application/x-toon').
        format (str): The short format name ('toon') used for content negotiation.

    Methods:
        render(data, accepted_media_type=None, renderer_context=None):
            Converts the provided Python object (dict, list, etc.) into
            Toon-encoded bytes. Returns an empty byte string if `data` is None.
            Raises ValueError if encoding fails.
    """

    media_type = "application/x-toon"
    format = "toon"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            return b""

        try:
            return encode(data)
        except Exception as e:
            raise ValueError(f"Cannot render data to Toon: {e}")
