"""
SDLC 5.0.0 Report Command.

Generate detailed validation reports in various formats.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from ..validation.engine import SDLCValidator, ValidationResult, ValidationSeverity
from ..validation.tier import STAGE_NAMES, Tier

console = Console()


def report_command(
    path: Path = typer.Option(
        Path.cwd(),
        "--path",
        "-p",
        help="Project root path",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    docs_root: str = typer.Option(
        "docs",
        "--docs",
        "-d",
        help="Documentation folder name",
    ),
    tier: Optional[str] = typer.Option(
        None,
        "--tier",
        "-t",
        help="Project tier: lite, standard, professional, enterprise",
    ),
    output_format: str = typer.Option(
        "markdown",
        "--format",
        "-f",
        help="Output format: markdown, json, html",
    ),
    output_path: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (prints to stdout if not specified)",
    ),
) -> None:
    """
    Generate SDLC 5.0.0 compliance report.

    Creates a detailed report of the project's SDLC compliance status
    suitable for documentation or CI/CD integration.

    Examples:

        sdlcctl report --format markdown --output COMPLIANCE.md

        sdlcctl report --format json

        sdlcctl report --format html --output report.html
    """
    # Parse tier
    project_tier: Optional[Tier] = None
    if tier:
        try:
            project_tier = Tier(tier.lower())
        except ValueError:
            console.print(f"[red]Error:[/red] Invalid tier '{tier}'")
            raise typer.Exit(code=1)

    # Run validation
    validator = SDLCValidator(
        project_root=path,
        docs_root=docs_root,
        tier=project_tier,
    )

    with console.status("[bold blue]Generating report...[/bold blue]"):
        result = validator.validate()

    # Generate report
    if output_format == "json":
        report = _generate_json_report(result)
    elif output_format == "html":
        report = _generate_html_report(result)
    else:
        report = _generate_markdown_report(result)

    # Output
    if output_path:
        output_path.write_text(report, encoding="utf-8")
        console.print(f"[green]✓ Report saved to:[/green] {output_path}")
    else:
        print(report)


def _generate_markdown_report(result: ValidationResult) -> str:
    """Generate Markdown report."""
    status_emoji = "✅" if result.is_compliant else "❌"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    compliance_status = 'COMPLIANT' if result.is_compliant else 'NON-COMPLIANT'
    p0_required = 'Yes' if result.tier_requirements.p0_required else 'No'

    # Build stages table
    stages_rows = []
    for stage_id in sorted(STAGE_NAMES.keys()):
        stage_name = STAGE_NAMES[stage_id]
        required = stage_id in result.tier_requirements.required_stages
        found = stage_id in result.scan_result.stages_found

        if found:
            stage_info = result.scan_result.stages_found[stage_id]
            status = "✅ Present"
            files = str(stage_info.file_count)
            readme = "✅" if stage_info.has_readme else "❌"
        else:
            status = "❌ Missing" if required else "⚪ Optional"
            files = "-"
            readme = "-"

        req_text = 'Required' if required else 'Optional'
        stages_rows.append(
            f"| {stage_id} | {stage_name} | {req_text} | {status} | {files} | {readme} |"
        )

    stages_table = "\n".join(stages_rows)

    # Build issues section
    issues_section = ""
    if result.issues:
        error_issues = [i for i in result.issues if i.severity == ValidationSeverity.ERROR]
        warning_issues = [i for i in result.issues if i.severity == ValidationSeverity.WARNING]
        info_issues = [i for i in result.issues if i.severity == ValidationSeverity.INFO]

        if error_issues:
            issues_section += "\n### ❌ Errors\n\n"
            for issue in error_issues:
                issues_section += f"- **[{issue.code}]** {issue.message}\n"
                if issue.fix_suggestion:
                    issues_section += f"  - Fix: `{issue.fix_suggestion}`\n"

        if warning_issues:
            issues_section += "\n### ⚠️ Warnings\n\n"
            for issue in warning_issues:
                issues_section += f"- **[{issue.code}]** {issue.message}\n"
                if issue.fix_suggestion:
                    issues_section += f"  - Fix: `{issue.fix_suggestion}`\n"

        if info_issues:
            issues_section += "\n### ℹ️ Info\n\n"
            for issue in info_issues:
                issues_section += f"- **[{issue.code}]** {issue.message}\n"

    # Build P0 artifacts section
    p0_section = "\n### P0 Artifacts\n\n"
    p0_section += f"- **Required for Tier**: {p0_required}\n"
    p0_section += f"- **Found**: {result.p0_result.artifacts_found}/{result.p0_result.artifacts_checked}\n"
    p0_section += f"- **Coverage**: {result.p0_result.coverage_percent}%\n"

    # Handle issues display
    issues_display = issues_section if issues_section else "\n✅ No issues found.\n"

    # Build recommendations
    recommendations = []
    if result.error_count > 0:
        recommendations.append("1. **Fix all errors** - Run `sdlcctl fix` to automatically create missing structures")
    if result.warning_count > 0:
        recommendations.append("2. **Address warnings** - Review naming conventions and P0 artifact content")
    if result.compliance_score < 100:
        recommendations.append("3. **Improve coverage** - Add missing P0 artifacts for full compliance")

    recommendations_text = "\n".join(recommendations) if recommendations else "No recommendations - great job!"

    return f"""# SDLC 5.0.0 Compliance Report

**Generated**: {timestamp}
**Project**: {result.project_root.name}
**Framework**: SDLC 5.0.0

