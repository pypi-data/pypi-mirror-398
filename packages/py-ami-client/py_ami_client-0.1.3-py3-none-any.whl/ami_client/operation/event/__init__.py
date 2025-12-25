from typing import Type
from ._base import Event
from ._hangup import Hangup
from ._newexten import Newexten
from ._varset import VarSet


event_map: dict[str, Type[Event] | None] = {
    'AGIExecEnd': None, #NotImplementedYet
    'AGIExecStart': None, #NotImplementedYet
    'AOC-D': None, #NotImplementedYet
    'AOC-E': None, #NotImplementedYet
    'AOC-S': None, #NotImplementedYet
    'AgentCalled': None, #NotImplementedYet
    'AgentComplete': None, #NotImplementedYet
    'AgentConnect': None, #NotImplementedYet
    'AgentDump': None, #NotImplementedYet
    'AgentLogin': None, #NotImplementedYet
    'AgentLogoff': None, #NotImplementedYet
    'AgentRingNoAnswer': None, #NotImplementedYet
    'Agents': None, #NotImplementedYet
    'AgentsComplete': None, #NotImplementedYet
    'Alarm': None, #NotImplementedYet
    'AlarmClear': None, #NotImplementedYet
    'AorDetail': None, #NotImplementedYet
    'AorList': None, #NotImplementedYet
    'AorListComplete': None, #NotImplementedYet
    'AsyncAGIEnd': None, #NotImplementedYet
    'AsyncAGIExec': None, #NotImplementedYet
    'AsyncAGIStart': None, #NotImplementedYet
    'AttendedTransfer': None, #NotImplementedYet
    'AuthDetail': None, #NotImplementedYet
    'AuthList': None, #NotImplementedYet
    'AuthListComplete': None, #NotImplementedYet
    'AuthMethodNotAllowed': None, #NotImplementedYet
    'BlindTransfer': None, #NotImplementedYet
    'BridgeCreate': None, #NotImplementedYet
    'BridgeDestroy': None, #NotImplementedYet
    'BridgeEnter': None, #NotImplementedYet
    'BridgeInfoChannel': None, #NotImplementedYet
    'BridgeInfoComplete': None, #NotImplementedYet
    'BridgeLeave': None, #NotImplementedYet
    'BridgeMerge': None, #NotImplementedYet
    'BridgeVideoSourceUpdate': None, #NotImplementedYet
    'CEL': None, #NotImplementedYet
    'Cdr': None, #NotImplementedYet
    'ChallengeResponseFailed': None, #NotImplementedYet
    'ChallengeSent': None, #NotImplementedYet
    'ChanSpyStart': None, #NotImplementedYet
    'ChanSpyStop': None, #NotImplementedYet
    'ChannelTalkingStart': None, #NotImplementedYet
    'ChannelTalkingStop': None, #NotImplementedYet
    'ConfbridgeEnd': None, #NotImplementedYet
    'ConfbridgeJoin': None, #NotImplementedYet
    'ConfbridgeLeave': None, #NotImplementedYet
    'ConfbridgeList': None, #NotImplementedYet
    'ConfbridgeListRooms': None, #NotImplementedYet
    'ConfbridgeMute': None, #NotImplementedYet
    'ConfbridgeRecord': None, #NotImplementedYet
    'ConfbridgeStart': None, #NotImplementedYet
    'ConfbridgeStopRecord': None, #NotImplementedYet
    'ConfbridgeTalking': None, #NotImplementedYet
    'ConfbridgeUnmute': None, #NotImplementedYet
    'ContactList': None, #NotImplementedYet
    'ContactListComplete': None, #NotImplementedYet
    'ContactStatus': None, #NotImplementedYet
    'ContactStatusDetail': None, #NotImplementedYet
    'CoreShowChannel': None, #NotImplementedYet
    'CoreShowChannelMapComplete': None, #NotImplementedYet
    'CoreShowChannelsComplete': None, #NotImplementedYet
    'DAHDIChannel': None, #NotImplementedYet
    'DNDState': None, #NotImplementedYet
    'DTMFBegin': None, #NotImplementedYet
    'DTMFEnd': None, #NotImplementedYet
    'DeadlockStart': None, #NotImplementedYet
    'DeviceStateChange': None, #NotImplementedYet
    'DeviceStateListComplete': None, #NotImplementedYet
    'DialBegin': None, #NotImplementedYet
    'DialEnd': None, #NotImplementedYet
    'DialState': None, #NotImplementedYet
    'EndpointDetail': None, #NotImplementedYet
    'EndpointDetailComplete': None, #NotImplementedYet
    'EndpointList': None, #NotImplementedYet
    'EndpointListComplete': None, #NotImplementedYet
    'ExtensionStateListComplete': None, #NotImplementedYet
    'ExtensionStatus': None, #NotImplementedYet
    'FAXSession': None, #NotImplementedYet
    'FAXSessionsComplete': None, #NotImplementedYet
    'FAXSessionsEntry': None, #NotImplementedYet
    'FAXStats': None, #NotImplementedYet
    'FAXStatus': None, #NotImplementedYet
    'FailedACL': None, #NotImplementedYet
    'Flash': None, #NotImplementedYet
    'FullyBooted': None, #NotImplementedYet
    'Hangup': Hangup,
    'HangupHandlerPop': None, #NotImplementedYet
    'HangupHandlerPush': None, #NotImplementedYet
    'HangupHandlerRun': None, #NotImplementedYet
    'HangupRequest': None, #NotImplementedYet
    'Hold': None, #NotImplementedYet
    'IdentifyDetail': None, #NotImplementedYet
    'InvalidAccountID': None, #NotImplementedYet
    'InvalidPassword': None, #NotImplementedYet
    'InvalidTransport': None, #NotImplementedYet
    'Load': None, #NotImplementedYet
    'LoadAverageLimit': None, #NotImplementedYet
    'LocalBridge': None, #NotImplementedYet
    'LocalOptimizationBegin': None, #NotImplementedYet
    'LocalOptimizationEnd': None, #NotImplementedYet
    'LogChannel': None, #NotImplementedYet
    'MCID': None, #NotImplementedYet
    'MWIGet': None, #NotImplementedYet
    'MWIGetComplete': None, #NotImplementedYet
    'MeetmeEnd': None, #NotImplementedYet
    'MeetmeJoin': None, #NotImplementedYet
    'MeetmeLeave': None, #NotImplementedYet
    'MeetmeList': None, #NotImplementedYet
    'MeetmeListRooms': None, #NotImplementedYet
    'MeetmeMute': None, #NotImplementedYet
    'MeetmeTalkRequest': None, #NotImplementedYet
    'MeetmeTalking': None, #NotImplementedYet
    'MemoryLimit': None, #NotImplementedYet
    'MessageWaiting': None, #NotImplementedYet
    'MiniVoiceMail': None, #NotImplementedYet
    'MixMonitorMute': None, #NotImplementedYet
    'MixMonitorStart': None, #NotImplementedYet
    'MixMonitorStop': None, #NotImplementedYet
    'MusicOnHoldStart': None, #NotImplementedYet
    'MusicOnHoldStop': None, #NotImplementedYet
    'NewAccountCode': None, #NotImplementedYet
    'NewCallerid': None, #NotImplementedYet
    'NewConnectedLine': None, #NotImplementedYet
    'Newexten': Newexten,
    'Newchannel': None, #NotImplementedYet
    'Newstate': None, #NotImplementedYet
    'OriginateResponse': None, #NotImplementedYet
    'ParkedCall': None, #NotImplementedYet
    'ParkedCallGiveUp': None, #NotImplementedYet
    'ParkedCallSwap': None, #NotImplementedYet
    'ParkedCallTimeOut': None, #NotImplementedYet
    'PeerStatus': None, #NotImplementedYet
    'Pickup': None, #NotImplementedYet
    'PresenceStateChange': None, #NotImplementedYet
    'PresenceStateListComplete': None, #NotImplementedYet
    'PresenceStatus': None, #NotImplementedYet
    'QueueCallerAbandon': None, #NotImplementedYet
    'QueueCallerJoin': None, #NotImplementedYet
    'QueueCallerLeave': None, #NotImplementedYet
    'QueueEntry': None, #NotImplementedYet
    'QueueMemberAdded': None, #NotImplementedYet
    'QueueMemberPause': None, #NotImplementedYet
    'QueueMemberPenalty': None, #NotImplementedYet
    'QueueMemberRemoved': None, #NotImplementedYet
    'QueueMemberRinginuse': None, #NotImplementedYet
    'QueueMemberStatus': None, #NotImplementedYet
    'QueueParams': None, #NotImplementedYet
    'RTCPReceived': None, #NotImplementedYet
    'RTCPSent': None, #NotImplementedYet
    'ReceiveFAX': None, #NotImplementedYet
    'Registry': None, #NotImplementedYet
    'Reload': None, #NotImplementedYet
    'Rename': None, #NotImplementedYet
    'RequestBadFormat': None, #NotImplementedYet
    'RequestNotAllowed': None, #NotImplementedYet
    'RequestNotSupported': None, #NotImplementedYet
    'SendFAX': None, #NotImplementedYet
    'SessionLimit': None, #NotImplementedYet
    'Shutdown': None, #NotImplementedYet
    'SoftHangupRequest': None, #NotImplementedYet
    'SpanAlarm': None, #NotImplementedYet
    'SpanAlarmClear': None, #NotImplementedYet
    'Status': None, #NotImplementedYet
    'StatusComplete': None, #NotImplementedYet
    'SuccessfulAuth': None, #NotImplementedYet
    'TransportDetail': None, #NotImplementedYet
    'UnParkedCall': None, #NotImplementedYet
    'UnexpectedAddress': None, #NotImplementedYet
    'Unhold': None, #NotImplementedYet
    'Unload': None, #NotImplementedYet
    'UserEvent': None, #NotImplementedYet
    'VarSet': VarSet,
    'VoicemailPasswordChange': None, #NotImplementedYet
    'Wink': None, #NotImplementedYet
}


__all__ = [
    'Event',
    'event_map',
    'Hangup',
    'Newexten',
    'VarSet',
]