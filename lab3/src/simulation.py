import random
from typing import List, Dict, Optional, Any
import numpy as np

from .config import SimulationConfig
from .entities import Customer, Department, Event, EventType
from .event_queue import EventQueue
from .statistics import StatisticsCollector


class SupermarketSimulation:
    def __init__(self, config: SimulationConfig, log_file: Optional[str] = None):
        self.config = config
        self.log_file = log_file
        self.trace_enabled = config.trace

        if config.rng_seed is not None:
            random.seed(config.rng_seed)
            np.random.seed(config.rng_seed)

        self.current_time = 0.0
        self.event_queue = EventQueue()
        self.stats = StatisticsCollector(num_departments=config.supermarket.num_departments)

        self.departments = [
            Department(i, name)
            for i, name in enumerate(config.supermarket.department_names)
        ]

        self.customers: Dict[int, Customer] = {}
        self.next_customer_id = 1
        self._log_handle = None

        if self.log_file:
            self._log_handle = open(self.log_file, "w", encoding="utf-8")

    def _log(self, message: str) -> None:
        formatted = f"[{self.current_time:7.2f} мин] {message}"
        if self.trace_enabled:
            print(formatted)
        if self._log_handle:
            self._log_handle.write(formatted + "\n")

    def _sample_arrival_interval(self) -> float:
        return random.expovariate(1.0 / self.config.supermarket.mean_arrival_interval)

    def _sample_service_time(self) -> float:
        p = self.config.supermarket.service_time
        val = random.gauss(p.mean, p.std)
        return max(p.min_time, val)

    def _sample_department_basket(self) -> List[int]:
        bp = self.config.supermarket.basket_params
        num_depts = self.config.supermarket.num_departments
        count = int(round(random.triangular(bp.min_count, bp.max_count, bp.mode_count)))
        count = max(1, min(num_depts, count))
        return random.sample(range(num_depts), count)

    def _update_continuous_stats(self) -> None:
        tot_q = sum(d.queue_length for d in self.departments)
        busy = sum(1 for d in self.departments if d.is_busy)
        in_sys = len([c for c in self.customers.values() if not c.is_finished])

        self.stats.total_queue_len.update(tot_q, self.current_time)
        self.stats.busy_sellers_count.update(busy, self.current_time)
        self.stats.buyers_in_supermarket.update(in_sys, self.current_time)

        for i, d in enumerate(self.departments):
            self.stats.dept_queue_lens[i].update(d.queue_length, self.current_time)
            self.stats.dept_utilization[i].update(1.0 if d.is_busy else 0.0, self.current_time)

    def _send_customer_to_department(self, customer: Customer, dept_id: int) -> None:
        dept = self.departments[dept_id]
        if not dept.is_busy:
            wait_time = dept.start_service(customer, self.current_time, from_queue=False)
            serv_time = self._sample_service_time()
            customer.total_service_time += serv_time

            self._log(
                f"Покупатель #{customer.customer_id} начал обслуживание в '{dept.name}' "
                f"(длительность: {serv_time:.2f} мин, ожидание: 0.00 мин)"
            )
            self.event_queue.schedule(
                time=self.current_time + serv_time,
                event_type=EventType.DEPT_SERVICE_END,
                customer_id=customer.customer_id,
                dept_id=dept_id
            )
        else:
            dept.add_to_queue(customer, self.current_time)
            self._log(
                f"Покупатель #{customer.customer_id} встал в очередь в '{dept.name}' "
                f"(длина очереди: {dept.queue_length})"
            )

    def _create_and_route_customer(self, cid: int, is_warmup: bool = False) -> Customer:
        basket = self._sample_department_basket()
        customer = Customer(
            customer_id=cid,
            arrival_time=self.current_time,
            departments_to_visit=basket
        )
        self.customers[cid] = customer
        self.stats.total_arrivals += 1

        basket_str = ", ".join(self.departments[i].name for i in basket)
        prefix = "СТАРТОВЫЙ" if is_warmup else "ВХОД"
        self._log(f"{prefix}: Покупатель #{cid} вошел в супермаркет. Корзина ({len(basket)} отд.): [{basket_str}]")

        first_dept = customer.current_dept
        self._send_customer_to_department(customer, first_dept)
        return customer

    def _handle_customer_arrival(self, event: Event) -> None:
        cid = event.customer_id
        self._create_and_route_customer(cid, is_warmup=False)

        next_arr_time = self.current_time + self._sample_arrival_interval()
        if next_arr_time < self.config.simulation_time:
            self.next_customer_id += 1
            self.event_queue.schedule(
                time=next_arr_time,
                event_type=EventType.CUSTOMER_ARRIVAL,
                customer_id=self.next_customer_id
            )

        self._update_continuous_stats()

    def _handle_service_end(self, event: Event) -> None:
        cid = event.customer_id
        dept_id = event.dept_id
        dept = self.departments[dept_id]
        customer = dept.complete_service(self.current_time)
        self.stats.total_department_transactions += 1

        self._log(
            f"ОБСЛУЖИВАНИЕ И РАСЧЕТ ЗАВЕРШЕНЫ: Покупатель #{cid} обслужен в '{dept.name}'"
        )

        customer.current_step += 1
        if not customer.is_finished:
            next_dept = customer.current_dept
            self._log(
                f"Покупатель #{cid} переходит в следующий отдел: '{self.departments[next_dept].name}'"
            )
            self._send_customer_to_department(customer, next_dept)
        else:
            customer.completion_time = self.current_time
            self.stats.total_served += 1
            self.stats.time_in_supermarket.record(customer.time_in_supermarket, self.current_time)
            self.stats.total_queue_wait_time.record(customer.total_wait_time, self.current_time)
            self.stats.departments_visited.record(len(customer.departments_to_visit), self.current_time)

            self._log(
                f"ВЫХОД: Покупатель #{cid} завершил все покупки и покинул магазин. "
                f"Общее время: {customer.time_in_supermarket:.2f} мин, "
                f"ожидание: {customer.total_wait_time:.2f} мин"
            )

        if dept.queue_length > 0:
            next_customer = dept.queue.pop(0)
            wait_time = dept.start_service(next_customer, self.current_time, from_queue=True)
            serv_time = self._sample_service_time()
            next_customer.total_service_time += serv_time

            self._log(
                f"Из очереди '{dept.name}' вызван покупатель #{next_customer.customer_id} "
                f"(ожидал: {wait_time:.2f} мин, расчетное время: {serv_time:.2f} мин)"
            )
            self.event_queue.schedule(
                time=self.current_time + serv_time,
                event_type=EventType.DEPT_SERVICE_END,
                customer_id=next_customer.customer_id,
                dept_id=dept_id
            )

        self._update_continuous_stats()

    def run(self) -> Dict[str, Any]:
        # 1. Стартовые покупатели (warm-up)
        for _ in range(self.config.warmup_buyers):
            self._create_and_route_customer(self.next_customer_id, is_warmup=True)
            self.next_customer_id += 1

        # 2. Первое событие прибытия
        first_arrival = self._sample_arrival_interval()
        if first_arrival < self.config.simulation_time:
            self.event_queue.schedule(
                time=first_arrival,
                event_type=EventType.CUSTOMER_ARRIVAL,
                customer_id=self.next_customer_id
            )

        # 3. Событие окончания фазы разогрева (warmup reset), если задано
        if self.config.warmup_time > 0.0 and self.config.warmup_time < self.config.simulation_time:
            self.event_queue.schedule(
                time=self.config.warmup_time,
                event_type=EventType.WARMUP_END,
                priority=0  # высший приоритет
            )

        self._log("=== СТАРТ ИМИТАЦИОННОГО ПРОГОНА ===")
        self._update_continuous_stats()

        while not self.event_queue.is_empty:
            event = self.event_queue.pop()

            if not self.config.with_clearance and event.time >= self.config.simulation_time:
                self.current_time = self.config.simulation_time
                break

            self.current_time = event.time

            if event.event_type == EventType.CUSTOMER_ARRIVAL:
                self._handle_customer_arrival(event)
            elif event.event_type == EventType.DEPT_SERVICE_END:
                self._handle_service_end(event)
            elif event.event_type == EventType.WARMUP_END:
                self._update_continuous_stats()
                self.stats.reset(self.current_time)
                self._log(f"ФАЗА WARM-UP ЗАВЕРШЕНА в t = {self.current_time:.2f} мин. Статистика сброшена.")

        end_time = max(self.current_time, self.config.simulation_time)
        self.stats.finalize(end_time)
        self._log(f"=== ПРОГОН ЗАВЕРШЕН в t = {end_time:.2f} мин ===")

        if self._log_handle:
            self._log_handle.close()

        return self.stats.summary()
