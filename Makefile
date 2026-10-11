.PHONY: help lr21 lr22 lab1 lab2 test diagrams excel docx all clean

help:
	@echo "Доступные команды для запуска лабораторной работы №2:"
	@echo "  make lr21       - Запуск Лабораторной 2.1 (контрольный прогон + трассировка + диаграммы)"
	@echo "  make lr22       - Запуск Лабораторной 2.2 (верификация, 1000 репликаций, 2x2 дашборды)"
	@echo "  make test       - Запуск пакета автоматических проверочных тестов (6/6 тестов)"
	@echo "  make diagrams   - Перегенерация концептуальных диаграмм (Слайд 6 и Слайд 15)"
	@echo "  make excel      - Перегенерация Excel-таблицы (supermarket_simulation.xlsx)"
	@echo "  make docx       - Перегенерация Word-отчетов (.docx)"
	@echo "  make all        - Полный цикл: тесты, диаграммы, LR21, LR22, Excel"
	@echo "  make clean      - Очистка временных файлов и кэша Python"

lab1: lr21
lab2: lr22

lr21: diagrams
	uv run python lab2/lr21/run_lr21.py

lr22: test
	uv run python lab2/lr22/run_lr22.py

test:
	uv run python -m unittest lab2/lr22/tests_verification.py

diagrams:
	uv run python lab2/generate_diagram.py
	uv run python lab2/generate_timeline_diagram.py

excel:
	uv run python lab2/generate_excel.py

docx:
	uv run --with python-docx python lab2/generate_docx_reports.py

all: test diagrams lr21 lr22 excel
	@echo "================================================================================"
	@echo "  Все данные, логи, таблицы и графики для LR21 и LR22 успешно сгенерированы!   "
	@echo "================================================================================"

clean:
	python -c "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__') if p.exists()]"
