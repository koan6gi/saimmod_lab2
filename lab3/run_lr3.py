import sys
import os

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import json
from typing import List, Dict, Any
import numpy as np
import scipy.stats as stats
from scipy.ndimage import uniform_filter1d

# Добавляем путь к корню lab3
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from src.config import SimulationConfig, SupermarketConfig, ServiceTimeParams, load_lab3_config
from src.simulation import SupermarketSimulation
from plotter import (
    plot_task_1_1,
    plot_task_1_2,
    plot_task_1_3,
    plot_task_1_4,
    plot_task_1_5,
    plot_task_1_6,
)
from report_builder import build_markdown_report


def build_supermarket_config(raw_cfg: Dict[str, Any]) -> SupermarketConfig:
    sc = raw_cfg.get("supermarket", {})
    return SupermarketConfig(
        num_departments=int(sc.get("num_departments", 5)),
        department_names=sc.get("department_names", ["Бакалея", "Молочный", "Мясной", "Овощи и фрукты", "Кулинария"]),
        mean_arrival_interval=float(sc.get("mean_arrival_interval", 1.0)),
        service_time=ServiceTimeParams(
            mean=float(sc.get("service_mean", 1.8)),
            std=float(sc.get("service_std", 0.5)),
            min_time=float(sc.get("service_min", 0.4))
        )
    )


