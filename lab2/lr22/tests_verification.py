import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config import load_config
from src.simulation import SupermarketSimulation


class TestSupermarketVerification(unittest.TestCase):
    def test_reproducibility(self):
        """Проверка детерминизма псевдослучайных последовательностей при одинаковом seed"""
        cfg1 = load_config("config.json")
        cfg1.simulation.seed = 12345
        cfg1.simulation.trace = False
        res1 = SupermarketSimulation(cfg1).run()

        cfg2 = load_config("config.json")
        cfg2.simulation.seed = 12345
        cfg2.simulation.trace = False
        res2 = SupermarketSimulation(cfg2).run()

        self.assertEqual(res1["total_arrivals"], res2["total_arrivals"])
        self.assertEqual(res1["total_served"], res2["total_served"])
        self.assertAlmostEqual(res1["avg_time_in_supermarket"], res2["avg_time_in_supermarket"], places=6)
        self.assertAlmostEqual(res1["avg_total_queue_len"], res2["avg_total_queue_len"], places=6)

    def test_clearance_completes_all_buyers(self):
        """Проверка режима дообслуживания: все вошедшие клиенты должны быть обслужены"""
        cfg = load_config("config.json")
        cfg.simulation.with_clearance = True
        cfg.simulation.seed = 777
        res = SupermarketSimulation(cfg).run()

        self.assertGreater(res["total_arrivals"], 0)
        self.assertEqual(res["total_arrivals"], res["total_served"])
        self.assertGreaterEqual(res["simulation_end_time"], cfg.simulation.run_time)

    def test_monotonicity_arrival_rate(self):
        """Тест монотонности: рост интенсивности прихода увеличивает среднюю длину очереди"""
        cfg_low = load_config("config.json")
        cfg_low.arrival.mean_interval = 2.5  # редкие приходы (0.4 клиента/мин)
        cfg_low.simulation.seed = 999
        res_low = SupermarketSimulation(cfg_low).run()

        cfg_high = load_config("config.json")
        cfg_high.arrival.mean_interval = 0.8  # частые приходы (1.25 клиента/мин)
        cfg_high.simulation.seed = 999
        res_high = SupermarketSimulation(cfg_high).run()

        self.assertGreater(res_high["avg_total_queue_len"], res_low["avg_total_queue_len"])
        self.assertGreater(res_high["avg_time_in_supermarket"], res_low["avg_time_in_supermarket"])

    def test_monotonicity_service_time(self):
        """Тест монотонности: увеличение времени обслуживания увеличивает время в магазине"""
        cfg_fast = load_config("config.json")
        cfg_fast.supermarket.service_time.mean = 1.0
        cfg_fast.simulation.seed = 555
        res_fast = SupermarketSimulation(cfg_fast).run()

        cfg_slow = load_config("config.json")
        cfg_slow.supermarket.service_time.mean = 2.4
        cfg_slow.simulation.seed = 555
        res_slow = SupermarketSimulation(cfg_slow).run()

        self.assertGreater(res_slow["avg_time_in_supermarket"], res_fast["avg_time_in_supermarket"])

    def test_littles_law_qualitative(self):
        """Качественная проверка закона Литтла: число покупателей в системе коррелирует с временем в системе"""
        cfg = load_config("config.json")
        cfg.simulation.seed = 888
        res = SupermarketSimulation(cfg).run()

        # N_sys = lambda * T_sys
        eff_lambda = res["total_served"] / res["simulation_end_time"]
        expected_in_system = eff_lambda * res["avg_time_in_supermarket"]
        actual_in_system = res["avg_buyers_in_supermarket"]

        # Допускаем погрешность переходного периода в пределах 25%
        rel_diff = abs(expected_in_system - actual_in_system) / actual_in_system
        self.assertLess(rel_diff, 0.25)

    def test_queue_wait_time_validity(self):
        """Проверка физического баланса времени: время ожидания в очередях строго меньше общего времени в магазине"""
        cfg = load_config("config.json")
        cfg.simulation.seed = 42
        res = SupermarketSimulation(cfg).run()

        # Время в очередях не может превышать суммарное время в магазине
        self.assertGreater(res["avg_queue_wait_time"], 0.0)
        self.assertLess(res["avg_queue_wait_time"], res["avg_time_in_supermarket"])
        # Разница должна соответствовать чистому времени обслуживания
        net_service = res["avg_time_in_supermarket"] - res["avg_queue_wait_time"]
        self.assertGreater(net_service, 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
