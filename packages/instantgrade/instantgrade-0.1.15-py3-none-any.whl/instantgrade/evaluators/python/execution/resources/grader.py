#!/usr/bin/env python
"""
Grader entrypoint that runs entirely inside the Docker container.

Responsibilities:
- Load instructor solution notebook: /workspace/solution.ipynb
- Load student notebook:          /workspace/student.ipynb
- Execute all student cells into a single namespace (with input/os.kill patched)
- Extract student `name` and `roll_number`:
    * First from the executed namespace
    * If missing, scan code cells with AST
    * If still missing, fall back to instructor defaults
    * If still equal to instructor defaults, treat as “not filled” and emit a fatal result
- For each question in the solution:
    * Run `ComparisonService.run_assertions(...)` in that namespace
- Write /workspace/results.json with:
    {
      "student": {"name": ..., "roll_number": ...},
      "results": [ {question, assertion, status, error, score, description}, ... ]
    }
"""

from __future__ import annotations

import ast
import builtins
import json
import os
import sys
import traceback
from pathlib import Path as _Path

# Ensure the project source is importable inside the Docker container regardless
# of whether the package was installed via pip. This helps cases where the
# build context or install step didn't populate site-packages as expected.
# We prefer /app/src (the mounted/copy location used by the Dockerfile) and
# fallback to /app. These are no-ops when imports already resolve.
for _p in ("/app/src", "/app"):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from pathlib import Path
from typing import Any, Dict, List, Tuple

import nbformat

from instantgrade.evaluators.python.ingestion.solution_ingestion import SolutionIngestion
from instantgrade.evaluators.python.comparison.comparison_service import ComparisonService


def log(msg: str) -> None:
    """Minimal stdout logging for the container."""
    print(f"[grader] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Helpers for executing the student notebook
# ---------------------------------------------------------------------------


def execute_student_notebook(nb_path: Path) -> Tuple[Dict[str, Any], List[str]]:
    """
    Execute all code cells in the student's notebook into a single namespace.

    - Patches input() so it never blocks.
    - Patches os.kill to avoid killing the container.
    - Collects cell-level errors but continues executing other cells.

    Returns
    -------
    namespace : dict
        The globals dictionary after executing all cells.
    errors : list[str]
        Any execution error messages for debugging.
    """
    errors: List[str] = []
    ns: Dict[str, Any] = {}

    # Patch input() and os.kill
    def dummy_input(prompt=None):
        msg = "[Warning] input() called during evaluation — ignored."
        errors.append(msg)
        return ""

    def safe_kill(*_args, **_kwargs):
        raise RuntimeError("os.kill is disabled in InstantGrade sandbox")

    builtins.input = dummy_input
    os.kill = safe_kill  # type: ignore[assignment]

    try:
        nb = nbformat.read(nb_path, as_version=4)
    except Exception:
        tb = traceback.format_exc()
        errors.append("Failed to read notebook:\n" + tb)
        return ns, errors

    for idx, cell in enumerate(nb.cells):
        if cell.cell_type != "code":
            continue
        src = cell.get("source", "")
        if not src.strip():
            continue

        try:
            code_obj = compile(src, f"<student_cell_{idx}>", "exec")
            exec(code_obj, ns)
        except Exception:
            tb = traceback.format_exc()
            errors.append(f"Error in student cell #{idx}:\n{tb}")
            # Continue executing remaining cells

    # Remove dunder keys
    ns_clean = {k: v for k, v in ns.items() if not k.startswith("__")}
    return ns_clean, errors


# ---------------------------------------------------------------------------
# Helpers for extracting name / roll_number
# ---------------------------------------------------------------------------


def extract_name_roll_from_ns(ns: Dict[str, Any]) -> Tuple[str | None, str | None]:
    name = ns.get("name")
    roll = ns.get("roll_number")
    if isinstance(name, str) and isinstance(roll, str):
        return name, roll
    return None, None


def extract_name_roll_from_cells(nb_path: Path) -> Tuple[str | None, str | None]:
    """
    Fallback: scan code cells with AST for assignments like:

        name = "Alice"
        roll_number = "23BDS001"

    Returns (name, roll_number) or (None, None).
    """
    try:
        nb = nbformat.read(nb_path, as_version=4)
    except Exception:
        return None, None

    found_name = None
    found_roll = None

    for idx, cell in enumerate(nb.cells):
        if cell.cell_type != "code":
            continue
        src = cell.get("source", "")
        if not src.strip():
            continue

        try:
            tree = ast.parse(src)
        except Exception:
            continue

        for node in tree.body:
            if isinstance(node, ast.Assign):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name):
                        if tgt.id == "name" and isinstance(node.value, (ast.Constant, ast.Str)):
                            # ast.Str for <3.8 compatibility, ast.Constant for newer
                            val = getattr(node.value, "s", None) or getattr(
                                node.value, "value", None
                            )
                            if isinstance(val, str):
                                found_name = val
                                log(f"Found name='{val}' in cell {idx}")
                        if tgt.id == "roll_number" and isinstance(
                            node.value, (ast.Constant, ast.Str)
                        ):
                            val = getattr(node.value, "s", None) or getattr(
                                node.value, "value", None
                            )
                            if isinstance(val, str):
                                found_roll = val
                                log(f"Found roll_number='{val}' in cell {idx}")

    return found_name, found_roll


