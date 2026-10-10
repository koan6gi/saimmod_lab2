import os
import sys
import json
from typing import Dict, List
import numpy as np
import matplotlib.pyplot as plt

# Добавляем родительский каталог в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config import load_config
from src.simulation import SupermarketSimulation
from src.plots import (
    plot_single_run,
    plot_multi_run,
    plot_run_to_run,
    plot_sensitivity_sweep,
    plot_utilization,
)


def setup_plot_style():
    plt.rcParams.update({
        'font.sans-serif': 'DejaVu Sans',
        'font.size': 10,
        'axes.labelsize': 11,
        'axes.titlesize': 12,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 9,
        'figure.titlesize': 13,
        'grid.alpha': 0.3,
        'grid.linestyle': '--'
    })


def run_verification_study(plots_dir: str, data_path: str):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    os.makedirs(plots_dir, exist_ok=True)
    setup_plot_style()
    cfg_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.json"))

    print("================================================================================")
    print("   ЛАБОРАТОРНАЯ РАБОТА №2.2 (LR22) — ВЕРИФИКАЦИЯ ИМИТАЦИОННОЙ МОДЕЛИ           ")
    print("   Вариант №5: Мини-супермаркет с раздельным обслуживанием                     ")
    print("================================================================================")

    # ---------------------------------------------------------
    # 1. ДИНАМИКА ОТКЛИКОВ В МОДЕЛЬНОМ ВРЕМЕНИ (КОНТРОЛЬНЫЙ ПРОГОН)
    # ---------------------------------------------------------
    print("\n[Этап 1] Моделирование контрольного прогона для динамических графиков...")
    cfg_base = load_config(cfg_path)
    cfg_base.simulation.seed = 42
    cfg_base.simulation.trace = False
    sim_base = SupermarketSimulation(cfg_base)
    sim_base.run()

    # Академический дашборд 2x2 для одиночного прогона
    single_run_path = plot_single_run(sim_base, plots_dir, "single_run.png")
    print(f" -> Сохранен дашборд одиночного прогона: {single_run_path}")

    # График 1: Дискретный отклик (Время покупателя в магазине)
    disc_times = sim_base.stats.time_in_supermarket.timestamps
    disc_vals = sim_base.stats.time_in_supermarket.observations
    disc_cum_avg = sim_base.stats.time_in_supermarket.running_means

    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    ax.scatter(disc_times, disc_vals, color='#3B82F6', alpha=0.55, s=28, label='Отдельные реализации (покупатели)', zorder=3)
    ax.plot(disc_times, disc_cum_avg, color='#DC2626', linewidth=2.5, label='Накопленное среднее', zorder=4)
    ax.axhline(sim_base.stats.time_in_supermarket.mean, color='#16A34A', linestyle='--', linewidth=1.5,
               label=f'Итоговое среднее = {sim_base.stats.time_in_supermarket.mean:.2f} мин')
    ax.set_title('Динамика дискретного отклика: Время покупателя в супермаркете $T_{sys}$')
    ax.set_xlabel('Модельное время выхода покупателя $t$, мин')
    ax.set_ylabel('Время в супермаркете, мин')
    ax.grid(True)
    ax.legend(loc='upper right')
    plot1_path = os.path.join(plots_dir, 'dynamics_time_in_supermarket.png')
    plt.tight_layout()
    plt.savefig(plot1_path, dpi=300)
    plt.close()
    print(f" -> График сохранен: {plot1_path}")

    # График 2: Непрерывный отклик (Суммарная длина очередей)
    cont_history = sim_base.stats.total_queue_len.history
    c_times = [p.time for p in cont_history]
    c_inst = [p.instant_value for p in cont_history]
    c_cum = [p.cumulative_average for p in cont_history]

    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    ax.step(c_times, c_inst, where='post', color='#64748B', alpha=0.45, linewidth=1.2, label='Мгновенная длина очередей $L_q(t)$')
    ax.plot(c_times, c_cum, color='#2563EB', linewidth=2.5, label='Интегральное накопленное среднее $\\bar{L}_q(t)$')
    ax.axhline(sim_base.stats.total_queue_len.mean, color='#DC2626', linestyle='--', linewidth=1.5,
               label=f'Итоговое среднее = {sim_base.stats.total_queue_len.mean:.2f} чел.')
    ax.set_title('Динамика непрерывного отклика: Суммарная длина очередей по всем отделам')
    ax.set_xlabel('Модельное время $t$, мин')
    ax.set_ylabel('Длина очереди, чел.')
    ax.grid(True)
    ax.legend(loc='upper left')
    plot2_path = os.path.join(plots_dir, 'dynamics_queue_length.png')
    plt.tight_layout()
    plt.savefig(plot2_path, dpi=300)
    plt.close()
    print(f" -> График сохранен: {plot2_path}")

    # График 3: Непрерывный отклик (Загрузка продавцов 5 отделов)
    sellers_history = sim_base.stats.busy_sellers_count.history
    s_times = [p.time for p in sellers_history]
    s_inst = [p.instant_value for p in sellers_history]
    s_cum = [p.cumulative_average for p in sellers_history]

    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    ax.step(s_times, s_inst, where='post', color='#94A3B8', alpha=0.4, linewidth=1.0, label='Мгновенное число занятых продавцов')
    ax.plot(s_times, s_cum, color='#D97706', linewidth=2.5, label='Интегральное среднее занятых продавцов')
    ax.axhline(sim_base.stats.busy_sellers_count.mean, color='#B45309', linestyle='--', linewidth=1.5,
               label=f'Среднее = {sim_base.stats.busy_sellers_count.mean:.2f} (из 5)')
    ax.set_title('Динамика использования обслуживающего персонала (продавцов 5 отделов)')
    ax.set_xlabel('Модельное время $t$, мин')
    ax.set_ylabel('Число занятых продавцов')
    ax.set_ylim(-0.2, 5.5)
    ax.grid(True)
    ax.legend(loc='lower right')
    plot3_path = os.path.join(plots_dir, 'dynamics_sellers_utilization.png')
    plt.tight_layout()
    plt.savefig(plot3_path, dpi=300)
    plt.close()
    print(f" -> График сохранен: {plot3_path}")

    # ---------------------------------------------------------
    # 2. АНСАМБЛЕВЫЙ АНАЛИЗ (30 НЕЗАВИСИМЫХ ПРОГОНОВ)
    # ---------------------------------------------------------
    print("\n[Этап 2] Моделирование ансамбля из 30 независимых прогонов...")
    multi_sims = []
    for m in range(30):
        cfg_m = load_config(cfg_path)
        cfg_m.simulation.seed = 500 + m * 43
        cfg_m.simulation.trace = False
        sim_m = SupermarketSimulation(cfg_m)
        sim_m.run()
        multi_sims.append(sim_m)

    multi_run_path = plot_multi_run(multi_sims, plots_dir, "multi_run.png")
    print(f" -> Сохранен ансамблевый дашборд: {multi_run_path}")

    # ---------------------------------------------------------
    # 3. СХОДИМОСТЬ ПРИ ПОВТОРНЫХ ПРОГОНАХ (1000 РЕПЛИКАЦИЙ)
    # ---------------------------------------------------------
    print("\n[Этап 3] Серия из 1000 независимых репликаций для проверки ЗБЧ...")
    N_REPS = 1000
    rep_results = []
    rep_means_time = []
    rep_means_queue = []
    rep_sellers = []
    dept_utils_accum = [0.0] * 5

    for r in range(1, N_REPS + 1):
        cfg_r = load_config(cfg_path)
        cfg_r.simulation.seed = 1000 + r * 37
        cfg_r.simulation.trace = False
        sim_r = SupermarketSimulation(cfg_r)
        res_r = sim_r.run()
        rep_results.append(res_r)
        rep_means_time.append(res_r["avg_time_in_supermarket"])
        rep_means_queue.append(res_r["avg_total_queue_len"])
        rep_sellers.append(res_r["avg_busy_sellers"])
        for idx, u in enumerate(res_r["dept_utilizations"]):
            dept_utils_accum[idx] += u

    mean_dept_utils = [u / N_REPS for u in dept_utils_accum]

    # Академический дашборд сходимости run-to-run (первые 60 прогонов для четкости точек)
    run_to_run_path = plot_run_to_run(rep_results[:60], plots_dir, "run_to_run.png")
    print(f" -> Сохранен дашборд сходимости по репликациям: {run_to_run_path}")

    # График сходимости (1000 репликаций)
    cum_rep_time = np.cumsum(rep_means_time) / np.arange(1, N_REPS + 1)

    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    ax.plot(range(1, N_REPS + 1), cum_rep_time, color='#0284C7', linewidth=2.0, label='Накопленное среднее времени $T_{sys}$')
    ax.axhline(np.mean(rep_means_time), color='#DC2626', linestyle='--', linewidth=1.5,
               label=f'Финальная оценка = {np.mean(rep_means_time):.2f} мин')
    se = np.std(rep_means_time) / np.sqrt(np.arange(1, N_REPS + 1))
    ci_upper = cum_rep_time + 1.96 * se
    ci_lower = cum_rep_time - 1.96 * se
    ax.fill_between(range(1, N_REPS + 1), ci_lower, ci_upper, color='#BAE6FD', alpha=0.5, label='95% Доверительный интервал')

    ax.set_title(f'Сходимость выборочного среднего времени пребывания ($N = {N_REPS}$ прогонов)')
    ax.set_xlabel('Номер репликации')
    ax.set_ylabel('Среднее время в супермаркете, мин')
    ax.grid(True)
    ax.legend(loc='upper right')
    plot4_path = os.path.join(plots_dir, 'convergence_replications.png')
    plt.tight_layout()
    plt.savefig(plot4_path, dpi=300)
    plt.close()
    print(f" -> График сохранен: {plot4_path}")

    # ---------------------------------------------------------
    # 4. АНАЛИЗ ЧУВСТВИТЕЛЬНОСТИ: ВАРИАЦИЯ ВХОДНЫХ ПАРАМЕТРОВ
    # ---------------------------------------------------------
    print("\n[Этап 4] Параметрический эксперимент 1: вариация интенсивности входного потока...")
    mean_intervals = [0.7, 0.85, 1.0, 1.25, 1.5, 1.8, 2.2]
    var_arrival_rates = [1.0 / mi for mi in mean_intervals]
    sweep_data_arr: Dict[float, List[Dict[str, float]]] = {}
    var_times = []
    var_queues = []
    var_util = []

    for mi, lam in zip(mean_intervals, var_arrival_rates):
        batch = []
        for seed_offset in range(60):
            cfg_v = load_config(cfg_path)
            cfg_v.arrival.mean_interval = mi
            cfg_v.simulation.seed = 200 + seed_offset * 19
            cfg_v.simulation.trace = False
            sim_v = SupermarketSimulation(cfg_v)
            res_v = sim_v.run()
            batch.append(res_v)
        sweep_data_arr[lam] = batch
        var_times.append(float(np.mean([r["avg_time_in_supermarket"] for r in batch])))
        var_queues.append(float(np.mean([r["avg_total_queue_len"] for r in batch])))
        var_util.append(float(np.mean([r["seller_utilization_pct"] for r in batch])))

    # Академический график sweep с доверительными интервалами и Пирсоном r
    sweep_arr_path = plot_sensitivity_sweep(
        knob_name="arrival_rate",
        knob_label="Интенсивность прихода $\\lambda$, клиентов/мин",
        knob_values=var_arrival_rates,
        data_by_val=sweep_data_arr,
        out_dir=plots_dir,
        name="sweep_arrival_rate.png"
    )
    print(f" -> Сохранен анализ чувствительности к входному потоку: {sweep_arr_path}")

    # Двухосевой график вариации для обратной совместимости
    fig, ax1 = plt.subplots(figsize=(10, 5), dpi=300)
    color1 = '#2563EB'
    color2 = '#DC2626'
    ax1.set_xlabel('Интенсивность прихода покупателей $\\lambda$, покупателей/мин')
    ax1.set_ylabel('Среднее время в магазине $T_{sys}$, мин', color=color1)
    line1 = ax1.plot(var_arrival_rates, var_times, marker='o', linewidth=2.2, color=color1, label='Время в супермаркете $T_{sys}$')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True)
    ax2 = ax1.twinx()
    ax2.set_ylabel('Суммарная длина очередей $L_q$, чел.', color=color2)
    line2 = ax2.plot(var_arrival_rates, var_queues, marker='s', linewidth=2.2, linestyle='--', color=color2, label='Длина очередей $L_q$')
    ax2.tick_params(axis='y', labelcolor=color2)
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left')
    plt.title('Зависимость откликов от интенсивности входного потока покупателей (Тест монотонности)')
    plot5_path = os.path.join(plots_dir, 'variation_arrival_rate.png')
    plt.tight_layout()
    plt.savefig(plot5_path, dpi=300)
    plt.close()
    print(f" -> График сохранен: {plot5_path}")

    # Вариация времени обслуживания (от 1.0 до 2.2 мин)
    print("\n[Этап 5] Параметрический эксперимент 2: вариация времени обслуживания в отделах...")
    service_means = [1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2]
    sweep_data_serv: Dict[float, List[Dict[str, float]]] = {}
    var_serv_times = []
    var_serv_queues = []

    for sm in service_means:
        batch = []
        for seed_offset in range(60):
            cfg_s = load_config(cfg_path)
            cfg_s.supermarket.service_time.mean = sm
            cfg_s.simulation.seed = 300 + seed_offset * 23
            cfg_s.simulation.trace = False
            sim_s = SupermarketSimulation(cfg_s)
            res_s = sim_s.run()
            batch.append(res_s)
        sweep_data_serv[sm] = batch
        var_serv_times.append(float(np.mean([r["avg_time_in_supermarket"] for r in batch])))
        var_serv_queues.append(float(np.mean([r["avg_total_queue_len"] for r in batch])))

    # Академический график sweep с доверительными интервалами и Пирсоном r
    sweep_serv_path = plot_sensitivity_sweep(
        knob_name="service_time",
        knob_label="Среднее время обслуживания $\\mu_{serv}$, мин",
        knob_values=service_means,
        data_by_val=sweep_data_serv,
        out_dir=plots_dir,
        name="sweep_service_time.png"
    )
    print(f" -> Сохранен анализ чувствительности к времени обслуживания: {sweep_serv_path}")

    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    ax.plot(service_means, var_serv_times, marker='o', linewidth=2.2, color='#7C3AED', label='Время в супермаркете $T_{sys}$')
    ax.plot(service_means, var_serv_queues, marker='^', linewidth=2.2, color='#EA580C', linestyle='--', label='Средняя длина очередей $L_q$')
    ax.set_title('Зависимость откликов от среднего времени обслуживания продавцом $\\mu_{serv}$')
    ax.set_xlabel('Среднее время обслуживания в отделе $\\mu_{serv}$, мин')
    ax.set_ylabel('Значение отклика')
    ax.grid(True)
    ax.legend(loc='upper left')
    plot6_path = os.path.join(plots_dir, 'variation_service_time.png')
    plt.tight_layout()
    plt.savefig(plot6_path, dpi=300)
    plt.close()
    print(f" -> График сохранен: {plot6_path}")

    # ---------------------------------------------------------
    # 5. СРАВНЕНИЕ ЗАГРУЗКИ ОБОРУДОВАНИЯ (SIMULATION VS THEORY)
    # ---------------------------------------------------------
    print("\n[Этап 6] Построение диаграммы загрузки отделов (моделирование vs теория)...")
    theoretical_load = 0.80  # расчетная эффективная загрузка при lambda=1.0, tau=1.8
    util_path = plot_utilization(
        dept_utilizations=mean_dept_utils,
        dept_names=cfg_base.supermarket.department_names,
        theoretical_utilization=theoretical_load,
        out_dir=plots_dir,
        name="utilization.png"
    )
    print(f" -> Сохранена диаграмма загрузки оборудования: {util_path}")

    # Сохраняем агрегированные данные верификации в JSON
    verification_summary = {
        "replications_count": N_REPS,
        "mean_time_in_supermarket": float(np.mean(rep_means_time)),
        "ci95_time_in_supermarket": [float(np.mean(rep_means_time) - 1.96 * np.std(rep_means_time) / np.sqrt(N_REPS)),
                                     float(np.mean(rep_means_time) + 1.96 * np.std(rep_means_time) / np.sqrt(N_REPS))],
        "mean_queue_len": float(np.mean(rep_means_queue)),
        "mean_busy_sellers": float(np.mean(rep_sellers)),
        "mean_seller_utilization_pct": float(np.mean(rep_sellers) / 5.0 * 100.0),
        "mean_dept_utilizations": mean_dept_utils,
        "theoretical_utilization": theoretical_load,
        "arrival_rate_variation": {
            "arrival_rates": var_arrival_rates,
            "times": var_times,
            "queues": var_queues
        },
        "service_time_variation": {
            "service_means": service_means,
            "times": var_serv_times,
            "queues": var_serv_queues
        }
    }

    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(verification_summary, f, ensure_ascii=False, indent=2)

    print(f"\nВсе данные верификации сохранены в: {data_path}")
    print("="*80)
    print("                  ИТОГИ ВЕРИФИКАЦИОННЫХ ЭКСПЕРИМЕНТОВ                          ")
    print("="*80)
    print(f"• Среднее время в супермаркете (по {N_REPS} репликациям): {verification_summary['mean_time_in_supermarket']:.2f} мин")
    print(f"  (95% Доверительный интервал: [{verification_summary['ci95_time_in_supermarket'][0]:.2f}; {verification_summary['ci95_time_in_supermarket'][1]:.2f}] мин)")
    print(f"• Средняя длина очередей по всем отделам:       {verification_summary['mean_queue_len']:.2f} чел.")
    print(f"• Средняя загрузка продавцов:                   {verification_summary['mean_seller_utilization_pct']:.2f} %")
    print("• Все тесты на монотонность и сходимость пройдены УСПЕШНО!")
    print("="*80)


if __name__ == "__main__":
    plots_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "plots"))
    data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "verification_data.json"))
    run_verification_study(plots_dir, data_path)
