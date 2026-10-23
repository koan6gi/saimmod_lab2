from dataclasses import dataclass, field
from typing import List, Optional
import json
import os


@dataclass
class ServiceTimeParams:
    mean: float = 1.8
    std: float = 0.5
    min_time: float = 0.4


@dataclass
class DeptBasketParams:
    min_count: int = 1
    max_count: int = 5
    mode_count: int = 3


@dataclass
class SupermarketConfig:
    num_departments: int = 5
    department_names: List[str] = field(default_factory=lambda: [
        "Бакалея",
        "Молочный",
        "Мясной",
        "Овощи и фрукты",
        "Кулинария"
    ])
    mean_arrival_interval: float = 1.0
    service_time: ServiceTimeParams = field(default_factory=ServiceTimeParams)
    basket_params: DeptBasketParams = field(default_factory=DeptBasketParams)


@dataclass
class SimulationConfig:
    simulation_time: float = 300.0
    warmup_time: float = 0.0
    warmup_buyers: int = 2
    with_clearance: bool = False
    rng_seed: Optional[int] = 42
    trace: bool = False
    supermarket: SupermarketConfig = field(default_factory=SupermarketConfig)


def load_lab3_config(config_path: str = "config.json") -> dict:
    if not os.path.isabs(config_path):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidate = os.path.join(base_dir, config_path)
        if os.path.exists(candidate):
            config_path = candidate

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)
