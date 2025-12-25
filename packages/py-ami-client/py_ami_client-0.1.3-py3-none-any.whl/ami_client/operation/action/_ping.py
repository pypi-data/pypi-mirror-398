from typing import Optional
from ._base import Action

class Ping(Action):
    def __init__(
            self,*,
            ActionID: Optional[int] = None,
            **additional_kwargs,
    ) -> None:

        self._asterisk_name = 'Ping'
        self._label = 'Ping'

        kwargs = {
            'ActionID': ActionID,
        }
        kwargs.update(additional_kwargs)
        filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}

        super().__init__(Action=self._asterisk_name, **filtered_kwargs)
