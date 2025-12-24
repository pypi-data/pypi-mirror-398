import nbformat
import ast
from pathlib import Path
from collections import OrderedDict
from instantgrade.utils.io_utils import safe_load_notebook


class SolutionIngestion:
    """
    Reads instructor's solution notebook.
    Expected pattern:
      [markdown: question description]
      [code: function definition]
      [code: asserts + helper code]
    """

    def __init__(self, path: Path):
        self.path = Path(path)

    def understand_notebook_solution(self):
        if not self.path.exists():
            raise FileNotFoundError(f"Solution notebook not found: {self.path}")

        nb = safe_load_notebook(self.path)
        questions = OrderedDict()
        metadata = {}

        total_assertions = 0
        total_questions = 0

        i = 0
        while i < len(nb.cells):
            cell = nb.cells[i]

            # Step 1: Markdown → question description
            if cell.cell_type == "markdown" and cell.source.strip().startswith("##"):
                description = cell.source.strip().split("\n", 1)[-1].strip()

                func_name, func_src, context_code, assert_lines = None, None, "", []

                # Step 2: Next cell (function definition)
                if i + 1 < len(nb.cells):
                    code_cell = nb.cells[i + 1]
                    if code_cell.cell_type == "code":
                        func_src = code_cell.source.strip()
                        func_name = self._extract_function_name(func_src)

                # Step 3: Next cell (assertions and context)
                if func_name and i + 2 < len(nb.cells):
                    test_cell = nb.cells[i + 2]
                    if test_cell.cell_type == "code":
                        setup_lines = []
                        for line in test_cell.source.splitlines():
                            stripped = line.strip()
                            if stripped.startswith("assert "):
                                assert_lines.append(stripped)
                            else:
                                setup_lines.append(line)
                        context_code = "\n".join(setup_lines)

                if func_name:
                    questions[func_name] = {
                        "description": description,
                        "function": func_src,
                        "context_code": context_code,
                        "tests": assert_lines,
                        "assert_count": len(assert_lines),
                    }
                    total_questions += 1
                    total_assertions += len(assert_lines)

                i += 3
                continue

            # Extract metadata (instructor info)
            if cell.cell_type == "code" and "name" in cell.source and "roll_number" in cell.source:
                try:
                    tree = ast.parse(cell.source)
                    for node in tree.body:
                        if isinstance(node, ast.Assign):
                            for target in node.targets:
                                if isinstance(target, ast.Name) and target.id == "name":
                                    metadata["name"] = getattr(node.value, "s", "InstructorName")
                                elif isinstance(target, ast.Name) and target.id == "roll_number":
                                    metadata["roll_number"] = getattr(node.value, "s", "0000")
                except Exception:
                    pass

            i += 1

        # --- Summary of instructor notebook ---
        summary = {
            "total_questions": total_questions,
            "total_assertions": total_assertions,
        }

        return {
            "type": "notebook",
            "metadata": metadata,
            "questions": questions,
            "summary": summary,
        }

    # ----------------------------------------------------------------------
    def _extract_function_name(self, code: str) -> str | None:
        try:
            tree = ast.parse(code)
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    return node.name
        except Exception:
            pass
        return None