# -----------------------------------------------------------------------------
# ЗАДАЧА 1.1: ПРОВЕРКА НОРМАЛЬНОСТИ ОТКЛИКА T_sys (КРИТЕРИЙ ХИ-КВАДРАТ)
# -----------------------------------------------------------------------------
def solve_task_1_1(raw_cfg: Dict[str, Any], plots_dir: str) -> Dict[str, Any]:
    task_cfg = raw_cfg["task_1_1"]
    print("\n" + "=" * 78)
    print("ЗАДАЧА 1.1: ПРОВЕРКА ГИПОТЕЗЫ О НОРМАЛЬНОСТИ ОТКЛИКА T_sys (КРИТЕРИЙ ХИ-КВАДРАТ)")
    print("=" * 78)

    n_reps = int(task_cfg["n_reps"])
    sim_time = float(task_cfg["sim_time"])
    seed_start = int(task_cfg.get("seed_start", 10000))
    responses = []

    print(f"Выполнение {n_reps} длинных повторных прогонов (T = {sim_time:.0f} мин)...")
    for s in range(n_reps):
        sc = build_supermarket_config(raw_cfg)
        cfg = SimulationConfig(
            simulation_time=sim_time,
            warmup_time=0.0,
            rng_seed=seed_start + s,
            supermarket=sc
        )
        sim = SupermarketSimulation(cfg)
        res = sim.run()
        responses.append(float(res["avg_time_in_supermarket"]))

    responses = np.array(responses)
    mean_val = float(np.mean(responses))
    std_val = float(np.std(responses, ddof=1))

    # Формула Стерджеса: k = 1 + floor(3.322 * lg(N))
    k_init = int(1 + np.floor(3.322 * np.log10(n_reps)))
    if k_init < 5:
        k_init = 5

    quantiles = [float(stats.norm.ppf(i / k_init, loc=mean_val, scale=std_val)) for i in range(1, k_init)]
    cuts = [-np.inf] + quantiles + [np.inf]
    raw_obs = []
    for i in range(k_init):
        cnt = int(np.sum((responses >= cuts[i]) & (responses < cuts[i + 1])))
        raw_obs.append(cnt)

    def calc_theor_exp(cut_list: List[float]) -> List[float]:
        return [
            n_reps * (stats.norm.cdf(cut_list[i + 1], loc=mean_val, scale=std_val) -
                      stats.norm.cdf(cut_list[i], loc=mean_val, scale=std_val))
            for i in range(len(cut_list) - 1)
        ]

    working_cuts = list(cuts)
    working_obs = list(raw_obs)
    working_exp = calc_theor_exp(working_cuts)
    initial_k = len(working_exp)

    # Проверка правила Кохрана / Пирсона
    had_merging = False
    num_merges = 0
    while True:
        k_curr = len(working_exp)
        if k_curr <= 4:
            break
        violates_1 = [i for i, e in enumerate(working_exp) if e < 1.0]
        violates_5 = [i for i, e in enumerate(working_exp) if e < 5.0]

        if not violates_1 and (len(violates_5) / k_curr <= 0.20):
            break

        had_merging = True
        num_merges += 1
        m_idx = int(np.argmin(working_exp))
        if m_idx == 0:
            target_idx = 1
        elif m_idx == k_curr - 1:
            target_idx = k_curr - 2
        else:
            target_idx = m_idx - 1 if working_exp[m_idx - 1] < working_exp[m_idx + 1] else m_idx + 1

        idx_low = min(m_idx, target_idx)
        idx_high = max(m_idx, target_idx)

        working_obs[idx_low] += working_obs[idx_high]
        del working_obs[idx_high]
        del working_cuts[idx_high]
        working_exp = calc_theor_exp(working_cuts)

    k_final = len(working_exp)

    table_rows = []
    for i in range(k_final):
        obs_val = working_obs[i]
        exp_val = working_exp[i]
        c_left = working_cuts[i]
        c_right = working_cuts[i + 1]
        disp_left = mean_val - 3.5 * std_val if np.isneginf(c_left) else c_left
        disp_right = mean_val + 3.5 * std_val if np.isposinf(c_right) else c_right
        obs_freq = obs_val / n_reps
        theor_prob = exp_val / n_reps
        norm_dev = ((obs_freq - theor_prob) ** 2) / theor_prob if theor_prob > 0 else 0.0

        table_rows.append({
            "num": i + 1,
            "cut_left": float(disp_left),
            "cut_right": float(disp_right),
            "observed": int(obs_val),
            "expected": float(exp_val),
            "obs_freq": float(obs_freq),
            "theor_prob": float(theor_prob),
            "norm_dev": float(norm_dev),
        })

    chi2_stat = float(sum(((o - e) ** 2) / e for o, e in zip(working_obs, working_exp)))
    df = k_final - 1 - 2
    if df < 1:
        df = 1
    chi2_crit = float(stats.chi2.ppf(0.95, df=df))
    p_value = float(1.0 - stats.chi2.cdf(chi2_stat, df=df))
    is_normal = bool(chi2_stat < chi2_crit)

    cells_less_5 = sum(1 for e in working_exp if e < 5.0)
    pct_less_5 = (cells_less_5 / k_final) * 100.0
    min_exp = float(min(working_exp))

    print(f"Выборочные оценки: M = {mean_val:.3f} мин, S = {std_val:.3f} мин")
    print(f"Количество интервалов (Стерджес -> итоговое): {initial_k} -> {k_final}")
    print(f"Проверка правила Кохрана: min(E_i) = {min_exp:.2f} (≥1.0), ячеек с E_i < 5: {cells_less_5}/{k_final} ({pct_less_5:.1f}% ≤ 20%)")
    print(f"Статистика Пирсона: chi2 = {chi2_stat:.4f}, df = {df}, chi2_crit(0.05) = {chi2_crit:.4f}")
    print(f"p-value = {p_value:.4f}")
    print(f"Результат проверки: {'ГИПОТЕЗА О НОРМАЛЬНОСТИ ПРИНИМАЕТСЯ' if is_normal else 'ГИПОТЕЗА ОТВЕРГАЕТСЯ'}")

    plot_path = plot_task_1_1(
        responses=responses.tolist(),
        working_cuts=working_cuts,
        mean_val=mean_val,
        std_val=std_val,
        k_final=k_final,
        min_exp=min_exp,
        cells_less_5=cells_less_5,
        n_reps=n_reps,
        sim_time=sim_time,
        df=df,
        chi2_stat=chi2_stat,
        chi2_crit=chi2_crit,
        p_value=p_value,
        is_normal=is_normal,
        plots_dir=plots_dir
    )

    return {
        "mean": mean_val,
        "std": std_val,
        "n_reps": n_reps,
        "sim_time": sim_time,
        "k_initial": initial_k,
        "k_intervals": k_final,
        "had_merging": had_merging,
        "num_merges": num_merges,
        "min_expected": min_exp,
        "cells_less_5": cells_less_5,
        "pct_less_5": pct_less_5,
        "chi2_stat": chi2_stat,
        "df": df,
        "chi2_crit": chi2_crit,
        "p_value": p_value,
        "is_normal": is_normal,
        "table": table_rows,
        "plot_path": plot_path
    }