# ---------------------------------------------------------------------------
# Main grading logic
# ---------------------------------------------------------------------------


def main() -> None:
    log("Starting grading...")

    solution_path = Path("/workspace/solution.ipynb")
    student_path = Path("/workspace/student.ipynb")
    results_path = Path("/workspace/results.json")

    # -----------------------------------------------------------------------
    # 1. Load instructor solution spec
    # -----------------------------------------------------------------------
    if not solution_path.exists():
        log(f"Fatal error: solution notebook missing at {solution_path}")
        return

    if not student_path.exists():
        log(f"Fatal error: student notebook missing at {student_path}")
        return

    try:
        sol = SolutionIngestion(solution_path).understand_notebook_solution()
    except Exception:
        tb = traceback.format_exc()
        log("Fatal error while loading instructor solution:")
        log(tb)
        return

    questions = sol.get("questions", {}) or {}
    sol_meta = sol.get("metadata", {}) or {}

    default_name = sol_meta.get("name", "student name")
    default_roll = sol_meta.get("roll_number", "student roll number")
    log(f"Instructor defaults -> name='{default_name}', roll='{default_roll}'")

    # -----------------------------------------------------------------------
    # 2. Execute student notebook into a namespace
    # -----------------------------------------------------------------------
    ns, exec_errors = execute_student_notebook(student_path)
    log(f"Namespace after execution: {sorted(ns.keys())}")

    # -----------------------------------------------------------------------
    # 3. Extract name / roll_number
    # -----------------------------------------------------------------------
    name, roll = extract_name_roll_from_ns(ns)
    if not name or not roll:
        log("Missing name/roll in namespace, scanning code cells...")
        cell_name, cell_roll = extract_name_roll_from_cells(student_path)
        if cell_name and not name:
            name = cell_name
        if cell_roll and not roll:
            roll = cell_roll

    # Fallback to instructor defaults if still missing
    if not name:
        name = default_name
    if not roll:
        roll = default_roll

    log(f"Final resolved student identity -> name='{name}', roll='{roll}'")

    # If they still match defaults, treat as not filled and return a single fatal result
    if name == default_name or roll == default_roll:
        msg = (
            "Student notebook missing personalized name/roll_number. "
            "Please define:\n\n"
            "name = 'Your Name'\n"
            "roll_number = 'Your Roll Number'\n"
        )
        log("❌ Fatal: student identity still matches instructor defaults. Skipping assertions.")
        # Write a minimal results.json so host sees a structured error
        output = {
            "student": {"name": name, "roll_number": roll},
            "results": [
                {
                    "question": "_identity_check_",
                    "assertion": "[missing student identity]",
                    "status": "failed",
                    "error": msg,
                    "score": 0,
                    "description": "Student did not customize name/roll_number.",
                }
            ],
            "execution_errors": exec_errors,
        }
        results_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
        return

    # -----------------------------------------------------------------------
    # 4. Run comparisons for each question
    # -----------------------------------------------------------------------
    comp = ComparisonService()
    all_results: List[Dict[str, Any]] = []

    # QUESTION_TIMEOUT from env (in seconds); default 20
    try:
        question_timeout = int(os.environ.get("QUESTION_TIMEOUT", "20"))
    except ValueError:
        question_timeout = 20

    for qname, qdata in questions.items():
        log(f"Evaluating question: {qname}")
        context_code = qdata.get("context_code", "") or ""
        assertions = qdata.get("tests", []) or []
        description = qdata.get("description", "") or ""

        try:
            res = comp.run_assertions(
                student_namespace=ns,
                assertions=assertions,
                question_name=qname,
                context_code=context_code,
                timeout=question_timeout,  # accepted (ignored or used) by ComparisonService
            )
        except Exception:
            tb = traceback.format_exc()
            log(f"❌ Error in ComparisonService for question {qname}:")
            log(tb)
            res = [
                {
                    "question": qname,
                    "assertion": "[comparison error]",
                    "status": "failed",
                    "error": tb,
                    "score": 0,
                }
            ]

        # Attach description to every row
        for r in res:
            r["description"] = description

        # Log a short summary of results for this question to aid debugging
        try:
            passed = sum(1 for r in res if r.get("score", 0) and float(r.get("score", 0)) > 0)
            failed = sum(1 for r in res if not (r.get("score", 0) and float(r.get("score", 0)) > 0))
            log(f"Question {qname}: {len(res)} assertions — passed={passed}, failed={failed}")
            # Also show a sample of first few scores for visibility
            sample_scores = [r.get("score", 0) for r in res[:5]]
            log(f"Question {qname}: sample scores: {sample_scores}")
        except Exception:
            # Don't let logging interfere with grading
            pass

        all_results.extend(res)

    # -----------------------------------------------------------------------
    # 5. Write results.json
    # -----------------------------------------------------------------------
    output = {
        "student": {"name": name, "roll_number": roll},
        "results": all_results,
        "execution_errors": exec_errors,
    }

    try:
        results_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
        log(f"results.json written with {len(all_results)} rows.")
    except Exception:
        tb = traceback.format_exc()
        log("❌ Fatal error while writing results.json:")
        log(tb)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Last resort crash log
        tb = traceback.format_exc()
        log("❌ Unhandled exception in grader:")
        log(tb)
