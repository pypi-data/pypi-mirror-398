from typing import Optional
from ._base import Response

class Success(Response):
    def __init__(
            self,*,
            Response: str,
            ActionID: Optional[int] = None,
            Message: Optional[str] = None,
            **additional_kwargs
        ) -> None:

        self._asterisk_name = 'Success'
        self._label = 'Success'

        self.message = Message

        kwargs = {
            'Response': Response,
            'ActionID': ActionID,
            'Message': Message,
        }
        kwargs.update(additional_kwargs)
        filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}

        super().__init__(**filtered_kwargs)
