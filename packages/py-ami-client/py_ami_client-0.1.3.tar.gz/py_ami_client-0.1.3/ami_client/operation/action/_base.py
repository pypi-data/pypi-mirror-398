import time, random
from typing import Optional
from ...operation.response import Response
from ...operation._base import Operation

class Action(Operation):
    def __init__(self, Action: str ,ActionID: Optional[int] = None, **kwargs) -> None:
        self._sent_to_server: bool = False
        self.server_response: Response | None = None
        self.action = Action
        self.action_id: int = int(ActionID) if ActionID else random.randint(0, 1_000_000_000)
        super().__init__(Action=Action, ActionID=self.action_id, **kwargs)

    def send(
            self,
            client,
            raise_timeout: bool = True,
            raise_on_error_response: bool = True,
            check_connection: bool = True,
            check_authentication: bool = True,
            close_connection: bool = False,
        ) -> Response | None:
        if check_connection:
            client.connect() if not client.is_connected() else None

        if check_authentication:
            client.login() if not client.is_authenticated() else None

        action_string = self.convert_to_raw_content(self._dict)
        client.socket.sendall(action_string.encode())
        self._sent_to_server = True

        start = time.time()
        while (time.time() - start) < client._timeout:
            response: Response | None = client.registry.get_response(self.action_id)
            time.sleep(0.005)  # to prevent tight locking
            if response is not None: break

        else:
            if raise_timeout and response is None:
                raise TimeoutError(
                    f'Timeout while getting response. action: {self.action} - action id: {self.action_id}'
                )

        if close_connection:
            client.disconnect()

        self.server_response = response

        if response and raise_on_error_response:
            response.raise_on_status()

        return response


    def __bool__(self) -> bool:
        return self._sent_to_server