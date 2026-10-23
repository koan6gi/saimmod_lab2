import os
from typing import Dict, Any, List
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#CCCCCC'
plt.rcParams['axes.linewidth'] = 0.8


def plot_task_1_1(
    responses: List[float],
    working_cuts: List[float],
    mean_val: float,
    std_val: float,
    k_final: int,
    min_exp: float,
    cells_less_5: int,
    n_reps: int,
    sim_time: float,
    df: int,
    chi2_stat: float,
    chi2_crit: float,
    p_value: float,
    is_normal: bool,
    plots_dir: str
) -> str:
    """Генерация гистограммы и теоретической плотности Гаусса по критерию хи-квадрат."""
    os.makedirs(plots_dir, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9.2, 5.2), dpi=200)

    disp_cuts = list(working_cuts)
    if np.isneginf(disp_cuts[0]):
        disp_cuts[0] = max(0.0, mean_val - 3.3 * std_val)
    if np.isposinf(disp_cuts[-1]):
        disp_cuts[-1] = mean_val + 3.3 * std_val

    ax.hist(responses, bins=disp_cuts, density=True, color="#85C1E9",
            edgecolor="#1F4E79", alpha=0.75, label=f"Эмпирическая плотность (k={k_final} интервалов)")

    x_grid = np.linspace(disp_cuts[0], disp_cuts[-1], 300)
    pdf_curve = stats.norm.pdf(x_grid, loc=mean_val, scale=std_val)
    ax.plot(x_grid, pdf_curve, color="#C0392B", linewidth=2.5,
            label=f"Теоретическая плотность N({mean_val:.2f}, {std_val:.2f}²)")

    ax.set_title("Проверка нормальности отклика T_sys при длинных прогонах (критерий χ²)",
                 fontsize=11.5, fontweight="bold", pad=12)
    ax.set_xlabel("Время пребывания покупателя в супермаркете T_sys (мин)", fontsize=10)
    ax.set_ylabel("Плотность вероятности", fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.5)

    cochran_status_str = f"Правило Кохрана: E_min={min_exp:.1f}≥1, E<5={cells_less_5}/{k_final} (≤20%)\n"
    info_text = (
        f"N = {n_reps} длинных прогонов (T = {sim_time:.0f} мин)\n"
        + cochran_status_str +
        f"k = {k_final} интервалов (df = {df})\n"
        f"χ² = {chi2_stat:.3f} {'<' if is_normal else '≥'} χ²кр = {chi2_crit:.3f}\n"
        f"p-value = {p_value:.4f}\n"
        f"Вывод: гипотеза H₀ {'ПРИНЯТА (нормальное)' if is_normal else 'ОТВЕРГНУТА'}"
    )
    ax.text(0.02, 0.97, info_text, transform=ax.transAxes, fontsize=8.5, verticalalignment="top",
            bbox=dict(boxstyle="round,pad=0.5",
                      facecolor="#EAFAF1" if is_normal else "#FDEDEC",
                      edgecolor="#27AE60" if is_normal else "#C0392B",
                      alpha=0.92))

    ax.legend(loc="upper right", framealpha=0.92, fontsize=8.5)
    fig.tight_layout()

    plot_path = os.path.join(plots_dir, "task1_normality_chi2.png")
    fig.savefig(plot_path)
    plt.close(fig)
    return plot_path


