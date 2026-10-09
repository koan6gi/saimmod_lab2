import random
import simpy
from typing import Dict, Any, List


def run_simpy_supermarket(
    run_time: float = 60.0,
    mean_interval: float = 1.0,
    serv_mean: float = 1.8,
    serv_std: float = 0.5,
    serv_min: float = 0.4,
    warmup_buyers: int = 2,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Процессная реализация имитационной модели супермаркета (SimPy)
    в соответствии со Слайдом 14 лекции (квазипараллелизм на генераторах yield).
    """
    random.seed(seed)
    env = simpy.Environment()

    # 5 отделов, каждый как отдельный ресурс с 1 продавцом
    departments = [simpy.Resource(env, capacity=1) for _ in range(5)]
    
    arrivals_count = 0
    served_count = 0
    times_in_supermarket: List[float] = []
    wait_times: List[float] = []

    def customer_process(env: simpy.Environment, customer_id: int):
        nonlocal served_count
        arrival_t = env.now
        
        # Выбираем от 1 до 5 отделов
        basket_count = int(round(random.triangular(1, 5, 3)))
        basket_count = max(1, min(5, basket_count))
        chosen_depts = random.sample(range(5), basket_count)

        customer_wait = 0.0

        for dept_id in chosen_depts:
            dept_res = departments[dept_id]
            req_start = env.now
            with dept_res.request() as req:
                yield req
                wait = env.now - req_start
                customer_wait += wait
                
                # Обслуживание и расчет
                serv_dur = max(serv_min, random.gauss(serv_mean, serv_std))
                yield env.timeout(serv_dur)

        total_time = env.now - arrival_t
        served_count += 1
        times_in_supermarket.append(total_time)
        wait_times.append(customer_wait)

    def buyer_generator(env: simpy.Environment):
        nonlocal arrivals_count
        # Прогрев
        for _ in range(warmup_buyers):
            arrivals_count += 1
            env.process(customer_process(env, arrivals_count))

        while env.now < run_time:
            interval = random.expovariate(1.0 / mean_interval)
            yield env.timeout(interval)
            if env.now < run_time:
                arrivals_count += 1
                env.process(customer_process(env, arrivals_count))

    env.process(buyer_generator(env))
    env.run()

    return {
        "model_type": "SimPy (Process Interaction)",
        "end_time": env.now,
        "total_arrivals": arrivals_count,
        "total_served": served_count,
        "avg_time_in_supermarket": sum(times_in_supermarket) / len(times_in_supermarket) if times_in_supermarket else 0.0,
        "avg_wait_time": sum(wait_times) / len(wait_times) if wait_times else 0.0,
    }


if __name__ == "__main__":
    res = run_simpy_supermarket()
    print("SimPy run results:", res)
