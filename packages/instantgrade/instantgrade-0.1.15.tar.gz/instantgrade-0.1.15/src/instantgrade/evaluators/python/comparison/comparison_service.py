"""
Comparison Service — Executes instructor-defined assertions
with detailed student-friendly diagnostics:
 - Expected vs Actual extraction
 - Side-by-side diff (lists, dicts, tuples, strings)
"""

import traceback
import ast
import difflib
from typing import List, Dict, Any


class ComparisonService:

    # --------------------------------------------------------------
    # AST helper: extract left-hand and right-hand expressions
    # --------------------------------------------------------------
    def _extract_expected_actual(self, code: str, namespace: dict):
        """
        Extracts:
            actual_value  ← left side of equality
            expected_value ← right side of equality
        Only works for: assert <expr> == <expr>
        """

        try:
            tree = ast.parse(code)
            node = tree.body[0]

            if not isinstance(node, ast.Assert):
                return None, None

            # Must be: assert <expr> == <expr>
            if not isinstance(node.test, ast.Compare):
                return None, None

            cmp = node.test
            if len(cmp.ops) != 1 or not isinstance(cmp.ops[0], ast.Eq):
                return None, None

            left_expr = cmp.left
            right_expr = cmp.comparators[0]

            # Convert AST → Python code string
            left_code = ast.unparse(left_expr)
            right_code = ast.unparse(right_expr)

            # Evaluate both sides safely
            actual = eval(left_code, namespace)
            expected = eval(right_code, namespace)

            return actual, expected

        except Exception:
            return None, None

    # --------------------------------------------------------------
    # Pretty diff generator
    # --------------------------------------------------------------
    def _make_diff(self, expected, actual):
        """
        Produces a colored diff for lists, dicts, tuples, strings.
        """

        try:
            exp = repr(expected).splitlines()
            act = repr(actual).splitlines()

            diff = difflib.unified_diff(exp, act, fromfile="Expected", tofile="Actual", lineterm="")

            return "\n".join(diff)

        except Exception:
            return None

    # --------------------------------------------------------------
    # Main method
    # --------------------------------------------------------------
    def run_assertions(
        self,
        assertions: List[Dict[str, Any]] = None,
        namespace: Dict[str, Any] = None,
        *,
        student_namespace: Dict[str, Any] = None,
        question_name: str | None = None,
        context_code: str = "",
        timeout: int = 20,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Run assertions.

        Compatibility: older callers (and the grader) call this with keywords like
        student_namespace and question_name. This method accepts either the
        positional style (assertions, namespace) or the keyword style and
        normalizes them for processing.
        """

        results = []

        # Normalize namespace: prefer explicit student_namespace when provided
        if student_namespace is not None:
            namespace = student_namespace

        # Ensure assertions is a list
        if assertions is None:
            assertions = kwargs.get("assertions") or []

        for a in assertions:
            # Support multiple assertion formats for backwards compatibility:
            # - a is a dict with keys: code, question, description
            # - a is a plain string containing the assertion code
            if isinstance(a, str):
                code = a
                question = question_name or "Unknown Question"
                description = ""
            elif isinstance(a, dict):
                # prefer 'code' key, but allow 'assertion' as an alias
                code = a.get("code") if a.get("code") is not None else a.get("assertion")
                question = a.get("question", question_name or "Unknown Question")
                description = a.get("description", "")
            else:
                # Fallback: coerce to string
                code = str(a)
                question = question_name or "Unknown Question"
                description = ""

            try:
                exec(compile(code, "<assertion>", "exec"), namespace)

                results.append(
                    {
                        "question": question,
                        "assertion": code,
                        "status": "passed",
                        "score": 1,
                        "error": None,
                        "description": description,
                    }
                )
                continue

            # ----------------------------------------------------------
            # ASSERTION ERROR ⇒ Extract Expected vs Actual + Diff
            # ----------------------------------------------------------
            except AssertionError:
                tb = traceback.format_exc()

                actual, expected = self._extract_expected_actual(code, namespace)

                if actual is not None:
                    diff = self._make_diff(expected, actual)

                    err_msg = (
                        "Assertion failed.\n\n"
                        f"Assertion: {code}\n\n"
                        "Expected:\n"
                        f"  {repr(expected)}\n\n"
                        "Actual:\n"
                        f"  {repr(actual)}\n\n"
                    )

                    if diff:
                        err_msg += f"Diff:\n{diff}\n\n"

                    # Add hint for None returns
                    if actual is None:
                        err_msg += "Hint: Your function returned None. Did you forget a return statement?\n"

                else:
                    # Fallback basic error message
                    err_msg = (
                        "Assertion failed.\n\n"
                        f"Assertion: {code}\n\n"
                        "Could not extract Expected/Actual automatically.\n"
                        "Traceback:\n"
                        f"{tb}"
                    )

                results.append(
                    {
                        "question": question,
                        "assertion": code,
                        "status": "failed",
                        "score": 0,
                        "error": err_msg,
                        "description": description,
                    }
                )
                continue

            # ----------------------------------------------------------
            # SYNTAX ERROR
            # ----------------------------------------------------------
            except SyntaxError as e:
                err_msg = (
                    "Syntax Error in student's code.\n"
                    f"Message: {e.msg}\n"
                    f"Line: {e.lineno}, Offset: {e.offset}\n"
                    f"Text: {e.text}\n"
                )

                results.append(
                    {
                        "question": question,
                        "assertion": code,
                        "status": "failed",
                        "score": 0,
                        "error": err_msg,
                        "description": description,
                    }
                )
                continue

            # ----------------------------------------------------------
            # FUNCTION NOT FOUND (NameError)
            # ----------------------------------------------------------
            except NameError as e:
                err_msg = (
                    f"NameError: {str(e)}\n"
                    "This means the required function was NOT defined,"
                    " or is spelled incorrectly.\n"
                )

                results.append(
                    {
                        "question": question,
                        "assertion": code,
                        "status": "failed",
                        "score": 0,
                        "error": err_msg,
                        "description": description,
                    }
                )
                continue

            # ----------------------------------------------------------
            # TYPE ERRORS
            # ----------------------------------------------------------
            except TypeError as e:
                tb = traceback.format_exc()
                err_msg = (
                    f"TypeError: {str(e)}\n"
                    "This often means the function returned the wrong data type.\n\n"
                    f"Traceback:\n{tb}"
                )

                results.append(
                    {
                        "question": question,
                        "assertion": code,
                        "status": "failed",
                        "score": 0,
                        "error": err_msg,
                        "description": description,
                    }
                )
                continue

            # ----------------------------------------------------------
            # OTHER RUNTIME ERRORS
            # ----------------------------------------------------------
            except Exception as e:
                tb = traceback.format_exc()
                err_msg = (
                    "Runtime error while evaluating this question.\n"
                    f"Error: {str(e)}\n\n"
                    f"Traceback:\n{tb}"
                )

                results.append(
                    {
                        "question": question,
                        "assertion": code,
                        "status": "failed",
                        "score": 0,
                        "error": err_msg,
                        "description": description,
                    }
                )
                continue

        return results