# -----------------------------------------------------------------------------
# ЗАДАЧА 1.2: ТОЧЕЧНЫЕ И ИНТЕРВАЛЬНЫЕ ОЦЕНКИ В ОПЫТЕ ИЗ 20 ПРОГОНОВ (α = 0.05)
# -----------------------------------------------------------------------------
def solve_task_1_2(raw_cfg: Dict[str, Any], plots_dir: str) -> Dict[str, Any]:
    task_cfg = raw_cfg["task_1_2"]
    print("\n" + "=" * 78)
    print("ЗАДАЧА 1.2: ТОЧЕЧНЫЕ И ИНТЕРВАЛЬНЫЕ ОЦЕНКИ В ОПЫТЕ ИЗ 20 ПРОГОНОВ (α = 0.05)")
    print("=" * 78)

    n_reps = int(task_cfg["n_reps"])
    sim_time = float(task_cfg["sim_time"])
    seed_start = int(task_cfg.get("seed_start", 3000))
    times_in_sys = []
    seller_utils = []

    print(f"Выполнение {n_reps} повторных прогонов (T = {sim_time:.0f} мин)...")
    for s in range(n_reps):
        sc = build_supermarket_config(raw_cfg)
        cfg = SimulationConfig(
            simulation_time=sim_time,
            rng_seed=seed_start + s,
            supermarket=sc
        )
        sim = SupermarketSimulation(cfg)
        res = sim.run()
        times_in_sys.append(float(res["avg_time_in_supermarket"]))
        seller_utils.append(float(res["seller_utilization_pct"]))

    def compute_estimates(data: List[float], name: str) -> Dict[str, Any]:
        arr = np.array(data)
        n = len(arr)
        mean = float(np.mean(arr))
        s2 = float(np.var(arr, ddof=1))
        s = float(np.std(arr, ddof=1))
        se = s / np.sqrt(n)
        cv = (s / mean) * 100.0 if mean > 0 else 0.0

        t_crit = float(stats.t.ppf(0.975, df=n - 1))
        delta_stud = t_crit * se
        ci_stud = [mean - delta_stud, mean + delta_stud]

        # Несмещенный коэффициент асимметрии и интервал Уиллинка
        mu3 = sum((arr[i] - mean) ** 3 for i in range(n)) * n / ((n - 1) * (n - 2))
        skewness = mu3 / (s ** 3) if s > 0 else 0.0
        a = mu3 / (6.0 * np.sqrt(n) * (s ** 3)) if s > 0 else 0.0

        term_left = 1.0 + 6.0 * a * (t_crit - a)
        term_right = 1.0 + 6.0 * a * (-t_crit - a)
        if term_left > 0 and term_right > 0 and abs(a) > 1e-9:
            g_left = ((term_left ** (1.0 / 3.0)) - 1.0) * 0.5 / a
            g_right = ((term_right ** (1.0 / 3.0)) - 1.0) * 0.5 / a
            ci_willink = [mean - g_left * s / np.sqrt(n), mean - g_right * s / np.sqrt(n)]
        else:
            ci_willink = ci_stud

        return {
            "name": name,
            "data": [float(x) for x in arr],
            "mean": mean,
            "variance": s2,
            "std": s,
            "se": se,
            "cv_pct": cv,
            "skewness": skewness,
            "ci_student": [float(ci_stud[0]), float(ci_stud[1])],
            "ci_willink": [float(ci_willink[0]), float(ci_willink[1])],
            "half_width_stud": delta_stud,
        }

    est_time = compute_estimates(times_in_sys, "T_sys (время в супермаркете, мин)")
    est_util = compute_estimates(seller_utils, "ρ (коэффициент загрузки продавцов, %)")

    print(f"Отклик T_sys: M = {est_time['mean']:.3f} мин, S = {est_time['std']:.3f} мин, γ₁ = {est_time['skewness']:+.3f}")
    print(f"  * 95% ДИ Стьюдента: [{est_time['ci_student'][0]:.2f}; {est_time['ci_student'][1]:.2f}] мин")
    print(f"  * 95% ДИ Уиллинка:  [{est_time['ci_willink'][0]:.2f}; {est_time['ci_willink'][1]:.2f}] мин")
    print(f"Отклик загрузки ρ: M = {est_util['mean']:.2f}%, S = {est_util['std']:.2f}%, γ₁ = {est_util['skewness']:+.3f}")

    plot_path = plot_task_1_2(est_time, est_util, plots_dir)

    return {
        "time_in_sys": est_time,
        "seller_util": est_util,
        "plot_path": plot_path
    }


