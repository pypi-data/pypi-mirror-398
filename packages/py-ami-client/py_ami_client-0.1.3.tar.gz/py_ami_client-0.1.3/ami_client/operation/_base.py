import time
from typing import Any, Dict

ASTERISK_BANNER: str = 'Asterisk Call Manager'

class Operation:
    _asterisk_name: str = ''
    _label: str = ''

    action: str | None
    event: str | None
    response: str | None

    def __init__(self, **kwargs: Any):
        self._list_id: int | None = None
        self._raw: str = ''
        self._dict: Dict[str, Any] = {}

        self._timestamp: float = time.time()

        self._dict.update(kwargs)
        self._raw = self.convert_to_raw_content(self._dict)

    @staticmethod
    def parse_raw_content(raw: str) -> Dict[str, Any]:
        """
        Parse `Asterisk` operation content to dictionary.

        Args:
            raw(str): Asterisk content.
        
        Returns:
            Dict[str, Any]: Asterisk data as dictionary.
        """
        lines = raw.strip().split('\r\n')
        operation_dict: Dict[str, Any] = {}
        for line in lines:
            if ASTERISK_BANNER in line: continue
            key, value = line.split(':', 1)
            operation_dict[key.lstrip()] = value.lstrip()

        return operation_dict

    @staticmethod
    def convert_to_raw_content(operation_dict: Dict[str, Any]) -> str:
        """
        Converts dictionary to `Asterisk` data.

        Args:
            operation_dict(Dict[str, Any]): Asterisk data as dictionary.
        
        Returns:
           str: Asterisk content.
        """
        raw_operation: str = ''
        for key, value in operation_dict.items():
            raw_operation += f'{key.replace('_', '-')}: {value}\r\n'

        raw_operation += '\r\n'
        return raw_operation


    def __str__(self) -> str:
        return f'<Operation: {self._asterisk_name}>'

    def __repr__(self) -> str:
        return f'<Operation: {self._asterisk_name}>'
