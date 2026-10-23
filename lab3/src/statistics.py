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
    mean = (1 / (T - T_start)) * integral(x(t) dt) = (1 / (T - T_start)) * sum(x_i * dt_i)
    """
    def __init__(self, name: str, initial_value: float = 0.0):
        self.name = name
        self.current_value = initial_value
        self.start_time = 0.0
        self.last_update_time = 0.0
        self.time_integral = 0.0
        self.history: List[TimePoint] = [TimePoint(0.0, initial_value, initial_value)]

    def reset(self, current_time: float) -> None:
        self.start_time = current_time
        self.last_update_time = current_time
        self.time_integral = 0.0
        self.history = [TimePoint(current_time, self.current_value, self.current_value)]

    def update(self, new_value: float, current_time: float) -> None:
        dt = current_time - self.last_update_time
        if dt > 0:
            self.time_integral += self.current_value * dt
            elapsed = current_time - self.start_time
            cum_avg = self.time_integral / elapsed if elapsed > 0 else self.current_value
            self.history.append(TimePoint(current_time, new_value, cum_avg))

        self.current_value = new_value
        self.last_update_time = current_time

    def finalize(self, total_time: float) -> None:
        if total_time > self.last_update_time:
            dt = total_time - self.last_update_time
            self.time_integral += self.current_value * dt
            self.last_update_time = total_time
            elapsed = total_time - self.start_time
            cum_avg = self.time_integral / elapsed if elapsed > 0 else self.current_value
            self.history.append(TimePoint(total_time, self.current_value, cum_avg))

    @property
    def mean(self) -> float:
        elapsed = self.last_update_time - self.start_time
        if elapsed > 0:
            return self.time_integral / elapsed
        return self.current_value


class DiscreteStatistic:
    """
    Дискретный во времени отклик.
    Вычисляется как обычное арифметическое среднее по выборке:
    mean = (1 / N) * sum(x_i)
    """
    def __init__(self, name: str):
        self.name = name
        self.observations: List[float] = []
        self.timestamps: List[float] = []
        self.running_means: List[float] = []
        self._sum = 0.0

    def reset(self, current_time: float) -> None:
        self.observations.clear()
        self.timestamps.clear()
        self.running_means.clear()
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
        return float(np.std(self.observations, ddof=1)) if len(self.observations) > 1 else 0.0


class StatisticsCollector:
    """
    Коллектор всех классов откликов модели:
    - Дискретные (время покупателя, ожидание в очереди, корзина)
    - Непрерывные (длина очереди, загрузка продавцов, число покупателей в зале)
    - Аддитивные (счетчики входов, завершений, транзакций)
    - Финальные (время завершения)
    """
    def __init__(self, num_departments: int = 5):
        self.num_departments = num_departments
        
        # 1. Непрерывные отклики
        self.total_queue_len = ContinuousStatistic("total_queue_len")
        self.busy_sellers_count = ContinuousStatistic("busy_sellers_count")
        self.buyers_in_supermarket = ContinuousStatistic("buyers_in_supermarket")
        
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

        # 3. Аддитивные счетчики
        self.total_arrivals = 0
        self.total_served = 0
        self.total_department_transactions = 0

        # 4. Финальный отклик
        self.simulation_end_time = 0.0

    def reset(self, current_time: float) -> None:
        """Сброс накопленной статистики после окончания фазы разогрева (warmup)."""
        self.total_queue_len.reset(current_time)
        self.busy_sellers_count.reset(current_time)
        self.buyers_in_supermarket.reset(current_time)
        for s in self.dept_queue_lens:
            s.reset(current_time)
        for s in self.dept_utilization:
            s.reset(current_time)

        self.time_in_supermarket.reset(current_time)
        self.total_queue_wait_time.reset(current_time)
        self.departments_visited.reset(current_time)

        self.total_arrivals = 0
        self.total_served = 0
        self.total_department_transactions = 0

    def finalize(self, total_time: float) -> None:
        self.simulation_end_time = total_time
        self.total_queue_len.finalize(total_time)
        self.busy_sellers_count.finalize(total_time)
        self.buyers_in_supermarket.finalize(total_time)
        for s in self.dept_queue_lens:
            s.finalize(total_time)
        for s in self.dept_utilization:
            s.finalize(total_time)

    def summary(self) -> Dict[str, Any]:
        return {
            "avg_time_in_supermarket": self.time_in_supermarket.mean,
            "std_time_in_supermarket": self.time_in_supermarket.std,
            "avg_queue_wait_time": self.total_queue_wait_time.mean,
            "avg_departments_visited": self.departments_visited.mean,
            "avg_total_queue_len": self.total_queue_len.mean,
            "avg_busy_sellers": self.busy_sellers_count.mean,
            "seller_utilization_pct": (self.busy_sellers_count.mean / float(self.num_departments)) * 100.0,
            "dept_utilizations": [u.mean for u in self.dept_utilization],
            "avg_buyers_in_supermarket": self.buyers_in_supermarket.mean,
            "total_arrivals": self.total_arrivals,
            "total_served": self.total_served,
            "total_transactions": self.total_department_transactions,
            "simulation_end_time": self.simulation_end_time,
        }
