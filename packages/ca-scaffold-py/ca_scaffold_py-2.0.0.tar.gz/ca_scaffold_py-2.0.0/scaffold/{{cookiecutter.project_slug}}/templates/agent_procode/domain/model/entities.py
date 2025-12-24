# app/domain/entities.py
from dataclasses import dataclass
from typing import List

@dataclass
class MessagePart:
    kind: str
    text: str

@dataclass
class Message:
    role: str
    parts: List[MessagePart]
    message_id: str

@dataclass
class Task:
    id: str
    status: str
    result: str | None = None
