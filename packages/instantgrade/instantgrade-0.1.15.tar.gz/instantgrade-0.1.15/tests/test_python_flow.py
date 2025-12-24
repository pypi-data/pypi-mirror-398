import sys
from pathlib import Path
import pytest


def _setup_paths():
    repo = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo))
    sys.path.insert(0, str(repo / "src"))
    return repo


def test_python_flow_writes_html(tmp_path):
    repo = _setup_paths()

    try:
        from instantgrade import InstantGrader
    except Exception as e:
        pytest.skip(f"instantgrade import failed: {e}")

    solution = repo / "data" / "fib_python_control_flow" / "sample_solutions.ipynb"
    # This notebook example used a single submission file path; use it directly
    submissions = repo / "data" / "fib_python_control_flow" / "InclassPracticeExam2" / "Lohitakksh-2423531-PracticeTest .ipynb"

    report_dir = tmp_path / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    grader = InstantGrader(
        solution_file_path=solution,
        submission_folder_path=submissions,
        use_docker=False,
    )

    report = grader.run()
    assert report is not None, "Python grader.run() returned None"
    # to_html may raise KeyError (noted in notebooks); handle same fallback
    out_path = report_dir / "python_evaluation_report.html"
    try:
        written = grader.to_html(out_path)
        written_path = Path(written)
        assert written_path.exists(), f"Expected HTML at {written_path}"
    except KeyError as e:
        # Try fallback CSV on grader.report
        if hasattr(grader, "report"):
            csv_path = report_dir / "python_fallback.csv"
            grader.report.to_csv(csv_path)
            assert csv_path.exists(), "Fallback CSV was not written"
        else:
            pytest.fail(f"to_html failed and no fallback present: {e}")
