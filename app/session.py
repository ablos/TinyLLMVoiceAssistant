import time
from collections import deque
from dataclasses import dataclass, field

HISTORY_TIMEOUT = 60

@dataclass
class Session:
    messages: deque = field(default_factory=lambda: deque(maxlen=8))
    last_active: float = field(default_factory=time.time)
    last_intent: str = ""

_sessions: dict[str, Session] = {}

def get_session(device_id: str, intent: str = "") -> Session:
    session = _sessions.get(device_id)

    if session is None or time.time() - session.last_active > HISTORY_TIMEOUT:
        session = Session()
        _sessions[device_id] = session
    elif intent and intent != session.last_intent:
        session.messages.clear()

    return session

def add_to_session(device_id: str, user_message: str, assistant_message: str, intent: str = ""):
    session = get_session(device_id, intent)
    session.messages.append({ "role": "user", "content": user_message })
    session.messages.append({ "role": "assistant", "content": assistant_message })
    session.last_active = time.time()
    session.last_intent = intent