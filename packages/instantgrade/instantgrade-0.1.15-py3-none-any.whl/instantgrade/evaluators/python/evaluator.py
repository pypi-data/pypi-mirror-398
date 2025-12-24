"""
Evaluator — The orchestrator for the entire grading pipeline.

Responsibilities:
  1. Ingest instructor solution
  2. Discover student submissions
  3. Delegate grading to the appropriate execution backend (Docker or local)
  4. Collect, consolidate, and report results
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from instantgrade.evaluators.python.ingestion.solution_ingestion import SolutionIngestion
from instantgrade.reporting.reporting_service import ReportingService
from instantgrade.utils.logger import setup_logger
from instantgrade.evaluators.python.execution_service_docker import ExecutionServiceDocker
from instantgrade.evaluators.python.notebook_executor import NotebookExecutor


class Evaluator:
    """
    The main orchestrator class responsible for grading workflows.

    Parameters
    ----------
    solution_file_path : str or Path
        Path to instructor's reference solution notebook.
    submission_folder_path : str or Path
        Folder containing all student notebooks, or a single notebook file path.
    use_docker : bool, optional
        Whether to use Docker-based isolated grading (default=True).
    parallel_workers : int, optional
        Number of parallel workers (future support, default=1).
    log_path : str, optional
        Path to directory for saving logs.
    log_level : str, optional
        Logging verbosity ("debug", "normal", "silent").

    best_n : Optional[int]
        If provided, ReportingService uses the Best-N scoring method.
        If None or 0, Best-N is disabled.

    scaled_range : Optional[Tuple[float, float]]
        If provided AND best_n provided, scores are scaled to this range.
    """

    def __init__(
        self,
        solution_file_path: str | Path,
        submission_folder_path: str | Path,
        use_docker: bool = True,
        parallel_workers: int = 1,
        log_path: str | Path = "./logs",
        log_level: str = "normal",
        # NEW OPTIONAL PARAMETERS FOR REPORTING
        best_n: Optional[int] = None,
        scaled_range: Optional[Tuple[float, float]] = None,
    ):
        self.solution_path = Path(solution_file_path)
        self.submission_path = Path(submission_folder_path)
        self.use_docker = use_docker
        self.parallel_workers = parallel_workers

        # LOGGING
        self.log_path = Path(log_path)
        self.log_path.mkdir(exist_ok=True, parents=True)
        self.logger = setup_logger(level=log_level)

        # REPORT + EXECUTION STORAGE
        self.report = None
        self.executed = []

        # NEW: store Best-N and scaling configuration
        self.best_n = best_n
        self.scaled_range = scaled_range

    # ------------------------------------------------------------------
    def run(self) -> ReportingService:
        """Run the full evaluation pipeline."""
        self.logger.info("Starting evaluation pipeline...")

        start_time = time.time()

        # 1. Load instructor solution
        self.logger.info("Loading instructor solution...")
        solution_service = SolutionIngestion(self.solution_path)
        self.solution = solution_service.understand_notebook_solution()
        self.logger.info(f"Loaded {len(self.solution['questions'])} questions.")

        # 2. Discover student submissions
        # Accept either a folder containing .ipynb files or a single .ipynb file.
        if not self.submission_path.exists():
            raise FileNotFoundError(f"Submission path does not exist: {self.submission_path}")

        if self.submission_path.is_file():
            # Single notebook file provided
            if self.submission_path.suffix.lower() != ".ipynb":
                raise FileNotFoundError(
                    f"Submission file provided is not a .ipynb: {self.submission_path}"
                )
            all_submissions = [self.submission_path]
        else:
            # Directory provided: discover all .ipynb files at top-level
            all_submissions = sorted(
                [f for f in self.submission_path.glob("*.ipynb") if f.is_file()]
            )
            if not all_submissions:
                raise FileNotFoundError(f"No student notebooks found in {self.submission_path}")

        self.logger.info(f"Discovered {len(all_submissions)} submissions to grade.")

        # 3. Execute grading
        executed = self.execute_all(all_submissions)
        self.executed = executed
        self.logger.info("Execution phase completed successfully.")

        # 4. Build report (NEW → pass best_n and scaled_range)
        self.report = ReportingService(
            executed_results=executed,
            logger=self.logger,
            total_assertions=self.solution["summary"]["total_assertions"],
            best_n=self.best_n,
            scaled_range=self.scaled_range,
        )

        self.logger.info("Report generation complete.")

        elapsed = round(time.time() - start_time, 2)
        self.logger.info(f"Total evaluation completed in {elapsed}s.")

        return self.report

    # ------------------------------------------------------------------
    def execute_all(self, submission_paths: List[Path]) -> List[Dict[str, Any]]:
        """Run grading across all students sequentially (parallel later)."""
        if self.use_docker:
            self.logger.info("Starting Docker-based evaluation pipeline...")
            execution_service = ExecutionServiceDocker(logger=self.logger)
            # Try to start a persistent container for reuse to speed up grading
            try:
                execution_service.start_container()
            except Exception:
                self.logger.warning(
                    "Could not start persistent Docker container; continuing with per-student docker runs"
                )
        else:
            self.logger.info("Starting Local evaluation pipeline...")
            execution_service = NotebookExecutor(timeout=120)

        results = []

        try:
            for idx, sub in enumerate(submission_paths, start=1):
                self.logger.info(f"[{idx}/{len(submission_paths)}] Grading: {sub.name}")

                try:
                    if self.use_docker:
                        result = execution_service.execute_student(self.solution_path, sub)
                    else:
                        result = self._grade_local_student(execution_service, sub)

                    results.append(result)

                except Exception as e:
                    self.logger.exception(f"Fatal error grading {sub.name}: {e}")

                    results.append(
                        {
                            "student_path": sub,
                            "execution": {
                                "success": False,
                                "errors": [str(e)],
                                "student_meta": {"name": "Unknown", "roll_number": "Unknown"},
                            },
                            "results": [],
                        }
                    )

        finally:
            # If using docker and we started a persistent container, teardown
            if self.use_docker and execution_service is not None:
                try:
                    execution_service.teardown()
                except Exception:
                    pass
        return results

    # ------------------------------------------------------------------
    def _grade_local_student(
        self, executor: NotebookExecutor, submission_path: Path
    ) -> Dict[str, Any]:
        """Grade a student locally by executing their notebook and running assertions."""
        self.logger.info(f"[Local] Grading {submission_path.name}")

        # Execute student notebook to get namespace. When grading locally we
        # must execute the notebook in-process to obtain the resulting
        # namespace (not via the Docker-path in NotebookExecutor.run_notebook)
        # which currently returns an empty namespace on the host. Use the
        # internal local runner for accurate evaluation.
        exec_result = executor._run_notebook_locally(submission_path)
        ns = exec_result.get("namespace", {})
        name = ns.get("name", "Unknown")
        roll = ns.get("roll_number", "Unknown")

        # Now run assertions using ComparisonService for each question
        from instantgrade.evaluators.python.comparison.comparison_service import ComparisonService

        comparison_svc = ComparisonService()

        # Build assertion list from solution questions
        assertions_list = []
        for question_name, question_data in self.solution.get("questions", {}).items():
            for assertion_code in question_data.get("tests", []):
                assertions_list.append(
                    {
                        "code": assertion_code,
                        "question": question_name,
                        "description": question_data.get("description", ""),
                    }
                )

        # Run all assertions
        results = comparison_svc.run_assertions(assertions_list, ns)

        return {
            "student_path": submission_path,
            "execution": {
                "success": exec_result.get("success", False),
                "errors": exec_result.get("errors", []),
                "namespace": ns,
                "student_meta": {"name": name, "roll_number": roll},
            },
            "results": results,
        }

    # ------------------------------------------------------------------
    def to_html(self, path: str | Path):
        """Generate HTML report for graded results."""
        if self.report is None:
            raise RuntimeError("No report available. Run Evaluator.run() first.")

        path = Path(path)
        self.report.to_html(path)
        self.logger.info(f"HTML report generated at: {path}")
        return str(path)

    # ------------------------------------------------------------------
    def summary(self, all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate quick text summary statistics."""
        total = len(all_results)
        passed = sum(1 for r in all_results if r.get("execution", {}).get("success", False))
        return {"total": total, "passed": passed, "failed": total - passed}
