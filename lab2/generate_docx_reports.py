import os
import sys
import docx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)


def create_lr21_docx(output_path: str, base_dir: str):
    doc = docx.Document()
    
    # Page margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # Title
    title = doc.add_paragraph()
    r = title.add_run("ОТЧЕТ ПО ЛАБОРАТОРНОЙ РАБОТЕ №2.1 (LR21)\n")
    r.font.size = Pt(16)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    sub = doc.add_paragraph()
    r2 = sub.add_run("Создание имитационной модели сложной системы\nВариант №5: Мини-супермаркет с раздельным обслуживанием")
    r2.font.size = Pt(12)
    r2.font.italic = True
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph("-" * 60)

    # Section 1: Conceptual model
    h1 = doc.add_heading("1. Концептуальная модель сложной системы", level=1)
    p = doc.add_paragraph(
        "Объектом моделирования является мини-супермаркет, состоящий из пяти специализированных отделов "
        "(Бакалея, Молочный, Мясной, Овощи и фрукты, Кулинария). В каждом отделе работает ровно один продавец, "
        "который осуществляет как непосредственный подбор и выдачу товара, так и окончательный расчет (оплату) с клиентом. "
        "Общего кассового узла на выходе нет — расчет распределен по отделам."
    )

    # Insert diagram
    diag_path = os.path.join(base_dir, "plots", "diagram_flow.png")
    if os.path.exists(diag_path):
        doc.add_paragraph("Потоковая диаграмма взаимодействия элементов системы:")
        doc.add_picture(diag_path, width=Inches(6.2))
        p_cap = doc.add_paragraph("Рис. 1. Потоковая диаграмма мини-супермаркета с 5 отделами")
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.runs[0].font.size = Pt(9)
        p_cap.runs[0].font.italic = True

    timeline_path = os.path.join(base_dir, "plots", "diagram_quasiparallel.png")
    if os.path.exists(timeline_path):
        doc.add_paragraph("Временная диаграмма квазипараллельного взаимодействия и синхронизации календаря событий:")
        doc.add_picture(timeline_path, width=Inches(6.2))
        p_cap2 = doc.add_paragraph("Рис. 2. Временная диаграмма квазипараллелизма (по лекции 2, слайд 15)")
        p_cap2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap2.runs[0].font.size = Pt(9)
        p_cap2.runs[0].font.italic = True

    # Section 2: Input parameters table
    doc.add_heading("2. Таблица входных параметров модели", level=1)
    table_data = [
        ["Данные прогона (Run input data)", "Параметры (Controlled)", "Переменные (Uncontrolled)"],
        ["Число репликаций: 1000", "Число отделов: 5 шт.", "Интервал прихода: Exp (1.0 мин)"],
        ["Время прогона: 60.0 мин", "Продавцов в отделе: 1 чел.", "Закон прихода: Экспоненциальный"],
        ["Режим: С дообслуживанием", "Покупателей на старте: 2 чел.", "Время обслуживания: Norm(1.8, 0.5)"],
        ["ДСЧ seed: 42", "Дисциплина очереди: FIFO", "Корзина покупок: 1..5 отделов"]
    ]
    t = doc.add_table(rows=len(table_data), cols=3)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r_idx, row in enumerate(table_data):
        for c_idx, val in enumerate(row):
            cell = t.cell(r_idx, c_idx)
            cell.text = val
            if r_idx == 0:
                set_cell_background(cell, "1E3A8A")
                cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                cell.paragraphs[0].runs[0].font.bold = True
            else:
                set_cell_background(cell, "F8FAFC" if r_idx % 2 == 1 else "FFFFFF")
                cell.paragraphs[0].runs[0].font.size = Pt(9.5)

    doc.add_paragraph()

    # Section 3: Run results
    doc.add_heading("3. Результаты контрольного прогона модели", level=1)
    res_text = (
        "1. Дискретные отклики:\n"
        "   • Среднее время в супермаркете (T_sys): 19.77 мин\n"
        "   • СКО времени пребывания: 10.65 мин\n"
        "   • Среднее время ожидания в очередях: 14.18 мин\n"
        "   • Среднее число отделов на покупателя: 3.16\n\n"
        "2. Непрерывные отклики:\n"
        "   • Средняя суммарная длина очередей (L_q): 10.35 чел.\n"
        "   • Среднее число занятых продавцов (K_busy): 4.07 из 5\n"
        "   • Коэффициент загрузки персонала (rho): 81.48 %\n"
        "   • Среднее число покупателей в магазине: 14.42 чел.\n\n"
        "3. Аддитивные отклики:\n"
        "   • Всего вошло покупателей: 64 чел.\n"
        "   • Полностью обслужено покупателей: 64 чел.\n"
        "   • Всего завершено транзакций в 5 отделах: 202 оп.\n\n"
        "4. Финальные отклики:\n"
        "   • Фактическое время завершения прогона: 87.71 мин"
    )
    p_res = doc.add_paragraph(res_text)
    p_res.runs[0].font.name = "Consolas"
    p_res.runs[0].font.size = Pt(9.5)

    # Section 4: Conclusions
    doc.add_heading("4. Выводы", level=1)
    doc.add_paragraph(
        "Программная модель полностью реализована на языке Python с использованием алгоритма "
        "Event Scheduling (календарь событий). Постоянный временной шаг не используется. "
        "Обеспечен сбор всех 4 обязательных типов откликов. Результаты подтверждают корректность модели."
    )

    doc.save(output_path)
    print(f"Отчет LR21 сохранен в docx: {output_path}")


