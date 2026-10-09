import heapq
from typing import Optional
from .entities import Event, EventType


class EventQueue:
    def __init__(self):
        self._heap = []
        self._seq = 0

    def schedule(self, time: float, event_type: EventType, customer_id: int, 
                 dept_id: Optional[int] = None, metadata: dict = None) -> None:
        self._seq += 1
        event = Event(
            time=time,
            seq=self._seq,
            event_type=event_type,
            customer_id=customer_id,
            dept_id=dept_id,
            metadata=metadata or {}
        )
        heapq.heappush(self._heap, event)

    def pop(self) -> Optional[Event]:
        if self._heap:
            return heapq.heappop(self._heap)
        return None

    def peek(self) -> Optional[Event]:
        if self._heap:
            return self._heap[0]
        return None

    @property
    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def __len__(self) -> int:
        return len(self._heap)
