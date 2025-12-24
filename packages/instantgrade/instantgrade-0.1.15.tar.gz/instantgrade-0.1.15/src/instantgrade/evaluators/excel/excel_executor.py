"""Minimal Excel executor for the new instantgrade architecture.

This is a lightweight stub that can be expanded later. It does not
modify any src/instantgrade files.
"""

from pathlib import Path


class ExcelExecutor:
    """Execute/grade Excel-based assignments minimally."""

    def __init__(self, timeout: int = 60):
        self.timeout = timeout

    def execute_student(self, solution_path: Path, submission_path: Path) -> dict:
        # Minimal runner: verify file exists and return a placeholder result
        solution_path = Path(solution_path)
        submission_path = Path(submission_path)

        if not submission_path.exists():
            return {
                "student_path": submission_path,
                "execution": {"success": False, "errors": ["File missing"]},
                "results": [],
            }

        # Placeholder: no real grading yet
        return {
            "student_path": submission_path,
            "execution": {"success": True, "errors": []},
            "results": [],
        }
