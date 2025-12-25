"""HTML representation utilities for AGM configuration."""

from __future__ import annotations

import random

import pandas as pd


def get_css_styles() -> str:
    """Get CSS styles for HTML display."""
    return """
    <style>
        .agm-config-container {
            font-size: 0.9em;
            margin: 8px 0;
        }
        .agm-config-section {
            margin-bottom: 12px;
            max-height: 400px;
            overflow-y: auto;
        }
        .agm-config-section.hidden {
            display: none;
        }
        .agm-config-title {
            font-weight: 600;
            margin-bottom: 4px;
            font-size: 1em;
        }
        .agm-config-table {
            border-collapse: collapse;
            width: 100%;
            font-size: 0.9em;
        }
        .agm-config-table th {
            text-align: left;
            padding: 4px 8px;
            border-bottom: 1px solid var(--jp-border-color2, #e0e0e0);
            font-weight: 600;
            font-size: 0.9em;
        }
        .agm-config-table td {
            text-align: left;
            padding: 3px 8px;
            border-bottom: 1px solid var(--jp-border-color3, #f0f0f0);
        }
        .agm-config-table tr:last-child td {
            border-bottom: none;
        }
        .agm-config-meta {
            display: inline;
            margin-right: 16px;
            font-size: 0.9em;
        }
        .agm-config-meta-label {
            font-weight: 600;
            margin-right: 4px;
        }
        .agm-config-filter {
            margin-bottom: 12px;
            display: flex;
            gap: 8px;
            align-items: center;
        }
        .agm-config-filter-label {
            font-weight: 600;
            font-size: 0.9em;
        }
        .agm-config-filter-btn {
            padding: 4px 12px;
            border: 1px solid var(--jp-border-color2, #e0e0e0);
            background: transparent;
            color: inherit;
            cursor: pointer;
            border-radius: 3px;
            font-size: 0.9em;
            transition: all 0.2s;
        }
        .agm-config-filter-btn:hover {
            border-color: var(--jp-brand-color1, #2196F3);
            background: var(--jp-layout-color1, transparent);
        }
        .agm-config-filter-btn.active {
            border-color: var(--jp-brand-color1, #2196F3);
            font-weight: 600;
            background: var(--jp-layout-color1, transparent);
            color: var(--jp-ui-font-color1, inherit);
        }
        .agm-config-search {
            margin-left: auto;
            display: flex;
            gap: 8px;
            align-items: center;
        }
        .agm-config-search-input {
            padding: 4px 8px;
            border: 1px solid var(--jp-border-color2, #e0e0e0);
            border-radius: 3px;
            font-size: 0.9em;
            background: transparent;
            color: inherit;
            min-width: 200px;
        }
        .agm-config-sources {
            margin-bottom: 12px;
            color: inherit;
        }
        .agm-config-sources-header {
            display: flex;
            align-items: center;
            gap: 4px;
            cursor: pointer;
            font-size: 0.85em;
            color: inherit;
            user-select: none;
        }
        .agm-config-sources-header:hover {
            color: inherit;
        }
        .agm-config-sources-toggle {
            font-size: 0.7em;
            transition: transform 0.2s;
            color: inherit;
        }
        .agm-config-sources-toggle.expanded {
            transform: rotate(90deg);
        }
        .agm-config-sources-content {
            display: none;
            padding: 8px 0 8px 16px;
            font-size: 0.85em;
            color: inherit;
        }
        .agm-config-sources-content.expanded {
            display: block;
        }
        .agm-config-source-item {
            margin-bottom: 4px;
            color: inherit;
        }
        .agm-config-source-label {
            color: inherit;
            margin-right: 4px;
        }
        .agm-config-source-link {
            color: inherit;
            text-decoration: none;
            word-break: break-all;
        }
        .agm-config-source-link:hover {
            text-decoration: underline;
        }
    </style>
    """