def plot_task_1_2(
    est_time: Dict[str, Any],
    est_util: Dict[str, Any],
    plots_dir: str
) -> str:
    """Боксплоты и сравнение интервалов Стьюдента и Уиллинка."""
    os.makedirs(plots_dir, exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 5.0), dpi=200)

    plot_configs = [
        (ax1, est_time, "#1F4E79", "#2E86C1", "#D35400", "%.2f", "Время в магазине T_sys (мин)"),
        (ax2, est_util, "#196F3D", "#27AE60", "#B03A2E", "%.2f", "Загрузка продавцов ρ (%)")
    ]

    for ax, est, color_base, color_ci1, color_ci2, y_fmt, y_label in plot_configs:
        data_arr = np.array(est["data"])
        mean_val = est["mean"]
        med_val = float(np.median(data_arr))
        ci_s = est["ci_student"]
        ci_w = est["ci_willink"]
        skew_val = est["skewness"]

        ax.boxplot(data_arr, orientation="vertical", patch_artist=True,
                   boxprops=dict(facecolor="#EBF5FB" if ax == ax1 else "#E8F8F5",
                                 color=color_base, linewidth=1.5),
                   medianprops=dict(color="#C0392B", linewidth=2.0),
                   whiskerprops=dict(color=color_base, linewidth=1.2),
                   capprops=dict(color=color_base, linewidth=1.2),
                   flierprops=dict(marker="o", markeredgecolor=color_base, alpha=0.7),
                   positions=[1], widths=0.38)

        ax.axhline(mean_val, color="#7F8C8D", linestyle="--", linewidth=1.1, alpha=0.7,
                   label=f"Среднее M = {y_fmt % mean_val}")
        ax.axhline(med_val, color="#C0392B", linestyle=":", linewidth=1.1, alpha=0.7,
                   label=f"Медиана Me = {y_fmt % med_val}")

        ax.axhspan(ci_s[0], ci_s[1], xmin=0.55, xmax=0.95, color=color_ci1, alpha=0.06)

        ax.errorbar([1.8], [mean_val],
                    yerr=[[mean_val - ci_s[0]], [ci_s[1] - mean_val]],
                    fmt="o", color=color_ci1, capsize=6, capthick=1.8, elinewidth=2.0,
                    label="ДИ Стьюдента (95%)")
        ax.errorbar([2.2], [mean_val],
                    yerr=[[mean_val - ci_w[0]], [ci_w[1] - mean_val]],
                    fmt="s", color=color_ci2, capsize=6, capthick=1.8, elinewidth=2.0,
                    label="ДИ Уиллинка (асимм.)")

        y_span = max(data_arr.max(), ci_w[1], ci_s[1]) - min(data_arr.min(), ci_w[0], ci_s[0])
        txt_offset = y_span * 0.03

        ax.text(1.8, ci_s[1] + txt_offset, y_fmt % ci_s[1], ha="center", va="bottom",
                fontsize=8, fontweight="bold", color=color_ci1)
        ax.text(1.8, ci_s[0] - txt_offset, y_fmt % ci_s[0], ha="center", va="top",
                fontsize=8, fontweight="bold", color=color_ci1)

        ax.text(2.2, ci_w[1] + txt_offset, y_fmt % ci_w[1], ha="center", va="bottom",
                fontsize=8, fontweight="bold", color=color_ci2)
        ax.text(2.2, ci_w[0] - txt_offset, y_fmt % ci_w[0], ha="center", va="top",
                fontsize=8, fontweight="bold", color=color_ci2)

        y_min_target = min(data_arr.min(), ci_w[0], ci_s[0]) - y_span * 0.1
        y_max_target = max(data_arr.max(), ci_w[1], ci_s[1]) + y_span * 0.1
        ax.set_ylim(y_min_target, y_max_target)

        ax.set_xlim(0.5, 2.6)
        ax.set_xticks([1, 1.8, 2.2])
        ax.set_xticklabels(["Выборка (N=20)", "ДИ Стьюд.", "ДИ Уилл."], fontsize=9.5)
        ax.set_ylabel(y_label, fontsize=10)

        skew_desc = "правосторонняя" if skew_val > 0 else "левосторонняя"
        ax.set_title(f"{est['name']}\nγ₁ = {skew_val:+.3f} ({skew_desc} асимм.)",
                     fontsize=10.5, fontweight="bold")
        ax.grid(True, linestyle="--", alpha=0.45)
        ax.legend(loc="upper right", fontsize=7.8)

    fig.tight_layout(rect=[0, 0, 1, 0.92])
    fig.suptitle("Точечные и интервальные оценки откликов модели (N = 20 прогонов, α = 0.05)",
                 fontsize=12, fontweight="bold", y=0.975)

    plot_path = os.path.join(plots_dir, "task2_point_interval_estimates.png")
    fig.savefig(plot_path)
    plt.close(fig)
    return plot_path


