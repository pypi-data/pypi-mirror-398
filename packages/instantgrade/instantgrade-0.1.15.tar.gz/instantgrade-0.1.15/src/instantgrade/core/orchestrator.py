"""Routing orchestrator for InstantGrade.

This module provides a small router class `InstantGrader` which decides
which evaluator to use based on the provided solution/submission paths
or an explicit override. It currently supports the existing Python
`Evaluator` (notebooks) and a new Excel `Evaluator` implemented under
`instantgrade.evaluators.excel.evaluator`.

The class is intentionally thin: it instantiates the correct evaluator
and delegates `run()`, `to_html()` and `summary()` calls so callers can
continue using a single entry point.
"""

from pathlib import Path
from typing import Optional

from instantgrade.reporting.reporting_service import ReportingService

try:
    # Existing python notebook evaluator
    from instantgrade.evaluators.python.evaluator import Evaluator as PythonEvaluator
except Exception:  # pragma: no cover - defensive
    PythonEvaluator = None

try:
    # Excel evaluator implemented as part of migration
    from instantgrade.evaluators.excel.evaluator import Evaluator as ExcelEvaluator
except Exception:  # pragma: no cover - defensive
    ExcelEvaluator = None


class InstantGrader:
    """Selects appropriate evaluator (python / excel) and delegates work.

    Parameters
    ----------
    solution_file_path, submission_folder_path : str | Path
        Paths used to determine evaluator type and perform grading.
    override_type : Optional[str]
        If provided, forces evaluator selection. Accepted values: "python", "excel".
    Any additional keyword args are forwarded to the selected evaluator's constructor.
    """

    def __init__(
        self,
        solution_file_path: str | Path,
        submission_folder_path: str | Path,
        override_type: Optional[str] = None,
        **kwargs,
    ):
        self.solution_path = Path(solution_file_path)
        self.submission_path = Path(submission_folder_path)
        self.override_type = override_type
        self.kwargs = kwargs

        self._evaluator = None

    def _select_evaluator(self):
        """Choose which evaluator class to instantiate.

        Priority:
        - If override_type provided -> use that.
        - Otherwise inspect solution file suffix and submission files.
        """
        if self.override_type:
            typ = str(self.override_type).lower()
            if typ == "python":
                if PythonEvaluator is None:
                    raise RuntimeError("Python evaluator not available")
                return PythonEvaluator(self.solution_path, self.submission_path, **self.kwargs)
            if typ in ("excel", "xlsx", "xls"):
                if ExcelEvaluator is None:
                    raise RuntimeError("Excel evaluator not available")
                return ExcelEvaluator(self.solution_path, self.submission_path, **self.kwargs)

        # No override: infer from file extensions
        suffix = self.solution_path.suffix.lower()
        if suffix in (".ipynb", ".py"):
            if PythonEvaluator is None:
                raise RuntimeError("Python evaluator not available")
            return PythonEvaluator(self.solution_path, self.submission_path, **self.kwargs)

        if suffix in (".xlsx", ".xls", ".xlsm"):
            if ExcelEvaluator is None:
                raise RuntimeError("Excel evaluator not available")
            return ExcelEvaluator(self.solution_path, self.submission_path, **self.kwargs)

        # If solution file is ambiguous (e.g. directory) inspect submissions
        if self.submission_path.exists() and self.submission_path.is_dir():
            # look for any .ipynb or .xlsx files
            ipynb = any(p.suffix.lower() == ".ipynb" for p in self.submission_path.glob("*.ipynb"))
            xlsx = any(p.suffix.lower() in (".xlsx", ".xls", ".xlsm") for p in self.submission_path.glob("*.xlsx"))
            if ipynb and PythonEvaluator is not None:
                return PythonEvaluator(self.solution_path, self.submission_path, **self.kwargs)
            if xlsx and ExcelEvaluator is not None:
                return ExcelEvaluator(self.solution_path, self.submission_path, **self.kwargs)

        raise RuntimeError("Could not select an evaluator for the provided paths")

    # ------------------------------------------------------------------
    def run(self):
        """Run the selected evaluator and return its ReportingService (or similar) result."""
        if self._evaluator is None:
            self._evaluator = self._select_evaluator()

        # delegate to evaluator's run method
        report = self._evaluator.run()

        # If evaluator returns a ReportingService directly, pass it through; if it
        # returns raw executed_results, wrap with ReportingService for compatibility.
        if isinstance(report, ReportingService):
            # Cache the report on the router for convenience (notebooks often
            # reference the router instance for fallbacks). This does not mutate
            # the evaluator but provides a stable place to read the generated
            # report DataFrame/HTML output.
            self.report = report
            return report

        # If evaluator returned executed_results list -> build ReportingService
        try:
            wrapped = ReportingService(executed_results=report)
            self.report = wrapped
            return wrapped
        except Exception:
            # If wrapping failed (e.g., evaluator returned an object already),
            # still cache the raw return so callers can inspect it.
            self.report = report
            return report

    # Delegation helpers
    def to_html(self, path: str | Path):
        if self._evaluator is None:
            self._evaluator = self._select_evaluator()
        # If we already have a cached ReportingService, prefer delegating to it
        # since it contains dataframe-level context. Otherwise fall back to the
        # evaluator's to_html implementation.
        if hasattr(self, "report") and hasattr(self.report, "to_html"):
            return self.report.to_html(path)

        if hasattr(self._evaluator, "to_html"):
            return self._evaluator.to_html(path)
        raise RuntimeError("Selected evaluator does not implement to_html()")

    def summary(self, all_results=None):
        if self._evaluator is None:
            self._evaluator = self._select_evaluator()
        if hasattr(self._evaluator, "summary"):
            return self._evaluator.summary(all_results)
        raise RuntimeError("Selected evaluator does not implement summary()")


