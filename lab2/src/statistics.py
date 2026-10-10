from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
import numpy as np


@dataclass
class TimePoint:
    time: float
    instant_value: float
    cumulative_average: float


class ContinuousStatistic:
    """
    Непрерывный во времени отклик.
    Вычисляется как интегральное взвешенное по времени среднее:
    mean = (1 / T) * integral(x(t) dt) = (1 / T) * sum(x_i * dt_i)
    """
    def __init__(self, name: str, initial_value: float = 0.0):
        self.name = name
        self.current_value = initial_value
        self.last_update_time = 0.0
        self.time_integral = 0.0
        self.history: List[TimePoint] = [TimePoint(0.0, initial_value, initial_value)]

    def update(self, new_value: float, current_time: float) -> None:
        dt = current_time - self.last_update_time
        if dt > 0:
            self.time_integral += self.current_value * dt
            cum_avg = self.time_integral / current_time if current_time > 0 else 0.0
            self.history.append(TimePoint(current_time, new_value, cum_avg))

        self.current_value = new_value
        self.last_update_time = current_time

    def finalize(self, total_time: float) -> None:
        if total_time > self.last_update_time:
            dt = total_time - self.last_update_time
            self.time_integral += self.current_value * dt
            self.last_update_time = total_time
            cum_avg = self.time_integral / total_time if total_time > 0 else 0.0
            self.history.append(TimePoint(total_time, self.current_value, cum_avg))

    @property
    def mean(self) -> float:
        if self.last_update_time > 0:
            return self.time_integral / self.last_update_time
        return self.current_value


class DiscreteStatistic:
    """
    Дискретный во времени отклик.
    Вычисляется как обычное арифметическое среднее по завершившимся событиям:
    mean = (1 / N) * sum(x_i)
    """
    def __init__(self, name: str):
        self.name = name
        self.observations: List[float] = []
        self.timestamps: List[float] = []
        self.running_means: List[float] = []
        self._sum = 0.0

    def record(self, value: float, current_time: float) -> None:
        self.observations.append(value)
        self.timestamps.append(current_time)
        self._sum += value
        self.running_means.append(self._sum / len(self.observations))

    @property
    def count(self) -> int:
        return len(self.observations)

    @property
    def mean(self) -> float:
        return self._sum / len(self.observations) if self.observations else 0.0

    @property
    def std(self) -> float:
        return float(np.std(self.observations)) if len(self.observations) > 1 else 0.0


class StatisticsCollector:
    """
    Сборщик всех 4 классов откликов модели:
    1. Непрерывные (Continuous)
    2. Дискретные (Discrete)
    3. Аддитивные (Additive)
    4. Финальные (Final)
    """
    def __init__(self, num_departments: int = 5):
        # 1. Непрерывные отклики
        self.total_queue_len = ContinuousStatistic("total_queue_len")
        self.busy_sellers_count = ContinuousStatistic("busy_sellers_count")
        self.buyers_in_supermarket = ContinuousStatistic("buyers_in_supermarket")
        
        # Отклики по отдельным отделам
        self.dept_queue_lens = [
            ContinuousStatistic(f"dept_{i+1}_queue_len") for i in range(num_departments)
        ]
        self.dept_utilization = [
            ContinuousStatistic(f"dept_{i+1}_utilization") for i in range(num_departments)
        ]

        # 2. Дискретные отклики
        self.time_in_supermarket = DiscreteStatistic("time_in_supermarket")
        self.total_queue_wait_time = DiscreteStatistic("total_queue_wait_time")
        self.departments_visited = DiscreteStatistic("departments_visited")

        # 3. Аддитивные отклики
        self.total_arrivals = 0
        self.total_served = 0
        self.total_department_transactions = 0
        self.arrivals_history: List[Tuple[float, int]] = [(0.0, 0)]
        self.served_history: List[Tuple[float, int]] = [(0.0, 0)]

        # 4. Финальные отклики
        self.simulation_end_time = 0.0

    def finalize(self, current_time: float) -> None:
        self.simulation_end_time = current_time
        self.arrivals_history.append((current_time, self.total_arrivals))
        self.served_history.append((current_time, self.total_served))
        self.total_queue_len.finalize(current_time)
        self.busy_sellers_count.finalize(current_time)
        self.buyers_in_supermarket.finalize(current_time)
        for stat in self.dept_queue_lens:
            stat.finalize(current_time)
        for stat in self.dept_utilization:
            stat.finalize(current_time)

    def summary(self) -> Dict[str, Any]:
        return {
            # Дискретные
            "avg_time_in_supermarket": self.time_in_supermarket.mean,
            "std_time_in_supermarket": self.time_in_supermarket.std,
            "avg_queue_wait_time": self.total_queue_wait_time.mean,
            "avg_departments_visited": self.departments_visited.mean,
            # Непрерывные
            "avg_total_queue_len": self.total_queue_len.mean,
            "avg_busy_sellers": self.busy_sellers_count.mean,
            "seller_utilization_pct": (self.busy_sellers_count.mean / 5.0) * 100.0,
            "dept_utilizations": [u.mean for u in self.dept_utilization],
            "avg_buyers_in_supermarket": self.buyers_in_supermarket.mean,
            # Аддитивные
            "total_arrivals": self.total_arrivals,
            "total_served": self.total_served,
            "total_transactions": self.total_department_transactions,
            # Финальные
            "simulation_end_time": self.simulation_end_time,
        }
