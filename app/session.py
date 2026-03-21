import time
from collections import deque
from dataclasses import dataclass, field

HISTORY_TIMEOUT = 60

@dataclass
class Session:
    messages: deque = field(default_factory=lambda: deque(maxlen=8))
    last_active: float = field(default_factory=time.time)
    
_sessions: dict[str, Session] = {}

def get_session(device_id: str) -> Session:
    session = _sessions.get(device_id)
    
    if session is None or time.time() - session.last_active > HISTORY_TIMEOUT:
        session = Session()
        _sessions[device_id] = session
        
    return session

def add_to_session(device_id: str, user_message: str, assistant_message: str):
    session = get_session(device_id)
    session.messages.append({ "role": "user", "content": user_message })
    session.messages.append({ "role": "assistant", "content": assistant_message })
    session.last_active = time.time()