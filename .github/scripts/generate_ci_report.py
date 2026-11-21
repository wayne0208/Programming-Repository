"""Generate a Markdown CI summary report from Ruff logs and JUnit XML results."""

from __future__ import annotations

import argparse
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

REPORT_MARKER = "<!-- ci-test-report -->"
ASSERTION_PREFIXES = ("AssertionError", "assert ", "Failed:")
MAX_RUFF_LINES = 80
MAX_TABLE_ROWS = 50


@dataclass
class FailureEntry:
    """Represents a single failed or errored test case."""

    node_id: str
    category: str
    summary: str


@dataclass
class SuiteResult:
    """Aggregated statistics and classified failures for a JUnit XML suite."""

    exists: bool = False
    total: int = 0
    passed: int = 0
    skipped: int = 0
    assertion_failures: list[FailureEntry] = field(default_factory=list)
    crashes: list[FailureEntry] = field(default_factory=list)

    @property
    def failed_total(self) -> int:
        return len(self.assertion_failures) + len(self.crashes)


def _escape_cell(text: str, limit: int = 180) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip().replace("|", "\\|")
    if len(cleaned) > limit:
        return cleaned[: limit - 1] + "…"
    return cleaned or "-"


def _extract_error_summary(message: str, body: str) -> str:
    e_lines = [line[4:].strip() for line in body.splitlines() if line.startswith("E   ")]
    if e_lines:
        if len(e_lines) > 1 and e_lines[0].startswith("AssertionError") and e_lines[-1].startswith("assert "):
            e_lines = e_lines[:-1]
        return " ".join(e_lines)
    if message.strip():
        return " ".join(line.strip() for line in message.strip().splitlines())
    non_empty = [line.strip() for line in body.splitlines() if line.strip()]
    return non_empty[-1] if non_empty else "Unknown error"


def _is_assertion_failure(message: str, body: str) -> bool:
    msg = message.strip()
    if msg.startswith(ASSERTION_PREFIXES):
        return True
    e_lines = [line[4:].strip() for line in body.splitlines() if line.startswith("E   ")]
    if e_lines:
        return any(line.startswith(ASSERTION_PREFIXES) for line in e_lines)
    return False


def parse_junit_xml(xml_path: Path) -> SuiteResult:
    """Parse a JUnit XML file and classify failures vs. unexpected crashes."""
    result = SuiteResult()
    if not xml_path.exists():
        return result

    try:
        tree = ET.parse(xml_path)
    except ET.ParseError as exc:
        result.exists = True
        result.crashes.append(FailureEntry(node_id=xml_path.name, category="💥 非預期例外中斷", summary=str(exc)))
        return result

    result.exists = True
    root = tree.getroot()
    for testcase in root.iter("testcase"):
        result.total += 1
        classname = testcase.get("classname", "").strip()
        name = testcase.get("name", "").strip()
        node_id = f"{classname}::{name}" if classname else name

        error_elem = testcase.find("error")
        failure_elem = testcase.find("failure")
        skipped_elem = testcase.find("skipped")

        if error_elem is not None:
            summary = _extract_error_summary(error_elem.get("message", ""), error_elem.text or "")
            result.crashes.append(FailureEntry(node_id=node_id, category="💥 非預期例外中斷", summary=summary))
        elif failure_elem is not None:
            msg = failure_elem.get("message", "")
            body = failure_elem.text or ""
            summary = _extract_error_summary(msg, body)
            if _is_assertion_failure(msg, body):
                result.assertion_failures.append(FailureEntry(node_id=node_id, category="❌ 斷言失敗", summary=summary))
            else:
                result.crashes.append(FailureEntry(node_id=node_id, category="💥 非預期例外中斷", summary=summary))
        elif skipped_elem is not None:
            result.skipped += 1
        else:
            result.passed += 1

    return result


def _status_badge(outcome: str, is_hard_gate: bool) -> str:
    if outcome == "success":
        return "✅ 通過"
    if outcome in {"skipped", "cancelled", ""}:
        return "⚪ 略過"
    return "❌ 失敗（阻斷）" if is_hard_gate else "⚠️ 警告（軟性）"