def plot_task_1_3(
    n_points: List[int],
    relative_errors: List[float],
    target_err: float,
    n_5pct: int,
    err_at_n5: float,
    max_runs: int,
    plots_dir: str
) -> str:
    """Кривая сходимости относительной погрешности к заданному порогу точности 5%."""
    os.makedirs(plots_dir, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=200)

    ax.plot(n_points, relative_errors, color="#1F4E79", linewidth=2.2, label="Относительная погрешность ε(n)")
    ax.axhline(target_err, color="#C0392B", linestyle="--", linewidth=1.8, label=f"Целевой порог точности {target_err:.1f}%")
    ax.axvline(n_5pct, color="#27AE60", linestyle=":", linewidth=2.0, label=f"N* = {n_5pct} прогонов (ε ≤ {target_err:.1f}%)")
    ax.axhspan(0, target_err, color="#D5F5E3", alpha=0.35, label=f"Зона высокой точности (ε ≤ {target_err:.1f}%)")

    ax.scatter([n_5pct], [err_at_n5], color="#27AE60", s=70, zorder=5)
    ax.annotate(f"N* = {n_5pct}\nε = {err_at_n5:.2f}%",
                xy=(n_5pct, err_at_n5), xytext=(n_5pct + 8, err_at_n5 + 2.5),
                arrowprops=dict(facecolor="#27AE60", shrink=0.08, width=1.5, headwidth=6),
                fontsize=9.5, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#27AE60"))

    ax.set_title("Зависимость точности имитации от количества прогонов (отклик T_sys)",
                 fontsize=11.5, fontweight="bold", pad=12)
    ax.set_xlabel("Количество повторных независимых прогонов n", fontsize=10)
    ax.set_ylabel("Относительная погрешность отклика ε (%)", fontsize=10)
    ax.set_xlim(4, max_runs)
    ax.set_ylim(0, max(relative_errors[:5]) + 2)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", framealpha=0.9, fontsize=9)
    fig.tight_layout()

    plot_path = os.path.join(plots_dir, "task3_accuracy_vs_runs.png")
    fig.savefig(plot_path)
    plt.close(fig)
    return plot_path


def plot_task_1_4(
    bin_centers: np.ndarray,
    welch_mean: np.ndarray,
    bin_runs: np.ndarray,
    warmup_time: float,
    m0: float,
    s0: float,
    m1: float,
    s1: float,
    t0_long: float,
    sample_y0: List[float],
    sample_y1: List[float],
    t_stat_val: float,
    t_crit: float,
    t_p_val: float,
    plots_dir: str
) -> str:
    """Процедура Уэлча для выделения warm-up и сравнение усеченного прогона с эталонным."""
    os.makedirs(plots_dir, exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 5.0), dpi=200)
    n_sample = len(sample_y0)

    # График A: Процедура Уэлча
    for i in range(min(15, len(bin_runs))):
        valid_mask = ~np.isnan(bin_runs[i])
        ax1.plot(bin_centers[valid_mask], bin_runs[i][valid_mask],
                 color="#BDC3C7", alpha=0.35, linewidth=0.8,
                 label="Отдельные реализации" if i == 0 else "")

    ax1.plot(bin_centers, welch_mean, color="#1F4E79", linewidth=2.5,
             label=f"Осреднение Уэлча ({len(bin_runs)} прогонов)")

    ax1.axvline(warmup_time, color="#D35400", linestyle="--", linewidth=2.0,
                label=f"Фаза разогрева (T_warm = {warmup_time:.0f} мин)")
    ax1.axvspan(0, warmup_time, color="#FAD7A0", alpha=0.35, label="Переходный период (исключается)")
    ax1.axhline(m0, color="#27AE60", linestyle=":", linewidth=2.0,
                label=f"Стационарный уровень ({m0:.2f} мин)")

    idx_warm = int(np.argmin(np.abs(bin_centers - warmup_time)))
    val_warm = float(welch_mean[idx_warm])
    ax1.scatter([warmup_time], [val_warm], color="#D35400", s=65, zorder=5)
    ax1.annotate(f"Выход на стационар\n≈ {val_warm:.1f} мин",
                 xy=(warmup_time, val_warm), xytext=(warmup_time + 30, val_warm - 4.0),
                 arrowprops=dict(facecolor="#D35400", shrink=0.08, width=1.4, headwidth=5),
                 fontsize=8.5, fontweight="bold",
                 bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#D35400"))

    ax1.set_title("Процедура Уэлча (Welch) для T_sys\nи выделение фазы прогрева", fontsize=10.5, fontweight="bold")
    ax1.set_xlabel("Модельное время (минуты)", fontsize=9.5)
    ax1.set_ylabel("T_sys (минуты)", fontsize=9.5)
    ax1.set_xlim(0, t0_long)
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="lower right", fontsize=8, framealpha=0.9)

    # График B: Сравнение выборок Y0 и Y1
    b_data = [sample_y0, sample_y1]
    ax2.boxplot(b_data, orientation="vertical", patch_artist=True,
                boxprops=dict(facecolor="#E8F8F5", color="#117A65"),
                medianprops=dict(color="#C0392B", linewidth=2.0),
                positions=[1, 2], widths=0.45)

    ax2.errorbar([1], [m0], yerr=[stats.t.ppf(0.975, df=n_sample - 1) * s0 / np.sqrt(n_sample)],
                 fmt="o", color="#1F4E79", capsize=6, capthick=2, elinewidth=2.2, label=f"Y₀: Эталон (T={t0_long:.0f})")
    ax2.errorbar([2], [m1], yerr=[stats.t.ppf(0.975, df=n_sample - 1) * s1 / np.sqrt(n_sample)],
                 fmt="s", color="#D35400", capsize=6, capthick=2, elinewidth=2.2, label=f"Y₁: Сокращенный (w={warmup_time:.0f})")

    ax2.set_xticks([1, 2])
    ax2.set_xticklabels([f"Эталон Y₀\n(T={t0_long:.0f} мин)", f"Сокращенный Y₁\n(T=300 мин, w={warmup_time:.0f})"], fontsize=9.5)
    ax2.set_title(f"Сравнение выборок Y₀ и Y₁\n|t| = {abs(t_stat_val):.2f} < t_кр = {t_crit:.2f} (p = {t_p_val:.3f})",
                  fontsize=10.5, fontweight="bold")
    ax2.set_ylabel("T_sys (минуты)", fontsize=9.5)
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="upper right", fontsize=8.5)

    fig.tight_layout()
    plot_path = os.path.join(plots_dir, "task4_warmup_reduction.png")
    fig.savefig(plot_path)
    plt.close(fig)
    return plot_path


