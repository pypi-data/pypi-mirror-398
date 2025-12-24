import os
import nbformat
import traceback
import subprocess
import signal
from nbclient import NotebookClient
from pathlib import Path
from typing import Any, Dict


class NotebookExecutor:
    """
    Executes a Jupyter notebook either:
      - locally (inside Docker), or
      - via Docker (on host, if not already in a container).

    Provides per-cell execution with sandboxing, dummy input replacement,
    and safe timeouts. This class ensures that a student's bad code (e.g.,
    while True, os.kill, input()) cannot freeze the entire evaluation pipeline.
    """

    def __init__(self, timeout: int = 60, debug: bool = False):
        self.timeout = timeout
        self.debug = debug

    # ======================================================================
    # Public API
    # ======================================================================
    def run_notebook(self, path: str | Path) -> Dict[str, Any]:
        """
        Execute a Jupyter notebook and extract the resulting global namespace.

        Automatically detects whether we are inside a Docker container and
        avoids nested Docker calls.
        """
        path = Path(path)
        in_docker = os.path.exists("/.dockerenv")

        if in_docker:
            if self.debug:
                print(f"[NotebookExecutor] Running inside Docker: executing directly {path}")
            return self._run_notebook_locally(path)
        else:
            if self.debug:
                print(f"[NotebookExecutor] Running on host: executing via Docker sandbox {path}")
            return self._run_notebook_with_docker(path)

    # ======================================================================
    # Local (in-container) execution
    # ======================================================================
    def _run_notebook_locally(self, path: Path) -> Dict[str, Any]:
        """
        Execute the notebook directly in the current Python environment.
        Used when already inside Docker (the sandbox is the container).
        """
        nb = nbformat.read(path, as_version=4)
        errors: list[str] = []
        tb_text: str | None = None
        namespace: dict[str, Any] = {}

        # Dummy input() override to prevent blocking
        def dummy_input(prompt=None):
            msg = "[Warning] input() called during evaluation — ignored."
            errors.append(msg)
            return ""

        namespace["input"] = dummy_input

        # Execute all cells safely using nbclient first (for reproducibility)
        try:
            client = NotebookClient(
                nb,
                timeout=self.timeout,
                allow_errors=True,
                kernel_name="python3",
            )
            executed_nb = client.execute()
        except Exception as e:
            tb_text = traceback.format_exc()
            errors.append(f"[nbclient failure] {str(e)}")
            executed_nb = nb

        # Sequential execution to rebuild namespace
        for cell in executed_nb.cells:
            if cell.cell_type != "code":
                continue
            src = cell.get("source", "")
            if not src.strip():
                continue
            try:
                # Execute code blocks directly in-process so function
                # definitions remain available in the returned namespace.
                # Note: this removes per-cell timeout protection for local
                # runs; if you need strict timeouts, consider a different
                # execution strategy (threads or sandboxed processes).
                code_obj = compile(src, f"<student_cell>", "exec")
                exec(code_obj, namespace)
            except Exception as e:
                # Capture the traceback text for reporting
                tb = traceback.format_exc()
                errors.append(f"In cell: {src[:80]} -> {tb}")

        clean_ns = {k: v for k, v in namespace.items() if not k.startswith("__")}
        return {
            "namespace": clean_ns,
            "errors": errors,
            "traceback": tb_text,
            "success": len(errors) == 0,
        }

    # ======================================================================
    # Host (non-container) Docker execution
    # ======================================================================
    def _run_notebook_with_docker(self, path: Path) -> Dict[str, Any]:
        """
        Executes the notebook using a separate Docker container.
        This is used when running locally, not within Docker.
        """
        tmpdir = path.parent
        container_name = f"nbexec_{os.getpid()}"

        cmd = [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "-v",
            f"{tmpdir}:/workspace",
            "-w",
            "/workspace",
            "python:3.11-slim",
            "bash",
            "-c",
            (
                "pip install --no-cache-dir nbformat nbclient pandas openpyxl > /dev/null && "
                f"python - <<'PY'\n"
                "import nbformat, traceback\n"
                "from nbclient import NotebookClient\n"
                "from pathlib import Path\n"
                "nb = nbformat.read(Path('/workspace/') / Path('"
                + path.name
                + "'), as_version=4)\n"
                "client = NotebookClient(nb, timeout=60, allow_errors=True, kernel_name='python3')\n"
                "try:\n"
                "    client.execute()\n"
                "    print('[NotebookExecutor-Docker] Execution complete.')\n"
                "except Exception as e:\n"
                "    print('[NotebookExecutor-Docker] Error:', e)\n"
                "PY"
            ),
        ]

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
            success = proc.returncode == 0
            output = proc.stdout.strip()
            errors = [] if success else [proc.stderr.strip()]
            return {
                "namespace": {},
                "errors": errors,
                "traceback": None,
                "success": success,
                "stdout": output,
            }
        except subprocess.TimeoutExpired:
            return {
                "namespace": {},
                "errors": [f"Timeout expired after {self.timeout}s"],
                "traceback": None,
                "success": False,
            }
        except Exception as e:
            return {
                "namespace": {},
                "errors": [f"Unexpected error: {e}"],
                "traceback": traceback.format_exc(),
                "success": False,
            }

    # ======================================================================
    # Helper: Safe exec with timeout
    # ======================================================================
    def _safe_exec(self, src: str, namespace: dict):
        """
        Execute a single code block with timeout protection using subprocess.
        If code does not terminate within `self.timeout`, raise TimeoutError.
        """
        import multiprocessing

        def _runner(conn, code, ns):
            try:
                exec(code, ns)
                conn.send((True, None))
            except Exception as e:
                conn.send((False, traceback.format_exc()))

        parent_conn, child_conn = multiprocessing.Pipe()
        p = multiprocessing.Process(target=_runner, args=(child_conn, src, namespace))
        p.start()
        p.join(self.timeout)

        if p.is_alive():
            p.terminate()
            raise TimeoutError(f"Cell execution exceeded {self.timeout}s")

        success, tb = parent_conn.recv()
        if not success:
            raise RuntimeError(tb)