def _suite_summary_text(suite: SuiteResult, outcome: str) -> str:
    if not suite.exists:
        return "未產生測試報告" if outcome != "skipped" else "已略過"
    if suite.total == 0:
        return "無測試案例"
    parts = [f"共 {suite.total} 項：{suite.passed} 通過"]
    if suite.assertion_failures:
        parts.append(f"{len(suite.assertion_failures)} 斷言失敗")
    if suite.crashes:
        parts.append(f"{len(suite.crashes)} 非預期中斷")
    if suite.skipped:
        parts.append(f"{suite.skipped} 略過")
    return "、".join(parts)


def _read_truncated_log(path: Path, max_lines: int = MAX_RUFF_LINES) -> tuple[str, bool]:
    if not path.exists():
        return "", False
    lines = path.read_text(encoding="utf-8", errors="replace").lstrip("\ufeff").splitlines()
    if not lines:
        return "", False
    if len(lines) <= max_lines:
        return "\n".join(lines), False
    truncated_note = f"...（共 {len(lines)} 行，此處僅顯示前 {max_lines} 行，完整日誌請下載 Artifact）"
    return "\n".join([*lines[:max_lines], truncated_note]), True


def build_markdown_report(
    *,
    report_dir: Path,
    lint_outcome: str,
    format_outcome: str,
    compile_outcome: str,
    build_outcome: str,
    feature_outcome: str,
    guardrail_outcome: str,
    commit_sha: str,
    ref_name: str,
    run_url: str,
) -> str:
    """Build the complete Markdown CI report."""
    feature_suite = parse_junit_xml(report_dir / "feature-junit.xml")
    guardrail_suite = parse_junit_xml(report_dir / "guardrail-junit.xml")

    lint_log, _ = _read_truncated_log(report_dir / "ruff-lint.txt")
    format_log, _ = _read_truncated_log(report_dir / "ruff-format.txt")

    lines: list[str] = [
        REPORT_MARKER,
        "# 🤖 CI 自動化建置、靜態分析與測試報告",
        "",
    ]

    meta_parts: list[str] = []
    if ref_name:
        meta_parts.append(f"**分支 / Ref**: `{ref_name}`")
    if commit_sha:
        meta_parts.append(f"**Commit**: `{commit_sha[:7]}`")
    if run_url:
        meta_parts.append(f"[查看完整執行紀錄與 Artifact]({run_url})")
    if meta_parts:
        lines.append(" | ".join(meta_parts))
        lines.append("")

    lines.extend(
        [
            "## 1. 門檻總覽",
            "",
            "| 檢查關卡 | 門檻類型 | 狀態 | 摘要 |",
            "| :--- | :--- | :--- | :--- |",
            f"| 靜態分析（Ruff Lint） | **硬性門檻** | {_status_badge(lint_outcome, True)} | "
            f"{'無違規' if lint_outcome == 'success' else '發現 Lint 問題，請檢視下方明細'} |",
            f"| 排版檢查（Ruff Format） | **硬性門檻** | {_status_badge(format_outcome, True)} | "
            f"{'格式一致' if format_outcome == 'success' else '部分檔案未依 Ruff 排版'} |",
            f"| 語法編譯（compileall） | **硬性門檻** | {_status_badge(compile_outcome, True)} | "
            f"{'全部 .py 語法正確' if compile_outcome == 'success' else '存在語法或編譯錯誤'} |",
            f"| 套件建置（uv build） | **硬性門檻** | {_status_badge(build_outcome, True)} | "
            f"{'Wheel / sdist 打包成功' if build_outcome == 'success' else '打包建置失敗'} |",
            f"| 提交者功能測試（Feature Tests） | **硬性門檻** | {_status_badge(feature_outcome, True)} | "
            f"{_suite_summary_text(feature_suite, feature_outcome)} |",
            f"| 通用規範測試（SPEC Guardrails） | **硬性門檻** | {_status_badge(guardrail_outcome, True)} | "
            f"{_suite_summary_text(guardrail_suite, guardrail_outcome)} |",
            "",
            "## 2. 非預期例外中斷檢查（Unhandled Exceptions / Crashes）",
            "",
        ]
    )

    if feature_suite.crashes:
        lines.append(
            f"> [!WARNING]\n> 偵測到 **{len(feature_suite.crashes)} 項**提交者功能測試因「非預期例外」導致程式直接中斷"
            "（而非一般測試斷言失敗），請優先修正錯誤捕捉與邊界檢查！"
        )
        lines.append("")
        lines.append("| 測資名稱 | 分類 | 例外摘要 |")
        lines.append("| :--- | :--- | :--- |")
        for entry in feature_suite.crashes[:MAX_TABLE_ROWS]:
            lines.append(
                f"| `{_escape_cell(entry.node_id, 100)}` | {entry.category} | `{_escape_cell(entry.summary)}` |"
            )
        if len(feature_suite.crashes) > MAX_TABLE_ROWS:
            lines.append(f"| ... | ... | 其餘 {len(feature_suite.crashes) - MAX_TABLE_ROWS} 筆請見 Artifact |")
        lines.append("")
    elif not feature_suite.exists:
        lines.append("⚠️ 未取得提交者功能測試結果（`feature-junit.xml` 不存在），無法確認是否發生非預期中斷。")
        lines.append("")
    else:
        lines.append("✅ 本次提交者功能測試未發生非預期例外中斷。")
        lines.append("")

    all_feature_failures = [*feature_suite.crashes, *feature_suite.assertion_failures]
    if all_feature_failures:
        lines.extend(
            [
                "<details>",
                f"<summary>📋 提交者功能測試失敗明細（共 {len(all_feature_failures)} 項）</summary>",
                "",
                "| 測資名稱 | 分類 | 錯誤摘要 |",
                "| :--- | :--- | :--- |",
            ]
        )
        for entry in all_feature_failures[:MAX_TABLE_ROWS]:
            lines.append(
                f"| `{_escape_cell(entry.node_id, 100)}` | {entry.category} | `{_escape_cell(entry.summary)}` |"
            )
        lines.extend(["", "</details>", ""])

    all_guardrail_issues = [*guardrail_suite.crashes, *guardrail_suite.assertion_failures]
    if all_guardrail_issues:
        summary_title = (
            f"<summary>🛡️ 通用規範測試（SPEC Guardrails）違規明細（共 {len(all_guardrail_issues)} 項違規）</summary>"
        )
        lines.extend(
            [
                "<details>",
                summary_title,
                "",
                "| 檢查項目與目標檔案 | 分類 | 違規摘要 |",
                "| :--- | :--- | :--- |",
            ]
        )
        for entry in all_guardrail_issues[:MAX_TABLE_ROWS]:
            lines.append(f"| `{_escape_cell(entry.node_id, 100)}` | ❌ 規範違規 | {_escape_cell(entry.summary, 240)} |")
        lines.extend(["", "</details>", ""])

    if lint_outcome != "success" and lint_log:
        lines.extend(
            [
                "<details>",
                "<summary>🔍 Ruff Lint 靜態分析明細</summary>",
                "",
                "```text",
                lint_log,
                "```",
                "",
                "</details>",
                "",
            ]
        )

    if format_outcome != "success" and format_log:
        lines.extend(
            [
                "<details>",
                "<summary>🎨 Ruff Format 排版檢查明細</summary>",
                "",
                "```diff",
                format_log,
                "```",
                "",
                "</details>",
                "",
            ]
        )

    return "\n".join(lines)