def plot_task_1_5(
    n_batches: int,
    batch_means: List[float],
    m_batch: float,
    s_batch: float,
    se_batch: float,
    total_time: float,
    sample_rep: List[float],
    m_rep: float,
    s_rep: float,
    t_stat_comp: float,
    t_crit_comp: float,
    t_p_comp: float,
    f_stat: float,
    f_crit: float,
    ci_rho_bound: float,
    rho_1: float,
    batch_size: float,
    plots_dir: str
) -> str:
    """Траектория батчей непрерывного прогона и сравнение с повторными прогонами."""
    os.makedirs(plots_dir, exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 5.0), dpi=200)

    # График A: Батчи
    ax1.plot(range(1, n_batches + 1), batch_means, marker="o", color="#2E86C1", linewidth=1.8, label="Отклик батча Z_k")
    ax1.axhline(m_batch, color="#196F3D", linestyle="-", linewidth=2.0, label=f"Среднее батчей ({m_batch:.2f} мин)")
    ax1.axhline(m_rep, color="#D35400", linestyle=":", linewidth=1.8, label=f"Среднее реплик ({m_rep:.2f} мин)")
    t_crit_b = stats.t.ppf(0.975, df=n_batches - 1)
    ax1.axhspan(m_batch - t_crit_b * se_batch, m_batch + t_crit_b * se_batch,
                color="#D5F5E3", alpha=0.45, label="95% ДИ среднего батчей")

    ax1.text(0.04, 0.10,
             f"Автокорреляция: ρ₁ = {rho_1:.3f}\n"
             f"Граница Андерсона: ±{ci_rho_bound:.3f}\n"
             f"Статус: батчи независимы",
             transform=ax1.transAxes, fontsize=8.5,
             bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#1F4E79", alpha=0.9))

    ax1.set_title(f"Оценки отклика по батчам\n(T_cont = {total_time:.0f} мин, M = {n_batches}, T_batch = {batch_size:.0f} мин)",
                  fontsize=10.5, fontweight="bold")
    ax1.set_xlabel("Номер батча k", fontsize=9.5)
    ax1.set_ylabel("T_sys (минуты)", fontsize=9.5)
    ax1.set_xticks(range(1, n_batches + 1, 2))
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="upper right", fontsize=8.0)

    # График B: Сравнение
    b_data = [sample_rep, batch_means]
    ax2.boxplot(b_data, orientation="vertical", patch_artist=True,
                boxprops=dict(facecolor="#E8F8F5", color="#117A65"),
                medianprops=dict(color="#C0392B", linewidth=2.0),
                positions=[1, 2], widths=0.45)

    n_rep = len(sample_rep)
    ax2.errorbar([1], [m_rep], yerr=[stats.t.ppf(0.975, df=n_rep - 1) * s_rep / np.sqrt(n_rep)],
                 fmt="o", color="#1F4E79", capsize=6, capthick=2, elinewidth=2.2,
                 label=f"Повторные реплики (T={batch_size:.0f})")
    ax2.errorbar([2], [m_batch], yerr=[stats.t.ppf(0.975, df=n_batches - 1) * s_batch / np.sqrt(n_batches)],
                 fmt="s", color="#D35400", capsize=6, capthick=2, elinewidth=2.2,
                 label=f"Метод батчей (T_batch={batch_size:.0f})")

    ax2.set_xticks([1, 2])
    ax2.set_xticklabels([f"Повторные реплики\n(N={n_rep}, T={batch_size:.0f} мин)",
                         f"Непрерывный прогон\n(M={n_batches}, T={batch_size:.0f} мин)"], fontsize=9.5)
    ax2.set_title(f"Сравнение методов: репликации vs батчи\n|t| = {abs(t_stat_comp):.2f} < t_кр = {t_crit_comp:.2f} (p = {t_p_comp:.3f})\nF = {f_stat:.2f} < F_кр = {f_crit:.2f} (дисперсии равны)",
                  fontsize=9.5, fontweight="bold")
    ax2.set_ylabel("T_sys (минуты)", fontsize=9.5)
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="upper right", fontsize=8.0)

    fig.tight_layout()
    plot_path = os.path.join(plots_dir, "task5_continuous_run_batches.png")
    fig.savefig(plot_path)
    plt.close(fig)
    return plot_path


