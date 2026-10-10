import argparse
import json
import os
import sys

# Добавляем родительский каталог в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config import load_config
from src.simulation import SupermarketSimulation


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="LR21: Запуск имитационной модели супермаркета (Вариант №5)")
    parser.add_argument("--time", type=float, default=None, help="Длительность прогона в минутах (по умолчанию из config.json)")
    parser.add_argument("--seed", type=int, default=None, help="Базовое зерно ДСЧ (по умолчанию из config.json)")
    parser.add_argument("--trace", action="store_true", default=None, help="Включить подробную трассировку событий в лог")
    args = parser.parse_args()

    cfg_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.json"))
    config = load_config(cfg_file)
    if args.time is not None:
        config.simulation.run_time = args.time
    if args.seed is not None:
        config.simulation.seed = args.seed
    if args.trace is not None:
        config.simulation.trace = args.trace
    else:
        config.simulation.trace = True  # Для ЛР2.1 по умолчанию трассировка активна

    trace_log_path = os.path.join(os.path.dirname(__file__), "trace.log")
    results_json_path = os.path.join(os.path.dirname(__file__), "run_results.json")

    print("================================================================================")
    print("   ЛАБОРАТОРНАЯ РАБОТА №2.1 (LR21) — КОНТРОЛЬНЫЙ ПРОГОН И ТРАССИРОВКА           ")
    print("   Вариант №5: Мини-супермаркет с раздельным обслуживанием (5 отделов)          ")
    print("================================================================================")
    print(f"Параметры: Т_мод = {config.simulation.run_time} мин, Seed = {config.simulation.seed}, Clearance = {config.simulation.with_clearance}")
    print(f"Трассировка записывается в: {trace_log_path}\n")

    sim = SupermarketSimulation(config, log_file=trace_log_path)
    results = sim.run()

    with open(results_json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n" + "="*80)
    print("                      РЕЗУЛЬТАТЫ КОНТРОЛЬНОГО ПРОГОНА                          ")
    print("="*80)
    print("1. ДИСКРЕТНЫЕ ОТКЛИКИ (Discrete-time responses):")
    print(f"   • Среднее время в супермаркете (T_sys):      {results['avg_time_in_supermarket']:.2f} мин")
    print(f"   • СКО времени в супермаркете:               {results['std_time_in_supermarket']:.2f} мин")
    print(f"   • Среднее время ожидания в очередях (W_q):   {results['avg_queue_wait_time']:.2f} мин")
    print(f"   • Среднее число отделов на покупателя:      {results['avg_departments_visited']:.2f}")

    print("\n2. НЕПРЕРЫВНЫЕ ОТКЛИКИ (Continuous-time responses):")
    print(f"   • Средняя суммарная длина очередей (L_q):   {results['avg_total_queue_len']:.2f} чел.")
    print(f"   • Среднее число занятых продавцов (K_busy): {results['avg_busy_sellers']:.2f} из 5")
    print(f"   • Коэффициент загрузки персонала (rho):     {results['seller_utilization_pct']:.2f} %")
    print(f"   • Среднее число покупателей в магазине:     {results['avg_buyers_in_supermarket']:.2f} чел.")

    print("\n3. АДДИТИВНЫЕ ОТКЛИКИ (Additive responses):")
    print(f"   • Всего вошло покупателей (N_arr):          {results['total_arrivals']}")
    print(f"   • Полностью обслужено покупателей (N_serv): {results['total_served']}")
    print(f"   • Всего транзакций в 5 отделах:             {results['total_transactions']}")

    print("\n4. ФИНАЛЬНЫЕ ОТКЛИКИ (Final responses):")
    print(f"   • Фактическое время завершения (T_fin):      {results['simulation_end_time']:.2f} мин")
    print("="*80)
    print(f"Результаты прогона сохранены в: {results_json_path}")


if __name__ == "__main__":
    main()
