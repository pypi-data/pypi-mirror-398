from typing import Optional
from ami_client.operation.response import Response
from ._base import Action

class Logoff(Action):
    def __init__(
            self,*,
            ActionID: Optional[int] = None,
            **additional_kwargs
    ) -> None:

        self._asterisk_name = 'Logoff'
        self._label = 'Logoff'

        kwargs = {
            'ActionID': ActionID,
        }
        kwargs.update(additional_kwargs)
        filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}

        super().__init__(Action=self._asterisk_name, **filtered_kwargs)

    def send(
            self,
            client,
            raise_timeout = False,
            raise_on_error_response = False,
            check_connection = False,
            check_authentication = False,
            close_connection = True
        ) -> Response | None:
        return super().send(client, raise_timeout, raise_on_error_response, check_connection, check_authentication, close_connection)