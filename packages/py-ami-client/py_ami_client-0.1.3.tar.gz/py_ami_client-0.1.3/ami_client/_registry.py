from typing import Set, Type, Deque
from collections import deque
from .operation import Operation, Action, Event, Response, UnknownOperation
from .operation import action_map, event_map, response_map
from ._exeptions import AMIExceptions


class Registry:
    def __init__(self) -> None:
        self.actions: Deque[Action] = deque(maxlen=1000)
        self.events: Deque[Event] = deque(maxlen=1000)
        self.responses: Deque[Response] = deque(maxlen=1000)

        self.whitelist: Set[Type[Operation]] = set()
        self.blacklist: Set[Type[Operation]] = set()

    def _register_new_operation(self, raw_operation: str) -> None:
        operation_dict = Operation.parse_raw_content(raw_operation)
        if not operation_dict:
            raise AMIExceptions.ClientError.InvalidOperation(
                'Unable to parse the operation to dict -> got None'
            )

        # Determine operation class using key-priority map
        for key, op_map in [('Action', action_map), ('Event', event_map), ('Response', response_map)]:
            if key in operation_dict:
                operation_class = op_map.get(operation_dict[key])
                break
        else:
            raise AMIExceptions.ClientError.UnknownOperation('Parsed unknown data from server')

        operation_class = UnknownOperation if operation_class is None else operation_class

        # Whitelist and Blacklist filtering
        if self.whitelist and not any(issubclass(operation_class, cls) and operation_class != cls for cls in self.whitelist): return
        if self.blacklist and     any(issubclass(operation_class, cls) or  operation_class == cls for cls in self.blacklist): return

        operation = operation_class(**operation_dict)

        ## Add operation to the targeted list
        type_list_map = {
            Action: self.actions,
            Event: self.events,
            Response: self.responses,
        }

        for op_type, target_list in type_list_map.items():
            if isinstance(operation, op_type):
                target_list.append(operation)
                return

        else:
            raise AMIExceptions.ClientError.OperationError(
                'operation must be an instance of Operation subclasses'
            )


    def get_response(self, action_id: int) -> Response | None:
        """
        Query reponse from registry.

        Args:
            action_id(int): `ActionID` of Asterisk Operation.

        Returns:
            Response | None: Server response object with the provided ActionID or None if no reponse object found
        """
        for response in reversed(self.responses):
            if response.action_id == action_id:
                return response
