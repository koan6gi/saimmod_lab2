from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional


class EventType(str, Enum):
    CUSTOMER_ARRIVAL = "CUSTOMER_ARRIVAL"
    DEPT_SERVICE_END = "DEPT_SERVICE_END"
    WARMUP_END = "WARMUP_END"


@dataclass
class Customer:
    customer_id: int
    arrival_time: float
    departments_to_visit: List[int]
    current_step: int = 0
    total_service_time: float = 0.0
    total_wait_time: float = 0.0
    completion_time: Optional[float] = None

    @property
    def is_finished(self) -> bool:
        return self.current_step >= len(self.departments_to_visit)

    @property
    def current_dept(self) -> Optional[int]:
        if not self.is_finished:
            return self.departments_to_visit[self.current_step]
        return None

    @property
    def time_in_supermarket(self) -> float:
        if self.completion_time is not None:
            return self.completion_time - self.arrival_time
        return 0.0


@dataclass
class Department:
    dept_id: int
    name: str
    queue: List[Customer] = field(default_factory=list)
    queue_enter_times: List[float] = field(default_factory=list)
    current_customer: Optional[Customer] = None
    service_start_time: Optional[float] = None
    total_served_customers: int = 0

    @property
    def is_busy(self) -> bool:
        return self.current_customer is not None

    @property
    def queue_length(self) -> int:
        return len(self.queue)

    def add_to_queue(self, customer: Customer, current_time: float) -> None:
        self.queue.append(customer)
        self.queue_enter_times.append(current_time)

    def start_service(self, customer: Customer, current_time: float, from_queue: bool = False) -> float:
        wait_time = 0.0
        if from_queue and self.queue_enter_times:
            enter_time = self.queue_enter_times.pop(0)
            wait_time = current_time - enter_time
            customer.total_wait_time += wait_time

        self.current_customer = customer
        self.service_start_time = current_time
        return wait_time

    def complete_service(self, current_time: float) -> Optional[Customer]:
        customer = self.current_customer
        self.current_customer = None
        self.service_start_time = None
        self.total_served_customers += 1
        return customer


@dataclass(order=True)
class Event:
    time: float
    priority: int = 1
    event_type: EventType = field(compare=False, default=EventType.CUSTOMER_ARRIVAL)
    customer_id: Optional[int] = field(compare=False, default=None)
    dept_id: Optional[int] = field(compare=False, default=None)
