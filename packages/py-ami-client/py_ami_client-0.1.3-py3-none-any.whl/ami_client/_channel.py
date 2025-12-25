import time
from collections import deque
from typing import Any, Dict, Deque
from ._exeptions import AMIExceptions
from .operation import Action, Event, Response, UnknownOperation


class Channel:
    def __init__(self, channel_id: str, **kwargs):
        self.channel_id = channel_id
        self.timestamp: float = time.time()
        self.dict: Dict[str, Any] = kwargs

        self.actions: Deque[Action | UnknownOperation] = deque(maxlen=1000)
        self.events: Deque[Event | UnknownOperation] = deque(maxlen=1000)
        self.responses: Deque[Response | UnknownOperation] = deque(maxlen=1000)

    def add_operation(self, operation) -> None:
        if isinstance(operation, Action) or hasattr(operation, 'action'):
            self.actions.append(operation)

        elif isinstance(operation, Event) or hasattr(operation, 'event'):
            self.events.append(operation)

        elif isinstance(operation, Response) or hasattr(operation, 'response'):
            self.responses.append(operation)

        else:
            raise AMIExceptions.ClientError.OperationError(
                'operation must be an instance of Operation subclasses'
                )
