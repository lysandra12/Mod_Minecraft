from __future__ import annotations

from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from .Message import Message
import collections

class MessageBus:
    def __init__(self):
        self._queues: dict[str, collections.deque[Message]] = {}

    def publish(self, msg: Message) -> None:
        q = self._queues.setdefault(msg.target, collections.deque())
        q.append(msg)

    def poll_for(self, target: str) -> Optional[Message]:
        q = self._queues.get(target)
        if not q:
            return None
        return q.popleft()
    
    def publish_command_message(self, target:str, command:str):
        msg = Message(
            type="control", 
            source="System",
            target=target,
            payload=command
        )
        self.publish(msg)