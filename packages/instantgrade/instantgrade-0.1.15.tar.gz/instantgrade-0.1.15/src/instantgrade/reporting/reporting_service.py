"""
ReportingService (Full updated version)

Features:
 - Best-N and scaling are optional:
     * If best_n is None or 0, Best-N logic is disabled.
     * If scaled_range is None, scaling is disabled.
 - Summary modal sorts students in ascending order by the displayed metric:
     * If Best-N enabled -> sort ascending by Highest Best-N
     * Otherwise -> sort ascending by raw total marks
 - HTML hides Best-N / Scaled columns & pills automatically when those features are disabled
 - Backwards-compatible with previous 'executed_results' structure
 - Preserves error escaping and preformatted error display
"""

import html as html_lib
from io import StringIO
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import pandas as pd


class ReportingService:
    def __init__(
        self,
        executed_results: Optional[List[Dict]] = None,
        solution: Optional[Dict] = None,
        debug: bool = False,
        logger=None,
        total_assertions: int = 0,
        best_n: Optional[int] = None,
        scaled_range: Optional[Tuple[float, float]] = None,
    ):
        self.debug = debug
        self.solution = solution or {}
        self.executed_results = executed_results or []
        self.logger = logger
        self.total_assertions = total_assertions or 1

        # Optional Best-N & scaling
        # If best_n is None or <= 0 -> disable Best-N logic
        self.best_n = int(best_n) if best_n and int(best_n) > 0 else None

        # scaling is enabled only when scaled_range is provided as a tuple (min, max)
        if scaled_range and isinstance(scaled_range, (list, tuple)) and len(scaled_range) == 2:
            self.scaled_range = (float(scaled_range[0]), float(scaled_range[1]))
            self.scaled_min, self.scaled_max = float(scaled_range[0]), float(scaled_range[1])
        else:
            self.scaled_range = None
            self.scaled_min = None
            self.scaled_max = None

        # DataFrames
        self.df: pd.DataFrame = pd.DataFrame()
        self.attempt_scores_df: pd.DataFrame = pd.DataFrame()
        self.student_best_df: pd.DataFrame = pd.DataFrame()

        # Build DF immediately
        self.df = self.dataframe(self.executed_results)

        if self.logger:
            try:
                self.logger.info(f"[Reporting] Processed {len(self.df)} result rows.")
            except Exception:
                pass

    # -------------------------------------------------------------------------
    def dataframe(self, executed_results: Optional[List[Dict]] = None) -> pd.DataFrame:
        executed_results = (
            executed_results if executed_results is not None else self.executed_results
        )
        all_rows = []

        for item in executed_results or []:
            student_path = Path(item.get("student_path", ""))
            results = item.get("results", [])
            ns = item.get("execution", {}).get("namespace", {})
            meta = item.get("execution", {}).get("student_meta", {})

            student = meta.get("name") or ns.get("name") or student_path.stem or "unknown"
            roll = meta.get("roll_number") or ns.get("roll_number") or "N/A"

            for r in results:
                all_rows.append(
                    {
                        "file": str(student_path),
                        "student": student,
                        "roll_number": roll,
                        "question": r.get("question"),
                        "assertion": r.get("assertion"),
                        "status": r.get("status"),
                        "score": r.get("score", 0),
                        "error": r.get("error"),
                        "description": r.get("description", ""),
                    }
                )

        df = pd.DataFrame(all_rows)

        if df.empty:
            # Ensure structures are defined but empty
            self.df = df
            self.attempt_scores_df = pd.DataFrame()
            self.student_best_df = pd.DataFrame()
            if self.debug:
                print("[ReportingService] dataframe: produced empty DataFrame.")
            return df

        # Normalize columns and compute percents
        df["max_score"] = 1
        df["total_possible"] = self.total_assertions
        df["score"] = df["score"].fillna(0).astype(float)
        df["percentage"] = (df["score"] / df["max_score"]) * 100

        # Per-question totals per attempt (attempt identified by file + student + roll)
        q_totals = (
            df.groupby(["file", "student", "roll_number", "question"], dropna=False)
            .agg(q_score=("score", "sum"))
            .reset_index()
        )

        # If Best-N is enabled, compute best-N totals per attempt and scaling (if enabled)
        if self.best_n:
            q_totals_sorted = q_totals.sort_values(
                ["file", "student", "roll_number", "q_score"], ascending=[True, True, True, False]
            )

            best_n_attempt = (
                q_totals_sorted.groupby(["file", "student", "roll_number"], sort=False)
                .head(self.best_n)
                .groupby(["file", "student", "roll_number"], sort=False)
                .agg(best_n_total=("q_score", "sum"))
                .reset_index()
            )

            best_n_attempt["best_n_total"] = best_n_attempt["best_n_total"].fillna(0).astype(float)

            # Scale mapping (only if scaled_range provided)
            if self.scaled_range and not best_n_attempt.empty:
                min_raw = float(best_n_attempt["best_n_total"].min())
                max_raw = float(best_n_attempt["best_n_total"].max())
                if min_raw == max_raw:
                    best_n_attempt["scaled"] = float(self.scaled_min)
                else:
                    span = self.scaled_max - self.scaled_min
                    best_n_attempt["scaled"] = self.scaled_min + (
                        best_n_attempt["best_n_total"] - min_raw
                    ) * span / (max_raw - min_raw)
            else:
                # scaling disabled -> set scaled to NaN (or 0 for merges)
                best_n_attempt["scaled"] = float(0.0)

        else:
            # Best-N disabled -> empty DataFrame but with expected columns for merging
            best_n_attempt = pd.DataFrame(
                columns=["file", "student", "roll_number", "best_n_total", "scaled"]
            )

        # Save attempt-level scores (used in summary)
        self.attempt_scores_df = best_n_attempt.copy()

        # Merge attempt-level data back into rows for rendering per-attempt
        # Always perform merge but fill missing values sensibly
        df = df.merge(
            best_n_attempt[["file", "student", "roll_number", "best_n_total", "scaled"]],
            on=["file", "student", "roll_number"],
            how="left",
        )

        # If best_n disabled, set best_n_total to 0 (or keep NaN -> we later check)
        # Ensure numeric types without triggering future pandas downcasting warnings.
        # Use to_numeric(..., errors='coerce') to convert object columns to numeric,
        # then fillna and cast to float.
        df["best_n_total"] = pd.to_numeric(df["best_n_total"], errors="coerce").fillna(0.0).astype(float)
        # Scaled may be disabled; fill with 0 to avoid rendering 'nan' when not used
        df["scaled"] = pd.to_numeric(df["scaled"], errors="coerce").fillna(0.0).astype(float)

        # Student-level best across attempts (only meaningful when best_n is enabled)
        if not self.attempt_scores_df.empty and self.best_n:
            try:
                idx = self.attempt_scores_df.groupby(["student", "roll_number"])[
                    "best_n_total"
                ].idxmax()
                student_best = self.attempt_scores_df.loc[idx].reset_index(drop=True)
                student_best = student_best.rename(
                    columns={"best_n_total": "best_n_best", "scaled": "best_scaled"}
                )
            except Exception:
                student_best = pd.DataFrame(
                    columns=["student", "roll_number", "best_n_best", "best_scaled"]
                )
        else:
            student_best = pd.DataFrame(
                columns=["student", "roll_number", "best_n_best", "best_scaled"]
            )

        self.student_best_df = student_best
        self.df = df
        return df

    # -------------------------------------------------------------------------
    def to_csv(self, path: str) -> Path:
        if self.df is None or self.df.empty:
            raise RuntimeError("Report not built yet or empty.")
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.df.to_csv(path, index=False)
        return path

    # -------------------------------------------------------------------------
    def _escape_error_html(self, err) -> str:
        """
        Safely escape and convert newlines to <br> for HTML display.
        """
        if err is None:
            return ""
        return html_lib.escape(str(err)).replace("\n", "<br>")

    # -------------------------------------------------------------------------
    def to_html(self, path: str) -> Path:
        if self.df is None:
            raise RuntimeError("Report not built yet.")
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        df = self.df.copy()
        # If no rows were produced (e.g., Docker grading failed) or required
        # grouping columns are missing, emit a minimal HTML report instead of
        # raising KeyError. This keeps calling code (notebooks) robust when
        # execution produced no results.
        required = {"file", "student", "roll_number"}
        if df.empty or not required.issubset(set(df.columns)):
            # write a tiny HTML page explaining there are no results
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(
                    """<!doctype html><html><head><meta charset='utf-8'><title>No Results</title></head><body>"
                    "<h1>No grading results</h1><p>No result rows were produced by the grader."
                    " Check the execution logs for errors (Docker build/run or grader output).</p>"
                    "</body></html>"""
                )
            return path
        # Defensive: ensure commonly-used columns exist so rendering never KeyErrors
        for _col, _default in (
            ("assertion", ""),
            ("description", ""),
            ("status", "unknown"),
            ("score", 0.0),
            ("best_n_total", 0.0),
            ("scaled", 0.0),
        ):
            if _col not in df.columns:
                df[_col] = _default

        # Exclude rows that represent missing identity (keeps selects clean)
        df_summary = df[df["assertion"] != "[missing student identity]"].copy()
        grouped = df.groupby(["file", "student", "roll_number"], sort=False)

        # Build a student-level summary table (used for the Summary modal)
        # If Best-N enabled -> rely on self.student_best_df (Highest Best-N)
        # If Best-N disabled -> compute raw total marks per student across attempts
        if self.best_n and (not self.student_best_df.empty):
            # use student_best_df with columns: student, roll_number, best_n_best, best_scaled
            summary_df = self.student_best_df.copy()
            summary_df["display_metric"] = summary_df["best_n_best"].astype(float)
            summary_df["scaled_display"] = summary_df.get("best_scaled", 0.0).astype(float)
            # sort ascending by Highest Best-N per user's request
            summary_df = summary_df.sort_values("display_metric", ascending=True)
            summary_rows = summary_df.to_dict("records")
        else:
            # Compute per-attempt totals correctly (not summed across attempts)
            attempt_totals = (
                df_summary.groupby(["file", "student", "roll_number", "question"], sort=False)
                .agg(q_score=("score", "sum"))
                .reset_index()
            )

            # Sum scores per attempt (file)
            attempt_totals = (
                attempt_totals.groupby(["file", "student", "roll_number"], sort=False)
                .agg(total_score=("q_score", "sum"))
                .reset_index()
            )

            # Now pick the BEST attempt per student
            best_attempts = (
                attempt_totals.sort_values("total_score", ascending=False)
                .groupby(["student", "roll_number"], sort=False)
                .head(1)
                .reset_index(drop=True)
            )

            # For summary, use this as display_metric
            best_attempts["display_metric"] = best_attempts["total_score"].astype(float)
            summary_rows = best_attempts.to_dict("records")

        html_out = StringIO()

        # Header, styles, scripts
        html_out.write(
            """<!doctype html>
<html>
<head>
<meta charset="UTF-8">
<title>Evaluator Report</title>
<meta name="viewport" content="width=device-width, initial-scale=1">

<style>
    :root {
        --bg: #ffffff;
        --text: #222222;
        --muted: #666666;
        --panel: #f8f9fb;
        --accent: #2b6cb0;
        --pass: #e6ffe6;
        --fail: #fff1f0;
        --error-bg: #fff7f6;
    }
    body.dark {
        --bg: #111216;
        --text: #e6eef8;
        --muted: #9aa7b2;
        --panel: #0f1114;
        --accent: #4aa3ff;
        --pass: #0b2b0b;
        --fail: #3a0f0f;
        --error-bg: #2a0b0b;
    }
    body { background: var(--bg); color: var(--text); font-family: Inter, Arial, sans-serif; margin: 18px; }
    h1, h2, h3, h4 { margin: 6px 0; }
    .controls { display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin-bottom:12px; }
    select, button, input[type="search"] { padding: 8px; font-size:14px; border-radius:6px; border:1px solid #ccc; }
    .controls .spacer { flex:1 1 auto; }
    .panel { background: var(--panel); padding: 12px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); margin-bottom: 12px; }
    .student-block { margin-bottom: 12px; padding: 12px; border-radius: 8px; border: 1px solid rgba(0,0,0,0.06); }
    .student-meta { display:flex; gap:12px; flex-wrap:wrap; align-items:center; margin-bottom:8px; }
    .summary-pill { background: #fff; padding:6px 10px; border-radius:999px; font-weight:600; box-shadow:0 1px 4px rgba(0,0,0,0.05); }
    .question-block { margin-top:10px; border-radius:6px; padding:8px; border:1px solid rgba(0,0,0,0.04); background: linear-gradient(90deg, rgba(0,0,0,0.01), transparent); }
    .question-header { display:flex; justify-content:space-between; align-items:center; cursor:pointer; }
    .question-header h4 { margin:0; font-size:15px; }
    .question-details { margin-top:8px; display:none; }
    table { border-collapse: collapse; width:100%; margin-top:8px; }
    th, td { padding: 8px 6px; border-bottom: 1px solid rgba(0,0,0,0.06); text-align:left; font-size:13px; }
    tr.passed td { background: var(--pass); }
    tr.failed td { background: var(--fail); }
    .error-box {
        white-space: normal;
        background: var(--error-bg);
        padding: 8px;
        border-radius: 6px;
        font-family: "Courier New", monospace;
        font-size: 13px;
        line-height: 1.35;
        border: 1px solid rgba(0,0,0,0.06);
    }
    .summary-modal {
        display:none;
        position:fixed;
        left:50%;
        top:10%;
        transform:translateX(-50%);
        width: 80%;
        max-width: 1100px;
        max-height: 78vh;
        overflow:auto;
        background: var(--panel);
        border-radius:10px;
        padding:18px;
        z-index:1002;
        box-shadow: 0 12px 40px rgba(0,0,0,0.3);
    }
    #overlay {
        display:none;
        position:fixed; left:0; top:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:1001;
    }
    .btn { background: var(--accent); color: white; border: none; padding:8px 12px; border-radius:6px; cursor:pointer; }
    .btn.ghost { background: transparent; color:var(--text); border:1px solid rgba(0,0,0,0.08); }
    .toggle { display:inline-flex; align-items:center; gap:8px; }
    .muted { color: var(--muted); font-size:13px; }
    .collapse-indicator { font-size:12px; margin-left:8px; color:var(--muted); }
    @media (max-width: 800px) {
        .controls { flex-direction:column; align-items:stretch; }
    }
</style>

<script>
    function toggleDarkMode() {
        document.body.classList.toggle('dark');
        try { localStorage.setItem('dark', document.body.classList.contains('dark')?'1':'0'); } catch(e){}
    }
    function initDarkModeFromStorage() {
        try {
            if(localStorage.getItem('dark') === '1') document.body.classList.add('dark');
        } catch(e){}
    }
    function filterReports() {
        const studentVal = document.getElementById("studentSelect").value;
        const rollVal = document.getElementById("rollSelect").value;
        const fileVal = document.getElementById("fileSelect").value;
        const searchVal = document.getElementById("searchInput").value.toLowerCase();

        document.querySelectorAll(".student-block").forEach(div => {
            const name = div.dataset.name || "";
            const roll = div.dataset.roll || "";
            const file = div.dataset.file || "";
            const txt = div.innerText.toLowerCase();
            const matches = (
                (studentVal === "" || name === studentVal) &&
                (rollVal === "" || roll === rollVal) &&
                (fileVal === "" || file === fileVal) &&
                (searchVal === "" || txt.indexOf(searchVal) !== -1)
            );
            div.style.display = matches ? "block" : "none";
        });
    }
    function sortStudents() {
        const sortType = document.getElementById("sortSelect").value;
        const container = document.getElementById("reportContainer");
        const blocks = Array.from(container.getElementsByClassName("student-block"));
        blocks.sort((a, b) => {
            const scoreA = parseFloat(a.dataset.total) || 0;
            const scoreB = parseFloat(b.dataset.total) || 0;
            const nameA = (a.dataset.name || "").toLowerCase();
            const nameB = (b.dataset.name || "").toLowerCase();
            const rollA = (a.dataset.roll || "").toLowerCase();
            const rollB = (b.dataset.roll || "").toLowerCase();
            const fileA = (a.dataset.file || "").toLowerCase();
            const fileB = (b.dataset.file || "").toLowerCase();
            switch(sortType) {
                case "marks": return scoreB - scoreA;
                case "name": return nameA.localeCompare(nameB);
                case "roll": return rollA.localeCompare(rollB);
                case "file": return fileA.localeCompare(fileB);
                default: return 0;
            }
        });
        blocks.forEach(b => container.appendChild(b));
    }
    function showSummary() {
        document.getElementById("overlay").style.display = "block";
        document.getElementById("summaryModal").style.display = "block";
    }
    function closeSummary() {
        document.getElementById("overlay").style.display = "none";
        document.getElementById("summaryModal").style.display = "none";
    }
    function toggleDetails(evt, qid) {
        const details = document.getElementById(qid);
        if(!details) return;
        if(details.style.display === "block") {
            details.style.display = "none";
            evt.currentTarget.querySelector(".collapse-indicator").innerText = "+";
        } else {
            details.style.display = "block";
            evt.currentTarget.querySelector(".collapse-indicator").innerText = "−";
        }
    }
    window.addEventListener('DOMContentLoaded', (event) => {
        initDarkModeFromStorage();
        document.querySelectorAll('.question-header').forEach((hdr) => {
            hdr.addEventListener('click', function(e) {
                const qid = this.getAttribute('data-qid');
                toggleDetails({ currentTarget: this }, qid);
            });
        });
    });
</script>
</head>
<body>
<h1>Evaluator Report</h1>

<div class="controls panel">
    <label for="sortSelect">Sort by:</label>
    <select id="sortSelect" onchange="sortStudents()">
        <option value="marks">Total Marks (High → Low)</option>
        <option value="name">Student Name (A → Z)</option>
        <option value="roll">Roll Number (A → Z)</option>
        <option value="file">File Name (A → Z)</option>
    </select>

    <label for="studentSelect">Student:</label>
    <select id="studentSelect" onchange="filterReports()">
        <option value="">-- All Students --</option>
"""
        )

        # populate select options
        for student in sorted(df_summary["student"].dropna().unique()):
            html_out.write(
                f"<option value='{html_lib.escape(student)}'>{html_lib.escape(student)}</option>"
            )
        html_out.write("</select>")

        html_out.write(
            """
    <label for="rollSelect">Roll:</label>
    <select id="rollSelect" onchange="filterReports()">
        <option value="">-- All Rolls --</option>
"""
        )
        for roll in sorted(df_summary["roll_number"].dropna().astype(str).unique()):
            html_out.write(
                f"<option value='{html_lib.escape(str(roll))}'>{html_lib.escape(str(roll))}</option>"
            )
        html_out.write("</select>")

        html_out.write(
            """
    <label for="fileSelect">File:</label>
    <select id="fileSelect" onchange="filterReports()">
        <option value="">-- All Files --</option>
"""
        )
        # file names
        unique_files = sorted({Path(f).name for f in df["file"].unique()})
        for file in unique_files:
            html_out.write(
                f"<option value='{html_lib.escape(file)}'>{html_lib.escape(file)}</option>"
            )
        html_out.write("</select>")

        html_out.write(
            """
    <input id="searchInput" type="search" placeholder="Search inside reports..." oninput="filterReports()" style="min-width:200px;">
    <div class="spacer"></div>
    <div class="toggle">
        <button class="btn" onclick="showSummary()">Show Summary</button>
        <button class="btn ghost" onclick="sortStudents()">Refresh Sort</button>
        <button class="btn ghost" onclick="filterReports()">Apply Filters</button>
    </div>
    <div style="width:12px;"></div>
    <div style="display:flex; gap:8px; align-items:center;">
        <label class="muted">Dark</label>
        <button class="btn ghost" onclick="toggleDarkMode()">Toggle Dark</button>
    </div>
</div>
<div id="reportContainer">
"""
        )

        # --- student blocks per attempt ---
        for (file, student, roll_number), g in grouped:
            # FIX: calculate total per attempt (per file), not accumulated across all attempts
            total_score = float(g.groupby("question", sort=False)["score"].sum().sum())

            total_possible = self.total_assertions
            percentage = round((total_score / total_possible) * 100, 2) if total_possible else 0.0
            best_n_val = float(g["best_n_total"].iloc[0]) if "best_n_total" in g.columns else 0.0
            scaled_val = float(g["scaled"].iloc[0]) if "scaled" in g.columns else 0.0

            short_file = Path(file).name if file else ""

            html_out.write(
                f'<div class="student-block panel" data-name="{html_lib.escape(student)}" '
                f'data-roll="{html_lib.escape(str(roll_number))}" data-file="{html_lib.escape(short_file)}" '
                f'data-total="{total_score}">'
            )

            html_out.write(
                f"<div class='student-meta'><div><h3>{html_lib.escape(student)}</h3><div class='muted'>Roll: {html_lib.escape(str(roll_number))}</div></div>"
            )
            html_out.write(
                f"<div style='margin-left:auto; display:flex; gap:8px; align-items:center;'>"
            )
            html_out.write(f"<div class='summary-pill'>File: {html_lib.escape(short_file)}</div>")
            html_out.write(
                f"<div class='summary-pill'>Total: {total_score}/{total_possible} ({percentage}%)</div>"
            )

            # Conditionally show Best-N and Scaled pills
            if self.best_n:
                html_out.write(f"<div class='summary-pill'>Best {self.best_n}: {best_n_val}</div>")

            if self.scaled_range:
                # scaled_val may be 0 if scaling disabled or not computable; show rounded
                html_out.write(f"<div class='summary-pill'>Scaled: {round(scaled_val,2)}</div>")

            html_out.write("</div></div>")  # end student-meta

            # group per question
            for q, subdf in g.groupby("question", sort=False):
                qid = f"q_{abs(hash((file, student, roll_number, str(q))))}"
                html_out.write(f"<div class='question-block'>")
                html_out.write(f"<div class='question-header' data-qid='{qid}'>")
                html_out.write(f"<h4>Question: {html_lib.escape(str(q))}</h4>")
                html_out.write(f"<div class='collapse-indicator'>+</div>")
                html_out.write("</div>")  # header
                html_out.write(f"<div class='question-details' id='{qid}'>")
                desc = subdf["description"].iloc[0] if "description" in subdf.columns else ""
                if desc:
                    html_out.write(
                        f"<div class='muted' style='margin-bottom:8px;'>Description: {html_lib.escape(str(desc))}</div>"
                    )

                html_out.write(
                    "<table><thead><tr><th style='width:55%'>Assertion</th><th style='width:10%'>Status</th><th style='width:8%'>Score</th><th>Error</th></tr></thead><tbody>"
                )

                for _, row in subdf.iterrows():
                    row_class = "passed" if row["status"] == "passed" else "failed"
                    assertion_text = html_lib.escape(str(row["assertion"]))
                    status_text = html_lib.escape(str(row["status"]))
                    score_text = row["score"]
                    err_html = ""
                    if row.get("error"):
                        err_html = f"<div class='error-box'>{self._escape_error_html(row.get('error'))}</div>"
                    html_out.write(
                        f"<tr class='{row_class}'>"
                        f"<td>{assertion_text}</td>"
                        f"<td>{status_text}</td>"
                        f"<td>{score_text}</td>"
                        f"<td>{err_html}</td>"
                        f"</tr>"
                    )

                html_out.write("</tbody></table>")
                html_out.write("</div>")  # end question-details
                html_out.write("</div>")  # end question-block

            html_out.write("</div>")  # end student-block

        # --- summary modal content ---
        html_out.write(
            """
</div> <!-- reportContainer -->
<div id="overlay" onclick="closeSummary()"></div>
<div id="summaryModal" class="summary-modal">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <h2>Student Summary</h2>
        <div><button class="btn ghost" onclick="closeSummary()">Close</button></div>
    </div>
    <div style="margin-top:12px;">
        <table style="width:100%;">
"""
        )

        # Build summary table header conditionally
        html_out.write("<thead><tr><th>Student</th><th>Roll Number</th>")
        if self.best_n:
            html_out.write("<th>Highest Best-N</th><th>Best out of</th>")
        if self.scaled_range:
            html_out.write("<th>Scaled Score</th>")
        if not self.best_n:
            html_out.write("<th>Marks Obtained</th><th>Out of</th>")

        html_out.write("</tr></thead><tbody>")

        # Now write rows from summary_rows
        if summary_rows:
            for row in summary_rows:
                student = html_lib.escape(str(row.get("student", row.get("student", ""))))
                roll = html_lib.escape(str(row.get("roll_number", row.get("roll_number", ""))))
                html_out.write(f"<tr><td>{student}</td><td>{roll}</td>")
                if self.best_n:
                    best_n_best = float(row.get("best_n_best", row.get("display_metric", 0.0)))
                    out_of = min(self.best_n, self.total_assertions)
                    html_out.write(f"<td>{best_n_best}</td><td>{out_of}</td>")
                if self.scaled_range:
                    # display scaled from either student_best_df or 0
                    scaled_val = float(row.get("best_scaled", row.get("scaled_display", 0.0)))
                    html_out.write(f"<td>{round(scaled_val,2)}</td>")
                if not self.best_n:
                    total_marks = float(row.get("display_metric", 0.0))
                    total_possible = self.total_assertions
                    html_out.write(f"<td>{total_marks}</td><td>{total_possible}</td>")

                html_out.write("</tr>")
        else:
            html_out.write("<tr><td colspan='5'>No student summaries available.</td></tr>")

        html_out.write(
            """
            </tbody>
        </table>
    </div>
</div>

<script>
    // small helper to expand all question details if needed
    function expandAll() {
        document.querySelectorAll('.question-details').forEach(d => d.style.display = 'block');
        document.querySelectorAll('.collapse-indicator').forEach(i => i.innerText = '−');
    }
    function collapseAll() {
        document.querySelectorAll('.question-details').forEach(d => d.style.display = 'none');
        document.querySelectorAll('.collapse-indicator').forEach(i => i.innerText = '+');
    }
</script>

</body>
</html>
"""
        )

        path.write_text(html_out.getvalue(), encoding="utf8")
        return path