# -----------------------------------------------------------------------------
# ЗАДАЧА 1.3: ОЦЕНКА ЗАВИСИМОСТИ ТОЧНОСТИ ОТ ЧИСЛА ПРОГОНОВ (ПОИСК N_5%)
# -----------------------------------------------------------------------------
def solve_task_1_3(raw_cfg: Dict[str, Any], plots_dir: str) -> Dict[str, Any]:
    task_cfg = raw_cfg["task_1_3"]
    print("\n" + "=" * 78)
    print("ЗАДАЧА 1.3: ОЦЕНКА ЗАВИСИМОСТИ ТОЧНОСТИ ОТ ЧИСЛА ПРОГОНОВ (ПОИСК N_5%)")
    print("=" * 78)

    max_runs = int(task_cfg["max_runs"])
    sim_time = float(task_cfg["sim_time"])
    target_err = float(task_cfg.get("target_error_pct", 5.0))
    seed_start = int(task_cfg.get("seed_start", 2000))
    sample_pool = []

    print(f"Набор пула из {max_runs} независимых прогонов...")
    for s in range(max_runs):
        sc = build_supermarket_config(raw_cfg)
        cfg = SimulationConfig(
            simulation_time=sim_time,
            rng_seed=seed_start + s,
            supermarket=sc
        )
        sim = SupermarketSimulation(cfg)
        res = sim.run()
        sample_pool.append(float(res["avg_time_in_supermarket"]))

    n_points = []
    rel_errors = []
    n_5pct = None
    err_at_n5 = None

    for n in range(2, max_runs + 1):
        sub = sample_pool[:n]
        m = float(np.mean(sub))
        s = float(np.std(sub, ddof=1))
        t_crit = float(stats.t.ppf(0.975, df=n - 1))
        delta = t_crit * s / np.sqrt(n)
        eps = (delta / m) * 100.0 if m > 0 else 0.0

        n_points.append(n)
        rel_errors.append(eps)

        if n_5pct is None and eps <= target_err and n >= 5:
            n_5pct = n
            err_at_n5 = eps

    if n_5pct is None:
        n_5pct = max_runs
        err_at_n5 = rel_errors[-1]

    # Теоретическая формула: N_theor = (t * V / eps_target)^2
    pool_arr = np.array(sample_pool)
    v_est = (float(np.std(pool_arr, ddof=1)) / float(np.mean(pool_arr))) * 100.0
    n_theor = int(np.ceil((1.96 * v_est / target_err) ** 2))

    print(f"Теоретическая оценка числа прогонов (при V = {v_est:.1f}%): N_теор = {n_theor}")
    print(f"Эмпирическое число прогонов: N* = {n_5pct} (погрешность ε = {err_at_n5:.2f}%)")
    print(f"При N = {max_runs} погрешность составляет: ε = {rel_errors[-1]:.2f}%")

    plot_path = plot_task_1_3(
        n_points=n_points,
        relative_errors=rel_errors,
        target_err=target_err,
        n_5pct=n_5pct,
        err_at_n5=err_at_n5,
        max_runs=max_runs,
        plots_dir=plots_dir
    )

    return {
        "n_5pct": n_5pct,
        "n_theor": n_theor,
        "err_at_n5": err_at_n5,
        "max_runs": max_runs,
        "final_error": rel_errors[-1],
        "plot_path": plot_path
    }


