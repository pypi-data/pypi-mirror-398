"""
HTML report generation for timeline diff results with dynamic filtering.

Provides functions to generate comprehensive, filterable HTML reports showing timeline changes.
"""

from __future__ import annotations

import json
import difflib
import tempfile
import webbrowser
from html import escape as html_escape
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ptr_editor.diffing.timeline_differ_simple import TimelineDiff


def _generate_html_diff(left_xml: str, right_xml: str) -> str:
    """
    Generate HTML diff visualization for two XML strings.

    Creates a side-by-side diff with color-coded changes:
    - Green background: added lines
    - Red background: removed lines
    - Yellow background: modified lines

    Args:
        left_xml: XML string from left block
        right_xml: XML string from right block

    Returns:
        HTML string containing the diff visualization
    """
    # Split into lines for comparison
    left_lines = left_xml.splitlines()
    right_lines = right_xml.splitlines()

    # Generate unified diff
    differ = difflib.HtmlDiff(wrapcolumn=80)
    diff_html = differ.make_table(
        left_lines,
        right_lines,
        fromdesc="Left Block",
        todesc="Right Block",
        context=True,  # Only show changed lines with context
        numlines=3,  # Number of context lines
    )

    # Add custom styling to the diff table
    styled_diff = f"""
    <div style="overflow-x: auto;">
        <style>
            .diff_header {{
                background-color: #e0e0e0;
                font-weight: bold;
                padding: 5px;
            }}
            .diff_next {{
                background-color: #c0c0c0;
            }}
            .diff_add {{
                background-color: #d4edda;
                color: #155724;
            }}
            .diff_chg {{
                background-color: #fff3cd;
                color: #856404;
            }}
            .diff_sub {{
                background-color: #f8d7da;
                color: #721c24;
            }}
            table.diff {{
                font-family: 'Courier New', monospace;
                font-size: 11px;
                border-collapse: collapse;
                width: 100%;
            }}
            table.diff td {{
                padding: 2px 5px;
                vertical-align: top;
                white-space: pre-wrap;
                word-break: break-all;
            }}
        </style>
        {diff_html}
    </div>
    """
    return styled_diff


