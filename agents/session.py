"""Simple in-memory session and memory service for agents.

This provides a tiny `InMemorySessionService` used by agents to persist
short-lived session state and a basic long-term memory list per session.
"""
from typing import Dict, Any
import uuid

class InMemorySessionService:
    _sessions: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def create_session(cls, initial: Dict[str, Any] = None) -> str:
        sid = str(uuid.uuid4())
        cls._sessions[sid] = {"state": {}, "memory": []}
        if initial:
            cls._sessions[sid]["state"].update(initial)
        return sid

    @classmethod
    def get_state(cls, session_id: str) -> Dict[str, Any]:
        return cls._sessions.get(session_id, {}).get("state", {})

    @classmethod
    def set_state_value(cls, session_id: str, key: str, value: Any):
        cls._sessions.setdefault(session_id, {"state": {}, "memory": []})
        cls._sessions[session_id]["state"][key] = value

    @classmethod
    def append_memory(cls, session_id: str, item: Any):
        cls._sessions.setdefault(session_id, {"state": {}, "memory": []})
        cls._sessions[session_id]["memory"].append(item)

    @classmethod
    def get_memory(cls, session_id: str):
        return cls._sessions.get(session_id, {}).get("memory", [])