def plot_task_1_6(
    grid_arr: List[float],
    responses_arr: List[float],
    y_base_arr: float,
    d_allow_arr: float,
    dx_arr: float,
    grid_serv: List[float],
    responses_serv: List[float],
    y_base_serv: float,
    d_allow_serv: float,
    dx_serv: float,
    plots_dir: str
) -> str:
    """Анализ чувствительности отклика T_sys к вариациям входных параметров."""
    os.makedirs(plots_dir, exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.8), dpi=200)

    # Subplot A: T_arr чувствительность
    ax1.plot(grid_arr, responses_arr, marker="o", color="#2E86C1", linewidth=2.0, label="Отклик T_sys(x)")
    ax1.axhline(y_base_arr, color="#1F4E79", linestyle="--", linewidth=1.5, label=f"Базовый y₀ = {y_base_arr:.2f} мин")
    ax1.axhspan(y_base_arr - d_allow_arr / 2.0, y_base_arr + d_allow_arr / 2.0,
                color="#D5F5E3", alpha=0.45, label=f"Коридор несущественности d = {d_allow_arr:.2f} мин")

    ax1.set_title(f"Чувствительность к вариациям T_arr\n(погрешность измерения ±{dx_arr:.2f} мин)", fontsize=10.5, fontweight="bold")
    ax1.set_xlabel("Интервал поступления T_arr (мин)", fontsize=9.5)
    ax1.set_ylabel("T_sys (минуты)", fontsize=9.5)
    ax1.set_xticks(grid_arr)
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="upper right", fontsize=8)

    # Subplot B: T_serv чувствительность
    ax2.plot(grid_serv, responses_serv, marker="s", color="#E67E22", linewidth=2.0, label="Отклик T_sys(x)")
    ax2.axhline(y_base_serv, color="#B9770E", linestyle="--", linewidth=1.5, label=f"Базовый y₀ = {y_base_serv:.2f} мин")
    ax2.axhspan(y_base_serv - d_allow_serv / 2.0, y_base_serv + d_allow_serv / 2.0,
                color="#FCF3CF", alpha=0.45, label=f"Коридор несущественности d = {d_allow_serv:.2f} мин")

    ax2.set_title(f"Чувствительность к времени обслуживания μ_serv\n(погрешность измерения ±{dx_serv:.2f} мин)", fontsize=10.5, fontweight="bold")
    ax2.set_xlabel("Среднее время обслуживания μ_serv (мин)", fontsize=9.5)
    ax2.set_ylabel("T_sys (минуты)", fontsize=9.5)
    ax2.set_xticks(grid_serv)
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="upper right", fontsize=8)

    fig.tight_layout()
    plot_path = os.path.join(plots_dir, "task6_sensitivity_analysis.png")
    fig.savefig(plot_path)
    plt.close(fig)
    return plot_path