def build_summary_header(
    objects_count: int,
    frames_count: int,
    directions_count: int,
    surfaces_count: int,
) -> str:
    """Build summary header with counts."""
    return (
        '<div class="agm-config-section">'
        f'<span class="agm-config-meta">'
        f'<span class="agm-config-meta-label">Objects:</span>'
        f"{objects_count}"
        f"</span>"
        f'<span class="agm-config-meta">'
        f'<span class="agm-config-meta-label">Frames:</span>'
        f"{frames_count}"
        f"</span>"
        f'<span class="agm-config-meta">'
        f'<span class="agm-config-meta-label">Directions:</span>'
        f"{directions_count}"
        f"</span>"
        f'<span class="agm-config-meta">'
        f'<span class="agm-config-meta-label">Surfaces:</span>'
        f"{surfaces_count}"
        f"</span>"
        "</div>"
    )


def build_filter_controls(
    widget_id: str,
    objects_count: int,
    frames_count: int,
    directions_count: int,
    surfaces_count: int,
) -> str:
    """Build filter control buttons."""
    return (
        '<div class="agm-config-filter">'
        '<span class="agm-config-filter-label">Show:</span>'
        f'<button class="agm-config-filter-btn" '
        f'onclick="filterAGM(\'{widget_id}\', \'objects\')" '
        f'id="{widget_id}-btn-objects">Objects ({objects_count})</button>'
        f'<button class="agm-config-filter-btn" '
        f'onclick="filterAGM(\'{widget_id}\', \'frames\')" '
        f'id="{widget_id}-btn-frames">Frames ({frames_count})</button>'
        f'<button class="agm-config-filter-btn active" '
        f'onclick="filterAGM(\'{widget_id}\', \'directions\')" '
        f'id="{widget_id}-btn-directions">'
        f"Directions ({directions_count})</button>"
        f'<button class="agm-config-filter-btn" '
        f'onclick="filterAGM(\'{widget_id}\', \'surfaces\')" '
        f'id="{widget_id}-btn-surfaces">Surfaces ({surfaces_count})</button>'
        '<div class="agm-config-search">'
        '<span class="agm-config-filter-label">Search:</span>'
        f'<input type="text" class="agm-config-search-input" '
        f'placeholder="Filter by name..." '
        f'oninput="searchAGM(\'{widget_id}\', this.value)" />'
        "</div>"
        "</div>"
    )


def build_filter_script(widget_id: str) -> str:
    """Build JavaScript for filtering functionality."""
    return f"""
    <script>
    (function() {{
        // Define functions first
        window.filterAGM = function(widgetId, type) {{
            // Hide all sections
            const sections = ['objects', 'frames', 'directions', 'surfaces'];
            sections.forEach(sec => {{
                const el = document.getElementById(widgetId + '-' + sec);
                if (el) {{
                    el.classList.add('hidden');
                }}
                const btn = document.getElementById(widgetId + '-btn-' + sec);
                if (btn) {{
                    btn.classList.remove('active');
                }}
            }});
            
            // Show selected section
            const selected = document.getElementById(widgetId + '-' + type);
            if (selected) {{
                selected.classList.remove('hidden');
            }}
            const activeBtn = document.getElementById(widgetId + '-btn-' + type);
            if (activeBtn) {{
                activeBtn.classList.add('active');
            }}
        }};
        
        window.searchAGM = function(widgetId, query) {{
            const lowerQuery = query.toLowerCase();
            const container = document.getElementById(widgetId);
            if (!container) return;
            
            const tables = container.querySelectorAll('.agm-config-table tbody');
            tables.forEach(tbody => {{
                const rows = tbody.querySelectorAll('tr');
                rows.forEach(row => {{
                    const text = row.textContent.toLowerCase();
                    if (text.includes(lowerQuery)) {{
                        row.style.display = '';
                    }} else {{
                        row.style.display = 'none';
                    }}
                }});
            }});
        }};
        
        // Initialize after a short delay to ensure DOM is ready
        setTimeout(function() {{
            filterAGM('{widget_id}', 'directions');
        }}, 10);
    }})();
    </script>
    """


def build_objects_table(
    objects_data: list[dict],
    section_id: str = "objects",
    *,
    hidden: bool = False,
) -> str:
    """Build HTML table for objects."""
    rows = "".join(
        f"<tr>"
        f"<td>{obj['name']}</td>"
        f"<td>{obj['mnemonic']}</td>"
        f"<td>{obj['spice_name']}</td>"
        f"<td>{obj['is_body']}</td>"
        f"<td>{obj['gravity']}</td>"
        f"</tr>"
        for obj in objects_data
    )
    hidden_class = " hidden" if hidden else ""
    return (
        f'<div class="agm-config-section{hidden_class}" id="{section_id}">'
        '<div class="agm-config-title">Objects</div>'
        '<table class="agm-config-table">'
        "<thead><tr>"
        "<th>Name</th><th>Mnemonic</th><th>SPICE Name</th>"
        "<th>Body</th><th>Gravity</th>"
        "</tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table>"
        "</div>"
    )