# -----------------------------------------------------------------------------
# ЗАДАЧА 1.4: УМЕНЬШЕНИЕ ВРЕМЕНИ ПРОГОНА С ИСКЛЮЧЕНИЕМ ПЕРЕХОДНОГО ПЕРИОДА
# -----------------------------------------------------------------------------
def solve_task_1_4(raw_cfg: Dict[str, Any], plots_dir: str) -> Dict[str, Any]:
    task_cfg = raw_cfg["task_1_4"]
    print("\n" + "=" * 78)
    print("ЗАДАЧА 1.4: УМЕНЬШЕНИЕ ВРЕМЕНИ ПРОГОНА С ИСКЛЮЧЕНИЕМ ПЕРЕХОДНОГО ПЕРИОДА (WARM-UP)")
    print("=" * 78)

    warmup_time = float(task_cfg.get("warmup_time", 25.0))
    t0_long = float(task_cfg.get("t0_long", 600.0))
    t1_short = float(task_cfg.get("t1_short", 300.0))
    n_sample = int(task_cfg.get("n_sample", 30))
    seed0 = int(task_cfg.get("seed_start_0", 5000))
    seed1 = int(task_cfg.get("seed_start_1", 6000))

    print(f"1) Эталонный опыт {n_sample} прогонов на интервале T0 = {t0_long:.0f} мин (процедура Уэлча)...")
    time_bins = np.arange(0, t0_long + 1, 15.0)
    bin_centers = (time_bins[:-1] + time_bins[1:]) / 2.0
    bin_runs = []
    sample_y0 = []

    for s in range(n_sample):
        sc = build_supermarket_config(raw_cfg)
        cfg0 = SimulationConfig(
            simulation_time=t0_long,
            warmup_time=0.0,
            rng_seed=seed0 + s,
            supermarket=sc
        )
        sim0 = SupermarketSimulation(cfg0)
        res0 = sim0.run()
        sample_y0.append(float(res0["avg_time_in_supermarket"]))

        timestamps = np.array(sim0.stats.time_in_supermarket.timestamps)
        observations = np.array(sim0.stats.time_in_supermarket.observations)
        row = []
        for i in range(len(time_bins) - 1):
            mask = (timestamps >= time_bins[i]) & (timestamps < time_bins[i + 1])
            if np.any(mask):
                row.append(float(np.mean(observations[mask])))
            else:
                row.append(np.nan)
        bin_runs.append(row)

    bin_runs = np.array(bin_runs)
    welch_instant = []
    for col in range(bin_runs.shape[1]):
        col_vals = bin_runs[:, col]
        valid = col_vals[~np.isnan(col_vals)]
        welch_instant.append(float(np.mean(valid)) if len(valid) > 0 else 0.0)
    welch_instant = np.array(welch_instant)
    welch_mean = uniform_filter1d(welch_instant, size=3)

    print(f"2) Сокращенный опыт {n_sample} прогонов на T1 = {t1_short:.0f} мин с отсечением warm-up {warmup_time:.0f} мин...")
    sample_y1 = []
    for s in range(n_sample):
        sc = build_supermarket_config(raw_cfg)
        cfg1 = SimulationConfig(
            simulation_time=t1_short,
            warmup_time=warmup_time,
            rng_seed=seed1 + s,
            supermarket=sc
        )
        sim1 = SupermarketSimulation(cfg1)
        res1 = sim1.run()
        sample_y1.append(float(res1["avg_time_in_supermarket"]))

    sample_y0 = np.array(sample_y0)
    sample_y1 = np.array(sample_y1)

    m0, s0 = float(np.mean(sample_y0)), float(np.std(sample_y0, ddof=1))
    m1, s1 = float(np.mean(sample_y1)), float(np.std(sample_y1, ddof=1))

    # F-критерий Фишера
    f_stat = float((s1 ** 2) / (s0 ** 2)) if s0 > 0 else 1.0
    f_crit = float(stats.f.ppf(0.975, dfd=n_sample - 1, dfn=n_sample - 1))
    var_equal = bool(f_stat < f_crit)

    # Двухвыборочный t-критерий Уэлча
    t_stat_val, t_p_val = stats.ttest_ind(sample_y0, sample_y1, equal_var=var_equal)
    t_stat_val = float(t_stat_val)
    t_p_val = float(t_p_val)
    t_crit = float(stats.t.ppf(0.975, df=2 * n_sample - 2))
    means_equal = bool(abs(t_stat_val) < t_crit)

    print(f"Выборка Y0 (T={t0_long:.0f} мин):  M0 = {m0:.3f} мин, S0 = {s0:.3f} мин")
    print(f"Выборка Y1 (T={t1_short:.0f} мин, w={warmup_time:.0f}): M1 = {m1:.3f} мин, S1 = {s1:.3f} мин")
    print(f"F-тест: F = {f_stat:.3f}, F_кр = {f_crit:.3f} -> дисперсии {'равны' if var_equal else 'не равны'}")
    print(f"t-тест Уэлча: |t| = {abs(t_stat_val):.3f}, t_кр = {t_crit:.3f}, p-value = {t_p_val:.4f}")
    print(f"Результат: гипотеза о сокращении времени прогона {'ПРИНЯТА' if means_equal else 'ОТВЕРГНУТА'}")

    plot_path = plot_task_1_4(
        bin_centers=bin_centers,
        welch_mean=welch_mean,
        bin_runs=bin_runs,
        warmup_time=warmup_time,
        m0=m0,
        s0=s0,
        m1=m1,
        s1=s1,
        t0_long=t0_long,
        sample_y0=sample_y0.tolist(),
        sample_y1=sample_y1.tolist(),
        t_stat_val=t_stat_val,
        t_crit=t_crit,
        t_p_val=t_p_val,
        plots_dir=plots_dir
    )

    return {
        "warmup_time": warmup_time,
        "t0_long": t0_long,
        "t1_short": t1_short,
        "n_sample": n_sample,
        "m0": m0,
        "s0": s0,
        "m1": m1,
        "s1": s1,
        "f_stat": f_stat,
        "f_crit": f_crit,
        "var_equal": var_equal,
        "t_stat": t_stat_val,
        "t_crit": t_crit,
        "t_p_val": t_p_val,
        "means_equal": means_equal,
        "plot_path": plot_path
    }


