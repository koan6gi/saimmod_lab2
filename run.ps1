# run.ps1 - Helper script for running lab assignments
param(
    [string]$Target = "help",
    [int]$Replications = 0
)

switch ($Target.ToLower()) {
    "lr21" {
        Write-Host ">>> [LR21] Generating diagrams & running 60-min trace..." -ForegroundColor Cyan
        uv run python lab2/generate_diagram.py
        uv run python lab2/generate_timeline_diagram.py
        uv run python lab2/lr21/run_lr21.py --time 60 --seed 42 --trace
    }
    "lab1" {
        & $PSCommandPath lr21
    }
    "lr22" {
        Write-Host ">>> [LR22] Running verification tests & replication study..." -ForegroundColor Cyan
        uv run python -m unittest lab2/lr22/tests_verification.py
        if ($Replications -gt 0) {
            uv run python lab2/lr22/run_lr22.py --replications $Replications
        } else {
            uv run python lab2/lr22/run_lr22.py
        }
    }
    "lab2" {
        & $PSCommandPath lr22
    }
    "test" {
        Write-Host ">>> Running automated verification tests..." -ForegroundColor Green
        uv run python -m unittest lab2/lr22/tests_verification.py
    }
    "diagrams" {
        Write-Host ">>> Generating conceptual diagrams..." -ForegroundColor Yellow
        uv run python lab2/generate_diagram.py
        uv run python lab2/generate_timeline_diagram.py
    }
    "excel" {
        Write-Host ">>> Generating Excel workbook (supermarket_simulation.xlsx)..." -ForegroundColor Green
        uv run python lab2/generate_excel.py
    }
    "docx" {
        Write-Host ">>> Generating Word report documents (.docx)..." -ForegroundColor Magenta
        uv run --with python-docx python lab2/generate_docx_reports.py
    }
    "all" {
        Write-Host ">>> [FULL RUN] Tests, Diagrams, LR21, LR22, Excel..." -ForegroundColor Cyan
        uv run python -m unittest lab2/lr22/tests_verification.py
        uv run python lab2/generate_diagram.py
        uv run python lab2/generate_timeline_diagram.py
        uv run python lab2/lr21/run_lr21.py --time 60 --seed 42 --trace
        uv run python lab2/lr22/run_lr22.py
        uv run python lab2/generate_excel.py
        Write-Host ">>> ALL DATA AND PLOTS GENERATED SUCCESSFULLY!" -ForegroundColor Green
    }
    default {
        Write-Host "Usage for run.ps1 script:" -ForegroundColor Yellow
        Write-Host "  .\run.ps1 lr21            - Run Lab 2.1 (Trace, Data, Diagrams)"
        Write-Host "  .\run.ps1 lr22            - Run Lab 2.2 (1000 Replications, 2x2 Dashboards)"
        Write-Host "  .\run.ps1 lr22 -Replications 500 - Run Lab 2.2 with custom replication count"
        Write-Host "  .\run.ps1 test            - Run automated unittest suite (6 tests)"
        Write-Host "  .\run.ps1 diagrams        - Generate Slide 6 and Slide 15 diagrams"
        Write-Host "  .\run.ps1 excel           - Generate supermarket_simulation.xlsx"
        Write-Host "  .\run.ps1 all             - Full end-to-end execution of all tasks"
    }
}
