from typing import Type
from ._base import Response
from ._error import Error
from ._success import Success


response_map: dict[str, Type[Response] | None] = {
    'Error': Error,
    'Success': Success,
}


__all__ = [
    'Response',
    'response_map',
    'Error',
    'Success',
]