def build_frames_table(
    frames_data: list[dict],
    section_id: str = "frames",
    *,
    hidden: bool = False,
) -> str:
    """Build HTML table for frames."""
    rows = "".join(
        f"<tr>"
        f"<td>{frame['name']}</td>"
        f"<td>{frame['mnemonic']}</td>"
        f"<td>{frame['spice_name']}</td>"
        f"<td>{frame['is_ref']}</td>"
        f"</tr>"
        for frame in frames_data
    )
    hidden_class = " hidden" if hidden else ""
    return (
        f'<div class="agm-config-section{hidden_class}" id="{section_id}">'
        '<div class="agm-config-title">Frames</div>'
        '<table class="agm-config-table">'
        "<thead><tr>"
        "<th>Name</th><th>Mnemonic</th><th>SPICE Name</th>"
        "<th>Ref Frame</th>"
        "</tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table>"
        "</div>"
    )


def build_directions_table(
    directions_data: list[dict],
    section_id: str = "directions",
    *,
    hidden: bool = False,
) -> str:
    """Build HTML table for directions."""
    rows = "".join(
        f"<tr><td>{direction['name']}</td>"
        f"<td>{direction['type']}</td>"
        f"<td>{direction.get('definition', '')}</td></tr>"
        for direction in directions_data
    )
    hidden_class = " hidden" if hidden else ""
    return (
        f'<div class="agm-config-section{hidden_class}" id="{section_id}">'
        '<div class="agm-config-title">Directions</div>'
        '<table class="agm-config-table">'
        "<thead><tr><th>Name</th><th>Type</th><th>Definition</th></tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table>"
        "</div>"
    )


def build_surfaces_table(
    surfaces_data: list[dict],
    section_id: str = "surfaces",
    *,
    hidden: bool = False,
) -> str:
    """Build HTML table for surfaces."""
    rows = "".join(
        f"<tr><td>{surface['name']}</td>"
        f"<td>{surface['type']}</td></tr>"
        for surface in surfaces_data
    )
    hidden_class = " hidden" if hidden else ""
    return (
        f'<div class="agm-config-section{hidden_class}" id="{section_id}">'
        '<div class="agm-config-title">Surfaces</div>'
        '<table class="agm-config-table">'
        "<thead><tr><th>Name</th><th>Type</th></tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table>"
        "</div>"
    )


def generate_widget_id() -> str:
    """Generate a unique widget ID for this instance."""
    return f"agm_{random.randint(1000, 9999)}"


def build_sources_dropdown(
    widget_id: str,
    sources: list[tuple[str, str]],
) -> str:
    """Build a collapsible dropdown showing source file links.

    Args:
        widget_id: Unique widget identifier for this instance.
        sources: List of (label, file_path) tuples for source files.

    Returns:
        HTML string for the sources dropdown.
    """
    if not sources:
        return ""

    source_items = []
    for label, file_path in sources:
        # Create a file:// URL for the path
        file_url = f"file://{file_path}"
        source_items.append(
            f'<div class="agm-config-source-item">'
            f'<span class="agm-config-source-label">{label}:</span>'
            f'<a class="agm-config-source-link" href="{file_url}" '
            f'title="{file_path}">{file_path}</a>'
            f"</div>"
        )

    items_html = "".join(source_items)

    return (
        f'<div class="agm-config-sources">'
        f'<div class="agm-config-sources-header" '
        f'onclick="toggleAGMSources(\'{widget_id}\')">'
        f'<span class="agm-config-sources-toggle" id="{widget_id}-sources-toggle">▶</span>'
        f"<span>Sources ({len(sources)} files)</span>"
        f"</div>"
        f'<div class="agm-config-sources-content" id="{widget_id}-sources-content">'
        f"{items_html}"
        f"</div>"
        f"</div>"
    )


