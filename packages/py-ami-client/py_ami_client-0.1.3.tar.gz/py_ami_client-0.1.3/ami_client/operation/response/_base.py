from ...operation._base import Operation
from ami_client._exeptions import AMIExceptions

class Response(Operation):
    message: str | None

    def __init__(self, Response: str, ActionID: int, **kwargs):
        self.response = Response
        self.action_id = int(ActionID)
        super().__init__(Response=Response, ActionID=ActionID, **kwargs)

    def raise_on_status(self) -> None:
        if self.response == 'Error':
            raise AMIExceptions.ServerError.ActionError(self.message)