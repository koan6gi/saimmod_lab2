import os
import sys
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def generate_diagram(output_path: str):
    """
    Генерация концептуальной схемы СМО супермаркета в соответствии со Слайдом 6 лекции (lec2.pptx).
    Канонические графические элементы теории массового обслуживания:
    - Треугольник: Источник заявок (Входной поток клиентов)
    - Полосатый прямоугольник: Накопитель / Очередь FIFO
    - Прямоугольник канала: Обслуживающий аппарат (Продавец)
    - Ромб / разветвитель: Узел маршрутизации по отделам
    - Терминальный блок: Выход из системы
    """
    fig, ax = plt.subplots(figsize=(14.5, 8.8), dpi=300)
    ax.set_xlim(-0.5, 14.5)
    ax.set_ylim(-0.2, 8.8)
    ax.axis("off")

    # Палитра
    bg_container = "#F8FAFC"
    border_color = "#1E293B"
    accent_blue = "#2563EB"
    amber_loop = "#D97706"
    green_exit = "#16A34A"
    green_bg = "#DCFCE7"

    # Заголовок схемы
    ax.text(7.0, 8.55, "Структурная схема имитационной модели супермаркета (СМО сетей обслуживания)",
            ha="center", va="center", fontsize=13, fontweight="bold", color="#0F172A")
    ax.text(7.0, 8.25, "Каноническое представление по Слайду 6 лекции: Источник $\\triangleright$, Очереди FIFO, Каналы $K_1..K_5$, Маршрутизация",
            ha="center", va="center", fontsize=9.5, style="italic", color="#475569")

    # 1. Входной треугольник (Источник заявок - Slide 6)
    tri_x = [0.3, 0.3, 1.1]
    tri_y = [4.6, 3.8, 4.2]
    triangle = patches.Polygon(xy=list(zip(tri_x, tri_y)), closed=True,
                               facecolor="#EFF6FF", edgecolor=border_color, linewidth=2)
    ax.add_patch(triangle)
    ax.text(0.7, 3.4, "Входной поток\nпокупателей\n($\\lambda=0.5$ мин$^{-1}$, Exp)",
            ha="center", va="top", fontsize=8.5, fontweight="bold", color="#1E293B")

    # Стрелка от источника к торговому залу
    ax.annotate("", xy=(2.0, 4.2), xytext=(1.1, 4.2),
                arrowprops=dict(arrowstyle="-|>", color=border_color, lw=2, mutation_scale=15))

    # 2. Торговый зал / Маршрутизатор корзины
    saleroom = patches.FancyBboxPatch((2.0, 2.7), 2.2, 3.0,
                                      boxstyle="round,pad=0.1,rounding_size=0.15",
                                      facecolor="#FFFFFF", edgecolor=border_color, linewidth=2)
    ax.add_patch(saleroom)
    ax.text(3.1, 4.7, "ТОРГОВЫЙ ЗАЛ\n(Saleroom)", ha="center", va="center",
            fontsize=11, fontweight="bold", color="#1E293B")
    ax.text(3.1, 3.6, "Генерация списка\nпокупок корзины\n$k \\sim Triang(1, 5, 3)$\nМаршрутизация",
            ha="center", va="center", fontsize=8.5, color="#475569")

    # Стрелка из торгового зала к отделам
    ax.annotate("", xy=(4.8, 4.2), xytext=(4.2, 4.2),
                arrowprops=dict(arrowstyle="-|>", color=border_color, lw=2, mutation_scale=15))

    # Контейнер для 5 параллельных отделов (высота уменьшена, чтобы исключить наложение)
    dept_container = patches.FancyBboxPatch((4.9, 0.8), 5.6, 6.3,
                                            boxstyle="round,pad=0.15,rounding_size=0.2",
                                            facecolor=bg_container, edgecolor=border_color,
                                            linewidth=1.8, linestyle="--")
    ax.add_patch(dept_container)
    ax.text(7.7, 6.9, "Мини-супермаркет: 5 отделов с раздельным обслуживанием",
            ha="center", va="center", fontsize=10.0, fontweight="bold", color="#1E293B")

    # 5 отделов и их координаты
    dept_info = [
        ("Отдел 1: Бакалея", 6.35, "#DBEAFE"),
        ("Отдел 2: Молочный", 5.15, "#E0E7FF"),
        ("Отдел 3: Мясной", 3.95, "#FCE7F3"),
        ("Отдел 4: Овощи/фрукты", 2.75, "#DCFCE7"),
        ("Отдел 5: Кулинария", 1.55, "#FEF3C7"),
    ]

    for name, y_c, bg_color in dept_info:
        # Линия ветвления от входа отделов к очереди
        ax.plot([4.8, 5.15, 5.15], [4.2, 4.2, y_c], color=border_color, lw=1.5)
        ax.annotate("", xy=(5.35, y_c), xytext=(5.15, y_c),
                    arrowprops=dict(arrowstyle="-|>", color=border_color, lw=1.5, mutation_scale=12))

        # Очередь FIFO (полосатый прямоугольник по Слайду 6)
        q_w, q_h = 0.9, 0.5
        q_x = 5.35
        q_y = y_c - q_h / 2
        queue_box = patches.Rectangle((q_x, q_y), q_w, q_h,
                                      facecolor="#FFFFFF", edgecolor=border_color, linewidth=1.4)
        ax.add_patch(queue_box)
        for s in np.linspace(q_x + 0.18, q_x + q_w - 0.18, 4):
            ax.plot([s, s], [q_y, q_y + q_h], color=border_color, lw=1.3)
        ax.text(q_x + q_w / 2, q_y - 0.18, "FIFO", ha="center", va="top", fontsize=6.5, color="#64748B")

        # Стрелка от очереди к прибору обслуживания
        ax.annotate("", xy=(6.7, y_c), xytext=(6.25, y_c),
                    arrowprops=dict(arrowstyle="-|>", color=border_color, lw=1.5, mutation_scale=12))

        # Прибор обслуживания (Канал СМО)
        serv_w, serv_h = 2.9, 0.72
        serv_x = 6.7
        serv_y = y_c - serv_h / 2
        terminal = patches.FancyBboxPatch((serv_x, serv_y), serv_w, serv_h,
                                          boxstyle="round,pad=0.08,rounding_size=0.1",
                                          facecolor=bg_color, edgecolor=border_color, linewidth=1.5)
        ax.add_patch(terminal)
        ax.text(serv_x + serv_w / 2, y_c + 0.1, name, ha="center", va="center",
                fontsize=9, fontweight="bold", color="#0F172A")
        ax.text(serv_x + serv_w / 2, y_c - 0.16, "1 продавец ($T_{serv} \\sim N(1.5, 0.4)$ мин)",
                ha="center", va="center", fontsize=7.2, color="#475569")

        # Линия выхода из прибора к вертикальной шине сбора
        ax.plot([serv_x + serv_w, 10.15], [y_c, y_c], color=border_color, lw=1.5)

    # Вертикальная собирающая шина после всех отделов
    ax.plot([10.15, 10.15], [1.55, 6.35], color=border_color, lw=1.5)
    ax.annotate("", xy=(10.7, 4.0), xytext=(10.15, 4.0),
                arrowprops=dict(arrowstyle="-|>", color=border_color, lw=1.8, mutation_scale=14))

    # 3. Ромб принятия решений (Маршрутизатор покупок)
    diamond_pts = [[10.7, 4.0], [11.3, 4.5], [11.9, 4.0], [11.3, 3.5]]
    diamond = patches.Polygon(diamond_pts, closed=True,
                              facecolor="#FEF9C3", edgecolor="#CA8A04", linewidth=1.8)
    ax.add_patch(diamond)
    ax.text(11.3, 4.0, "Корзина\nпуста?", ha="center", va="center",
            fontsize=7.8, fontweight="bold", color="#854D0E")

    # Ветка 1: НЕТ -> Возврат к следующему отделу
    # Аккуратная траектория сверху без пересечения текста
    ax.annotate("", xy=(3.1, 5.7), xytext=(3.1, 7.6),
                arrowprops=dict(arrowstyle="-|>", color=amber_loop, lw=1.8, mutation_scale=14, linestyle=":"))
    ax.plot([11.3, 11.3, 3.1], [4.5, 7.6, 7.6], color=amber_loop, lw=1.8, linestyle=":")
    ax.text(11.35, 4.9, "НЕТ\n(есть еще отделы)", ha="left", va="bottom",
            fontsize=8, fontweight="bold", color=amber_loop)
    ax.text(7.2, 7.72, "Переход к следующему отделу из списка покупок (обратная связь)",
            ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#B45309")

    # Ветка 2: ДА -> Выход из магазина
    ax.annotate("", xy=(12.4, 4.0), xytext=(11.9, 4.0),
                arrowprops=dict(arrowstyle="-|>", color=border_color, lw=2.0, mutation_scale=15))
    ax.text(12.15, 4.25, "ДА", ha="center", va="bottom",
            fontsize=8.5, fontweight="bold", color=green_exit)

    # 4. Блок выхода из системы (Slide 6)
    exit_box = patches.FancyBboxPatch((12.4, 3.2), 1.8, 1.6,
                                      boxstyle="round,pad=0.1,rounding_size=0.15",
                                      facecolor=green_bg, edgecolor=green_exit, linewidth=2)
    ax.add_patch(exit_box)
    ax.text(13.3, 4.0, "ВЫХОД\nиз магазина\n(с покупками)", ha="center", va="center",
            fontsize=9.5, fontweight="bold", color="#15803D")

    # 5. Легенда элементов СМО внизу
    legend_card = patches.FancyBboxPatch((0.2, 0.1), 14.1, 0.55,
                                         boxstyle="round,pad=0.08,rounding_size=0.1",
                                         facecolor="#F1F5F9", edgecolor="#CBD5E1", linewidth=1)
    ax.add_patch(legend_card)
    legend_text = (
        "Условные обозначения (по Слайду 6):   "
        "$\\triangleright$ — Источник заявок (входной поток)   |   "
        "FIFO — Накопитель / буфер очереди   |   "
        "Канал — Прибор обслуживания (продавец)   |   "
        "$\\diamond$ — Узел маршрутизации   |   "
        "$\\rightarrow$ — Потоки заявок"
    )
    ax.text(7.25, 0.37, legend_text, ha="center", va="center", fontsize=8, color="#334155")

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Схема СМО успешно сохранена в: {output_path}")


if __name__ == "__main__":
    default_out = os.path.abspath(os.path.join(os.path.dirname(__file__), "plots", "diagram_flow.png"))
    generate_diagram(default_out)
