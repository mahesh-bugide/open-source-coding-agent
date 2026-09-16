from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(slots=True)
class AgentEvent:
    event_type: str
    session_id: str
    payload: dict

    def to_sse(self) -> str:
        timestamp = datetime.now(UTC).isoformat()
        body = {
            "type": self.event_type,
            "timestamp": timestamp,
            "session_id": self.session_id,
            "payload": self.payload,
        }
        import json

        return f"data: {json.dumps(body, default=str)}\n\n"


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue[AgentEvent]]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def publish(self, session_id: str, event_type: str, payload: dict) -> None:
        event = AgentEvent(event_type=event_type, session_id=session_id, payload=payload)
        async with self._lock:
            subscribers = list(self._subscribers.get(session_id, set()))
        for queue in subscribers:
            await queue.put(event)

    async def subscribe(self, session_id: str) -> asyncio.Queue[AgentEvent]:
        queue: asyncio.Queue[AgentEvent] = asyncio.Queue(maxsize=200)
        async with self._lock:
            self._subscribers[session_id].add(queue)
        return queue

    async def unsubscribe(self, session_id: str, queue: asyncio.Queue[AgentEvent]) -> None:
        async with self._lock:
            group = self._subscribers.get(session_id)
            if not group:
                return
            group.discard(queue)
            if not group:
                self._subscribers.pop(session_id, None)
