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
    в последовательную цепочку дискретных событий на оси системного модельного времени t_0.
    """
    fig, ax = plt.subplots(figsize=(14.5, 9.2), dpi=300)
    ax.set_xlim(-0.2, 13.0)
    ax.set_ylim(-2.1, 6.2)
    ax.axis("off")

    # Стили и палитра
    axis_color = "#1E293B"
    sync_color = "#64748B"
    event_dot_color = "#0284C7"
    t0_marker_color = "#DC2626"
    bg_t0 = "#EFF6FF"
    interval_color = "#2563EB"

    # Заголовок диаграммы
    ax.text(6.4, 5.85, "Организация квазипараллелизма: объединение локальных времен элементов в системное время $t_0$",
            ha="center", va="center", fontsize=13, fontweight="bold", color="#0F172A")
    ax.text(6.4, 5.48, "(В точном соответствии со Слайдом 15 лекции: преобразование параллельных процессов в последовательные)",
            ha="center", va="center", fontsize=9.5, style="italic", color="#475569")

    # Уровни по вертикали для осей
    y_k3 = 4.3  # Элемент K3: Отдел 2 (Молочный)
    y_k2 = 3.0  # Элемент K2: Отдел 1 (Бакалея)
    y_k1 = 1.7  # Элемент K1: Поток покупателей (Генератор)
    y_t0 = 0.2  # Системное модельное время t0 (Future Event List)

    # Фоновая подсветка для системной оси t0
    t0_bg = patches.Rectangle((0.1, -0.65), 12.6, 1.25, facecolor=bg_t0, edgecolor="#BFDBFE",
                              linewidth=1.2, linestyle="--", zorder=0)
    ax.add_patch(t0_bg)

    # 1. Горизонтальные оси со стрелками
    axes_info = [
        (y_k3, "$t_3$  (Отдел 2 'Молочный' — элемент $K_3$)"),
        (y_k2, "$t_2$  (Отдел 1 'Бакалея' — элемент $K_2$)"),
        (y_k1, "$t_1$  (Входной поток покупателей — элемент $K_1$)"),
        (y_t0, "$t_0$  (Системное время имитатора — Календарь FEL)"),
    ]

    for y, label in axes_info:
        # Линия оси со стрелкой
        ax.annotate("", xy=(12.4, y), xytext=(0.5, y),
                    arrowprops=dict(arrowstyle="-|>", color=axis_color, lw=2.0, mutation_scale=15))
        # Метка оси
        is_t0 = (y == y_t0)
        ax.text(0.4, y, label, ha="right", va="center",
                fontsize=9.2 if not is_t0 else 10.0,
                fontweight="bold" if is_t0 else "normal",
                color="#B91C1C" if is_t0 else "#1E293B")

    # 2. Сегменты интервалов активности (как на Слайде 15)
    # Для каждого элемента: список интервалов (x_start, x_end, activity_label, tau_label)
    intervals_k3 = [
        (0.5, 3.2, r"$\alpha_{30}$", r"$\tau_{30}$"),
        (3.2, 6.6, r"$\alpha_{31}$", r"$\tau_{31}$"),
        (6.6, 9.9, r"$\alpha_{32}$", r"$\tau_{32}$"),
        (9.9, 12.0, r"$\alpha_{33}$", r"$\tau_{33}$"),
    ]
    intervals_k2 = [
        (0.5, 2.2, r"$\alpha_{20}$", r"$\tau_{20}$"),
        (2.2, 5.5, r"$\alpha_{21}$", r"$\tau_{21}$"),
        (5.5, 7.6, r"$\alpha_{22}$", r"$\tau_{22}$"),
        (7.6, 11.0, r"$\alpha_{23}$", r"$\tau_{23}$"),
        (11.0, 12.0, r"$\alpha_{24}$", r"$\tau_{24}$"),
    ]
    intervals_k1 = [
        (0.5, 1.3, r"$\alpha_{10}$", r"$\tau_{10}$"),
        (1.3, 4.2, r"$\alpha_{11}$", r"$\tau_{11}$"),
        (4.2, 8.5, r"$\alpha_{12}$", r"$\tau_{12}$"),
        (8.5, 12.0, r"$\alpha_{13}$", r"$\tau_{13}$"),
    ]

    for y, intervals in [(y_k3, intervals_k3), (y_k2, intervals_k2), (y_k1, intervals_k1)]:
        for x_s, x_e, a_lbl, tau_lbl in intervals:
            # Горизонтальная стрелка интервала активности (как в Слайде 15)
            if x_e <= 12.0:
                ax.annotate("", xy=(x_e, y), xytext=(x_s, y),
                            arrowprops=dict(arrowstyle="->", color=interval_color, lw=1.5,
                                            mutation_scale=10))
            mid_x = (x_s + min(x_e, 12.0)) / 2.0
            # Подпись активности сверху стрелки
            ax.text(mid_x, y + 0.16, a_lbl, ha="center", va="bottom",
                    fontsize=8.5, fontweight="bold", color="#1E3A8A")
            # Подпись длительности тау снизу стрелки
            ax.text(mid_x, y - 0.16, tau_lbl, ha="center", va="top",
                    fontsize=8.0, color="#475569")

    # 3. Хронологический список системных событий на оси t0
    # События отсортированы строго по возрастанию модельного времени: T0 < T1 < ... < T9
    events_timeline = [
        # x_time, y_axis, event_id, activity_desc, t0_label
        (1.3, y_k1, r"$e_{10}$", "Прибытие клиента #1", r"$T_0\ (t_{10})$"),
        (2.2, y_k2, r"$e_{20}$", "Конец обслуживания K2", r"$T_1\ (t_{20})$"),
        (3.2, y_k3, r"$e_{30}$", "Конец обслуживания K3", r"$T_2\ (t_{30})$"),
        (4.2, y_k1, r"$e_{11}$", "Прибытие клиента #2", r"$T_3\ (t_{11})$"),
        (5.5, y_k2, r"$e_{21}$", "Конец обслуживания K2", r"$T_4\ (t_{21})$"),
        (6.6, y_k3, r"$e_{31}$", "Конец обслуживания K3", r"$T_5\ (t_{31})$"),
        (7.6, y_k2, r"$e_{22}$", "Конец обслуживания K2", r"$T_6\ (t_{22})$"),
        (8.5, y_k1, r"$e_{12}$", "Прибытие клиента #3", r"$T_7\ (t_{12})$"),
        (9.9, y_k3, r"$e_{32}$", "Конец обслуживания K3", r"$T_8\ (t_{32})$"),
        (11.0, y_k2, r"$e_{23}$", "Конец обслуживания K2", r"$T_9\ (t_{23})$"),
    ]

    # Отрисовка маркеров событий и проекций на t0
    for i, (x, y, e_lbl, desc, t0_lbl) in enumerate(events_timeline):
        # 1. Вертикальная пунктирная линия синхронизации от оси элемента к оси t0
        ax.plot([x, x], [y, y_t0], color=sync_color, linestyle="--", lw=1.2, alpha=0.8)

        # 2. Точка события на локальной оси элемента
        ax.plot(x, y, marker="o", markersize=6.5, color=event_dot_color,
                markeredgecolor="#0C4A6E", markeredgewidth=1.2, zorder=4)
        ax.text(x, y + 0.32, e_lbl, ha="center", va="bottom",
                fontsize=8.5, fontweight="bold", color="#0F172A")

        # 3. Маркер засечки на оси системного времени t0
        ax.plot(x, y_t0, marker="D", markersize=6.0, color=t0_marker_color,
                markeredgecolor="#7F1D1D", markeredgewidth=1.0, zorder=5)

        # 4. Подпись T_k(t_ij) под системной осью (с наклоном 40 градусов)
        ax.text(x, y_t0 - 0.22, t0_lbl, ha="right", va="top",
                fontsize=8.2, fontweight="bold", rotation=40, color="#991B1B")

    # Стрелки скачков модельного системного времени t0 := Tk вдоль оси t0
    for i in range(len(events_timeline) - 1):
        x1 = events_timeline[i][0]
        x2 = events_timeline[i + 1][0]
        # Маленькая дуговая стрелочка между соседними событиями
        ax.annotate("", xy=(x2 - 0.08, y_t0 + 0.04), xytext=(x1 + 0.08, y_t0 + 0.04),
                    arrowprops=dict(arrowstyle="->", color="#DC2626", lw=1.2,
                                    connectionstyle="arc3,rad=-0.25", mutation_scale=8))

    ax.text(6.0, y_t0 + 0.28, "Скачки системных часов имитатора:  $t_0 := T_k = \\min(T_{events})$",
            ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#B91C1C")

    # 4. Поясняющая панель строго внизу (НЕ перекрывает оси и графики!)
    legend_card = patches.FancyBboxPatch((0.2, -1.95), 12.5, 1.15,
                                         boxstyle="round,pad=0.1,rounding_size=0.15",
                                         facecolor="#F8FAFC", edgecolor="#CBD5E1", linewidth=1.2)
    ax.add_patch(legend_card)

    legend_title = "Теоретические основы квазипараллелизма (по Слайду 15 лекции):"
    legend_body = (
        "• Квазипараллелизм — псевдопараллельное моделирование на однопроцессорной ЭВМ нескольких физически параллельных процессов.\n"
        "• Локальные времена $t_1, t_2, t_3$ — непрерывное время работы отдельных компонентов (K1 — входной поток, K2, K3 — отделы магазина).\n"
        "• $\\alpha_{ij}$ — активность (активная фаза элемента $i$ в шаге $j$), $\\tau_{ij}$ — длительность ожидания или обслуживания.\n"
        "• $e_{ij}$ — событие завершения фазы элемента $i$. Момент наступления регистрируется в Календаре событий (Future Event List).\n"
        "• $t_0$ — системное модельное время. Часы НЕ идут непрерывно, а дискретно перескакивают к ближайшему событию: "
        "$T_0 < T_1 < T_2 < \\dots < T_9$."
    )
    ax.text(0.45, -1.0, legend_title, ha="left", va="top", fontsize=9.2, fontweight="bold", color="#0F172A")
    ax.text(0.45, -1.18, legend_body, ha="left", va="top", fontsize=8.2, color="#334155", linespacing=1.35)

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Диаграмма квазипараллелизма успешно сохранена в: {output_path}")


if __name__ == "__main__":
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "plots"))
    os.makedirs(out_dir, exist_ok=True)
    generate_quasiparallel_diagram(os.path.join(out_dir, "diagram_quasiparallel.png"))