def build_sources_script() -> str:
    """Build JavaScript for sources toggle functionality."""
    return """
    <script>
    (function() {
        window.toggleAGMSources = function(widgetId) {
            const toggle = document.getElementById(widgetId + '-sources-toggle');
            const content = document.getElementById(widgetId + '-sources-content');
            if (toggle && content) {
                toggle.classList.toggle('expanded');
                content.classList.toggle('expanded');
            }
        };
    })();
    </script>
    """


def repr_html(obj) -> str:
    """
    Generate HTML representation for Jupyter notebooks with theme-neutral styling.

    Returns a compact table view of AGM configuration including objects, frames,
    directions, and surfaces with interactive filtering.
    """
    from pathlib import Path

    # Collect data for tables
    objects_data = _collect_objects_data(obj)
    frames_data = _collect_frames_data(obj)
    directions_data = _collect_directions_data(obj)
    surfaces_data = _collect_surfaces_data(obj)

    # Collect source file paths
    sources = []
    if hasattr(obj, "cfg_file") and obj.cfg_file:
        sources.append(("Config", str(Path(obj.cfg_file).resolve())))
    if hasattr(obj, "fixed_definition_file") and obj.fixed_definition_file:
        sources.append(("Definitions", str(Path(obj.fixed_definition_file).resolve())))

    # Generate unique ID for this instance to avoid conflicts
    widget_id = generate_widget_id()

    # Build HTML
    html_parts = [get_css_styles()]
    html_parts.append(build_sources_script())
    html_parts.append(f'<div class="agm-config-container" id="{widget_id}">')

    # Sources dropdown (compact, at the top)
    if sources:
        html_parts.append(build_sources_dropdown(widget_id, sources))

    # Header with summary counts
    # html_parts.append(
    #     build_summary_header(
    #         len(objects_data),
    #         len(frames_data),
    #         len(directions_data),
    #         len(surfaces_data),
    #     ),
    # )

    # Filter controls
    html_parts.append(
        build_filter_controls(
            widget_id,
            len(objects_data),
            len(frames_data),
            len(directions_data),
            len(surfaces_data),
        ),
    )

    # Add tables for each section
    if objects_data:
        html_parts.append(
            build_objects_table(
                objects_data, section_id=f"{widget_id}-objects", hidden=True
            ),
        )
    if frames_data:
        html_parts.append(
            build_frames_table(
                frames_data, section_id=f"{widget_id}-frames", hidden=True
            ),
        )
    if directions_data:
        html_parts.append(
            build_directions_table(
                directions_data, section_id=f"{widget_id}-directions", hidden=False
            ),
        )
    if surfaces_data:
        html_parts.append(
            build_surfaces_table(
                surfaces_data, section_id=f"{widget_id}-surfaces", hidden=True
            ),
        )

    # Add JavaScript for filtering
    html_parts.append(build_filter_script(widget_id))

    html_parts.append("</div>")

    return "".join(html_parts)

def _collect_objects_data(obj) -> list[dict]:
    """Collect object data for HTML display."""
    df = obj.as_pandas_objects()
    if df.empty:
        return []
    
    # Format for HTML display
    df_display = df[["name", "mnemonic", "spice_name"]].copy()
    df_display["is_body"] = df["is_body"].apply(lambda x: "✓" if x else "")
    df_display["gravity"] = df["gravity"].apply(
        lambda x: f"{x:.2e}" if pd.notna(x) else ""
    )
    
    return df_display.to_dict("records")

def _collect_frames_data(obj) -> list[dict]:
    """Collect frame data for HTML display."""
    df = obj.as_pandas_frames()
    if df.empty:
        return []
    
    # Format for HTML display
    df_display = df[["name", "mnemonic", "spice_name"]].copy()
    df_display["is_ref"] = df["is_reference_frame"].apply(
        lambda x: "✓" if x else ""
    )
    
    return df_display.to_dict("records")

def _collect_directions_data(obj) -> list[dict]:
    """Collect direction data for HTML display."""
    data = []
    for vec in obj.definitions.dir_vectors:
        data.append({
            "name": vec.name,
            "type": vec.__class__.__name__,
            "definition": str(vec),
        })
    return data

def _collect_surfaces_data(obj) -> list[dict]:
    """Collect surface data for HTML display."""
    df = obj.as_pandas_surfaces()
    if df.empty:
        return []

    return df[["name", "type"]].to_dict("records")