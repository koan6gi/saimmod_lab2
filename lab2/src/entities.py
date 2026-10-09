from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Any


class EventType(Enum):
    CUSTOMER_ARRIVAL = auto()
    DEPT_SERVICE_END = auto()


@dataclass(order=True)
class Event:
    time: float
    seq: int
    event_type: EventType = field(compare=False)
    customer_id: int = field(compare=False)
    dept_id: Optional[int] = field(default=None, compare=False)
    metadata: dict = field(default_factory=dict, compare=False)


@dataclass
class Customer:
    customer_id: int
    arrival_time: float
    departments_to_visit: List[int]
    current_step: int = 0
    total_service_time: float = 0.0
    total_wait_time: float = 0.0
    queue_enter_time: float = 0.0
    completion_time: Optional[float] = None

    @property
    def current_dept(self) -> Optional[int]:
        if self.current_step < len(self.departments_to_visit):
            return self.departments_to_visit[self.current_step]
        return None

    @property
    def is_finished(self) -> bool:
        return self.current_step >= len(self.departments_to_visit)

    @property
    def time_in_supermarket(self) -> float:
        if self.completion_time is not None:
            return self.completion_time - self.arrival_time
        return 0.0


class Department:
    def __init__(self, dept_id: int, name: str):
        self.dept_id = dept_id
        self.name = name
        self.queue: List[Customer] = []
        self.current_customer: Optional[Customer] = None
        self.total_served_count = 0
        self.last_busy_change_time = 0.0

    @property
    def is_busy(self) -> bool:
        return self.current_customer is not None

    @property
    def queue_length(self) -> int:
        return len(self.queue)

    def add_to_queue(self, customer: Customer, current_time: float) -> None:
        customer.queue_enter_time = current_time
        self.queue.append(customer)

    def start_service(self, customer: Customer, current_time: float, from_queue: bool = False) -> float:
        self.current_customer = customer
        wait_time = (current_time - customer.queue_enter_time) if from_queue else 0.0
        customer.total_wait_time += wait_time
        return wait_time

    def complete_service(self, current_time: float) -> Customer:
        customer = self.current_customer
        self.current_customer = None
        self.total_served_count += 1
        return customer
