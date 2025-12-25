from typing import Optional

from ami_client.operation.response import Response

from ._base import Action

class CoreStatus(Action):
    def __init__(
            self,*,
            ActionID: Optional[int] = None,
            **additional_kwargs
    ) -> None:

        self._asterisk_name = 'CoreStatus'
        self._label = 'CoreStatus'

        kwargs = {
            'ActionID': ActionID,
        }
        kwargs.update(additional_kwargs)
        filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}

        super().__init__(Action=self._asterisk_name, **filtered_kwargs)