def to_html(
    diff_result: TimelineDiff,
    output_file: str | Path | None = None,
    compact: bool = False,
    open: bool = False,
) -> str:
    """
    Generate interactive HTML report for timeline diff results with dynamic filtering.

    Creates a comprehensive HTML report with:
    - Summary statistics
    - Dynamic filtering by status (added/removed/changed/unchanged) and designer
    - Single unified table showing all blocks
    - Expandable rows with XML viewing and diffs for changed blocks

    Args:
        diff_result: TimelineDiff object from timeline differ
        output_file: Path to save HTML file. If None, returns HTML string.
        compact: If True, uses minimal styling suitable for Jupyter notebooks.
                If False, uses full styled report for standalone HTML files.
        open: If True, opens the report in a web browser. If output_file is None,
              creates a temporary file first.

    Returns:
        HTML string of the generated report.
    """
    if compact:
        return diff_result._repr_html_()

    # Get comprehensive dataframe with all block information
    df = diff_result.to_pandas_full()

    if df.empty:
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>Timeline Diff Report</title></head>
        <body>
        <h1>📊 Timeline Diff Report</h1>
        <p>No blocks to display</p>
        </body>
        </html>
        """
        if output_file:
            Path(output_file).write_text(html)
        return html

    # Use full dataframe (no filtering)
    df_filtered = df

    # Extract unique change types from the dataframe
    change_types_set = set()
    for change_types_str in df_filtered["Change Types"].unique():
        if change_types_str != "N/A":
            # Parse comma-separated change types
            for ct in str(change_types_str).split(","):
                ct = ct.strip()
                if ct:
                    change_types_set.add(ct)
    change_types_list = sorted(list(change_types_set))

    # Convert dataframe to rows with proper escaping and generate diffs
    rows_data = []
    for idx, row in df_filtered.iterrows():
        status = str(row["Status"])
        block_id = html_escape(str(row["Block ID"]))

        designer = html_escape(str(row["Designer"]))
        start = html_escape(str(row["Start"])) if row["Start"] != "N/A" else "N/A"
        duration = row["Duration (min)"]
        change_types = html_escape(str(row["Change Types"])) if row["Change Types"] != "N/A" else "N/A"
        description = html_escape(str(row["Description"])) if row["Description"] != "N/A" else "N/A"
        current_xml = str(row["Current XML"]) if row["Current XML"] != "N/A" else "N/A"
        incoming_xml = str(row["Incoming XML"]) if row["Incoming XML"] != "N/A" else "N/A"

        # Generate diff HTML for changed blocks
        diff_html = ""
        if status == "changed" and current_xml != "N/A" and incoming_xml != "N/A":
            diff_html = _generate_html_diff(current_xml, incoming_xml)

        rows_data.append({
            "Status": status,
            "Block ID": block_id,
            "Designer": designer,
            "Start": start,
            "Duration": duration,
            "Change Types": change_types,
            "Description": description,
            "Current XML": current_xml,
            "Incoming XML": incoming_xml,
            "Diff HTML": diff_html,
        })

    # Compute counts for each filter option
    status_counts = df["Status"].value_counts().to_dict()
    designer_counts = df["Designer"].value_counts().to_dict()
    changetype_counts = {}
    for ct in change_types_list:
        count = sum(1 for row in rows_data if ct in row["Change Types"])
        changetype_counts[ct] = count

    # Convert to JSON for JavaScript filtering
    rows_json = json.dumps(rows_data)
    status_counts_json = json.dumps(status_counts)
    designer_counts_json = json.dumps(designer_counts)
    changetype_counts_json = json.dumps(changetype_counts)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Timeline Diff Report</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism.min.css" rel="stylesheet" />
        <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/line-numbers/prism-line-numbers.min.css" rel="stylesheet" />
        <style>
            * {{ box-sizing: border-box; }}
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            h1 {{ color: #2c3e50; }}
            h2 {{ color: #34495e; margin-top: 30px; margin-bottom: 15px; }}
            h3 {{ color: #555; margin: 15px 0 10px 0; }}
            
            .summary {{
                background: white;
                padding: 20px;
                margin: 20px 0;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            
            .metrics {{
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
            }}
            
            .metric {{
                flex: 1;
                min-width: 140px;
                text-align: center;
                padding: 15px;
                background: #ecf0f1;
                border-radius: 5px;
            }}
            
            .filter-group {{
                margin: 12px 0;
            }}
            
            .filter-group label {{
                display: block;
                margin-bottom: 6px;
                font-weight: 600;
                color: #2c3e50;
                font-size: 13px;
            }}
            
            .filter-buttons {{
                margin-top: 12px;
            }}
            
            .button-group {{
                display: flex;
                flex-wrap: wrap;
                gap: 6px;
                margin: 8px 0;
            }}
            
            .filter-button {{
                padding: 6px 10px;
                border: 2px solid #bdc3c7;
                background: white;
                color: #2c3e50;
                border-radius: 16px;
                cursor: pointer;
                font-size: 12px;
                transition: all 0.2s;
                font-weight: 500;
                display: flex;
                align-items: center;
                gap: 6px;
            }}
            
            .filter-button:hover {{
                border-color: #3498db;
                background: #ecf0f1;
            }}
            
            .filter-button.active {{
                background: #3498db;
                color: white;
                border-color: #3498db;
            }}
            
            .btn-count {{
                background: rgba(0,0,0,0.1);
                padding: 2px 6px;
                border-radius: 10px;
                font-size: 11px;
                font-weight: 600;
            }}
            
            .filter-button.active .btn-count {{
                background: rgba(255,255,255,0.3);
            }}
            
            .toggle-btn {{
                background: #ecf0f1;
                border: 1px solid #bdc3c7;
                padding: 3px 8px;
                border-radius: 4px;
                font-size: 11px;
                cursor: pointer;
                color: #2c3e50;
                transition: all 0.2s;
            }}
            
            .toggle-btn:hover {{
                background: #d5dbdb;
            }}
            
            .preset-btn {{
                background: #e8f4fd;
                border: 1px solid #3498db;
                color: #2c3e50;
                padding: 5px 10px;
                border-radius: 12px;
                font-size: 11px;
                cursor: pointer;
                transition: all 0.2s;
                font-weight: 500;
            }}
            
            .preset-btn:hover {{
                background: #3498db;
                color: white;
            }}
            
            button {{
                background: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                cursor: pointer;
                font-weight: bold;
                margin-right: 10px;
            }}
            
            button:hover {{ background: #2980b9; }}
            button.secondary {{ background: #95a5a6; }}
            button.secondary:hover {{ background: #7f8c8d; }}
            
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
                background: white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            
            th {{
                background: #34495e;
                color: white;
                padding: 12px;
                text-align: left;
                position: sticky;
                top: 0;
                font-weight: bold;
            }}
            
            td {{ 
                padding: 10px; 
                border-bottom: 1px solid #ecf0f1;
                word-break: break-word;
            }}
            
            tr:hover {{ background: #f8f9fa; }}
            
            .status-changed {{ background: #fff3cd; }}
            .status-added {{ background: #d4edda; }}
            .status-removed {{ background: #f8d7da; }}
            .status-unchanged {{ background: #e8f5e9; }}
            
            .expand-btn {{
                background: #3498db;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
                margin-right: 5px;
            }}
            
            .expand-btn:hover {{ background: #2980b9; }}
            
            .detail-row {{
                display: none;
            }}
            
            .detail-row.show {{
                display: table-row;
            }}
            
            .detail-content {{
                padding: 20px;
                background: #f9f9f9;
            }}
            
            .xml-panels {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin: 15px 0;
            }}
            
            .xml-panel {{
                min-width: 0;
                overflow-x: auto;
            }}
            
            .xml-panel strong {{
                display: block;
                margin-bottom: 8px;
                color: #2c3e50;
                font-size: 14px;
            }}
            
            .xml-panel pre {{
                margin: 0;
                max-height: 400px;
                overflow: auto;
                word-break: break-all;
                white-space: pre-wrap;
                font-size: 11px;
                background: #f5f5f5;
                padding: 10px;
                border-radius: 4px;
                border: 1px solid #ddd;
            }}
            
            .diff-container {{
                overflow-x: auto;
                font-size: 11px;
                font-family: monospace;
                margin: 10px 0;
            }}
            
            .status-badge {{
                display: inline-block;
                padding: 3px 8px;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
            }}
            
            .status-badge.changed {{ background: #fd7e14; color: white; }}
            .status-badge.added {{ background: #28a745; color: white; }}
            .status-badge.removed {{ background: #dc3545; color: white; }}
            .status-badge.unchanged {{ background: #6c757d; color: white; }}
            
            /* Sidebar Layout */
            .layout-container {{
                display: flex;
                height: 100vh;
                overflow: hidden;
            }}
            
            .sidebar {{
                width: 280px;
                background: #f8f9fa;
                border-right: 2px solid #dee2e6;
                overflow-y: auto;
                transition: margin-left 0.3s ease;
                position: relative;
            }}
            
            .sidebar.collapsed {{
                margin-left: -280px;
            }}
            
            .sidebar-toggle {{
                position: absolute;
                right: -30px;
                top: 10px;
                background: #3498db;
                color: white;
                border: none;
                padding: 8px 10px;
                cursor: pointer;
                border-radius: 0 4px 4px 0;
                font-size: 16px;
                z-index: 100;
            }}
            
            .sidebar-toggle:hover {{
                background: #2980b9;
            }}
            
            .sidebar-content {{
                padding: 15px;
            }}
            
            .main-content {{
                flex: 1;
                overflow-y: auto;
                padding: 20px;
            }}
            
            .summary {{
                background: white;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            
            .summary h2 {{
                margin: 0 0 10px 0;
                font-size: 16px;
                color: #2c3e50;
            }}
            
            .metrics {{
                display: flex;
                flex-direction: column;
                gap: 8px;
            }}
            
            .metric {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 5px 0;
                border-bottom: 1px solid #ecf0f1;
            }}
            
            .metric:last-child {{
                border-bottom: none;
            }}
            
            .metric-label {{
                font-size: 13px;
                color: #7f8c8d;
            }}
            
            .metric-value {{
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
            }}
            
            .filters {{
                background: white;
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            
            .filters h2 {{
                margin: 0 0 15px 0;
                font-size: 16px;
                color: #2c3e50;
            }}
        </style>
    </head>
    <body>
        <div class="layout-container">
            <div class="sidebar" id="sidebar">
                <button class="sidebar-toggle" onclick="toggleSidebar()">◀</button>
                <div class="sidebar-content">
                    <div class="summary">
            <h2>Summary Statistics</h2>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-label">Total Blocks</div>
                    <div class="metric-value">{len(df)}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Changed</div>
                    <div class="metric-value">{len(df[df["Status"] == "changed"])}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Added</div>
                    <div class="metric-value">{len(df[df["Status"] == "added"])}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Removed</div>
                    <div class="metric-value">{len(df[df["Status"] == "removed"])}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Unchanged</div>
                    <div class="metric-value">{len(df[df["Status"] == "unchanged"])}</div>
                </div>
            </div>
                    </div>
                    
                    <div class="filters">
                        <h2>🔍 Filters</h2>
                        
                        <!-- Search Box -->
                        <div class="filter-group">
                            <label>Search:</label>
                            <input type="text" id="search-box" placeholder="Search blocks, designers, changes..." 
                                   oninput="applyFilters()" style="width: 100%; padding: 8px; border: 1px solid #bdc3c7; border-radius: 4px; font-size: 13px;">
                            <div style="font-size: 11px; color: #7f8c8d; margin-top: 4px;">
                                Searches: Block ID, Designer, Change Types, Description
                            </div>
                        </div>
                        
                        <!-- Quick Presets -->
                        <div class="filter-group">
                            <label>Quick Filters:</label>
                            <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 6px;">
                                <button class="preset-btn" onclick="applyPreset('allchanges')" title="Show added, changed, and removed blocks (excludes unchanged)">🔄 All Changes</button>
                                <button class="preset-btn" onclick="applyPreset('changedonly')" title="Show only modified blocks">📝 Changed Only</button>
                                <button class="preset-btn" onclick="applyPreset('additions')" title="Show only new blocks">➕ Additions</button>
                                <button class="preset-btn" onclick="applyPreset('removals')" title="Show only removed blocks">➖ Removed</button>
                            </div>
                        </div>
                        
                        <!-- Active Filters Summary -->
                        <div id="active-filters" style="margin: 10px 0; padding: 8px; background: #e8f4fd; border-radius: 4px; font-size: 12px; display: none;">
                            <strong>Active:</strong> <span id="active-filters-text"></span>
                        </div>
                        
                        <div class="filter-group">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                                <label>Status:</label>
                                <div style="display: flex; gap: 4px;">
                                    <button class="toggle-btn" onclick="toggleAll('status', true)" title="Select all">All</button>
                                    <button class="toggle-btn" onclick="toggleAll('status', false)" title="Deselect all">None</button>
                                </div>
                            </div>
                            <div class="button-group" id="status-buttons">
                                {chr(10).join(f'<button class="filter-button status-btn" data-filter="status" data-value="{status}" onclick="toggleButton(this)"><span class="btn-text">{status.capitalize()}</span> <span class="btn-count" data-status="{status}">0</span></button>' for status in ['added', 'changed', 'removed', 'unchanged'])}
                            </div>
                        </div>
                        
                        <div class="filter-group">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                                <label>Designer:</label>
                                <div style="display: flex; gap: 4px;">
                                    <button class="toggle-btn" onclick="toggleAll('designer', true)">All</button>
                                    <button class="toggle-btn" onclick="toggleAll('designer', false)">None</button>
                                </div>
                            </div>
                            <div class="button-group" id="designer-buttons">
                                {chr(10).join(f'<button class="filter-button designer-btn" data-filter="designer" data-value="{designer}" onclick="toggleButton(this)"><span class="btn-text">{designer}</span> <span class="btn-count" data-designer="{designer}">0</span></button>' for designer in sorted(df_filtered["Designer"].unique().tolist()))}
                            </div>
                        </div>
                        
                        {'<div class="filter-group">\n                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">\n                                <label>Change Types:</label>\n                                <div style="display: flex; gap: 4px;">\n                                    <button class="toggle-btn" onclick="toggleAll(\'changetype\', true)">All</button>\n                                    <button class="toggle-btn" onclick="toggleAll(\'changetype\', false)">None</button>\n                                </div>\n                            </div>\n                            <div class="button-group" id="changetype-buttons">\n                                ' + chr(10).join(f'<button class="filter-button changetype-btn" data-filter="changetype" data-value="{ct}" onclick="toggleButton(this)"><span class="btn-text">{ct}</span> <span class="btn-count" data-changetype="{ct}">0</span></button>' for ct in change_types_list) + '\n                            </div>\n                        </div>' if change_types_list else ''}
                        
                        <div class="filter-buttons">
                            <button onclick="resetFilters()">Reset All</button>
                        </div>
                        
                        <div style="margin-top: 10px; color: #666; font-size: 12px; font-weight: 600;">
                            Showing: <span id="row-count">{len(df)}</span> / <span id="total-count">{len(df)}</span> blocks
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="main-content">
                <h1>📊 Timeline Diff Report</h1>
                
                <table id="blocks-table">
            <thead>
                <tr>
                    <th>Status</th>
                    <th>Block ID</th>
                    <th>Designer</th>
                    <th>Start</th>
                    <th>Duration (min)</th>
                    <th>Change Types</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody id="table-body">
            </tbody>
        </table>
        
        <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-xml.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/line-numbers/prism-line-numbers.min.js"></script>
        
        <script>
            const allRows = {rows_json};
            const statusCounts = {status_counts_json};
            const designerCounts = {designer_counts_json};
            const changetypeCounts = {changetype_counts_json};
            
            function escapeHtml(text) {{
                if (typeof text !== 'string') return text;
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }}
            
            function renderTable(rowsToShow) {{
                const tbody = document.getElementById('table-body');
                tbody.innerHTML = '';
                
                rowsToShow.forEach((row, idx) => {{
                    // Main row
                    const tr = document.createElement('tr');
                    tr.className = 'status-' + row.Status;
                    tr.id = 'row-' + idx;
                    
                    const statusBadge = '<span class="status-badge ' + row.Status + '">' + row.Status.toUpperCase() + '</span>';
                    const durationDisplay = row.Duration !== null && row.Duration !== undefined ? parseFloat(row.Duration).toFixed(1) : 'N/A';
                    
                    tr.innerHTML = `
                        <td>${{statusBadge}}</td>
                        <td><strong>${{row['Block ID']}}</strong></td>
                        <td>${{row.Designer}}</td>
                        <td style="font-size: 0.9em;">${{row.Start}}</td>
                        <td>${{durationDisplay}}</td>
                        <td style="font-size: 0.85em;">${{row['Change Types']}}</td>
                        <td style="text-align: center;">
                            <button class="expand-btn" onclick="toggleDetail(${{idx}}, this)">📄 Details</button>
                        </td>
                    `;
                    
                    tbody.appendChild(tr);
                    
                    // Detail row
                    const detailTr = document.createElement('tr');
                    detailTr.className = 'detail-row';
                    detailTr.id = 'detail-' + idx;
                    
                    let detailContent = '<div class="detail-content">';
                    
                    // Show diff only for changed blocks (use pre-generated diff HTML)
                    if (row['Diff HTML']) {{
                        detailContent += '<div style="margin-bottom: 20px;"><h3 style="margin-top: 0;">🔀 XML Diff</h3>';
                        detailContent += row['Diff HTML'];
                        detailContent += '</div>';
                    }}
                    
                    // Show XML panels
                    detailContent += '<div><h3>📄 Full XML</h3>';
                    detailContent += '<div class="xml-panels">';
                    
                    if (row['Current XML'] !== 'N/A') {{
                        detailContent += '<div class="xml-panel">';
                        detailContent += '<strong>Current Block XML</strong>';
                        detailContent += '<pre><code class="language-xml">' + escapeHtml(row['Current XML']) + '</code></pre>';
                        detailContent += '</div>';
                    }}
                    
                    if (row['Incoming XML'] !== 'N/A') {{
                        detailContent += '<div class="xml-panel">';
                        detailContent += '<strong>' + (row.Status === 'added' ? 'Block XML' : 'Incoming Block XML') + '</strong>';
                        detailContent += '<pre><code class="language-xml">' + escapeHtml(row['Incoming XML']) + '</code></pre>';
                        detailContent += '</div>';
                    }}
                    
                    detailContent += '</div></div></div>';
                    
                    detailTr.innerHTML = `<td colspan="7" style="padding: 0; background: #f9f9f9;">${{detailContent}}</td>`;
                    tbody.appendChild(detailTr);
                }});
                
                // Syntax highlight
                if (window.Prism) {{
                    Prism.highlightAllUnder(tbody);
                }}
            }}
            
            function toggleDetail(idx, btn) {{
                const detail = document.getElementById('detail-' + idx);
                if (detail.classList.contains('show')) {{
                    detail.classList.remove('show');
                    btn.textContent = '📄 Details';
                }} else {{
                    detail.classList.add('show');
                    btn.textContent = '📄 Hide';
                }}
            }}
            
            function toggleButton(btn) {{
                btn.classList.toggle('active');
                applyFilters();
            }}
            
            function applyFilters() {{
                // Get search text
                const searchText = document.getElementById('search-box').value.toLowerCase();
                
                // Get selected status filters
                const statusButtons = Array.from(document.querySelectorAll('.status-btn.active')).map(b => b.getAttribute('data-value'));
                
                // Get selected designer filters
                const designerButtons = Array.from(document.querySelectorAll('.designer-btn.active')).map(b => b.getAttribute('data-value'));
                
                // Get selected change type filters
                const changetypeButtons = Array.from(document.querySelectorAll('.changetype-btn.active')).map(b => b.getAttribute('data-value'));
                
                let filtered = allRows;
                
                // Apply search filter
                if (searchText) {{
                    filtered = filtered.filter(r => {{
                        const searchableText = [
                            r['Block ID'],
                            r.Designer,
                            r['Change Types'],
                            r.Description
                        ].join(' ').toLowerCase();
                        return searchableText.includes(searchText);
                    }});
                }}
                
                // Apply status filter - only if some buttons exist
                const allStatusButtons = document.querySelectorAll('.status-btn');
                if (allStatusButtons.length > 0) {{
                    if (statusButtons.length === 0) {{
                        filtered = [];
                    }} else {{
                        filtered = filtered.filter(r => statusButtons.includes(r.Status));
                    }}
                }}
                
                // Apply designer filter
                const allDesignerButtons = document.querySelectorAll('.designer-btn');
                if (allDesignerButtons.length > 0 && designerButtons.length > 0) {{
                    filtered = filtered.filter(r => designerButtons.includes(r.Designer));
                }} else if (allDesignerButtons.length > 0 && designerButtons.length === 0) {{
                    filtered = [];
                }}
                
                // Apply change type filter
                const allChangetypeButtons = document.querySelectorAll('.changetype-btn');
                if (allChangetypeButtons.length > 0 && changetypeButtons.length > 0) {{
                    filtered = filtered.filter(r => {{
                        if (r['Change Types'] === 'N/A' || r['Change Types'] === '') {{
                            return true;
                        }}
                        const changeTypes = r['Change Types'].split(',').map(ct => ct.trim());
                        return changetypeButtons.some(ct => changeTypes.includes(ct));
                    }});
                }} else if (allChangetypeButtons.length > 0 && changetypeButtons.length === 0) {{
                    filtered = filtered.filter(r => r['Change Types'] === 'N/A' || r['Change Types'] === '');
                }}
                
                renderTable(filtered);
                updateCounts(filtered);
                updateActiveFilters(searchText, statusButtons, designerButtons, changetypeButtons);
            }}
            
            function updateCounts(filteredRows) {{
                document.getElementById('row-count').textContent = filteredRows.length;
                document.getElementById('total-count').textContent = allRows.length;
                
                // Update button counts
                document.querySelectorAll('.btn-count').forEach(span => {{
                    const status = span.getAttribute('data-status');
                    const designer = span.getAttribute('data-designer');
                    const changetype = span.getAttribute('data-changetype');
                    
                    if (status) {{
                        const count = filteredRows.filter(r => r.Status === status).length;
                        span.textContent = count;
                    }} else if (designer) {{
                        const count = filteredRows.filter(r => r.Designer === designer).length;
                        span.textContent = count;
                    }} else if (changetype) {{
                        const count = filteredRows.filter(r => {{
                            if (r['Change Types'] === 'N/A') return false;
                            return r['Change Types'].split(',').map(ct => ct.trim()).includes(changetype);
                        }}).length;
                        span.textContent = count;
                    }}
                }});
            }}
            
            function updateActiveFilters(searchText, statusButtons, designerButtons, changetypeButtons) {{
                const activeDiv = document.getElementById('active-filters');
                const activeText = document.getElementById('active-filters-text');
                const filters = [];
                
                if (searchText) filters.push(`Search: "${{searchText}}"`);
                if (statusButtons.length > 0 && statusButtons.length < 4) filters.push(`Status: ${{statusButtons.join(', ')}}`);
                if (designerButtons.length > 0) {{
                    const total = document.querySelectorAll('.designer-btn').length;
                    if (designerButtons.length < total) filters.push(`Designers: ${{designerButtons.length}}/${{total}}`);
                }}
                if (changetypeButtons.length > 0) {{
                    const total = document.querySelectorAll('.changetype-btn').length;
                    if (changetypeButtons.length < total) filters.push(`Changes: ${{changetypeButtons.length}}/${{total}}`);
                }}
                
                if (filters.length > 0) {{
                    activeText.textContent = filters.join(' | ');
                    activeDiv.style.display = 'block';
                }} else {{
                    activeDiv.style.display = 'none';
                }}
            }}
            
            function toggleAll(filterType, activate) {{
                const selector = `.${{filterType}}-btn`;
                document.querySelectorAll(selector).forEach(btn => {{
                    if (activate) {{
                        btn.classList.add('active');
                    }} else {{
                        btn.classList.remove('active');
                    }}
                }});
                applyFilters();
            }}
            
            function applyPreset(preset) {{
                // Clear search
                document.getElementById('search-box').value = '';
                
                if (preset === 'allchanges') {{
                    // Show changed, added, removed (exclude unchanged)
                    document.querySelectorAll('.status-btn').forEach(btn => {{
                        const value = btn.getAttribute('data-value');
                        if (['changed', 'added', 'removed'].includes(value)) {{
                            btn.classList.add('active');
                        }} else {{
                            btn.classList.remove('active');
                        }}
                    }});
                }} else if (preset === 'changedonly') {{
                    // Show only changed blocks
                    document.querySelectorAll('.status-btn').forEach(btn => {{
                        const value = btn.getAttribute('data-value');
                        if (value === 'changed') {{
                            btn.classList.add('active');
                        }} else {{
                            btn.classList.remove('active');
                        }}
                    }});
                }} else if (preset === 'additions') {{
                    // Show only added
                    document.querySelectorAll('.status-btn').forEach(btn => {{
                        const value = btn.getAttribute('data-value');
                        if (value === 'added') {{
                            btn.classList.add('active');
                        }} else {{
                            btn.classList.remove('active');
                        }}
                    }});
                }} else if (preset === 'removals') {{
                    // Show only removed
                    document.querySelectorAll('.status-btn').forEach(btn => {{
                        const value = btn.getAttribute('data-value');
                        if (value === 'removed') {{
                            btn.classList.add('active');
                        }} else {{
                            btn.classList.remove('active');
                        }}
                    }});
                }}
                
                // Activate all designers and change types
                toggleAll('designer', true);
                toggleAll('changetype', true);
                
                applyFilters();
            }}
            
            function resetFilters() {{
                // Clear search
                document.getElementById('search-box').value = '';
                
                // Activate all buttons except unchanged
                document.querySelectorAll('.filter-button').forEach(btn => {{
                    if (btn.classList.contains('status-btn') && btn.getAttribute('data-value') === 'unchanged') {{
                        btn.classList.remove('active');
                    }} else {{
                        btn.classList.add('active');
                    }}
                }});
                applyFilters();
            }}
            
            function initializeFilters() {{
                // Pre-select all buttons except unchanged at load time
                document.querySelectorAll('.filter-button').forEach(btn => {{
                    if (btn.classList.contains('status-btn') && btn.getAttribute('data-value') === 'unchanged') {{
                        btn.classList.remove('active');
                    }} else {{
                        btn.classList.add('active');
                    }}
                }});
                
                // Apply the filters
                applyFilters();
            }}
            
            function toggleSidebar() {{
                const sidebar = document.getElementById('sidebar');
                const toggle = document.querySelector('.sidebar-toggle');
                sidebar.classList.toggle('collapsed');
                if (sidebar.classList.contains('collapsed')) {{
                    toggle.textContent = '▶';
                }} else {{
                    toggle.textContent = '◀';
                }}
            }}
            
            // Initialize filters and render on page load
            window.addEventListener('load', initializeFilters);
        </script>
            </div>
        </div>
    </body>
    </html>
    """

    # Save to file if output_file is provided
    if output_file is not None:
        output_path = Path(output_file).resolve()  # Convert to absolute path
        output_path.write_text(html)
        print(f"HTML diff report saved to {output_path}")
        
        # Open in browser if requested
        if open:
            print(f"Opening HTML diff report in browser: {output_path}")
            webbrowser.open(output_path.as_uri())
    
    # Open in browser using temporary file if requested and no output_file
    elif open:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(html)
            tmp_path = Path(tmp.name)
        
        print(f"Opening HTML diff report in browser: {tmp_path}")
        webbrowser.open(tmp_path.as_uri())

    return html
