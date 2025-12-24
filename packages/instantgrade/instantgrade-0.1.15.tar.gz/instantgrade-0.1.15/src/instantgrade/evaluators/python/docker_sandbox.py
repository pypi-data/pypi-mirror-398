import docker
import tempfile
import shutil
from pathlib import Path
import os
import uuid
import json
import traceback
import subprocess


class DockerSandbox:
    """
    Run student notebooks inside a Docker sandbox for isolation and timeout control.
    """

    def __init__(self, image: str = "python:3.11-slim", timeout: int = 60):
        self.image = image
        self.timeout = timeout
        self.client = docker.from_env()

    def run_notebook(self, notebook_path: Path) -> dict:
        """
        Execute a Jupyter notebook in a Docker container and return its results.
        """
        notebook_path = Path(notebook_path)
        if not notebook_path.exists():
            raise FileNotFoundError(f"Notebook not found: {notebook_path}")

        # Create temporary directory to mount
        temp_dir = Path(tempfile.mkdtemp())
        nb_copy = temp_dir / notebook_path.name
        shutil.copy(notebook_path, nb_copy)

        container_name = f"instantgrade_{uuid.uuid4().hex[:8]}"

        try:
            # Ensure image is available
            self.client.images.pull(self.image)

            # Command: execute notebook safely
            command = [
                "bash",
                "-c",
                f"pip install jupyter nbconvert pandas numpy matplotlib seaborn >/dev/null 2>&1 && "
                f"jupyter nbconvert --to notebook --execute {notebook_path.name} "
                f"--output output.ipynb --ExecutePreprocessor.timeout={self.timeout}",
            ]

            container = self.client.containers.run(
                image=self.image,
                name=container_name,
                command=command,
                working_dir="/workspace",
                volumes={str(temp_dir): {"bind": "/workspace", "mode": "rw"}},
                detach=True,
                mem_limit="1g",
                network_disabled=True,
                stderr=True,
                stdout=True,
            )

            result = container.wait(timeout=self.timeout + 10)
            logs = container.logs().decode("utf-8")

            # Parse result
            output_path = temp_dir / "output.ipynb"
            if output_path.exists():
                with open(output_path, "r", encoding="utf-8") as f:
                    executed_notebook = f.read()
            else:
                executed_notebook = None

            return {
                "container_name": container_name,
                "status": result.get("StatusCode", 1),
                "logs": logs,
                "executed_notebook": executed_notebook,
                "namespace": {},  # optional for now; could later extract variables
            }

        except subprocess.TimeoutExpired:
            self.client.containers.get(container_name).kill()
            return {"error": "Execution timed out"}
        except Exception as e:
            return {"error": str(e), "traceback": traceback.format_exc()}
        finally:
            # Cleanup
            try:
                self.client.containers.get(container_name).remove(force=True)
            except Exception:
                pass
            shutil.rmtree(temp_dir, ignore_errors=True)