---

## Summary

| Metric | Value |
|--------|-------|
| **Status** | {status_emoji} {compliance_status} |
| **Compliance Score** | {result.compliance_score}/100 |
| **Tier** | {result.tier.value.upper()} |
| **Validation Time** | {result.validation_time_ms:.1f}ms |
| **Errors** | {result.error_count} |
| **Warnings** | {result.warning_count} |

---

## Stage Compliance

| ID | Stage Name | Requirement | Status | Files | README |
|----|------------|-------------|--------|-------|--------|
{stages_table}

---
{p0_section}
---

## Issues
{issues_display}

---

## Recommendations

{recommendations_text}

---

*Report generated by sdlcctl v1.0.0*
"""


def _generate_json_report(result: ValidationResult) -> str:
    """Generate JSON report."""
    report_data = result.to_dict()
    report_data["generated_at"] = datetime.now().isoformat()
    report_data["generator"] = "sdlcctl v1.0.0"
    return json.dumps(report_data, indent=2)


def _generate_html_report(result: ValidationResult) -> str:
    """Generate HTML report."""
    status_color = "#28a745" if result.is_compliant else "#dc3545"
    status_text = "COMPLIANT" if result.is_compliant else "NON-COMPLIANT"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Build stages table rows
    stages_rows = ""
    for stage_id in sorted(STAGE_NAMES.keys()):
        stage_name = STAGE_NAMES[stage_id]
        required = stage_id in result.tier_requirements.required_stages
        found = stage_id in result.scan_result.stages_found

        if found:
            stage_info = result.scan_result.stages_found[stage_id]
            status_html = '<span style="color: #28a745;">✅ Present</span>'
            files = str(stage_info.file_count)
            readme = "✅" if stage_info.has_readme else "❌"
        else:
            if required:
                status_html = '<span style="color: #dc3545;">❌ Missing</span>'
            else:
                status_html = '<span style="color: #6c757d;">⚪ Optional</span>'
            files = "-"
            readme = "-"

        stages_rows += f"""
        <tr>
            <td>{stage_id}</td>
            <td>{stage_name}</td>
            <td>{'Required' if required else 'Optional'}</td>
            <td>{status_html}</td>
            <td>{files}</td>
            <td>{readme}</td>
        </tr>
        """

    # Build issues section
    issues_html = ""
    if result.issues:
        for issue in result.issues:
            color = {
                ValidationSeverity.ERROR: "#dc3545",
                ValidationSeverity.WARNING: "#ffc107",
                ValidationSeverity.INFO: "#17a2b8",
            }.get(issue.severity, "#6c757d")

            issues_html += f"""
            <div style="border-left: 4px solid {color}; padding: 10px; margin: 10px 0; background: #f8f9fa;">
                <strong>[{issue.code}]</strong> {issue.message}
                {f'<br><small style="color: #6c757d;">Fix: {issue.fix_suggestion}</small>' if issue.fix_suggestion else ''}
            </div>
            """
    else:
        issues_html = '<p style="color: #28a745;">✅ No issues found.</p>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SDLC 5.0.0 Compliance Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #fff;
            color: #333;
        }}
        h1, h2, h3 {{ color: #212529; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #dee2e6;
            padding: 12px;
            text-align: left;
        }}
        th {{ background: #f8f9fa; }}
        .summary-card {{
            display: inline-block;
            padding: 20px;
            margin: 10px;
            border-radius: 8px;
            background: #f8f9fa;
            min-width: 150px;
            text-align: center;
        }}
        .summary-card .value {{
            font-size: 24px;
            font-weight: bold;
        }}
        .summary-card .label {{
            color: #6c757d;
            font-size: 14px;
        }}
        .status {{ color: {status_color}; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>SDLC 5.0.0 Compliance Report</h1>
    <p><strong>Generated:</strong> {timestamp} | <strong>Project:</strong> {result.project_root.name}</p>

    <h2>Summary</h2>
    <div>
        <div class="summary-card">
            <div class="value status">{status_text}</div>
            <div class="label">Status</div>
        </div>
        <div class="summary-card">
            <div class="value">{result.compliance_score}/100</div>
            <div class="label">Score</div>
        </div>
        <div class="summary-card">
            <div class="value">{result.tier.value.upper()}</div>
            <div class="label">Tier</div>
        </div>
        <div class="summary-card">
            <div class="value" style="color: #dc3545;">{result.error_count}</div>
            <div class="label">Errors</div>
        </div>
        <div class="summary-card">
            <div class="value" style="color: #ffc107;">{result.warning_count}</div>
            <div class="label">Warnings</div>
        </div>
    </div>

    <h2>Stage Compliance</h2>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Stage Name</th>
                <th>Requirement</th>
                <th>Status</th>
                <th>Files</th>
                <th>README</th>
            </tr>
        </thead>
        <tbody>
            {stages_rows}
        </tbody>
    </table>

    <h2>P0 Artifacts</h2>
    <p>
        <strong>Required for Tier:</strong> {'Yes' if result.tier_requirements.p0_required else 'No'}<br>
        <strong>Found:</strong> {result.p0_result.artifacts_found}/{result.p0_result.artifacts_checked}<br>
        <strong>Coverage:</strong> {result.p0_result.coverage_percent}%
    </p>

    <h2>Issues</h2>
    {issues_html}

    <hr>
    <p style="color: #6c757d; font-size: 12px;">
        Report generated by sdlcctl v1.0.0
    </p>
</body>
</html>
"""
