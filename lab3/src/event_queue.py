import heapq
from typing import Optional
from .entities import Event, EventType


class EventQueue:
    def __init__(self):
        self._heap = []

    def schedule(
        self,
        time: float,
        event_type: EventType,
        customer_id: Optional[int] = None,
        dept_id: Optional[int] = None,
        priority: int = 1
    ) -> None:
        event = Event(
            time=time,
            priority=priority,
            event_type=event_type,
            customer_id=customer_id,
            dept_id=dept_id
        )
        heapq.heappush(self._heap, event)

    def pop(self) -> Event:
        return heapq.heappop(self._heap)

    def peek(self) -> Optional[Event]:
        if self._heap:
            return self._heap[0]
        return None

    @property
    def is_empty(self) -> bool:
        return len(self._heap) == 0

    @property
    def size(self) -> int:
        return len(self._heap)