# -------------------------------------------------------------------------
# Quick local test / example usage when run as script
# -------------------------------------------------------------------------
if __name__ == "__main__":
    # small synthetic demonstration; replace with real executed_results structure
    example_results = [
        {
            "student_path": "submissions/alice_attempt1.py",
            "execution": {"namespace": {"name": "Alice"}, "student_meta": {"roll_number": "R001"}},
            "results": [
                {
                    "question": "Pairs",
                    "assertion": "assert normalize_pairs(find_pairs([1,2,3,4,5],6)) == normalize_pairs([(1,5),(2,4)])",
                    "status": "passed",
                    "score": 1,
                },
                {
                    "question": "Pairs",
                    "assertion": "assert normalize_pairs(find_pairs([1,1,1,1],2)) == normalize_pairs([(1,1),(1,1),(1,1),(1,1),(1,1),(1,1)])",
                    "status": "failed",
                    "score": 0,
                    "error": "Assertion failed.\nAssertion: assert normalize_pairs(find_pairs([1,1,1,1], 2)) == normalize_pairs([(1,1),(1,1),(1,1),(1,1),(1,1),(1,1)])\nExpected: 6 items\nActual:   2 items.",
                },
            ],
        },
        {
            "student_path": "submissions/bob_attempt1.py",
            "execution": {"namespace": {"name": "Bob"}, "student_meta": {"roll_number": "R002"}},
            "results": [
                {"question": "Pairs", "assertion": "assert True", "status": "passed", "score": 1},
            ],
        },
    ]

    # Example 1: totals only
    svc1 = ReportingService(executed_results=example_results, total_assertions=15)
    out1 = Path("evaluator_report_totals_only.html")
    svc1.to_html(out1)
    print(f"Wrote demo report to: {out1.resolve()}")

    # Example 2: best-n but no scaling
    svc2 = ReportingService(executed_results=example_results, total_assertions=15, best_n=3)
    out2 = Path("evaluator_report_bestn.html")
    svc2.to_html(out2)
    print(f"Wrote demo report to: {out2.resolve()}")

    # Example 3: best-n with scaling
    svc3 = ReportingService(
        executed_results=example_results, total_assertions=15, best_n=3, scaled_range=(10, 20)
    )
    out3 = Path("evaluator_report_bestn_scaled.html")
    svc3.to_html(out3)
    print(f"Wrote demo report to: {out3.resolve()}")
