from ptr_editor.validation.result import Result


def repr_html_validation_result(result: Result) -> str:
    """HTML representation for Jupyter notebooks with light/dark mode support."""
    if not result.issues:
        return """
        <style>
            .validation-success {
                padding: 12px;
                border-left: 4px solid #28a745;
                background-color: rgba(40, 167, 69, 0.1);
                border-radius: 6px;
                font-family: sans-serif;
            }
        </style>
        <div class="validation-success">
            <strong>✓ Validation Passed</strong>
        </div>
        """

    error_count = len(result.errors())
    warning_count = len(result.warnings())
    info_count = len(result.infos())

    if error_count > 0:
        border_color = "#f85149"
        bg_color = "rgba(248, 81, 73, 0.1)"
        icon = "✗"
        status = "Failed"
    elif warning_count > 0:
        border_color = "#d29922"
        bg_color = "rgba(210, 153, 34, 0.1)"
        icon = "⚠"
        status = "Passed with Warnings"
    else:
        border_color = "#58a6ff"
        bg_color = "rgba(88, 166, 255, 0.1)"
        icon = "ℹ"
        status = "Passed with Info"

    html = f"""
    <style>
        .validation-result {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            margin: 10px 0;
        }}

        .validation-header {{
            padding: 12px;
            border-left: 4px solid {border_color};
            background-color: {bg_color};
            border-radius: 6px;
            margin-bottom: 10px;
        }}

        .validation-header strong {{
            font-size: 14px;
        }}

        .validation-summary {{
            margin-top: 5px;
            opacity: 0.8;
            font-size: 13px;
        }}

        .validation-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            border: 1px solid rgba(128, 128, 128, 0.2);
            border-radius: 6px;
            overflow: hidden;
        }}

        .validation-table thead {{
            background-color: rgba(128, 128, 128, 0.05);
        }}

        .validation-table th {{
            padding: 8px 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 1px solid rgba(128, 128, 128, 0.2);
        }}

        .validation-table tbody tr {{
            border-bottom: 1px solid rgba(128, 128, 128, 0.1);
        }}

        .validation-table tbody tr:last-child {{
            border-bottom: none;
        }}

        .validation-table td {{
            padding: 8px 12px;
        }}

        .validation-table .path-cell {{
            font-family: 'SF Mono', Monaco, Consolas, monospace;
            font-size: 12px;
            opacity: 0.8;
        }}

        .validation-table .source-cell {{
            font-family: 'SF Mono', Monaco, Consolas, monospace;
            font-size: 11px;
            opacity: 0.6;
        }}

        .severity-badge {{
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: 600;
            display: inline-block;
            text-transform: uppercase;
        }}

        .severity-badge.CRITICAL {{
            background-color: rgba(248, 81, 73, 0.2);
            color: #ff7b72;
            border: 1px solid rgba(248, 81, 73, 0.4);
        }}

        .severity-badge.ERROR {{
            background-color: rgba(248, 81, 73, 0.2);
            color: #ff7b72;
            border: 1px solid rgba(248, 81, 73, 0.4);
        }}

        .severity-badge.WARNING {{
            background-color: rgba(210, 153, 34, 0.2);
            color: #e3b341;
            border: 1px solid rgba(210, 153, 34, 0.4);
        }}

        .severity-badge.INFO {{
            background-color: rgba(88, 166, 255, 0.2);
            color: #79c0ff;
            border: 1px solid rgba(88, 166, 255, 0.4);
        }}
    </style>
    <div class="validation-result">
        <div class="validation-header">
            <strong>{icon} Validation {status}</strong>
            <div class="validation-summary">
                {error_count} errors · {warning_count} warnings · {info_count} info
            </div>
        </div>
        <table class="validation-table">
            <thead>
                <tr>
                    <th>Severity</th>
                    <th>Path</th>
                    <th>Message</th>
                    <th>Source</th>
                </tr>
            </thead>
            <tbody>
    """

    for issue in result.issues:
        html += f"""
            <tr>
                <td>
                    <span class="severity-badge {issue.severity.value.upper()}">
                        {issue.severity.value}
                    </span>
                </td>
                <td class="path-cell">{issue.path}</td>
                <td>{issue.message}</td>
                <td class="source-cell">{issue.source if issue.source else "—"}</td>
            </tr>
        """

    html += """
            </tbody>
        </table>
    </div>
    """
    return html
