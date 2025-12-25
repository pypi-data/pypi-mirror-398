import json
import uuid

from .file_info import VersionedFileInfo
from .manager import VersionedFileManager


def repr_html_manager(self: VersionedFileManager) -> str:
    """
    HTML representation for Jupyter notebooks.

    Returns:
        HTML string with summary and latest versions highlighted
    """
    # Generate unique ID for this instance to avoid conflicts

    instance_id = str(uuid.uuid4())[:8]

    # Build searchable file list (JSON)
    file_list = [
        {
            "filename": f.filename,
            "instrument": f.instrument,
            "scenario": f.scenario,
            "version": (
                "SXXPYY"
                if f.is_sxxpyy_copy
                else f"S{f.soc_version:02d}P{f.pi_version:02d}"
            ),
            "path": str(f.path),
            "uri": f.path.as_uri(),
        }
        for f in self.files
    ]
    file_list_json = json.dumps(file_list)

    html = f"""
    <div style="border: 1px solid var(--jp-border-color2, #e0e0e0); border-radius: 4px; padding: 12px; margin: 8px 0; font-size: 0.9em;">
        <div style="margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid var(--jp-border-color2, #e0e0e0);">
            <strong style="font-size: 1.1em;">📁 Versioned File Manager</strong>
        </div>

        <!-- Search Area -->
        <div style="margin-bottom: 16px;">
            <div style="position: relative;">
                <input
                    type="text"
                    id="search-input-{instance_id}"
                    placeholder="🔍 Search files by name, instrument, or version..."
                    style="width: 100%; padding: 8px 12px; border: 1px solid var(--jp-border-color2, #e0e0e0); border-radius: 4px; font-size: 0.9em; font-family: inherit; background: var(--jp-layout-color1, white); color: var(--jp-ui-font-color1, #333);"
                />
            </div>
            <div
                id="search-results-{instance_id}"
                style="display: none; margin-top: 8px; max-height: 300px; overflow-y: auto; border: 1px solid var(--jp-border-color2, #e0e0e0); border-radius: 4px; background: var(--jp-layout-color1, white);">
            </div>
        </div>

        <script>
        (function() {{
            const files = {file_list_json};
            const searchInput = document.getElementById('search-input-{instance_id}');
            const searchResults = document.getElementById('search-results-{instance_id}');

            function wildcardToRegex(pattern) {{
                // Escape special regex characters except *
                const escaped = pattern.replace(/[.+?^${{}}()|[\\]\\\\]/g, '\\$&');
                // Replace * with .*
                return escaped.replace(/\\*/g, '.*');
            }}

            function matchesPattern(text, pattern) {{
                const regexPattern = wildcardToRegex(pattern);
                const regex = new RegExp(regexPattern, 'i');
                return regex.test(text);
            }}

            function highlightMatch(text, query) {{
                if (!query) return text;
                // Check if query contains wildcards
                if (query.includes('*')) {{
                    const regexPattern = wildcardToRegex(query);
                    const regex = new RegExp(`(${{regexPattern}})`, 'gi');
                    return text.replace(regex, '<mark style="background-color: var(--jp-search-selected-match-background-color, #ffeb3b); color: var(--jp-search-selected-match-color, #000); padding: 0 2px; border-radius: 2px;">$1</mark>');
                }} else {{
                    const regex = new RegExp(`(${{query}})`, 'gi');
                    return text.replace(regex, '<mark style="background-color: var(--jp-search-selected-match-background-color, #ffeb3b); color: var(--jp-search-selected-match-color, #000); padding: 0 2px; border-radius: 2px;">$1</mark>');
                }}
            }}

            function performSearch() {{
                const query = searchInput.value.trim().toLowerCase();

                if (query.length === 0) {{
                    searchResults.style.display = 'none';
                    return;
                }}

                const matches = files.filter(file => {{
                    // Support wildcard matching
                    if (query.includes('*')) {{
                        return matchesPattern(file.filename.toLowerCase(), query) ||
                                matchesPattern(file.instrument.toLowerCase(), query) ||
                                matchesPattern(file.scenario.toLowerCase(), query) ||
                                matchesPattern(file.version.toLowerCase(), query);
                    }} else {{
                        // Default substring matching
                        return file.filename.toLowerCase().includes(query) ||
                                file.instrument.toLowerCase().includes(query) ||
                                file.scenario.toLowerCase().includes(query) ||
                                file.version.toLowerCase().includes(query);
                    }}
                }});

                if (matches.length === 0) {{
                    searchResults.innerHTML = '<div style="padding: 12px; text-align: center; opacity: 0.6; color: var(--jp-ui-font-color2, #666);">No files found</div>';
                    searchResults.style.display = 'block';
                    return;
                }}

                let html = '<table style="width: 100%; border-collapse: collapse; font-size: 0.85em;">';
                html += '<tr style="border-bottom: 1px solid var(--jp-border-color2, #e0e0e0); background: var(--jp-layout-color2, #f5f5f5);"><th style="padding: 6px 8px; text-align: left; font-weight: 500; color: var(--jp-ui-font-color1, #333);">Instrument</th><th style="padding: 6px 8px; text-align: left; font-weight: 500; color: var(--jp-ui-font-color1, #333);">Version</th><th style="padding: 6px 8px; text-align: left; font-weight: 500; color: var(--jp-ui-font-color1, #333);">Filename</th></tr>';

                matches.forEach(file => {{
                    html += '<tr style="border-bottom: 1px solid var(--jp-border-color3, #f0f0f0); background: var(--jp-layout-color1, white);">';
                    html += `<td style="padding: 6px 8px; font-family: monospace; color: var(--jp-ui-font-color1, #333);">${{highlightMatch(file.instrument, query)}}</td>`;
                    html += `<td style="padding: 6px 8px; font-family: monospace; color: var(--jp-ui-font-color1, #333);">${{highlightMatch(file.version, query)}}</td>`;
                    html += `<td style="padding: 6px 8px; font-size: 0.9em;"><a href="${{file.uri}}" style="color: var(--jp-content-link-color, #2196f3); text-decoration: none; font-family: monospace;" title="${{file.path}}">${{highlightMatch(file.filename, query)}}</a></td>`;
                    html += '</tr>';
                }});

                html += '</table>';
                html += `<div style="padding: 8px 12px; text-align: right; background: var(--jp-layout-color2, #f5f5f5); border-top: 1px solid var(--jp-border-color2, #e0e0e0); font-size: 0.8em; opacity: 0.7; color: var(--jp-ui-font-color2, #666);">${{matches.length}} result(s)</div>`;

                searchResults.innerHTML = html;
                searchResults.style.display = 'block';
            }}

            searchInput.addEventListener('input', performSearch);
            searchInput.addEventListener('keyup', function(e) {{
                if (e.key === 'Escape') {{
                    searchInput.value = '';
                    searchResults.style.display = 'none';
                }}
            }});
        }})();
        </script>
"""

    # Summary metrics
    total_files = len(self.files)
    instruments = self.get_all_instruments()
    scenarios = self.get_all_scenarios()
    primary_scenario = self.scenario
    sxxpyy_count = sum(1 for f in self.files if f.is_sxxpyy_copy)

    html += """
        <div style="margin-bottom: 12px;">
"""

    metrics = [
        (f"{total_files} files", "📝"),
        (f"{len(instruments)} instruments", "🔭"),
        (f"{len(scenarios)} scenarios", "🔮"),
    ]

    if sxxpyy_count > 0:
        metrics.append((f"{sxxpyy_count} SXXPYY copies", "📌"))

    for text, symbol in metrics:
        html += f"""
            <span style="margin-right: 16px; white-space: nowrap;">
                <span style="margin-right: 4px;">{symbol}</span>
                <span>{text}</span>
            </span>
"""

    html += """
        </div>
"""

    # Primary scenario
    if primary_scenario:
        # Get current SOC version
        soc_file = self.get_latest_version(
            instrument="SOC",
            scenario=primary_scenario,
        )
        current_soc_version = None
        if soc_file and soc_file.soc_version is not None:
            current_soc_version = soc_file.soc_version

        soc_version_badge = ""
        if current_soc_version is not None:
            soc_version_badge = f"<span style='background-color: var(--jp-brand-color1, #2196f3); color: white; padding: 2px 8px; border-radius: 3px; font-family: monospace; font-size: 0.9em; font-weight: 500; margin-left: 8px;'>SOC S{current_soc_version:02d}</span>"

        html += f"""
        <div style="margin-bottom: 12px; font-size: 0.9em; opacity: 0.8;">
            <strong>Primary Scenario:</strong> <span style="font-family: monospace;">{primary_scenario}</span>{soc_version_badge}
        </div>
"""

    # Latest versions per instrument
    if primary_scenario:
        latest_versions = self.get_latest_per_instrument(scenario=primary_scenario)

        if latest_versions:
            html += """
        <details open style="margin-bottom: 12px;">
            <summary style="cursor: pointer; font-weight: 500; margin-bottom: 8px;">
                🔝 Latest Versions
            </summary>
            <div style="margin-left: 16px; max-height: 300px; overflow-y: auto;">
            <table style="width: 100%; border-collapse: collapse; font-size: 0.85em;">
                <tr style="border-bottom: 1px solid var(--jp-border-color2, #e0e0e0);">
                    <th style="padding: 6px 8px; text-align: left; font-weight: 500;">Instrument</th>
                    <th style="padding: 6px 8px; text-align: left; font-weight: 500;">Version</th>
                    <th style="padding: 6px 8px; text-align: left; font-weight: 500;">Filename</th>
                </tr>
"""

            for instrument in sorted(latest_versions.keys()):
                file_info = latest_versions[instrument]
                if file_info.is_sxxpyy_copy:
                    version = (
                        "<span style='opacity: 0.6; font-style: italic;'>SXXPYY</span>"
                    )
                else:
                    soc_v = file_info.soc_version
                    pi_v = file_info.pi_version
                    version = f"<strong>S{soc_v:02d}P{pi_v:02d}</strong>"

                # Create clickable filename link
                file_uri = file_info.path.as_uri()
                filename_link = f'<a href="{file_uri}" style="color: var(--jp-content-link-color, #2196f3); text-decoration: none; cursor: pointer;" title="{file_info.path}">{file_info.filename}</a>'

                html += f"""
                <tr style="border-bottom: 1px solid var(--jp-border-color3, #f0f0f0);">
                    <td style="padding: 6px 8px; text-align: left; font-family: monospace;">{instrument}</td>
                    <td style="padding: 6px 8px; text-align: left;">{version}</td>
                    <td style="padding: 6px 8px; text-align: left; font-size: 0.9em; font-family: monospace;">{filename_link}</td>
                </tr>
"""

            html += """
            </table>
            </div>
        </details>
"""

    # Files by instrument
    grouped = self.group_by_instrument()
    if grouped:
        html += """
        <details style="margin-bottom: 12px;">
            <summary style="cursor: pointer; font-weight: 500; margin-bottom: 8px;">
                📊 Files per Instrument
            </summary>
            <div style="margin-left: 16px; font-size: 0.85em; max-height: 200px; overflow-y: auto;">
"""

        for instrument in sorted(grouped.keys()):
            files = grouped[instrument]
            versions = []
            for f in files:
                if f.is_sxxpyy_copy:
                    versions.append("SXXPYY")
                else:
                    versions.append(f"S{f.soc_version:02d}P{f.pi_version:02d}")

            unique_versions = sorted({v for v in versions if v != "SXXPYY"})
            if "SXXPYY" in versions:
                unique_versions.append("SXXPYY")

            html += f"""
                <div style="margin-bottom: 6px; padding: 4px 0; border-bottom: 1px solid var(--jp-border-color3, #f0f0f0);">
                    <span style="font-family: monospace; font-weight: 500; margin-right: 8px;">{instrument}:</span>
                    <span style="opacity: 0.7;">{len(files)} files</span>
                    <span style="margin-left: 8px; opacity: 0.6; font-size: 0.9em;">({", ".join(unique_versions)})</span>
                </div>
"""

        html += """
            </div>
        </details>
"""

    # Latest PI responses to latest SOC
    if primary_scenario:
        latest_soc = self.get_latest_version(
            instrument="SOC",
            scenario=primary_scenario,
        )
        if latest_soc and latest_soc.soc_version is not None:
            pi_responses = self.get_latest_pi_versions_for_soc(
                soc_version=latest_soc.soc_version,
                scenario=primary_scenario,
            )

            if pi_responses:
                html += f"""
        <details style="margin-bottom: 12px;">
            <summary style="cursor: pointer; font-weight: 500; margin-bottom: 8px;">
                🔄 PI Responses to SOC <strong style="font-family: monospace;">S{latest_soc.soc_version:02d}</strong>
            </summary>
            <div style="margin-left: 16px; max-height: 300px; overflow-y: auto;">
            <table style="width: 100%; border-collapse: collapse; font-size: 0.85em;">
                <tr style="border-bottom: 1px solid var(--jp-border-color2, #e0e0e0);">
                    <th style="padding: 6px 8px; text-align: left; font-weight: 500;">Instrument</th>
                    <th style="padding: 6px 8px; text-align: left; font-weight: 500;">Version</th>
                    <th style="padding: 6px 8px; text-align: left; font-weight: 500;">Filename</th>
                </tr>
"""

                for instrument in sorted(pi_responses.keys()):
                    file_info = pi_responses[instrument]
                    soc_v = file_info.soc_version
                    pi_v = file_info.pi_version
                    version = f"<strong>S{soc_v:02d}P{pi_v:02d}</strong>"

                    # Create clickable filename link
                    file_uri = file_info.path.as_uri()
                    filename_link = f'<a href="{file_uri}" style="color: var(--jp-content-link-color, #2196f3); text-decoration: none; cursor: pointer;" title="{file_info.path}">{file_info.filename}</a>'

                    html += f"""
                <tr style="border-bottom: 1px solid var(--jp-border-color3, #f0f0f0);">
                    <td style="padding: 6px 8px; text-align: left; font-family: monospace;">{instrument}</td>
                    <td style="padding: 6px 8px; text-align: left;">{version}</td>
                    <td style="padding: 6px 8px; text-align: left; font-size: 0.9em; font-family: monospace;">{filename_link}</td>
                </tr>
"""

                html += """
            </table>
            </div>
        </details>
"""

    # Unmatched files section
    if self.unmatched_files:
        html += f"""
        <details style="margin-bottom: 12px;">
            <summary style="cursor: pointer; font-weight: 500; margin-bottom: 8px; color: var(--vscode-editorWarning-foreground, #ff9800);">
                ⚠️  Unmatched Files ({len(self.unmatched_files)})
            </summary>
            <div style="margin-left: 16px; max-height: 300px; overflow-y: auto; font-size: 0.85em;">
                <p style="margin-bottom: 8px; opacity: 0.7;">
                    Files found but excluded (wrong prefix or invalid format).
                </p>
"""

        for unmatched_path in sorted(self.unmatched_files):
            html += f"""
                <div style="margin-bottom: 4px; padding: 4px 8px; font-family: monospace; font-size: 0.9em; opacity: 0.8;">
                    {unmatched_path.name}
                </div>
"""

        html += """
            </div>
        </details>
"""

    html += """
    </div>
"""

    return html


