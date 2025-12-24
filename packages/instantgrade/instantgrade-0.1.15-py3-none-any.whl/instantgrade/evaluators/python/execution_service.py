from pathlib import Path
import os
import shutil
import copy
import traceback
from instantgrade.evaluators.python.notebook_executor import NotebookExecutor
from instantgrade.evaluators.python.comparison.comparison_service import ComparisonService
from instantgrade.utils.logger import setup_logger


class ExecutionService:
    """
    Central execution dispatcher for all submission types and environments.

    Responsibilities:
    - Detect environment (Docker or local).
    - Dispatch execution to the appropriate backend.
    - Handle notebooks, Excel files, and future formats uniformly.
    """

    def __init__(self, timeout: int = 60, debug: bool = False, logger=None):
        self.timeout = timeout
        self.debug = debug
        self.logger = logger or setup_logger(level="normal")

        # Decide environment automatically
        self.use_docker = self._detect_docker_env()
        backend = "Docker sandbox" if self.use_docker else "Local notebook"
        self.logger.info(f"[ExecutionService] Using backend: {backend}")

    # ------------------------------------------------------------------
    def _detect_docker_env(self) -> bool:
        """Detect if Docker can be used."""
        in_colab = "COLAB_GPU" in os.environ or "google.colab" in str(
            getattr(__import__("sys"), "modules", {})
        )
        docker_available = shutil.which("docker") is not None
        return docker_available and not in_colab

    # ------------------------------------------------------------------
    def execute(self, solution: dict, submission_path: Path):
        """
        Execute a student's submission based on file type and environment.
        """
        file_type = solution.get("type")
        if not file_type:
            raise ValueError("Solution dict missing 'type' key.")

        if file_type == "notebook":
            if self.use_docker:
                from instantgrade.evaluators.python.execution_service_docker import (
                    ExecutionServiceDocker,
                )

                executor = ExecutionServiceDocker(
                    timeout=self.timeout, debug=self.debug, logger=self.logger
                )
                return executor.execute_student(solution, submission_path)
            else:
                return self._execute_notebook_locally(solution, submission_path)

        elif file_type == "excel":
            pass

        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    # ------------------------------------------------------------------
    def _execute_notebook_locally(self, solution: dict, submission_path: Path) -> dict:
        """
        Run a Jupyter notebook directly (no Docker) and evaluate all assertions.
        """
        self.logger.info(f"[ExecutionService] Running locally: {submission_path.name}")
        notebook_exec = NotebookExecutor(timeout=self.timeout)
        student_exec = notebook_exec.run_notebook(submission_path)
        base_ns = student_exec.get("namespace", {})

        # --- Safety Check for Required Variables ---
        student_name = base_ns.get("name", None)
        roll_number = base_ns.get("roll_number", None)
        default_name = solution.get("default_name", None)
        default_roll = solution.get("default_roll_number", None)

        if (student_name in [None, "", default_name]) or (roll_number in [None, "", default_roll]):
            msg = (
                f"Skipping {submission_path.name}: missing or default name/roll_number "
                f"(name={student_name}, roll={roll_number})"
            )
            self.logger.warning(msg)
            return {
                "student_path": submission_path,
                "execution": student_exec,
                "results": [],
                "skipped": True,
                "error": msg,
            }

        comparator = ComparisonService()
        all_results = []

        for qname, qdata in solution.get("questions", {}).items():
            ctx_code = qdata.get("context_code", "")
            assertions = qdata.get("tests", [])
            description = qdata.get("description", "")

            if self.debug:
                print(f"[LocalExecution] Evaluating {qname} ({len(assertions)} assertions)")

            q_ns = copy.copy(base_ns)
            try:
                q_results = comparator.run_assertions(
                    student_namespace=q_ns,
                    assertions=assertions,
                    question_name=qname,
                    context_code=ctx_code,
                )
            except Exception:
                tb = traceback.format_exc()
                q_results = [
                    {
                        "question": qname,
                        "assertion": "[internal error]",
                        "status": "failed",
                        "error": tb,
                        "score": 0,
                    }
                ]

            for r in q_results:
                r["description"] = description
            all_results.extend(q_results)

        # Construct unified result dict (same as Docker output)
        return {
            "student_path": submission_path,
            "execution": {
                "namespace": base_ns,
                "errors": student_exec.get("errors", []),
                "success": student_exec.get("success", True),
                "traceback": student_exec.get("traceback"),
                "docker_stdout": "",
                "docker_stderr": "",
            },
            "results": all_results,
            "skipped": False,
            "error": None,
        }