# -----------------------------------------------------------------------------
# ЗАДАЧА 1.5: ОПЫТ С НЕПРЕРЫВНЫМ ПРОГОНОМ (МЕТОД БАТЧЕЙ / BATCH MEANS)
# -----------------------------------------------------------------------------
def solve_task_1_5(raw_cfg: Dict[str, Any], plots_dir: str) -> Dict[str, Any]:
    task_cfg = raw_cfg["task_1_5"]
    print("\n" + "=" * 78)
    print("ЗАДАЧА 1.5: ОПЫТ С НЕПРЕРЫВНЫМ ПРОГОНОМ (МЕТОД БАТЧЕЙ / BATCH MEANS)")
    print("=" * 78)

    warmup_time = float(task_cfg.get("warmup_time", 25.0))
    batch_size = float(task_cfg.get("batch_size", 150.0))
    n_batches = int(task_cfg.get("n_batches", 30))
    seed_cont = int(task_cfg.get("seed_cont", 7777))
    seed_rep = int(task_cfg.get("seed_rep_bench", 8000))
    total_time = warmup_time + n_batches * batch_size

    print(f"1) Серия {n_batches} повторных независимых прогонов с длительностью T = {batch_size:.0f} мин (с отсечением warm-up)...")
    sample_rep = []
    for s in range(n_batches):
        sc = build_supermarket_config(raw_cfg)
        cfg_r = SimulationConfig(
            simulation_time=warmup_time + batch_size,
            warmup_time=warmup_time,
            rng_seed=seed_rep + s,
            supermarket=sc
        )
        sim_r = SupermarketSimulation(cfg_r)
        res_r = sim_r.run()
        sample_rep.append(float(res_r["avg_time_in_supermarket"]))

    print(f"2) Единый непрерывный прогон T_cont = {total_time:.0f} мин с нарезкой на {n_batches} батчей...")
    sc_c = build_supermarket_config(raw_cfg)
    cfg_cont = SimulationConfig(
        simulation_time=total_time,
        warmup_time=0.0,
        rng_seed=seed_cont,
        supermarket=sc_c
    )
    sim_cont = SupermarketSimulation(cfg_cont)
    sim_cont.run()

    timestamps = np.array(sim_cont.stats.time_in_supermarket.timestamps)
    observations = np.array(sim_cont.stats.time_in_supermarket.observations)

    batch_means = []
    for j in range(n_batches):
        t_start = warmup_time + j * batch_size
        t_end = warmup_time + (j + 1) * batch_size
        mask = (timestamps >= t_start) & (timestamps < t_end)
        if np.any(mask):
            batch_means.append(float(np.mean(observations[mask])))
        else:
            batch_means.append(float(np.mean(observations)))

    batch_means = np.array(batch_means)
    sample_rep = np.array(sample_rep)

    m_batch = float(np.mean(batch_means))
    s_batch = float(np.std(batch_means, ddof=1))
    se_batch = s_batch / np.sqrt(n_batches)

    m_rep = float(np.mean(sample_rep))
    s_rep = float(np.std(sample_rep, ddof=1))

    # Оценка автокорреляции первого порядка
    centered = batch_means - m_batch
    denom = np.sum(centered ** 2)
    numer = np.sum(centered[:-1] * centered[1:])
    rho_1 = float(numer / denom) if denom > 0 else 0.0

    ci_rho_bound = float(1.96 / np.sqrt(n_batches))
    is_independent = bool(abs(rho_1) < ci_rho_bound)

    # Сравнение выборок (F-критерий и t-критерий)
    f_stat = float((s_rep ** 2) / (s_batch ** 2)) if s_batch > 0 else 1.0
    f_crit = float(stats.f.ppf(0.975, dfd=n_batches - 1, dfn=n_batches - 1))
    var_equal = bool(f_stat < f_crit)

    t_stat_comp, t_p_comp = stats.ttest_ind(sample_rep, batch_means, equal_var=var_equal)
    t_stat_comp = float(t_stat_comp)
    t_p_comp = float(t_p_comp)
    t_crit_comp = float(stats.t.ppf(0.975, df=2 * n_batches - 2))
    means_equal = bool(abs(t_stat_comp) < t_crit_comp)

    print(f"Выборка репликаций: M_rep = {m_rep:.3f} мин, S_rep = {s_rep:.3f} мин")
    print(f"Выборка батчей:     M_batch = {m_batch:.3f} мин, S_batch = {s_batch:.3f} мин, SE = {se_batch:.3f}")
    print(f"Автокорреляция: rho_1 = {rho_1:.4f}, порог Андерсона = ±{ci_rho_bound:.4f} -> {'БАТЧИ НЕЗАВИСИМЫ' if is_independent else 'КОРРЕЛИРОВАНЫ'}")
    print(f"Сравнение средних: |t| = {abs(t_stat_comp):.3f} < t_кр = {t_crit_comp:.3f} (p = {t_p_comp:.4f})")
    print(f"Результат: метод батчей {'ПОДТВЕРЖДЕН КАК СОСТОЯТЕЛЬНЫЙ' if (is_independent and means_equal) else 'ОТВЕРГНУТ'}")

    plot_path = plot_task_1_5(
        n_batches=n_batches,
        batch_means=batch_means.tolist(),
        m_batch=m_batch,
        s_batch=s_batch,
        se_batch=se_batch,
        total_time=total_time,
        sample_rep=sample_rep.tolist(),
        m_rep=m_rep,
        s_rep=s_rep,
        t_stat_comp=t_stat_comp,
        t_crit_comp=t_crit_comp,
        t_p_comp=t_p_comp,
        f_stat=f_stat,
        f_crit=f_crit,
        ci_rho_bound=ci_rho_bound,
        rho_1=rho_1,
        batch_size=batch_size,
        plots_dir=plots_dir
    )

    return {
        "warmup_time": warmup_time,
        "total_time": total_time,
        "n_batches": n_batches,
        "batch_size": batch_size,
        "m_batch": m_batch,
        "s_batch": s_batch,
        "se_batch": se_batch,
        "m_rep": m_rep,
        "s_rep": s_rep,
        "rho_1": rho_1,
        "ci_rho_bound": ci_rho_bound,
        "is_independent": is_independent,
        "f_stat": f_stat,
        "f_crit": f_crit,
        "var_equal": var_equal,
        "t_stat_comp": t_stat_comp,
        "t_crit_comp": t_crit_comp,
        "t_p_comp": t_p_comp,
        "means_equal": means_equal,
        "plot_path": plot_path
    }


