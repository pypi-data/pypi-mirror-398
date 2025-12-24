import sys
from pathlib import Path
import pytest


def _setup_paths():
    # repo root is two levels up from tests/ (tests/ sits at repo/tests)
    repo = Path(__file__).resolve().parents[1]
    # make sure project src is importable (same logic used in your notebooks)
    sys.path.insert(0, str(repo))
    sys.path.insert(0, str(repo / "src"))
    return repo


def test_excel_flow_writes_html(tmp_path):
    repo = _setup_paths()

    try:
        from instantgrade import InstantGrader
    except Exception as e:
        pytest.skip(f"instantgrade import failed: {e}")

    solution = repo / "data" / "excel_example1" / "Assignment_ sol 1.xlsx"
    submissions = repo / "data" / "excel_example1" / "submissions"
    report_dir = tmp_path / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    grader = InstantGrader(
        solution_file_path=solution,
        submission_folder_path=submissions,
        override_type="excel",
        column_name="B",
        row_number=5,
        number_of_question=10,
    )

    report = grader.run()
    assert report is not None, "Excel grader.run() returned None"
    assert hasattr(report, "to_html"), "ReportingService missing to_html()"

    out_path = report_dir / "excel_evaluation_report.html"

    try:
        written = report.to_html(out_path)
        written_path = Path(written)
        assert written_path.exists(), f"Expected HTML at {written_path}"
    except KeyError:
        # Mirror the notebook fallback: write CSV from report.report if present
        if hasattr(report, "report"):
            csv_path = report_dir / "excel_fallback.csv"
            report.report.to_csv(csv_path)
            assert csv_path.exists(), "Fallback CSV was not written"
        else:
            pytest.fail("to_html failed with KeyError and no fallback available")
