import json
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SimulationParams:
    run_time: float = 60.0
    with_clearance: bool = True
    seed: Optional[int] = 42
    trace: bool = False
    num_replications: int = 1000
    warmup_buyers: int = 2


@dataclass
class ArrivalParams:
    mean_interval: float = 1.0  # minutes between arrivals
    distribution: str = "exponential"


@dataclass
class ServiceTimeParams:
    mean: float = 1.8  # minutes per service + payment
    std: float = 0.5
    min_time: float = 0.4


@dataclass
class DeptBasketParams:
    min_count: int = 1
    max_count: int = 5
    mode_count: int = 3


@dataclass
class SupermarketParams:
    num_departments: int = 5
    department_names: List[str] = field(default_factory=lambda: [
        "Бакалея",
        "Молочный",
        "Мясной",
        "Овощи и фрукты",
        "Кулинария"
    ])
    service_time: ServiceTimeParams = field(default_factory=ServiceTimeParams)
    departments_per_buyer: DeptBasketParams = field(default_factory=DeptBasketParams)


@dataclass
class Config:
    simulation: SimulationParams = field(default_factory=SimulationParams)
    arrival: ArrivalParams = field(default_factory=ArrivalParams)
    supermarket: SupermarketParams = field(default_factory=SupermarketParams)


def load_config(file_path: str = "config.json") -> Config:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return Config()

    sim_data = data.get("simulation", {})
    arr_data = data.get("arrival", {})
    market_data = data.get("supermarket", {})
    serv_data = market_data.get("service_time", {})
    dept_basket_data = market_data.get("departments_per_buyer", {})

    return Config(
        simulation=SimulationParams(
            run_time=float(sim_data.get("run_time", 60.0)),
            with_clearance=bool(sim_data.get("with_clearance", True)),
            seed=sim_data.get("seed", 42),
            trace=bool(sim_data.get("trace", False)),
            num_replications=int(sim_data.get("num_replications", 1000)),
            warmup_buyers=int(sim_data.get("warmup_buyers", 2)),
        ),
        arrival=ArrivalParams(
            mean_interval=float(arr_data.get("mean_interval", 1.0)),
            distribution=str(arr_data.get("distribution", "exponential")),
        ),
        supermarket=SupermarketParams(
            num_departments=int(market_data.get("num_departments", 5)),
            department_names=list(market_data.get("department_names", [
                "Бакалея", "Молочный", "Мясной", "Овощи и фрукты", "Кулинария"
            ])),
            service_time=ServiceTimeParams(
                mean=float(serv_data.get("mean", 1.8)),
                std=float(serv_data.get("std", 0.5)),
                min_time=float(serv_data.get("min_time", 0.4)),
            ),
            departments_per_buyer=DeptBasketParams(
                min_count=int(dept_basket_data.get("min_count", 1)),
                max_count=int(dept_basket_data.get("max_count", 5)),
                mode_count=int(dept_basket_data.get("mode_count", 3)),
            )
        )
    )
