"""Excel evaluator runner (minimal)."""

from .excel_executor import ExcelExecutor
from pathlib import Path


def run(solution: str | Path, submissions_folder: str | Path):
    sol = Path(solution)
    subs = Path(submissions_folder)
    exe = ExcelExecutor()
    results = []
    for f in sorted(subs.glob("*.xlsx")):
        results.append(exe.execute_student(sol, f))
    return results