def repr_html_file_info(self: VersionedFileInfo) -> str:
    """HTML representation for Jupyter notebooks."""
    if self.soc_version is None:
        version_badge = (
            "<span style='background-color: var(--jp-layout-color2, #e0e0e0); "
            "color: var(--jp-ui-font-color1, #333); padding: 2px 6px; "
            "border-radius: 3px; font-family: monospace; font-size: 0.9em; "
            "opacity: 0.8;'>SXXPYY</span>"
        )
    else:
        soc_v = self.soc_version
        pi_v = self.pi_version
        version_badge = (
            f"<span style='background-color: var(--jp-brand-color1, #2196f3); "
            f"color: white; padding: 2px 6px; "
            f"border-radius: 3px; font-family: monospace; font-size: 0.9em; "
            f"font-weight: 500;'>S{soc_v:02d}P{pi_v:02d}</span>"
        )

    prefix_color = {
        "PTR": "#4caf50",
        "ITL": "#2196f3",
        "OPL": "#ff9800",
    }.get(self.prefix, "#9e9e9e")

    # Determine provider badge
    if self.is_soc_delivery:
        provider_badge = (
            "<span style='background-color: #9c27b0; color: white; padding: 2px 6px; "
            "border-radius: 3px; font-size: 0.85em; margin-left: 8px;'>SOC Delivery</span>"
        )
    elif self.is_pi_delivery:
        provider_badge = (
            "<span style='background-color: #4caf50; color: white; padding: 2px 6px; "
            "border-radius: 3px; font-size: 0.85em; margin-left: 8px;'>PI Delivery</span>"
        )
    else:
        provider_badge = ""

    html = f"""
    <div style="border: 1px solid var(--jp-border-color2, #e0e0e0); border-radius: 4px; padding: 12px; margin: 8px 0; font-size: 0.9em;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="background-color: {prefix_color}; color: white; padding: 2px 8px; border-radius: 3px; font-weight: 600; font-size: 0.85em;">
                    {self.prefix}
                </span>
                <span style="font-family: monospace; font-weight: 500; font-size: 1.1em;">
                    {self.instrument}
                </span>
                {version_badge}
                {provider_badge}
            </div>
            <span style="font-family: monospace; background-color: var(--jp-layout-color2, #f5f5f5); padding: 3px 8px; border-radius: 3px; font-weight: 600; border: 1px solid var(--jp-border-color2, #e0e0e0); font-size: 0.85em;">
                {self.scenario}
            </span>
        </div>
        <div style="margin-bottom: 6px;">
            <span style="opacity: 0.6; font-size: 0.85em;">Owner:</span>
            <span style="font-family: monospace; margin-left: 8px; font-weight: 500;">
                {self.owner_instrument}
            </span>
        </div>
        <div style="margin-bottom: 6px;">
            <span style="opacity: 0.6; font-size: 0.85em;">Provider:</span>
            <span style="font-family: monospace; margin-left: 8px; font-weight: 500;">
                {self.provider_instrument}
            </span>
        </div>
        <div style="margin-bottom: 6px;">
            <span style="opacity: 0.6; font-size: 0.85em;">Filename:</span>
            <span style="font-family: monospace; margin-left: 8px;">
                {self.filename}
            </span>
        </div>
        <div style="margin-bottom: 6px;">
            <span style="opacity: 0.6; font-size: 0.85em;">Extension:</span>
            <span style="font-family: monospace; margin-left: 8px;">.{self.extension}</span>
        </div>
        <div style="font-size: 0.8em; opacity: 0.5; margin-top: 8px; word-break: break-all;">
            {self.path}
        </div>
    </div>
    """
    return html
