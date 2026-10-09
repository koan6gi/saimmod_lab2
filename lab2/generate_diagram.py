import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def generate_diagram(output_path):
    fig, ax = plt.subplots(figsize=(13, 7.5), dpi=300)
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 7.5)
    ax.axis('off')

    # Color palette - clean academic style
    bg_box = '#F8FAFC'
    border_color = '#1E293B'
    accent_blue = '#2563EB'
    queue_color = '#475569'

    # 1. Entrance triangle (Source of customers)
    tri_x = [0.4, 0.4, 1.1]
    tri_y = [4.1, 3.3, 3.7]
    triangle = patches.Polygon(xy=list(zip(tri_x, tri_y)), closed=True,
                               facecolor='#FFFFFF', edgecolor=border_color, linewidth=2)
    ax.add_patch(triangle)
    ax.text(0.75, 2.9, 'Входной\nпоток\nпокупателей\n($\\lambda$, Exp)', 
            ha='center', va='top', fontsize=9, fontweight='bold', color='#334155')

    # Arrow from triangle to Saleroom
    ax.annotate('', xy=(2.0, 3.7), xytext=(1.1, 3.7),
                arrowprops=dict(arrowstyle="-|>", color=border_color, lw=2, mutation_scale=15))

    # 2. Saleroom / Shopping router box
    saleroom = patches.FancyBboxPatch((2.0, 2.2), 2.2, 3.0,
                                      boxstyle="round,pad=0.1,rounding_size=0.15",
                                      facecolor='#FFFFFF', edgecolor=border_color, linewidth=2)
    ax.add_patch(saleroom)
    ax.text(3.1, 3.9, 'Торговый зал\n(Saleroom)', ha='center', va='center',
            fontsize=12, fontweight='bold', color=border_color)
    ax.text(3.1, 2.9, 'Выбор корзины\nотделов и\nмаршрутизация', ha='center', va='center',
            fontsize=9, color='#64748B')

    # Arrow from Saleroom to Department hub
    ax.annotate('', xy=(4.9, 3.7), xytext=(4.2, 3.7),
                arrowprops=dict(arrowstyle="-|>", color=border_color, lw=2, mutation_scale=15))

    # Big container box for 5 departments
    dept_container = patches.FancyBboxPatch((5.0, 0.5), 5.5, 6.5,
                                           boxstyle="round,pad=0.15,rounding_size=0.2",
                                           facecolor=bg_box, edgecolor=border_color, linewidth=2, linestyle='--')
    ax.add_patch(dept_container)
    ax.text(7.75, 6.75, 'Мини-супермаркет: 5 отделов с раздельным обслуживанием',
            ha='center', va='center', fontsize=11, fontweight='bold', color=border_color)

    # 5 Departments info
    dept_names = [
        ('Отдел 1: Бакалея', 5.8),
        ('Отдел 2: Молочный', 4.6),
        ('Отдел 3: Мясной', 3.4),
        ('Отдел 4: Овощи/фрукты', 2.2),
        ('Отдел 5: Кулинария', 1.0)
    ]

    for name, y_center in dept_names:
        # Branch line from Saleroom exit (4.9, 3.7) to department queue entrance
        ax.plot([4.9, 5.3, 5.3], [3.7, 3.7, y_center], color=border_color, lw=1.5)
        ax.annotate('', xy=(5.5, y_center), xytext=(5.3, y_center),
                    arrowprops=dict(arrowstyle="-|>", color=border_color, lw=1.5, mutation_scale=12))

        # Queue symbol (striped box)
        q_width = 1.0
        q_height = 0.5
        q_x = 5.5
        q_y = y_center - q_height / 2
        queue_box = patches.Rectangle((q_x, q_y), q_width, q_height,
                                      facecolor='#FFFFFF', edgecolor=border_color, linewidth=1.5)
        ax.add_patch(queue_box)
        # Vertical stripes inside queue
        for step in np.linspace(q_x + 0.2, q_x + q_width - 0.2, 4):
            ax.plot([step, step], [q_y, q_y + q_height], color=border_color, lw=1.5)

        # Arrow from queue to seller terminal
        ax.annotate('', xy=(7.0, y_center), xytext=(6.5, y_center),
                    arrowprops=dict(arrowstyle="-|>", color=border_color, lw=1.5, mutation_scale=12))

        # Department / Seller terminal box
        terminal = patches.FancyBboxPatch((7.0, y_center - 0.35), 3.0, 0.7,
                                          boxstyle="round,pad=0.08,rounding_size=0.1",
                                          facecolor='#FFFFFF', edgecolor=border_color, linewidth=1.5)
        ax.add_patch(terminal)
        ax.text(8.5, y_center + 0.08, name, ha='center', va='center',
                fontsize=9.5, fontweight='bold', color=border_color)
        ax.text(8.5, y_center - 0.18, 'Продавец (обслуживание + расчет)', ha='center', va='center',
                fontsize=7.5, color='#475569')

        # Arrow out from terminal
        ax.plot([10.0, 10.7, 10.7], [y_center, y_center, 3.7], color=border_color, lw=1.5)

    # Reconnection hub after departments:
    # 1) Loop back arrow to Saleroom (if more departments to visit)
    ax.annotate('', xy=(3.1, 5.2), xytext=(3.1, 7.2),
                arrowprops=dict(arrowstyle="-|>", color='#D97706', lw=1.8, mutation_scale=14, linestyle=':'))
    ax.plot([10.7, 10.7, 3.1], [3.7, 7.2, 7.2], color='#D97706', lw=1.8, linestyle=':')
    ax.text(6.8, 7.35, 'Переход к следующему отделу из списка покупок',
            ha='center', va='bottom', fontsize=9, fontweight='bold', color='#B45309')

    # 2) Exit arrow (when all chosen departments are visited)
    ax.annotate('', xy=(12.4, 3.7), xytext=(10.7, 3.7),
                arrowprops=dict(arrowstyle="-|>", color=border_color, lw=2.2, mutation_scale=16))
    exit_box = patches.FancyBboxPatch((11.4, 2.8), 1.2, 1.8,
                                      boxstyle="round,pad=0.1,rounding_size=0.15",
                                      facecolor='#DCFCE7', edgecolor='#16A34A', linewidth=2)
    ax.add_patch(exit_box)
    ax.text(12.0, 3.7, 'ВЫХОД\nиз\nмагазина\n(с покупками)', ha='center', va='center',
            fontsize=9.5, fontweight='bold', color='#15803D')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Diagram saved to {output_path}")

if __name__ == "__main__":
    import os
    default_out = os.path.abspath(os.path.join(os.path.dirname(__file__), "plots", "diagram_flow.png"))
    generate_diagram(default_out)
