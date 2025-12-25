from ...operation._base import Operation

class Event(Operation):
    def __init__(self, Event: str, **kwargs):
        self.event = Event
        super().__init__(Event=Event, **kwargs)