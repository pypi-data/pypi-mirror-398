import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional
import importlib.util

from instantgrade.utils.logger import setup_logger


class ExecutionServiceDocker:
    """
    Executes each student's notebook inside Docker.

    Host only mounts:
      - instructor's .ipynb
      - student's .ipynb
      - grader.py
    Docker performs ingestion, execution, and writes results.json.
    """

    def __init__(
        self,
        docker_image: str = "instantgrade:latest",
        base_image: str = "python:3.11-slim",
        per_question_timeout: int = 20,
        per_student_timeout: int = 1800,
        memory_limit: str = "1g",
        cpu_limit: str = "1.0",
        pids_limit: int = 256,
        network_mode: str = "none",
        debug: bool = False,
        logger=None,
    ):
        self.docker_image = docker_image
        self.base_image = base_image
        self.per_question_timeout = per_question_timeout
        self.per_student_timeout = per_student_timeout
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        self.pids_limit = pids_limit
        self.network_mode = network_mode
        self.debug = debug
        self.logger = logger or setup_logger(level="normal")

    # ------------------------------------------------------------------
    def execute_student(self, solution_path: Path, submission_path: Path) -> Dict[str, Any]:
        """Run a student's notebook inside Docker."""
        submission_path = Path(submission_path)
        solution_path = Path(solution_path)
        start_time = time.time()
        self.logger.info(f"[Docker] Starting grading for {submission_path.name}")

        self.ensure_docker_image_exists()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Copy required files into workspace
            shutil.copy(submission_path, tmpdir_path / "student.ipynb")
            shutil.copy(solution_path, tmpdir_path / "solution.ipynb")

            grader_path = self._get_grader_source()
            shutil.copy(grader_path, tmpdir_path / "grader.py")

            # Build docker command
            cmd = [
                "docker",
                "run",
                "--rm",
                "--memory",
                self.memory_limit,
                "--cpus",
                self.cpu_limit,
                "--pids-limit",
                str(self.pids_limit),
                "--network",
                self.network_mode,
                "-e",
                f"QUESTION_TIMEOUT={self.per_question_timeout}",
                "-v",
                f"{tmpdir_path}:/workspace",
                "-w",
                "/workspace",
                self.docker_image,
                "bash",
                "-c",
                "python grader.py",
            ]

            if self.debug:
                self.logger.debug("Docker command: " + " ".join(cmd))

            # Launch Docker
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            stdout_lines = []
            hard_timeout_hit = False

            try:
                while True:
                    elapsed = time.time() - start_time
                    if elapsed > self.per_student_timeout:
                        hard_timeout_hit = True
                        self.logger.warning(f"[Docker] Timeout for {submission_path.name}")
                        proc.kill()
                        break

                    line = proc.stdout.readline()
                    if not line:
                        if proc.poll() is not None:
                            break
                        time.sleep(0.05)
                        continue

                    line = line.rstrip("\n")
                    stdout_lines.append(line)
                    self.logger.info(f"[{submission_path.name}][docker] {line}")

                proc.wait(timeout=5)
            except Exception as e:
                self.logger.exception(f"Error streaming logs for {submission_path.name}: {e}")
                try:
                    proc.kill()
                except Exception:
                    pass
                hard_timeout_hit = True

            total_elapsed = round(time.time() - start_time, 2)
            full_stdout = "\n".join(stdout_lines)

            results_file = tmpdir_path / "results.json"
            if hard_timeout_hit or not results_file.exists():
                msg = f"[grader] results.json not found in /workspace for {submission_path.name}."
                self.logger.warning(msg)
                return self._make_error_result(submission_path, msg, total_elapsed, full_stdout)

            # Parse results.json
            try:
                graded = json.loads(results_file.read_text(encoding="utf-8"))
            except Exception as e:
                self.logger.exception(
                    f"Failed to parse results.json for {submission_path.name}: {e}"
                )
                return self._make_error_result(
                    submission_path, f"Invalid results.json: {e}", total_elapsed, full_stdout
                )

            # Emit host-side log summary of graded results for debugging
            try:
                results_list = graded.get("results", []) or []
                cnt = len(results_list)
                scores = [r.get("score", 0) for r in results_list]
                passed = sum(1 for s in scores if s and float(s) > 0)
                self.logger.info(
                    f"[Docker] Parsed results.json for {submission_path.name}: {cnt} rows — passed={passed}"
                )
                if self.debug:
                    self.logger.debug(f"[Docker] Sample results (first 5): {results_list[:5]}")
            except Exception:
                pass

            return {
                "student_path": submission_path,
                "execution": {
                    "success": True,
                    "errors": [],
                    "docker_stdout": full_stdout,
                    "docker_stderr": "",
                    "elapsed": total_elapsed,
                    "student_meta": graded.get("student", {}),
                },
                "results": graded.get("results", []),
            }

    # ------------------------------------------------------------------
    def ensure_docker_image_exists(self, force_rebuild: bool = False):
        """
        Ensure the Docker image exists and includes the instantgrade package.
        Automatically rebuilds if missing or explicitly forced.
        """
        import importlib.util

        # If possible, compute a git-based tag so images are tied to source.
        try:
            package_root = Path(__file__).parent.parent.parent.parent
            git_sha = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=package_root, text=True).strip()
            image_tag = f"instantgrade:{git_sha}"
        except Exception:
            # Fallback to the configured docker_image tag
            image_tag = self.docker_image

        # Check if an image with this tag already exists
        result = subprocess.run(["docker", "images", "-q", image_tag], capture_output=True, text=True)

        # Allow forcing a rebuild via environment variable or debug flag
        env_force = False
        try:
            import os as _os

            env_force = _os.environ.get("instantgrade_FORCE_REBUILD", "0") == "1"
        except Exception:
            env_force = False

        effective_force_rebuild = force_rebuild or env_force or bool(self.debug)

        if result.stdout.strip() and not effective_force_rebuild:
            # Image already exists and rebuild not requested — reuse it.
            # Ensure we use the git-tagged image name for subsequent runs.
            self.docker_image = image_tag
            return
        self.logger.info(f"[Docker] Building image {image_tag} from {self.base_image}...")

        # ----------------------------------------------------------------------
        # 1. Locate instantgrade package source
        # ----------------------------------------------------------------------
        spec = importlib.util.find_spec("instantgrade")
        if not spec or not spec.origin:
            raise RuntimeError("Could not locate 'instantgrade' package on host.")

        package_root = Path(spec.origin).parent.parent  # /src/instantgrade/ → /src
        project_root = package_root.parent  # /evaluator (repo root)

        # Determine installation method
        use_pyproject = (project_root / "pyproject.toml").exists() or (
            project_root / "setup.py"
        ).exists()
        install_cmd = "pip install ." if use_pyproject else "pip install /app/src"

        self.logger.info(
            f"[Docker] Using {'pyproject.toml' if use_pyproject else 'direct /src'} install mode"
        )

        # ----------------------------------------------------------------------
        # 2. Generate Dockerfile dynamically
        # ----------------------------------------------------------------------
        dockerfile = f"""
FROM {self.base_image}

# Install required packages once
RUN pip install --no-cache-dir nbformat nbclient pandas openpyxl

# Copy the evaluator project into container
COPY . /app
# Also ensure the source tree is available at /app/src so grader.py and
# runtime imports can resolve local package modules even if pip install
# behaves differently across environments.
COPY src /app/src
WORKDIR /app

# Install instantgrade either from pyproject or /src
RUN {install_cmd}

# Ensure PYTHONPATH includes /app/src (escape $ for BuildKit variable parsing)
ENV PYTHONPATH=/app/src:\$PYTHONPATH
WORKDIR /workspace
"""

        # ----------------------------------------------------------------------
        # 3. Write and build Dockerfile
        # ----------------------------------------------------------------------
        with tempfile.TemporaryDirectory() as tmpdir:
            dockerfile_path = Path(tmpdir) / "Dockerfile"
            dockerfile_path.write_text(dockerfile)

            # Choose correct build context (root if pyproject exists, else src)
            build_context = project_root if use_pyproject else package_root

            self.logger.info(f"[Docker] Build context: {build_context}")
            try:
                # Build the image tagged with the git SHA tag
                subprocess.run(
                    [
                        "docker",
                        "build",
                        "-t",
                        image_tag,
                        "-f",
                        str(dockerfile_path),
                        str(build_context),
                    ],
                    check=True,
                )
                # Also tag as latest for convenience
                try:
                    subprocess.run(["docker", "tag", image_tag, "instantgrade:latest"], check=True)
                except Exception:
                    pass
                # Update the instance docker_image to the built tag
                self.docker_image = image_tag
            except subprocess.CalledProcessError as e:
                self.logger.error(f"[Docker] Build failed: {e}")
                raise

        self.logger.info(f"[Docker] Built image {self.docker_image} successfully.")

    # ------------------------------------------------------------------
    def _get_grader_source(self) -> Path:
        """Return path to grader.py, with fallback for local dev."""
        import importlib.util

        # Prefer the local development grader.py in the source tree. When running
        # Docker builds from the repo, we want to copy the source grader so that
        # any local fixes (like adding /app/src to sys.path) are used inside the
        # container even if the installed package on the host differs.
        local_path = Path(__file__).parent / "resources" / "grader.py"
        if local_path.exists():
            return local_path

        # Fallback to the grader shipped in the installed package (if present).
        spec = importlib.util.find_spec("instantgrade.evaluators.python.execution.resources")
        if spec and spec.origin:
            path = Path(spec.origin).parent / "grader.py"
            if path.exists():
                return path

        raise RuntimeError(
            "grader.py not found in instantgrade/execution/resources. "
            "Ensure it exists in source or package_data includes it."
        )

    # ------------------------------------------------------------------
    def _make_error_result(
        self,
        submission_path: Path,
        message: str,
        elapsed: float,
        stdout: str = "",
    ) -> dict:
        return {
            "student_path": submission_path,
            "execution": {
                "success": False,
                "errors": [message],
                "docker_stdout": stdout,
                "docker_stderr": "",
                "elapsed": elapsed,
                "student_meta": {"name": "Unknown", "roll_number": "N/A"},
            },
            "results": [],
        }