def create_lr22_docx(output_path: str, base_dir: str):
    doc = docx.Document()
    
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    title = doc.add_paragraph()
    r = title.add_run("ОТЧЕТ ПО ЛАБОРАТОРНОЙ РАБОТЕ №2.2 (LR22)\n")
    r.font.size = Pt(16)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    sub = doc.add_paragraph()
    r2 = sub.add_run("Верификация имитационной модели сложной системы\nВариант №5: Мини-супермаркет с раздельным обслуживанием")
    r2.font.size = Pt(12)
    r2.font.italic = True
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph("-" * 60)

    doc.add_heading("1. Динамика откликов в модельном времени", level=1)
    
    plots = [
        ("dynamics_time_in_supermarket.png", "Рис. 1. Динамика времени покупателя в супермаркете T_sys (дискретный отклик)"),
        ("dynamics_queue_length.png", "Рис. 2. Динамика суммарной длины очередей во времени L_q(t) (непрерывный отклик)"),
        ("dynamics_sellers_utilization.png", "Рис. 3. Динамика использования продавцов 5 отделов")
    ]
    for p_name, cap in plots:
        p_path = os.path.join(base_dir, "plots", p_name)
        if os.path.exists(p_path):
            doc.add_picture(p_path, width=Inches(5.8))
            p_cap = doc.add_paragraph(cap)
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.runs[0].font.size = Pt(9)
            p_cap.runs[0].font.italic = True

    doc.add_heading("2. Сходимость при повторных прогонах (1000 репликаций)", level=1)
    conv_path = os.path.join(base_dir, "plots", "convergence_replications.png")
    if os.path.exists(conv_path):
        doc.add_picture(conv_path, width=Inches(5.8))
        p_cap = doc.add_paragraph("Рис. 4. Сходимость среднего времени в супермаркете и 95% доверительный интервал")
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.runs[0].font.size = Pt(9)
        p_cap.runs[0].font.italic = True

    doc.add_paragraph(
        "По результатам 1000 независимых стохастических прогонов среднее время пребывания в магазине "
        "составило 17.98 мин. 95% доверительный интервал равен [17.68; 18.28] мин (полуширина интервала всего 0.30 мин)."
    )

    doc.add_heading("3. Параметрический анализ чувствительности", level=1)
    sens_plots = [
        ("variation_arrival_rate.png", "Рис. 5. Зависимость откликов от интенсивности входного потока lambda (тест монотонности)"),
        ("variation_service_time.png", "Рис. 6. Зависимость откликов от среднего времени обслуживания в отделах")
    ]
    for p_name, cap in sens_plots:
        p_path = os.path.join(base_dir, "plots", p_name)
        if os.path.exists(p_path):
            doc.add_picture(p_path, width=Inches(5.8))
            p_cap = doc.add_paragraph(cap)
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.runs[0].font.size = Pt(9)
            p_cap.runs[0].font.italic = True

    doc.add_heading("4. Результаты автоматических юнит-тестов", level=1)
    unit_text = (
        "Разработан и успешно выполнен пакет из 6 верификационных тестов:\n"
        "1. test_reproducibility: идентичность числовых откликов при совпадении seed (ОК);\n"
        "2. test_clearance_completes_all_buyers: гарантия обслуживания всех вошедших клиентов (ОК);\n"
        "3. test_monotonicity_arrival_rate: строгий монотонный рост очередей при росте lambda (ОК);\n"
        "4. test_monotonicity_service_time: монотонный рост времени в системе при росте mu_serv (ОК);\n"
        "5. test_queue_wait_time_validity: физический баланс времени (W_q < T_sys, разница равна времени на кассах) (ОК);\n"
        "6. test_littles_law_qualitative: соответствие фундаментальному закону Литтла N_sys = lambda * T_sys (ОК)."
    )
    doc.add_paragraph(unit_text)

    doc.add_heading("5. Выводы", level=1)
    doc.add_paragraph(
        "Имитационная модель успешно прошла верификацию. Продемонстрирована высокая статистическая точность "
        "и строгое соответствие физическим законам предметной области."
    )

    doc.save(output_path)
    print(f"Отчет LR22 сохранен в docx: {output_path}")


if __name__ == "__main__":
    base = os.path.abspath(os.path.dirname(__file__))
    create_lr21_docx(os.path.join(base, "lr21", "report_lr21.docx"), base)
    create_lr22_docx(os.path.join(base, "lr22", "report_lr22.docx"), base)
