"""IO utilities copied into the new instantgrade package.

Copied from src/instantgrade/utils/io_utils.py and kept unchanged.
"""

import json
from pathlib import Path
import pandas as pd
import nbformat
from openpyxl import load_workbook
import ast
from nbformat import validate, ValidationError
from uuid import uuid4


def safe_load_notebook(path: Path) -> nbformat.NotebookNode:
    try:
        nb = nbformat.read(path, as_version=4)

        modified = False
        for cell in nb.cells:
            if "id" not in cell:
                cell["id"] = str(uuid4())
                modified = True

        try:
            validate(nb)
        except ValidationError:
            nb = nbformat.v4.upgrade(nb)
            validate(nb)

        if modified:
            print(f"[safe_load_notebook] Added missing IDs in memory for {path.name}")

        return nb

    except Exception as e:
        raise RuntimeError(f"Unable to load notebook {path}: {e}")


def normalize_notebook(path=None, inplace: bool = True) -> nbformat.NotebookNode:
    path = Path(path)
    nb = nbformat.read(path, as_version=4)

    nbformat.validate(nb)
    normalized_nb = nbformat.v4.upgrade(nb)
    nbformat.v4.validate_cell_ids(normalized_nb)

    if inplace:
        nbformat.write(normalized_nb, path)
        return normalized_nb

    return normalized_nb


def load_notebook(path: Path) -> nbformat.NotebookNode:
    return nbformat.read(path, as_version=4)


def load_excel(path: Path):
    return load_workbook(path, data_only=False)


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf8") as f:
        return json.load(f)


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def load_raw_code(path: Path) -> str:
    return Path(path).read_text(encoding="utf8")


def generate_student_notebook(instructor_path: str | Path, output_path: str | Path):
    instructor_path = Path(instructor_path)
    output_path = Path(output_path)

    if not instructor_path.exists():
        raise FileNotFoundError(f"Notebook not found: {instructor_path}")

    nb = nbformat.read(instructor_path, as_version=4)
    new_cells = []

    for cell in nb.cells:
        if cell.cell_type == "markdown":
            new_cells.append(cell)
            continue

        if cell.cell_type != "code":
            new_cells.append(cell)
            continue

        src = cell.source or ""
        stripped_lines = [l.strip() for l in src.splitlines() if l.strip()]

        if any(line.startswith("assert ") for line in stripped_lines):
            continue

        try:
            tree = ast.parse(src)
            new_body: list[ast.stmt] = []

            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    node.body = [ast.Pass()]
                    new_body.append(node)
                elif isinstance(node, (ast.Import, ast.ImportFrom, ast.Assign, ast.Expr)):
                    new_body.append(node)

            new_module = ast.Module(body=new_body, type_ignores=[])
            new_source = ast.unparse(new_module).strip()

            if new_source:
                cell.source = new_source
                new_cells.append(cell)

        except Exception:
            cleaned_lines = []
            for line in src.splitlines():
                stripped = line.strip()
                if stripped.startswith("assert "):
                    continue
                cleaned_lines.append(line)

            new_src = "\n".join(cleaned_lines).strip()
            if new_src:
                cell.source = new_src
                new_cells.append(cell)

    new_nb = nbformat.v4.new_notebook()
    new_nb.cells = new_cells
    new_nb.metadata = nb.metadata

    output_path.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(new_nb, output_path)
    print(f"✅ Student notebook generated at: {output_path}")


def remove_notebook_with_line(directory: str | Path, line: str):
    directory = Path(directory)
    if not directory.is_dir():
        raise ValueError(f"The specified path is not a directory: {directory}")

    for notebook_path in directory.glob("*.ipynb"):
        try:
            nb = nbformat.read(notebook_path, as_version=4)
            for cell in nb.cells:
                if cell.cell_type == "code" and line in cell.source:
                    notebook_path.unlink()
                    print(f"Deleted notebook: {notebook_path}")
                    break
        except Exception as e:
            print(f"Error processing {notebook_path}: {e}")