# -----------------------------------------------------------------------------
# ЗАДАЧА 1.6: ОЦЕНКА ЧУВСТВИТЕЛЬНОСТИ И ДОСТАТОЧНАЯ ТОЧНОСТЬ ПАРАМЕТРОВ
# -----------------------------------------------------------------------------
def solve_task_1_6(raw_cfg: Dict[str, Any], plots_dir: str) -> Dict[str, Any]:
    task_cfg = raw_cfg["task_1_6"]
    print("\n" + "=" * 78)
    print("ЗАДАЧА 1.6: ОЦЕНКА ЧУВСТВИТЕЛЬНОСТИ И ДОСТАТОЧНАЯ ТОЧНОСТЬ ЗАДАНИЯ ПЕРЕМЕННЫХ")
    print("=" * 78)

    n_runs_per_pt = int(task_cfg.get("n_runs_per_pt", 30))
    sim_time = float(task_cfg.get("sim_time", 300.0))
    tol_pct = float(task_cfg.get("tolerance_pct", 5.0)) / 100.0

    # Фактор 1: Интервал прихода покупателей T_arr
    x0_arr = float(task_cfg.get("arr_x0", 1.0))
    dx_arr = float(task_cfg.get("arr_dx", 0.02))
    grid_arr = [round(x0_arr + i * dx_arr, 3) for i in [-2, -1, 0, 1, 2]]
    seed_arr = int(task_cfg.get("seed_start_arr", 9000))

    print(f"1) Варьирование интервала прихода T_arr по 5 точкам: {grid_arr} мин...")
    resp_arr = []
    for idx_pt, x_val in enumerate(grid_arr):
        sub_runs = []
        for s in range(n_runs_per_pt):
            sc = build_supermarket_config(raw_cfg)
            sc.mean_arrival_interval = x_val
            cfg = SimulationConfig(
                simulation_time=sim_time,
                rng_seed=seed_arr + s,
                supermarket=sc
            )
            sim = SupermarketSimulation(cfg)
            res = sim.run()
            sub_runs.append(float(res["avg_time_in_supermarket"]))
        resp_arr.append(float(np.mean(sub_runs)))

    y0_arr = resp_arr[2]
    spread_arr = float(max(resp_arr) - min(resp_arr))
    d_allow_arr = float(tol_pct * y0_arr)
    is_insens_arr = bool(spread_arr <= d_allow_arr)

    # Фактор 2: Время обслуживания mu_serv
    x0_serv = float(task_cfg.get("serv_x0", 1.4))
    dx_serv = float(task_cfg.get("serv_dx", 0.002))
    grid_serv = [round(x0_serv + i * dx_serv, 4) for i in [-2, -1, 0, 1, 2]]
    seed_serv = int(task_cfg.get("seed_start_serv", 9500))

    print(f"2) Варьирование времени обслуживания mu_serv по 5 точкам: {grid_serv} мин...")
    resp_serv = []
    for idx_pt, x_val in enumerate(grid_serv):
        sub_runs = []
        for s in range(n_runs_per_pt):
            sc = build_supermarket_config(raw_cfg)
            sc.service_time.mean = x_val
            cfg = SimulationConfig(
                simulation_time=sim_time,
                rng_seed=seed_serv + s,
                supermarket=sc
            )
            sim = SupermarketSimulation(cfg)
            res = sim.run()
            sub_runs.append(float(res["avg_time_in_supermarket"]))
        resp_serv.append(float(np.mean(sub_runs)))

    y0_serv = resp_serv[2]
    spread_serv = float(max(resp_serv) - min(resp_serv))
    d_allow_serv = float(tol_pct * y0_serv)
    is_insens_serv = bool(spread_serv <= d_allow_serv)

    print(f"T_arr:  размах Δy = {spread_arr:.3f} мин, коридор d(5%) = {d_allow_arr:.3f} мин -> {'НЕЧУВСТВИТЕЛЬНА (точность достаточна)' if is_insens_arr else 'ЧУВСТВИТЕЛЬНА'}")
    print(f"mu_serv: размах Δy = {spread_serv:.3f} мин, коридор d(5%) = {d_allow_serv:.3f} мин -> {'НЕЧУВСТВИТЕЛЬНА (точность достаточна)' if is_insens_serv else 'ЧУВСТВИТЕЛЬНА'}")

    plot_path = plot_task_1_6(
        grid_arr=grid_arr,
        responses_arr=resp_arr,
        y_base_arr=y0_arr,
        d_allow_arr=d_allow_arr,
        dx_arr=dx_arr,
        grid_serv=grid_serv,
        responses_serv=resp_serv,
        y_base_serv=y0_serv,
        d_allow_serv=d_allow_serv,
        dx_serv=dx_serv,
        plots_dir=plots_dir
    )

    return {
        "dx_arr": dx_arr,
        "grid_arr": grid_arr,
        "responses_arr": resp_arr,
        "spread_arr": spread_arr,
        "d_allow_arr": d_allow_arr,
        "is_insensitive_arr": is_insens_arr,
        "dx_serv": dx_serv,
        "grid_serv": grid_serv,
        "responses_serv": resp_serv,
        "spread_serv": spread_serv,
        "d_allow_serv": d_allow_serv,
        "is_insensitive_serv": is_insens_serv,
        "plot_path": plot_path
    }


