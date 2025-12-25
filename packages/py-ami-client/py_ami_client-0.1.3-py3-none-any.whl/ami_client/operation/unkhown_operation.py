from ._base import Operation

class UnknownOperation(Operation):
    def __init__(self, **kwargs: str):        
        self.asterisk_name: str = 'Unkhown'
        self.label: str = 'Unkhown Operation'

        if 'Action' in kwargs.keys():
            self.action = kwargs.get('Action', '')
            self.action_id = int(kwargs.get('ActionID', 0))

        elif 'Event' in kwargs.keys():
            self.event = kwargs.get('Event', '')

        elif 'Response' in kwargs.keys():
            self.response = kwargs.get('Response', '')
            self.action_id = int(kwargs.get('ActionID', 0))

        super().__init__(**kwargs)
