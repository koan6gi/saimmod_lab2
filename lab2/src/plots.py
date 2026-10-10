"""
Модуль визуализации результатов имитационного моделирования (Matplotlib).
Реализует академический стандарт визуализации СМО:
1. single_run.png: 2x2 дашборд динамики всех 4 классов откликов в модельном времени одного прогона.
2. multi_run.png: 2x2 дашборд ансамблевого среднего по серии повторных прогонов (индивидуальные траектории + ансамбль).
3. run_to_run.png: 2x2 дашборд сходимости выборочных оценок по закону больших чисел (ЗБЧ).
4. sweep_arrival_rate.png / sweep_service_time.png: параметрический анализ чувствительности с 95% ДИ, регрессией МНК и корреляцией Пирсона r.
5. utilization.png: диаграмма загрузки обслуживающих аппаратов отделов (моделирование vs теория).
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Dict, List, Sequence, Tuple, Any, Optional

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats

# Цветовая палитра - чистый академический стиль
C = ["#2563EB", "#DC2626", "#16A34A", "#D97706", "#7C3AED", "#0284C7", "#EA580C", "#475569"]
INK = "#0F172A"
INK2 = "#475569"
GRID = "#E2E8F0"

matplotlib.rcParams.update({
    "figure.facecolor": "#FFFFFF",
    "axes.facecolor": "#FFFFFF",
    "axes.edgecolor": "#CBD5E1",
    "axes.labelcolor": INK2,
    "axes.titlecolor": INK,
    "axes.titlesize": 10.5,
    "axes.labelsize": 9.5,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.7,
    "grid.linestyle": "--",
    "xtick.color": INK2,
    "ytick.color": INK2,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "legend.fontsize": 8.5,
    "legend.frameon": True,
    "legend.facecolor": "#F8FAFC",
    "legend.edgecolor": "#E2E8F0",
    "lines.linewidth": 1.6,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def _save(fig, out_dir: Path | str, name: str) -> Path:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    target = out_path / name
    fig.savefig(target, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return target


def step_values(series: Sequence[Tuple[float, float]], grid: np.ndarray, initial: float = 0.0) -> np.ndarray:
    """Вычисляет кусочно-постоянный временной ряд (t_i, v_i) на равномерной сетке grid."""
    if not series:
        return np.full_like(grid, initial, dtype=float)
    t = np.array([p[0] for p in series])
    v = np.array([p[1] for p in series])
    idx = np.searchsorted(t, grid, side="right") - 1
    out = np.where(idx >= 0, v[np.clip(idx, 0, len(v) - 1)], initial)
    return out.astype(float)


# -----------------------------------------------------------------------------
# 1. ДАШБОРД ОДНОГО ПРОГОНА (SINGLE RUN)
# -----------------------------------------------------------------------------
def plot_single_run(sim, out_dir: Path | str, name: str = "single_run.png") -> Path:
    """
    Дашборд 2x2 динамики откликов в модельном времени для одного прогона (seed):
    - [0,0] Непрерывный отклик: Суммарная длина очередей L_q(t)
    - [0,1] Дискретный отклик: Время покупателя в супермаркете T_sys
    - [1,0] Аддитивные отклики: Накопленные вошедшие и обслуженные покупатели
    - [1,1] Непрерывный отклик: Число занятых продавцов N_busy(t)
    """
    fig, axes = plt.subplots(2, 2, figsize=(12.5, 8.0), dpi=300)
    fig.suptitle(f"Динамика откликов в модельном времени (Контрольный прогон, seed={sim.config.simulation.seed})",
                 fontsize=12, fontweight="bold", color=INK)

    # 1. Суммарная длина очередей (Непрерывный отклик)
    ax = axes[0][0]
    q_hist = sim.stats.total_queue_len.history
    t_q = [p.time for p in q_hist]
    v_inst = [p.instant_value for p in q_hist]
    v_cum = [p.cumulative_average for p in q_hist]
    ax.step(t_q, v_inst, where="post", color="#94A3B8", linewidth=1.0, alpha=0.6, label="Мгновенная длина $L_q(t)$")
    ax.plot(t_q, v_cum, color=C[0], linewidth=2.0, label="Интегральное среднее $\\bar{L}_q(t)$")
    ax.axhline(sim.stats.total_queue_len.mean, color=C[1], linestyle=":", linewidth=1.4,
               label=f"Итог = {sim.stats.total_queue_len.mean:.2f} чел.")
    ax.set_title("Суммарная длина очередей (Непрерывный отклик)")
    ax.set_xlabel("Модельное время $t$, мин")
    ax.set_ylabel("Покупатели в очередях, чел.")
    ax.legend(loc="upper left")

    # 2. Время в магазине (Дискретный отклик)
    ax = axes[0][1]
    d_times = sim.stats.time_in_supermarket.timestamps
    d_obs = sim.stats.time_in_supermarket.observations
    d_cum = sim.stats.time_in_supermarket.running_means
    ax.scatter(d_times, d_obs, s=14, color=C[0], alpha=0.55, label="Отдельные покупатели $T_i$")
    ax.plot(d_times, d_cum, color=C[1], linewidth=2.2, label="Накопленное среднее $\\bar{T}_{sys}$")
    ax.axhline(sim.stats.time_in_supermarket.mean, color=C[2], linestyle=":", linewidth=1.4,
               label=f"Итог = {sim.stats.time_in_supermarket.mean:.2f} мин")
    ax.set_title("Время покупателя в супермаркете (Дискретный отклик)")
    ax.set_xlabel("Модельное время выхода $t$, мин")
    ax.set_ylabel("Время в системе, мин")
    ax.legend(loc="upper right")

    # 3. Накопленные счетчики (Аддитивные отклики)
    ax = axes[1][0]
    t_arr, v_arr = [p[0] for p in sim.stats.arrivals_history], [p[1] for p in sim.stats.arrivals_history]
    t_srv, v_srv = [p[0] for p in sim.stats.served_history], [p[1] for p in sim.stats.served_history]
    ax.step(t_arr, v_arr, where="post", color=C[0], linewidth=1.8, label=f"Вошло покупателей ({sim.stats.total_arrivals})")
    ax.step(t_srv, v_srv, where="post", color=C[2], linewidth=1.8, label=f"Обслужено и вышло ({sim.stats.total_served})")
    ax.set_title("Кумулятивные счетчики покупателей (Аддитивные отклики)")
    ax.set_xlabel("Модельное время $t$, мин")
    ax.set_ylabel("Количество покупателей, чел.")
    ax.legend(loc="upper left")

    # 4. Число занятых продавцов (Непрерывный отклик)
    ax = axes[1][1]
    s_hist = sim.stats.busy_sellers_count.history
    t_s = [p.time for p in s_hist]
    s_inst = [p.instant_value for p in s_hist]
    s_cum = [p.cumulative_average for p in s_hist]
    ax.step(t_s, s_inst, where="post", color="#CBD5E1", linewidth=0.9, alpha=0.7, label="Мгновенно занято")
    ax.plot(t_s, s_cum, color=C[3], linewidth=2.2, label="Интегральное среднее")
    ax.axhline(sim.stats.busy_sellers_count.mean, color=C[1], linestyle=":", linewidth=1.4,
               label=f"Итог = {sim.stats.busy_sellers_count.mean:.2f} / 5")
    ax.set_ylim(-0.2, 5.4)
    ax.set_title("Занятость обслуживающего персонала (5 продавцов)")
    ax.set_xlabel("Модельное время $t$, мин")
    ax.set_ylabel("Число занятых продавцов")
    ax.legend(loc="lower right")

    fig.tight_layout()
    return _save(fig, out_dir, name)


# -----------------------------------------------------------------------------
# 2. АНСАМБЛЕВЫЙ ДАШБОРД (MULTI RUN / ENSEMBLE)
# -----------------------------------------------------------------------------
def plot_multi_run(sim_runs: Sequence[Any], out_dir: Path | str, name: str = "multi_run.png") -> Path:
    """
    Дашборд 2x2 ансамблевого среднего по серии прогонов:
    Тонкие полупрозрачные линии — отдельные реализации, жирная линия — ансамблевое среднее по времени.
    """
    T = max(sim.stats.simulation_end_time for sim in sim_runs)
    grid = np.linspace(0, T, 400)
    fig, axes = plt.subplots(2, 2, figsize=(12.5, 8.0), dpi=300)
    fig.suptitle(f"Ансамблевые траектории откликов в модельном времени ({len(sim_runs)} независимых прогонов)\n"
                 f"(тонкие линии: индивидуальные прогоны, жирная линия: ансамблевое среднее)",
                 fontsize=11.5, fontweight="bold", color=INK)

    # 1. Среднее время пребывания
    ax = axes[0][0]
    all_time_curves = []
    for s in sim_runs:
        ts = s.stats.time_in_supermarket.timestamps
        rm = s.stats.time_in_supermarket.running_means
        if len(ts) > 0:
            curve = step_values(list(zip(ts, rm)), grid, initial=np.nan)
            all_time_curves.append(curve)
            ax.plot(grid, curve, color=C[0], alpha=0.18, linewidth=0.8)
    if all_time_curves:
        with np.errstate(invalid="ignore"):
            ens_time = np.nanmean(np.vstack(all_time_curves), axis=0)
        ax.plot(grid, ens_time, color=C[1], linewidth=2.4, label="Ансамблевое среднее")
        valid_final = ens_time[~np.isnan(ens_time)]
        if len(valid_final) > 0:
            final_val = valid_final[-1]
            ax.axhline(final_val, color=INK2, linestyle=":", linewidth=1.2,
                       label=f"Установившийся уровень: {final_val:.2f} мин")
    ax.set_title("Время покупателя в супермаркете $\\bar{T}_{sys}(t)$")
    ax.set_xlabel("Модельное время $t$, мин")
    ax.set_ylabel("Время, мин")
    ax.legend(loc="upper right")

    # 2. Суммарная длина очередей
    ax = axes[0][1]
    all_q_curves = []
    for s in sim_runs:
        pts = [(p.time, p.cumulative_average) for p in s.stats.total_queue_len.history]
        curve = step_values(pts, grid, initial=0.0)
        all_q_curves.append(curve)
        ax.plot(grid, curve, color=C[0], alpha=0.18, linewidth=0.8)
    ens_q = np.mean(np.vstack(all_q_curves), axis=0)
    ax.plot(grid, ens_q, color=C[1], linewidth=2.4, label="Ансамблевое среднее")
    final_q = ens_q[-1]
    ax.axhline(final_q, color=INK2, linestyle=":", linewidth=1.2,
               label=f"Установившийся уровень: {final_q:.2f} чел.")
    ax.set_title("Суммарная длина очередей $\\bar{L}_q(t)$")
    ax.set_xlabel("Модельное время $t$, мин")
    ax.set_ylabel("Очередь, чел.")
    ax.legend(loc="upper left")

    # 3. Кумулятивные счетчики покупателей
    ax = axes[1][0]
    all_arr, all_srv = [], []
    for s in sim_runs:
        arr_pts = s.stats.arrivals_history
        srv_pts = s.stats.served_history
        c_arr = step_values(arr_pts, grid, initial=0.0)
        c_srv = step_values(srv_pts, grid, initial=0.0)
        all_arr.append(c_arr)
        all_srv.append(c_srv)
        ax.plot(grid, c_arr, color=C[0], alpha=0.12, linewidth=0.7)
        ax.plot(grid, c_srv, color=C[2], alpha=0.12, linewidth=0.7)
    mean_arr = np.mean(np.vstack(all_arr), axis=0)
    mean_srv = np.mean(np.vstack(all_srv), axis=0)
    ax.plot(grid, mean_arr, color=C[0], linewidth=2.2, label=f"Входной поток (ср. {mean_arr[-1]:.0f})")
    ax.plot(grid, mean_srv, color=C[2], linewidth=2.2, label=f"Обслужено (ср. {mean_srv[-1]:.0f})")
    ax.set_title("Накопленное число покупателей")
    ax.set_xlabel("Модельное время $t$, мин")
    ax.set_ylabel("Покупатели, чел.")
    ax.legend(loc="upper left")

    # 4. Среднее число занятых продавцов
    ax = axes[1][1]
    all_sellers = []
    for s in sim_runs:
        pts = [(p.time, p.cumulative_average) for p in s.stats.busy_sellers_count.history]
        curve = step_values(pts, grid, initial=0.0)
        all_sellers.append(curve)
        ax.plot(grid, curve, color=C[3], alpha=0.18, linewidth=0.8)
    ens_sellers = np.mean(np.vstack(all_sellers), axis=0)
    ax.plot(grid, ens_sellers, color=C[1], linewidth=2.4, label="Ансамблевое среднее")
    final_s = ens_sellers[-1]
    ax.axhline(final_s, color=INK2, linestyle=":", linewidth=1.2,
               label=f"Установившийся уровень: {final_s:.2f} (из 5)")
    ax.set_ylim(-0.1, 4.0)
    ax.set_title("Использование продавцов 5 отделов $\\bar{N}_{busy}(t)$")
    ax.set_xlabel("Модельное время $t$, мин")
    ax.set_ylabel("Число занятых продавцов")
    ax.legend(loc="lower right")

    fig.tight_layout()
    return _save(fig, out_dir, name)


# -----------------------------------------------------------------------------
# 3. СХОДИМОСТЬ ПО РЕПЛИКАЦИЯМ (RUN TO RUN)
# -----------------------------------------------------------------------------
def plot_run_to_run(results_list: Sequence[Dict[str, float]], out_dir: Path | str,
                    name: str = "run_to_run.png") -> Path:
    """
    Дашборд 2x2 сходимости откликов при накоплении независимых репликаций (ЗБЧ):
    Точки — значения в отдельном прогоне; сплошная линия — кумулятивное выборочное среднее.
    """
    n = np.arange(1, len(results_list) + 1)
    fig, axes = plt.subplots(2, 2, figsize=(12.5, 7.5), dpi=300)
    fig.suptitle(f"Сходимость выборочных средних по числу независимых репликаций ($N = {len(results_list)}$)\n"
                 f"(точки: значения отдельных прогонов, сплошная линия: кумулятивное среднее)",
                 fontsize=11.5, fontweight="bold", color=INK)

    configs = [
        (axes[0][0], "avg_time_in_supermarket", "Среднее время в магазине $T_{sys}$", "мин", C[0]),
        (axes[0][1], "avg_total_queue_len", "Средняя длина очередей $L_q$", "чел.", C[1]),
        (axes[1][0], "avg_busy_sellers", "Число занятых продавцов $N_{busy}$", "продавцов", C[3]),
        (axes[1][1], "total_served", "Обслужено покупателей $N_{serv}$", "чел.", C[2]),
    ]

    for ax, key, title, unit, color in configs:
        vals = np.array([r[key] for r in results_list])
        cum_mean = np.cumsum(vals) / n
        ax.scatter(n, vals, color=color, alpha=0.35, s=12, label="Значение в прогоне")
        ax.plot(n, cum_mean, color=INK, linewidth=2.2, label=f"Кумулятивное среднее ({cum_mean[-1]:.2f})")
        # 95% доверительный интервал для среднего
        if len(vals) > 5:
            se = np.array([np.std(vals[:i]) / np.sqrt(i) if i > 1 else 0.0 for i in n])
            ax.fill_between(n, cum_mean - 1.96 * se, cum_mean + 1.96 * se, color=color, alpha=0.18, label="95% ДИ")
        ax.set_title(title)
        ax.set_xlabel("Номер прогона")
        ax.set_ylabel(unit)
        ax.legend(loc="upper right")

    fig.tight_layout()
    return _save(fig, out_dir, name)


# -----------------------------------------------------------------------------
# 4. АНАЛИЗ ЧУВСТВИТЕЛЬНОСТИ С ДОВЕРИТЕЛЬНЫМИ ИНТЕРВАЛАМИ И МНК (SWEEPS)
# -----------------------------------------------------------------------------
def plot_sensitivity_sweep(knob_name: str, knob_label: str, knob_values: Sequence[float],
                           data_by_val: Dict[float, List[Dict[str, float]]],
                           out_dir: Path | str, name: str) -> Path:
    """
    Академический график анализа чувствительности (3 отклика на один входной фактор):
    - Точки со средними значениями и усами 95% доверительного интервала (errorbar).
    - Линейная аппроксимация МНК y = kx + b.
    - Коэффициент линейной корреляции Пирсона r и p-value критерия Стьюдента.
    """
    x = np.asarray(knob_values, float)
    fig, axes = plt.subplots(1, 3, figsize=(15.0, 4.5), dpi=300)
    fig.suptitle(f"Анализ чувствительности откликов к фактору: {knob_label}",
                 fontsize=12, fontweight="bold", color=INK)

    metrics = [
        ("avg_time_in_supermarket", "Время в супермаркете $T_{sys}$", "мин", C[0]),
        ("avg_total_queue_len", "Суммарная длина очередей $L_q$", "чел.", C[1]),
        ("avg_busy_sellers", "Число занятых продавцов $N_{busy}$", "продавцов", C[3]),
    ]

    for ax, (key, label, unit, color) in zip(axes, metrics):
        means = np.array([np.mean([run[key] for run in data_by_val[v]]) for v in knob_values])
        stds = np.array([np.std([run[key] for run in data_by_val[v]], ddof=1) for v in knob_values])
        ns = np.array([len(data_by_val[v]) for v in knob_values])
        cis = 1.96 * stds / np.sqrt(ns)

        # 1. Errorbar с 95% ДИ
        ax.errorbar(x, means, yerr=cis, fmt="o", color=color, ecolor=color, elinewidth=1.6,
                    capsize=4, markersize=6, label=f"Среднее с 95% ДИ (N={ns[0]})")

        # 2. МНК прямая
        if len(x) > 1 and np.std(x) > 0:
            k, b = np.polyfit(x, means, 1)
            x_line = np.linspace(x.min(), x.max(), 100)
            ax.plot(x_line, k * x_line + b, color=INK, linestyle="--", linewidth=1.3,
                    label=f"МНК: $y = {k:+.2f}x {b:+.2f}$")

        # 3. Корреляция Пирсона r и p-value
        r, p_val = stats.pearsonr(x, means)
        dep_kind = "прямая" if r > 0 else "обратная"
        significance = "значима ($p < 0.05$)" if p_val < 0.05 else "не значима"
        ax.set_title(f"{label}\n$r = {r:+.3f}$ ({dep_kind}, {significance})", fontsize=10)
        ax.set_xlabel(knob_label)
        ax.set_ylabel(f"{label}, {unit}")
        ax.legend(loc="upper left")

    fig.tight_layout()
    return _save(fig, out_dir, name)


# -----------------------------------------------------------------------------
# 5. ГИСТОГРАММА ЗАГРУЗКИ ОБОРУДОВАНИЯ (UTILIZATION)
# -----------------------------------------------------------------------------
def plot_utilization(dept_utilizations: Sequence[float], dept_names: Sequence[str],
                     theoretical_utilization: float, out_dir: Path | str,
                     name: str = "utilization.png") -> Path:
    """
    Сравнение коэффициентов загрузки продавцов отделов (Simulation vs Analytical Theory).
    """
    fig, ax = plt.subplots(figsize=(9.0, 4.8), dpi=300)
    labels = list(dept_names) + ["В среднем по магазину"]
    mean_all = float(np.mean(dept_utilizations))
    sim_vals = list(dept_utilizations) + [mean_all]

    x = np.arange(len(labels))
    w = 0.38

    ax.bar(x - w / 2, sim_vals, w, color=C[0], label="Имитационное моделирование (Sim)")
    ax.bar(x + w / 2, [theoretical_utilization] * len(labels), w, color=C[3],
           label=f"Теоретический расчет по СМО ({theoretical_utilization:.2f})")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Коэффициент использования продавцов $\\rho$")
    ax.set_title("Сравнение коэффициентов загрузки обслуживающего персонала (Simulation vs Theory)",
                 fontsize=11, fontweight="bold")
    ax.legend(loc="upper right")

    # Подписи значений над столбиками
    for i, val in enumerate(sim_vals):
        ax.text(x[i] - w / 2, val + 0.02, f"{val:.2f}", ha="center", va="bottom", fontsize=8)
    for i in range(len(labels)):
        ax.text(x[i] + w / 2, theoretical_utilization + 0.02, f"{theoretical_utilization:.2f}",
                ha="center", va="bottom", fontsize=8)

    fig.tight_layout()
    return _save(fig, out_dir, name)