def main():
    root_dir = CURRENT_DIR
    config_path = os.path.join(root_dir, "config.json")
    plots_dir = os.path.join(root_dir, "plots")
    results_json_path = os.path.join(root_dir, "lr3_results.json")
    report_md_path = os.path.join(root_dir, "REPORT_LR3.md")

    print("=" * 78)
    print("  ЛАБОРАТОРНАЯ РАБОТА №3: ИССЛЕДОВАНИЕ СВОЙСТВ ИМИТАЦИОННОЙ МОДЕЛИ")
    print("  Вариант №5: Мини-супермаркет с раздельным обслуживанием")
    print(f"  Загрузка конфигурации из: {config_path}")
    print("=" * 78)

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    results = {}
    results["task_1_1"] = solve_task_1_1(cfg, plots_dir)
    results["task_1_2"] = solve_task_1_2(cfg, plots_dir)
    results["task_1_3"] = solve_task_1_3(cfg, plots_dir)
    results["task_1_4"] = solve_task_1_4(cfg, plots_dir)
    results["task_1_5"] = solve_task_1_5(cfg, plots_dir)
    results["task_1_6"] = solve_task_1_6(cfg, plots_dir)

    with open(results_json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] Все числовые результаты сохранены в: {results_json_path}")

    print(f"[OK] Генерация Markdown-отчета: {report_md_path}...")
    build_markdown_report(results, report_md_path)
    print(f"[OK] Отчет успешно сформирован: {report_md_path}")

    print("\n" + "=" * 78)
    print("  ВСЕ ЗАДАЧИ ЛАБОРАТОРНОЙ РАБОТЫ №3 ВЫПОЛНЕНЫ УСПЕШНО!")
    print("=" * 78)


if __name__ == "__main__":
    main()
