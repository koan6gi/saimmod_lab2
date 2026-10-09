import os
import sys
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def generate_quasiparallel_diagram(output_path: str):
    """
    Генерация диаграммы организации квазипараллелизма (временной развертки),
    в точности соответствующей Слайду 15 лекции (lec2.pptx) «Динамика взаимодействия нескольких элементов».
    Демонстрирует преобразование параллельных локальных процессов компонентов (K_1..K_3)
    в последовательную цепочку событий на оси системного модельного времени t_0.
    """
    fig, ax = plt.subplots(figsize=(13, 7.5), dpi=300)
    ax.set_xlim(-0.5, 12.5)
    ax.set_ylim(-0.8, 6.2)
    ax.axis("off")

    # Стили
    axis_color = "#1E293B"
    sync_color = "#64748B"
    highlight_color = "#2563EB"
    bg_t0 = "#EFF6FF"

    # Заголовок
    ax.text(6.0, 5.8, "Организация квазипараллелизма: объединение локальных времен элементов в системное время $t_0$",
            ha="center", va="center", fontsize=13, fontweight="bold", color="#0F172A")
    ax.text(6.0, 5.4, "(В соответствии со Слайдом 15 лекции: преобразование параллельных процессов в последовательные)",
            ha="center", va="center", fontsize=9.5, style="italic", color="#475569")

    # Уровни по вертикали
    y_k3 = 4.3  # Элемент K3: Отдел 2 (Молочный)
    y_k2 = 3.0  # Элемент K2: Отдел 1 (Бакалея)
    y_k1 = 1.7  # Элемент K1: Поток покупателей (Генератор)
    y_t0 = 0.3  # Системное модельное время t0 (Future Event List)

    # Фоновая подсветка для оси системного времени
    t0_bg = patches.Rectangle((-0.2, -0.6), 12.4, 1.3, facecolor=bg_t0, edgecolor="#BFDBFE",
                              linewidth=1.2, linestyle="--", zorder=0)
    ax.add_patch(t0_bg)

    # 1. Горизонтальные оси со стрелками
    axes_info = [
        (y_k3, "$t_3$ (Локальное время $K_3$ — Отдел 2 'Молочный')"),
        (y_k2, "$t_2$ (Локальное время $K_2$ — Отдел 1 'Бакалея')"),
        (y_k1, "$t_1$ (Локальное время $K_1$ — Генератор покупателей)"),
        (y_t0, "$t_0$ (Системное модельное время имитатора — Календарь событий)"),
    ]

    for y, label in axes_info:
        # Линия оси
        ax.annotate("", xy=(11.8, y), xytext=(0.5, y),
                    arrowprops=dict(arrowstyle="-|>", color=axis_color, lw=2.0, mutation_scale=15))
        # Метка оси слева
        is_t0 = (y == y_t0)
        ax.text(0.3, y, label, ha="right", va="center",
                fontsize=9.5 if not is_t0 else 10.5,
                fontweight="bold" if is_t0 else "normal",
                color="#1D4ED8" if is_t0 else "#1E293B")

    # 2. События и активности элементов
    # Формат события: (x_time, y_axis, event_label, activity_label, duration_label)
    # Определим хронологический порядок модельных событий
    events_timeline = [
        # x, y_axis, local_name, activity_name, tau_name, t0_name
        (1.2, y_k1, r"$e_{10}$", r"$\alpha_{10}$", r"$\tau_{10}$", r"$T_0\ (t_{10})$"),
        (2.0, y_k2, r"$e_{20}$", r"$\alpha_{21}$", r"$\tau_{20}$", r"$T_1\ (t_{20})$"),
        (2.8, y_k3, r"$e_{30}$", r"$\alpha_{31}$", r"$\tau_{30}$", r"$T_2\ (t_{30})$"),
        (4.0, y_k1, r"$e_{11}$", r"$\alpha_{11}$", r"$\tau_{11}$", r"$T_3\ (t_{11})$"),
        (5.2, y_k2, r"$e_{21}$", r"$\alpha_{22}$", r"$\tau_{21}$", r"$T_4\ (t_{21})$"),
        (6.3, y_k3, r"$e_{31}$", r"$\alpha_{32}$", r"$\tau_{31}$", r"$T_5\ (t_{31})$"),
        (7.5, y_k2, r"$e_{22}$", r"$\alpha_{23}$", r"$\tau_{22}$", r"$T_6\ (t_{22})$"),
        (8.4, y_k1, r"$e_{12}$", r"$\alpha_{12}$", r"$\tau_{12}$", r"$T_7\ (t_{12})$"),
        (9.8, y_k3, r"$e_{32}$", r"$\alpha_{33}$", r"$\tau_{32}$", r"$T_8\ (t_{32})$"),
        (10.8, y_k2, r"$e_{23}$", r"$\alpha_{24}$", r"$\tau_{23}$", r"$T_9\ (t_{23})$"),
    ]

    # Отрисовка маркеров событий и связующих линий с осью t0
    for x, y, e_lbl, a_lbl, tau_lbl, t0_lbl in events_timeline:
        # Вертикальная пунктирная линия синхронизации от оси элемента к t0
        ax.plot([x, x], [y, y_t0], color=sync_color, linestyle=":", lw=1.3, alpha=0.85)

        # Точка на локальной оси
        ax.plot(x, y, marker="o", markersize=6, color="#0284C7", zorder=4)
        ax.text(x, y + 0.22, a_lbl, ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#0F172A")
        ax.text(x - 0.25, y - 0.25, tau_lbl, ha="center", va="top", fontsize=8, color="#64748B")

        # Засечка и подпись на системной оси t0
        ax.plot(x, y_t0, marker="|", markersize=10, markeredgewidth=2, color="#DC2626", zorder=5)
        ax.text(x, y_t0 - 0.25, t0_lbl, ha="center", va="top", fontsize=8, fontweight="bold",
                rotation=45, color="#991B1B")

    # Поясняющие плашки
    legend_text = (
        "Пояснение к диаграмме:\n"
        "• t_0 — системное модельное время (часы имитатора, перескакивающие по событиям).\n"
        "• T_k — моменты событий в календаре Future Event List (отсортированы по возрастанию: T_0 < T_1 < T_2...).\n"
        "• t_i — локальные времена элементов (K_1 — входной поток, K_2..K_n — отделы магазина).\n"
        "• e_ij — j-е событие i-го элемента, \\u03c4_ij — интервал до следующего события, \\u03b1_ij — активность (обработчик)."
    )
    ax.text(0.5, 4.9, legend_text, fontsize=8, va="top", ha="left",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#F8FAFC", edgecolor="#CBD5E1", lw=1))

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Диаграмма квазипараллелизма успешно сохранена: {output_path}")


if __name__ == "__main__":
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "plots"))
    os.makedirs(out_dir, exist_ok=True)
    generate_quasiparallel_diagram(os.path.join(out_dir, "diagram_quasiparallel.png"))