def main() -> None:
    """Parse CLI arguments and write the CI Markdown report."""
    parser = argparse.ArgumentParser(description="Generate CI Markdown test report.")
    parser.add_argument("--report-dir", type=Path, default=Path("build/ci-reports"))
    parser.add_argument("--output", type=Path, default=Path("build/ci-reports/ci-report.md"))
    parser.add_argument("--lint-outcome", default="skipped")
    parser.add_argument("--format-outcome", default="skipped")
    parser.add_argument("--compile-outcome", default="skipped")
    parser.add_argument("--build-outcome", default="skipped")
    parser.add_argument("--feature-outcome", default="skipped")
    parser.add_argument("--guardrail-outcome", default="skipped")
    parser.add_argument("--commit-sha", default="")
    parser.add_argument("--ref-name", default="")
    parser.add_argument("--run-url", default="")

    args = parser.parse_args()
    report = build_markdown_report(
        report_dir=args.report_dir,
        lint_outcome=args.lint_outcome,
        format_outcome=args.format_outcome,
        compile_outcome=args.compile_outcome,
        build_outcome=args.build_outcome,
        feature_outcome=args.feature_outcome,
        guardrail_outcome=args.guardrail_outcome,
        commit_sha=args.commit_sha,
        ref_name=args.ref_name,
        run_url=args.run_url,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
