"""
Visualization tools for matching results.

Provides various plotting and reporting capabilities to evaluate and visualize
matching results between two sets of time-based blocks.
"""

from __future__ import annotations

import difflib
from html import escape as html_escape
from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

if TYPE_CHECKING:
    from ptr_editor.diffing.matcher import MatchResult


def _extract_block(obj):
    """
    Extract the actual block from an UnmatchedBlock wrapper if needed.

    Args:
        obj: Either a block or an UnmatchedBlock wrapper

    Returns:
        The actual block object
    """
    from ptr_editor.diffing.matcher import UnmatchedBlock

    if isinstance(obj, UnmatchedBlock):
        return obj.block
    return obj


def plot_match_timeline(
    result: MatchResult,
    figsize: tuple[float, float] = (16, 10),
    max_blocks: int = 1000,
    output_file: str | Path | None = None,
) -> plt.Figure:
    """
    Plot timeline showing matched and unmatched blocks as horizontal bars.

    Creates a side-by-side visualization with left blocks on the left panel
    and right blocks on the right panel. Blocks are colored by status:
    matched (green), unmatched (red), or ambiguous (orange).

    Args:
        result: MatchResult object from matcher.match()
        figsize: Figure size (width, height) in inches
        max_blocks: Maximum number of blocks to show (for readability)
        output_file: Optional path to save figure to disk

    Returns:
        matplotlib Figure object
    """
    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=figsize, sharey=True)

    # Collect all blocks with their y-positions
    left_blocks = {}
    right_blocks = {}

    # Matched blocks - keep same y-position for visual connection
    for i, match in enumerate(result.matches[:max_blocks]):
        left_blocks[id(match.left_block)] = (match.left_block, i, "matched")
        right_blocks[id(match.right_block)] = (match.right_block, i, "matched")

    # Unmatched blocks
    offset = len(result.matches[:max_blocks])
    for i, unmatched in enumerate(result.unmatched_left[:max_blocks]):
        block = _extract_block(unmatched)
        left_blocks[id(block)] = (block, offset + i, "unmatched")

    for i, unmatched in enumerate(result.unmatched_right[:max_blocks]):
        block = _extract_block(unmatched)
        right_blocks[id(block)] = (block, offset + i, "unmatched")

    # Ambiguous blocks
    offset += max(
        len(result.unmatched_left[:max_blocks]),
        len(result.unmatched_right[:max_blocks]),
    )
    for i, block in enumerate(result.ambiguous_left[:max_blocks]):
        left_blocks[id(block)] = (block, offset + i, "ambiguous")

    # Find time range
    all_blocks = [b[0] for b in left_blocks.values()] + [
        b[0] for b in right_blocks.values()
    ]
    valid_blocks = [
        b for b in all_blocks if hasattr(b, "start") and hasattr(b, "end") and b.start
    ]

    if not valid_blocks:
        ax_left.text(0.5, 0.5, "No blocks with timing data", ha="center", va="center")
        ax_right.text(0.5, 0.5, "No blocks with timing data", ha="center", va="center")
        return fig

    min_time = min(b.start for b in valid_blocks)
    max_time = max(b.end for b in valid_blocks)

    # Color scheme
    colors = {"matched": "#2ecc71", "unmatched": "#e74c3c", "ambiguous": "#f39c12"}

    # Plot left blocks
    for block, y_pos, status in left_blocks.values():
        if hasattr(block, "start") and hasattr(block, "end") and block.start:
            duration = (block.end - block.start).total_seconds() / 3600  # hours
            start = (block.start - min_time).total_seconds() / 3600
            ax_left.barh(
                y_pos,
                duration,
                left=start,
                height=0.8,
                color=colors[status],
                alpha=0.7,
                edgecolor="black",
                linewidth=0.5,
            )
            # Add ID label
            if hasattr(block, "id") and block.id:
                ax_left.text(
                    start + duration / 2,
                    y_pos,
                    str(block.id)[:20],
                    va="center",
                    ha="center",
                    fontsize=6,
                )

    # Plot right blocks
    for block, y_pos, status in right_blocks.values():
        if hasattr(block, "start") and hasattr(block, "end") and block.start:
            duration = (block.end - block.start).total_seconds() / 3600
            start = (block.start - min_time).total_seconds() / 3600
            ax_right.barh(
                y_pos,
                duration,
                left=start,
                height=0.8,
                color=colors[status],
                alpha=0.7,
                edgecolor="black",
                linewidth=0.5,
            )
            if hasattr(block, "id") and block.id:
                ax_right.text(
                    start + duration / 2,
                    y_pos,
                    str(block.id)[:20],
                    va="center",
                    ha="center",
                    fontsize=6,
                )

    # Configure axes
    ax_left.set_xlabel("Time (hours from start)")
    ax_left.set_ylabel("Block Index")
    ax_left.set_title(f"Left Timeline ({result.left_total} blocks)")
    ax_left.invert_yaxis()
    ax_left.grid(axis="x", alpha=0.3)

    ax_right.set_xlabel("Time (hours from start)")
    ax_right.set_title(f"Right Timeline ({result.right_total} blocks)")
    ax_right.grid(axis="x", alpha=0.3)

    # Add legend
    legend_elements = [
        mpatches.Patch(color=colors["matched"], label="Matched"),
        mpatches.Patch(color=colors["unmatched"], label="Unmatched"),
        mpatches.Patch(color=colors["ambiguous"], label="Ambiguous"),
    ]
    ax_left.legend(handles=legend_elements, loc="upper left")

    plt.suptitle(
        f"Match Results: {result.match_count} matches, "
        f"{result.unmatched_left_count} unmatched left, "
        f"{result.unmatched_right_count} unmatched right",
        fontsize=12,
        fontweight="bold",
    )
    plt.tight_layout()

    if output_file:
        fig.savefig(output_file, dpi=150, bbox_inches="tight")

    return fig


def plot_match_statistics(
    result: MatchResult,
    figsize: tuple[float, float] = (14, 6),
    output_file: str | Path | None = None,
) -> plt.Figure:
    """
    Plot statistical breakdown of matching results.

    Creates three panels:
    1. Pie chart of overall match status
    2. Bar chart of matches by rule
    3. Bar chart of match rates

    Args:
        result: MatchResult object from matcher.match()
        figsize: Figure size (width, height) in inches
        output_file: Optional path to save figure to disk

    Returns:
        matplotlib Figure object
    """
    fig, axes = plt.subplots(1, 3, figsize=figsize)

    # Pie chart: Match status
    ax = axes[0]
    matched = result.match_count
    unmatched = result.unmatched_left_count + result.unmatched_right_count
    ambiguous = result.ambiguous_count

    sizes = [matched * 2, unmatched, ambiguous]  # *2 because matched affects both sides
    labels = [
        f"Matched\n({matched} pairs)",
        f"Unmatched\n({unmatched})",
        f"Ambiguous\n({ambiguous})",
    ]
    colors_pie = ["#2ecc71", "#e74c3c", "#f39c12"]

    # Filter out zero values
    sizes_filtered = [(s, l, c) for s, l, c in zip(sizes, labels, colors_pie) if s > 0]
    if sizes_filtered:
        sizes_f, labels_f, colors_f = zip(*sizes_filtered)
        ax.pie(
            sizes_f,
            labels=labels_f,
            colors=colors_f,
            autopct="%1.1f%%",
            startangle=90,
        )
    ax.set_title("Overall Match Status")

    # Bar chart: Matches by rule
    ax = axes[1]
    rule_counts = result.matches_by_rule()
    if rule_counts:
        rules = list(rule_counts.keys())
        counts = list(rule_counts.values())

        bars = ax.barh(range(len(rules)), counts, color="#3498db")
        ax.set_yticks(range(len(rules)))
        ax.set_yticklabels([r[:30] + "..." if len(r) > 30 else r for r in rules])
        ax.set_xlabel("Number of Matches")
        ax.set_title("Matches by Rule")

        # Add count labels
        for i, (bar, count) in enumerate(zip(bars, counts)):
            ax.text(count, i, f" {count}", va="center", fontsize=8)
    else:
        ax.text(0.5, 0.5, "No matches", ha="center", va="center", fontsize=12)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

    # Bar chart: Match rates
    ax = axes[2]
    categories = ["Left\nBlocks", "Right\nBlocks", "Overall"]
    rates = [
        result.match_rate_left * 100,
        result.match_rate_right * 100,
        result.overall_match_rate * 100,
    ]

    bars = ax.bar(categories, rates, color=["#3498db", "#9b59b6", "#1abc9c"])
    ax.set_ylabel("Match Rate (%)")
    ax.set_title("Match Rates")
    ax.set_ylim(0, 100)
    ax.grid(axis="y", alpha=0.3)

    # Add percentage labels
    for bar, rate in zip(bars, rates):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{rate:.1f}%",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    plt.tight_layout()

    if output_file:
        fig.savefig(output_file, dpi=150, bbox_inches="tight")

    return fig


def plot_timing_drift(
    result: MatchResult,
    max_matches: int = 100,
    figsize: tuple[float, float] = (12, 6),
    output_file: str | Path | None = None,
) -> plt.Figure:
    """
    Plot timing drift between matched blocks.

    Shows histograms of start and end time differences to identify
    systematic timing shifts between left and right blocks.

    Args:
        result: MatchResult object from matcher.match()
        max_matches: Maximum number of matches to analyze
        figsize: Figure size (width, height) in inches
        output_file: Optional path to save figure to disk

    Returns:
        matplotlib Figure object
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    start_diffs = []
    end_diffs = []

    for match in result.matches[:max_matches]:
        if all(
            hasattr(b, "start") and hasattr(b, "end") and b.start and b.end
            for b in [match.left_block, match.right_block]
        ):
            start_diff = (
                match.right_block.start - match.left_block.start
            ).total_seconds() / 60
            end_diff = (
                match.right_block.end - match.left_block.end
            ).total_seconds() / 60
            start_diffs.append(start_diff)
            end_diffs.append(end_diff)

    if not start_diffs:
        ax1.text(
            0.5,
            0.5,
            "No timing data available",
            ha="center",
            va="center",
            fontsize=12,
        )
        ax2.text(
            0.5,
            0.5,
            "No timing data available",
            ha="center",
            va="center",
            fontsize=12,
        )
        return fig

    # Start time drift
    ax1.hist(start_diffs, bins=30, color="#3498db", alpha=0.7, edgecolor="black")
    ax1.axvline(0, color="red", linestyle="--", linewidth=2, label="No drift")
    ax1.set_xlabel("Start Time Drift (minutes)")
    ax1.set_ylabel("Number of Matches")
    mean_start = np.mean(start_diffs)
    std_start = np.std(start_diffs)
    ax1.set_title(f"Start Time Drift\n(μ={mean_start:.1f} min, σ={std_start:.1f})")
    ax1.legend()
    ax1.grid(alpha=0.3)

    # End time drift
    ax2.hist(end_diffs, bins=30, color="#9b59b6", alpha=0.7, edgecolor="black")
    ax2.axvline(0, color="red", linestyle="--", linewidth=2, label="No drift")
    ax2.set_xlabel("End Time Drift (minutes)")
    ax2.set_ylabel("Number of Matches")
    mean_end = np.mean(end_diffs)
    std_end = np.std(end_diffs)
    ax2.set_title(f"End Time Drift\n(μ={mean_end:.1f} min, σ={std_end:.1f})")
    ax2.legend()
    ax2.grid(alpha=0.3)

    plt.tight_layout()

    if output_file:
        fig.savefig(output_file, dpi=150, bbox_inches="tight")

    return fig


def plot_match_matrix(
    result: MatchResult,
    max_size: int = 100,
    figsize: tuple[float, float] = (12, 12),
    output_file: str | Path | None = None,
) -> plt.Figure:
    """
    Plot match matrix showing which left blocks matched which right blocks.

    Creates a heatmap where a bright cell indicates a match between
    left block (row) and right block (column). Useful for seeing
    patterns in matching, such as diagonal patterns (sequential matching)
    or scattered patterns (reordering).

    Args:
        result: MatchResult object from matcher.match()
        max_size: Maximum matrix dimension (for readability)
        figsize: Figure size (width, height) in inches
        output_file: Optional path to save figure to disk

    Returns:
        matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Create matrix
    matrix = np.zeros(
        (min(result.left_total, max_size), min(result.right_total, max_size))
    )

    # Fill in matches
    for match in result.matches:
        if match.left_index < max_size and match.right_index < max_size:
            matrix[match.left_index, match.right_index] = 1

    # Plot
    im = ax.imshow(matrix, cmap="RdYlGn", aspect="auto", interpolation="nearest")

    ax.set_xlabel("Right Block Index")
    ax.set_ylabel("Left Block Index")
    ax.set_title(
        f"Match Matrix ({result.match_count} matches)\n"
        f"Showing first {max_size} blocks from each side"
    )

    plt.colorbar(im, ax=ax, label="Match (1) / No Match (0)")
    plt.tight_layout()

    if output_file:
        fig.savefig(output_file, dpi=150, bbox_inches="tight")

    return fig


def plot_duration_comparison(
    result: MatchResult,
    max_matches: int = 100,
    figsize: tuple[float, float] = (12, 6),
    output_file: str | Path | None = None,
) -> plt.Figure:
    """
    Plot duration comparison between matched blocks.

    Shows scatter plot and histogram of duration differences to identify
    blocks that changed duration between left and right timelines.

    Args:
        result: MatchResult object from matcher.match()
        max_matches: Maximum number of matches to analyze
        figsize: Figure size (width, height) in inches
        output_file: Optional path to save figure to disk

    Returns:
        matplotlib Figure object
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    left_durations = []
    right_durations = []
    duration_diffs = []

    for match in result.matches[:max_matches]:
        if all(
            hasattr(b, "start") and hasattr(b, "end") and b.start and b.end
            for b in [match.left_block, match.right_block]
        ):
            left_dur = (
                match.left_block.end - match.left_block.start
            ).total_seconds() / 60
            right_dur = (
                match.right_block.end - match.right_block.start
            ).total_seconds() / 60
            left_durations.append(left_dur)
            right_durations.append(right_dur)
            duration_diffs.append(right_dur - left_dur)

    if not left_durations:
        ax1.text(
            0.5,
            0.5,
            "No duration data available",
            ha="center",
            va="center",
            fontsize=12,
        )
        ax2.text(
            0.5,
            0.5,
            "No duration data available",
            ha="center",
            va="center",
            fontsize=12,
        )
        return fig

    # Scatter plot: left vs right durations
    ax1.scatter(left_durations, right_durations, alpha=0.6, s=30, color="#3498db")
    # Add diagonal line (perfect match)
    max_dur = max(max(left_durations), max(right_durations))
    ax1.plot([0, max_dur], [0, max_dur], "r--", linewidth=2, label="Perfect match")
    ax1.set_xlabel("Left Block Duration (minutes)")
    ax1.set_ylabel("Right Block Duration (minutes)")
    ax1.set_title("Duration Comparison")
    ax1.legend()
    ax1.grid(alpha=0.3)

    # Histogram: duration differences
    ax2.hist(duration_diffs, bins=30, color="#9b59b6", alpha=0.7, edgecolor="black")
    ax2.axvline(0, color="red", linestyle="--", linewidth=2, label="No change")
    ax2.set_xlabel("Duration Change (minutes)")
    ax2.set_ylabel("Number of Matches")
    mean_diff = np.mean(duration_diffs)
    std_diff = np.std(duration_diffs)
    ax2.set_title(f"Duration Changes\n(μ={mean_diff:.1f} min, σ={std_diff:.1f})")
    ax2.legend()
    ax2.grid(alpha=0.3)

    plt.tight_layout()

    if output_file:
        fig.savefig(output_file, dpi=150, bbox_inches="tight")

    return fig


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


def generate_html_report(
    result: MatchResult,
    output_file: str | Path | None = None,
    compact: bool = False,
) -> Path | str:
    """
    Generate interactive HTML report with sortable tables.

    Creates a comprehensive HTML report including:
    - Summary statistics
    - Matches grouped by rule
    - Detailed match table with timing information
    - Lists of unmatched blocks

    Args:
        result: MatchResult object from matcher.match()
        output_file: Path to save HTML file. If None, returns HTML string without saving.
        compact: If True, uses minimal theme-aware styling suitable for Jupyter notebooks.
                If False, uses full styled report for standalone HTML files.

    Returns:
        Path to generated HTML file if output_file is provided, otherwise HTML string
    """
    if compact:
        return _generate_compact_html(result)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Match Report</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism.min.css" rel="stylesheet" />
        <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/line-numbers/prism-line-numbers.min.css" rel="stylesheet" />
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            h1 {{ color: #2c3e50; }}
            h2 {{ color: #34495e; margin-top: 30px; }}
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
                min-width: 150px;
                text-align: center;
                padding: 15px;
                background: #ecf0f1;
                border-radius: 5px;
            }}
            .metric-label {{ font-size: 12px; color: #7f8c8d; text-transform: uppercase; }}
            .metric-value {{ font-size: 28px; font-weight: bold; color: #3498db; margin-top: 5px; }}
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
            }}
            td {{ padding: 10px; border-bottom: 1px solid #ecf0f1; }}
            tr:hover {{ background: #f8f9fa; }}
            .matched {{ background: #d5f4e6; }}
            .unmatched {{ background: #fadbd8; }}
            .ambiguous {{ background: #fdeaa8; }}
            .progress-bar {{
                width: 100%;
                height: 20px;
                background: #ecf0f1;
                border-radius: 10px;
                overflow: hidden;
                margin: 10px 0;
            }}
            .progress-fill {{
                height: 100%;
                background: linear-gradient(90deg, #3498db, #2ecc71);
                transition: width 0.3s;
            }}
            .xml-row {{
                display: none;
            }}
            .xml-row.show {{
                display: table-row;
            }}
            .diff-row {{
                display: none;
            }}
            .diff-row.show {{
                display: table-row;
            }}
        </style>
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                // Handle XML toggle buttons
                const xmlButtons = document.querySelectorAll('.xml-toggle');
                xmlButtons.forEach(function(button) {{
                    button.addEventListener('click', function() {{
                        const rowIndex = this.getAttribute('data-row-index');
                        const xmlRow = document.getElementById('xml-row-' + rowIndex);
                        const diffRow = document.getElementById('diff-row-' + rowIndex);
                        
                        if (!xmlRow) return;
                        
                        // Hide diff row if open
                        if (diffRow && diffRow.style.display === 'table-row') {{
                            diffRow.style.display = 'none';
                            const diffButton = document.querySelector('.diff-toggle[data-row-index="' + rowIndex + '"]');
                            if (diffButton) diffButton.innerHTML = '🔀 View Diff';
                        }}
                        
                        // Toggle XML row
                        if (xmlRow.style.display === 'none') {{
                            xmlRow.style.display = 'table-row';
                            this.innerHTML = '📄 Hide XML';
                        }} else {{
                            xmlRow.style.display = 'none';
                            this.innerHTML = '📄 View XML';
                        }}
                    }});
                }});
                
                // Handle Diff toggle buttons
                const diffButtons = document.querySelectorAll('.diff-toggle');
                diffButtons.forEach(function(button) {{
                    button.addEventListener('click', function() {{
                        const rowIndex = this.getAttribute('data-row-index');
                        const diffRow = document.getElementById('diff-row-' + rowIndex);
                        const xmlRow = document.getElementById('xml-row-' + rowIndex);
                        
                        if (!diffRow) return;
                        
                        // Hide XML row if open
                        if (xmlRow && xmlRow.style.display === 'table-row') {{
                            xmlRow.style.display = 'none';
                            const xmlButton = document.querySelector('.xml-toggle[data-row-index="' + rowIndex + '"]');
                            if (xmlButton) xmlButton.innerHTML = '📄 View XML';
                        }}
                        
                        // Toggle diff row
                        if (diffRow.style.display === 'none') {{
                            diffRow.style.display = 'table-row';
                            this.innerHTML = '� Hide Diff';
                        }} else {{
                            diffRow.style.display = 'none';
                            this.innerHTML = '� View Diff';
                        }}
                    }});
                }});
            }});
        </script>
    </head>
    <body>
        <h1>🔍 Matching Results Report</h1>

        <div class="summary">
            <h2>Summary Statistics</h2>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-label">Total Matches</div>
                    <div class="metric-value">{result.match_count}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Match Rate</div>
                    <div class="metric-value">{result.overall_match_rate:.1%}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Unmatched Left</div>
                    <div class="metric-value">{result.unmatched_left_count}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Unmatched Right</div>
                    <div class="metric-value">{result.unmatched_right_count}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Ambiguous</div>
                    <div class="metric-value">{result.ambiguous_count}</div>
                </div>
            </div>

            <h3>Match Rates by Side</h3>
            <div>
                <strong>Left Blocks:</strong> {result.match_rate_left:.1%}
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {result.match_rate_left * 100}%"></div>
                </div>
            </div>
            <div>
                <strong>Right Blocks:</strong> {result.match_rate_right:.1%}
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {result.match_rate_right * 100}%"></div>
                </div>
            </div>
        </div>

        <h2>📊 Matches by Rule</h2>
        <table>
            <tr><th>Rule</th><th>Count</th><th>Percentage</th></tr>
    """

    for rule, count in sorted(result.matches_by_rule().items(), key=lambda x: -x[1]):
        pct = (count / result.match_count * 100) if result.match_count > 0 else 0
        html += f"<tr><td>{rule}</td><td>{count}</td><td>{pct:.1f}%</td></tr>\n"

    html += """
        </table>

        <h2>✅ Matched Blocks</h2>
    """

    # Separate matches into changed and unchanged
    changed_matches = []
    unchanged_matches = []

    for idx, match in enumerate(result.matches):
        # Get XML for comparison
        left_xml_raw = "N/A"
        right_xml_raw = "N/A"
        try:
            if hasattr(match.left_block, "xml"):
                left_xml_raw = match.left_block.xml
        except Exception:
            pass

        try:
            if hasattr(match.right_block, "xml"):
                right_xml_raw = match.right_block.xml
        except Exception:
            pass

        # Check if XML is identical
        if left_xml_raw == right_xml_raw:
            unchanged_matches.append((idx, match))
        else:
            changed_matches.append((idx, match))

    # Display changed matches first
    if changed_matches:
        html += f"""
        <h3 style="color: #e67e22; margin-top: 20px;">🔄 Changed Blocks ({len(changed_matches)})</h3>
        <p style="color: #666; font-size: 14px;">Blocks with XML differences</p>
        <table>
            <tr>
                <th>Left ID</th>
                <th>Right ID</th>
                <th>Rule</th>
                <th>Start Drift (min)</th>
                <th>End Drift (min)</th>
                <th>Duration Change (min)</th>
                <th>XML</th>
            </tr>
    """

    for idx, match in changed_matches:
        left_id = getattr(match.left_block, "id", "N/A")
        right_id = getattr(match.right_block, "id", "N/A")
        start_drift = end_drift = duration_change = "N/A"

        if all(
            hasattr(b, "start") and hasattr(b, "end") and b.start and b.end
            for b in [match.left_block, match.right_block]
        ):
            start_drift_sec = (
                match.right_block.start - match.left_block.start
            ).total_seconds()
            end_drift_sec = (
                match.right_block.end - match.left_block.end
            ).total_seconds()
            left_dur = (match.left_block.end - match.left_block.start).total_seconds()
            right_dur = (
                match.right_block.end - match.right_block.start
            ).total_seconds()

            start_drift = f"{start_drift_sec / 60:.1f}"
            end_drift = f"{end_drift_sec / 60:.1f}"
            duration_change = f"{(right_dur - left_dur) / 60:.1f}"

        # Get XML for both blocks (unescaped for diff generation)
        left_xml_raw = "N/A"
        right_xml_raw = "N/A"
        try:
            if hasattr(match.left_block, "xml"):
                left_xml_raw = match.left_block.xml
        except Exception as e:
            left_xml_raw = f"Error: {e}"

        try:
            if hasattr(match.right_block, "xml"):
                right_xml_raw = match.right_block.xml
        except Exception as e:
            right_xml_raw = f"Error: {e}"

        # Generate HTML diff
        diff_html = _generate_html_diff(left_xml_raw, right_xml_raw)

        # HTML-escaped versions for display
        left_xml = html_escape(left_xml_raw)
        right_xml = html_escape(right_xml_raw)

        html += f"""
            <tr class="matched" data-row-index="{idx}">
                <td>{left_id}</td>
                <td>{right_id}</td>
                <td>{match.rule.description}</td>
                <td>{start_drift}</td>
                <td>{end_drift}</td>
                <td>{duration_change}</td>
                <td style="text-align: center;">
                    <button class="diff-toggle" data-row-index="{idx}" style="cursor: pointer; color: #28a745; font-weight: bold; background: none; border: 1px solid #28a745; padding: 5px 10px; border-radius: 4px; margin-right: 5px;">
                        🔀 View Diff
                    </button>
                    <button class="xml-toggle" data-row-index="{idx}" style="cursor: pointer; color: #3498db; font-weight: bold; background: none; border: 1px solid #3498db; padding: 5px 10px; border-radius: 4px;">
                        � View XML
                    </button>
                </td>
            </tr>
            <tr class="diff-row" id="diff-row-{idx}" style="display: none;">
                <td colspan="7" style="padding: 15px; background: #f9f9f9;">
                    <div style="margin-bottom: 10px;">
                        <strong style="color: #2c3e50; font-size: 14px;">🔀 XML Differences</strong>
                        <span style="margin-left: 10px; color: #666; font-size: 12px;">(Only showing changed lines)</span>
                    </div>
                    {diff_html}
                </td>
            </tr>
            <tr class="xml-row" id="xml-row-{idx}" style="display: none;">
                <td colspan="7" style="padding: 0; background: #f9f9f9;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; padding: 15px;">
                        <div>
                            <strong style="display: block; margin-bottom: 8px; color: #2c3e50; font-size: 14px;">📄 Left Block XML</strong>
                            <pre class="line-numbers" style="margin: 0; max-height: 500px; overflow-y: auto;"><code class="language-xml">{left_xml}</code></pre>
                        </div>
                        <div>
                            <strong style="display: block; margin-bottom: 8px; color: #2c3e50; font-size: 14px;">📄 Right Block XML</strong>
                            <pre class="line-numbers" style="margin: 0; max-height: 500px; overflow-y: auto;"><code class="language-xml">{right_xml}</code></pre>
                        </div>
                    </div>
                </td>
            </tr>
        """

    if changed_matches:
        html += """
        </table>
        """

    # Display unchanged matches in a collapsed section
    if unchanged_matches:
        html += f"""
        <h3 style="color: #27ae60; margin-top: 30px;">✓ Unchanged Blocks ({len(unchanged_matches)})</h3>
        <details style="margin: 20px 0; background: #e8f5e9; padding: 15px; border-radius: 8px; border: 1px solid #a5d6a7;">
            <summary style="cursor: pointer; font-weight: bold; color: #2c3e50; font-size: 16px;">
                📋 Show {len(unchanged_matches)} identical blocks (no XML differences)
            </summary>
            <table style="margin-top: 15px;">
                <tr>
                    <th>Left ID</th>
                    <th>Right ID</th>
                    <th>Rule</th>
                    <th>Start Drift (min)</th>
                    <th>End Drift (min)</th>
                    <th>Duration Change (min)</th>
                </tr>
        """

        for idx, match in unchanged_matches:
            left_id = getattr(match.left_block, "id", "N/A")
            right_id = getattr(match.right_block, "id", "N/A")
            start_drift = end_drift = duration_change = "N/A"

            if all(
                hasattr(b, "start") and hasattr(b, "end") and b.start and b.end
                for b in [match.left_block, match.right_block]
            ):
                start_drift_sec = (
                    match.right_block.start - match.left_block.start
                ).total_seconds()
                end_drift_sec = (
                    match.right_block.end - match.left_block.end
                ).total_seconds()
                left_dur = (
                    match.left_block.end - match.left_block.start
                ).total_seconds()
                right_dur = (
                    match.right_block.end - match.right_block.start
                ).total_seconds()

                start_drift = f"{start_drift_sec / 60:.1f}"
                end_drift = f"{end_drift_sec / 60:.1f}"
                duration_change = f"{(right_dur - left_dur) / 60:.1f}"

            html += f"""
                <tr class="matched" style="background: #f1f8e9;">
                    <td>{left_id}</td>
                    <td>{right_id}</td>
                    <td>{match.rule.description}</td>
                    <td>{start_drift}</td>
                    <td>{end_drift}</td>
                    <td>{duration_change}</td>
                </tr>
            """

        html += """
            </table>
        </details>
        """

    # Add unmatched blocks if any
    if result.unmatched_left:
        html += f"""
        <h2>❌ Unmatched Left Blocks (First 50)</h2>
        <table>
            <tr><th>ID</th><th>Start</th><th>End</th><th>Overlapping Candidates</th><th>XML</th></tr>
        """
        for unmatched in result.unmatched_left[:50]:
            # Extract actual block from UnmatchedBlock wrapper
            block = _extract_block(unmatched)
            block_id = getattr(block, "id", "N/A")
            start = getattr(block, "start", "N/A")
            end = getattr(block, "end", "N/A")

            # Get overlapping candidates info if available
            from ptr_editor.diffing.matcher import UnmatchedBlock

            overlap_info = "N/A"
            if isinstance(unmatched, UnmatchedBlock):
                overlap_count = len(unmatched.overlapping_candidates)
                if overlap_count > 0:
                    candidate_ids = [
                        getattr(c, "id", "?") for c in unmatched.overlapping_candidates
                    ]
                    overlap_info = f"{overlap_count} blocks: {', '.join(str(cid) for cid in candidate_ids[:5])}"
                    if overlap_count > 5:  # noqa: PLR2004
                        overlap_info += f" ... (+{overlap_count - 5} more)"
                else:
                    overlap_info = "None"

            # Get XML and HTML-escape it
            block_xml = "N/A"
            try:
                if hasattr(block, "xml"):
                    block_xml = html_escape(block.xml)
            except Exception as e:
                block_xml = html_escape(f"Error: {e}")

            html += f"""
            <tr class="unmatched">
                <td>{block_id}</td>
                <td>{start}</td>
                <td>{end}</td>
                <td style="font-size: 0.9em;">{overlap_info}</td>
                <td>
                    <details>
                        <summary style="cursor: pointer; color: #3498db;">View XML</summary>
                        <pre class="line-numbers" style="margin-top: 8px; max-height: 400px; overflow-y: auto;"><code class="language-xml">{block_xml}</code></pre>
                    </details>
                </td>
            </tr>
            """
        html += "</table>"

    if result.unmatched_right:
        html += """
        <h2>❌ Unmatched Right Blocks (First 50)</h2>
        <table>
            <tr>
                <th>ID</th><th>Start</th><th>End</th>
                <th>Overlapping Candidates</th><th>XML</th>
            </tr>
        """
        for unmatched in result.unmatched_right[:50]:
            # Extract actual block from UnmatchedBlock wrapper
            block = _extract_block(unmatched)
            block_id = getattr(block, "id", "N/A")
            start = getattr(block, "start", "N/A")
            end = getattr(block, "end", "N/A")

            # Get overlapping candidates info if available
            from ptr_editor.diffing.matcher import UnmatchedBlock

            overlap_info = "N/A"
            if isinstance(unmatched, UnmatchedBlock):
                overlap_count = len(unmatched.overlapping_candidates)
                if overlap_count > 0:
                    candidate_ids = [
                        getattr(c, "id", "?") for c in unmatched.overlapping_candidates
                    ]
                    overlap_info = (
                        f"{overlap_count} blocks: "
                        f"{', '.join(str(cid) for cid in candidate_ids[:5])}"
                    )
                    if overlap_count > 5:  # noqa: PLR2004
                        overlap_info += f" ... (+{overlap_count - 5} more)"
                else:
                    overlap_info = "None"

            # Get XML and HTML-escape it
            block_xml = "N/A"
            try:
                if hasattr(block, "xml"):
                    block_xml = html_escape(block.xml)
            except Exception as e:
                block_xml = html_escape(f"Error: {e}")

            html += f"""
            <tr class="unmatched">
                <td>{block_id}</td>
                <td>{start}</td>
                <td>{end}</td>
                <td style="font-size: 0.9em;">{overlap_info}</td>
                <td>
                    <details>
                        <summary style="cursor: pointer; color: #3498db;">
                            View XML
                        </summary>
                        <pre class="line-numbers" style="margin-top: 8px; max-height: 400px; overflow-y: auto;">
                            <code class="language-xml">{block_xml}</code>
                        </pre>
                    </details>
                </td>
            </tr>
            """
        html += "</table>"

    html += """
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-xml.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/line-numbers/prism-line-numbers.min.js"></script>
    </body>
    </html>
    """

    if output_file is None:
        return html

    output_path = Path(output_file)
    output_path.write_text(html)
    print(f"HTML report saved to {output_path}")

    return output_path


def _generate_compact_html(result: MatchResult) -> str:
    """
    Generate compact, theme-aware HTML for Jupyter notebook display.

    Uses CSS variables with fallbacks and minimal styling to respect
    the notebook theme. Uses pandas DataFrames for table rendering.

    Args:
        result: MatchResult object from matcher.match()

    Returns:
        Compact HTML string for notebook display
    """
    html = """
    <div style="border: 1px solid var(--jp-border-color2, #e0e0e0); border-radius: 4px; padding: 12px; margin: 8px 0; font-size: 0.9em;">
        <div style="margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid var(--jp-border-color2, #e0e0e0);">
            <strong style="font-size: 1.1em;">🔍 Match Results</strong>
        </div>
"""

    # Summary metrics as inline elements
    html += """
        <div style="margin-bottom: 12px;">
"""

    metrics = [
        (f"{result.match_count} matches", "✓"),
        (f"{result.equal_match_count} identical", "═"),
        (f"{result.unequal_match_count} differ", "≠"),
        (f"{result.overall_match_rate:.1%} rate", "⊙"),
        (f"{result.unmatched_left_count} unmatched left", "←"),
        (f"{result.unmatched_right_count} unmatched right", "→"),
    ]

    if result.ambiguous_count > 0:
        metrics.append((f"{result.ambiguous_count} ambiguous", "⚠"))

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

    # Totals
    html += f"""
        <div style="margin-bottom: 12px; font-size: 0.85em; opacity: 0.8;">
            Total: {result.left_total:,} left blocks, {result.right_total:,} right blocks
        </div>
"""

    # Matches by rule summary using pandas
    if result.matches:
        summary_df = result.as_pandas_summary()
        html += """
        <details style="margin-bottom: 12px;">
            <summary style="cursor: pointer; font-weight: 500; margin-bottom: 6px;">
                📊 Matches by Rule
            </summary>
            <div style="margin-left: 16px; font-size: 0.85em; max-height: 300px; overflow-y: auto;">
"""
        html += summary_df.to_html(index=False, border=0, classes="dataframe")
        html += """
            </div>
        </details>
"""

    # All matched blocks using pandas
    if result.matches:
        df_matches = result.as_pandas_matches()
        # Select key columns for display (check which ones exist)
        display_cols = []
        for col in [
            "left_id",
            "right_id",
            "rule",
            "start_drift_min",
            "duration_change_min",
        ]:
            if col in df_matches.columns:
                display_cols.append(col)

        if not display_cols:
            display_cols = df_matches.columns.tolist()[:5]  # Fallback to first 5

        df_display = df_matches[display_cols].copy()

        # Rename for better display
        rename_map = {
            "left_id": "Left ID",
            "right_id": "Right ID",
            "rule": "Rule",
            "start_drift_min": "Drift (min)",
            "duration_change_min": "Δ Duration (min)",
        }
        df_display = df_display.rename(
            columns={k: v for k, v in rename_map.items() if k in df_display.columns}
        )

        html += f"""
        <details style="margin-bottom: 12px;">
            <summary style="cursor: pointer; font-weight: 500; margin-bottom: 6px;">
                ✅ All Matched Blocks ({len(result.matches)})
            </summary>
            <div style="margin-left: 16px; max-height: 400px; overflow-y: auto; font-size: 0.85em;">
"""
        html += df_display.to_html(index=False, border=0, classes="dataframe")
        html += """
            </div>
        </details>
"""

    # Blocks that differ by equality (matched but have differences)
    unequal_matches = result.get_unequal_matches()
    if unequal_matches:
        df_unequal = result.as_pandas_unequal_matches()
        # Select key columns
        display_cols = []
        for col in [
            "left_id",
            "right_id",
            "rule",
            "start_drift_min",
            "duration_change_min",
        ]:
            if col in df_unequal.columns:
                display_cols.append(col)

        if not display_cols:
            display_cols = df_unequal.columns.tolist()[:5]

        df_display = df_unequal[display_cols].copy()

        # Rename for better display
        rename_map = {
            "left_id": "Left ID",
            "right_id": "Right ID",
            "rule": "Rule",
            "start_drift_min": "Drift (min)",
            "duration_change_min": "Δ Duration (min)",
        }
        df_display = df_display.rename(
            columns={k: v for k, v in rename_map.items() if k in df_display.columns}
        )

        html += f"""
        <details style="margin-bottom: 12px;">
            <summary style="cursor: pointer; font-weight: 500; margin-bottom: 6px; color: #f39c12;">
                ≠ Blocks with Differences ({len(unequal_matches)})
            </summary>
            <div style="margin-left: 16px; max-height: 400px; overflow-y: auto; font-size: 0.85em;">
                <div style="margin-bottom: 8px; font-size: 0.9em; color: #666;">
                    These blocks matched by ID/timing but have content differences
                </div>
"""
        html += df_display.to_html(index=False, border=0, classes="dataframe")
        html += """
            </div>
        </details>
"""

    # Unmatched left blocks using pandas
    if result.unmatched_left:
        df_unmatched_left = result.as_pandas_unmatched_left()
        # Select key columns
        display_cols = []
        if "id" in df_unmatched_left.columns:
            display_cols.append("id")
        if "start" in df_unmatched_left.columns:
            display_cols.append("start")
        if "end" in df_unmatched_left.columns:
            display_cols.append("end")
        if "overlapping_candidates_count" in df_unmatched_left.columns:
            display_cols.append("overlapping_candidates_count")
        if "overlapping_candidates_ids" in df_unmatched_left.columns:
            display_cols.append("overlapping_candidates_ids")

        if display_cols:
            df_display = df_unmatched_left[display_cols].copy()
            df_display = df_display.rename(
                columns={
                    "id": "ID",
                    "start": "Start",
                    "end": "End",
                    "overlapping_candidates_count": "Overlap Count",
                    "overlapping_candidates_ids": "Overlapping IDs",
                }
            )
        else:
            df_display = df_unmatched_left

        html += f"""
        <details style="margin-bottom: 12px;">
            <summary style="cursor: pointer; font-weight: 500; margin-bottom: 6px;">
                ❌ Unmatched Left Blocks ({len(result.unmatched_left)})
            </summary>
            <div style="margin-left: 16px; max-height: 300px; overflow-y: auto; font-size: 0.85em;">
"""
        html += df_display.to_html(index=False, border=0, classes="dataframe")
        html += """
            </div>
        </details>
"""

    # Unmatched right blocks using pandas
    if result.unmatched_right:
        df_unmatched_right = result.as_pandas_unmatched_right()
        # Select key columns
        display_cols = []
        if "id" in df_unmatched_right.columns:
            display_cols.append("id")
        if "start" in df_unmatched_right.columns:
            display_cols.append("start")
        if "end" in df_unmatched_right.columns:
            display_cols.append("end")
        if "overlapping_candidates_count" in df_unmatched_right.columns:
            display_cols.append("overlapping_candidates_count")
        if "overlapping_candidates_ids" in df_unmatched_right.columns:
            display_cols.append("overlapping_candidates_ids")

        if display_cols:
            df_display = df_unmatched_right[display_cols].copy()
            df_display = df_display.rename(
                columns={
                    "id": "ID",
                    "start": "Start",
                    "end": "End",
                    "overlapping_candidates_count": "Overlap Count",
                    "overlapping_candidates_ids": "Overlapping IDs",
                }
            )
        else:
            df_display = df_unmatched_right

        html += f"""
        <details style="margin-bottom: 12px;">
            <summary style="cursor: pointer; font-weight: 500; margin-bottom: 6px;">
                ❌ Unmatched Right Blocks ({len(result.unmatched_right)})
            </summary>
            <div style="margin-left: 16px; max-height: 300px; overflow-y: auto; font-size: 0.85em;">
"""
        html += df_display.to_html(index=False, border=0, classes="dataframe")
        html += """
            </div>
        </details>
"""

    # Ambiguous blocks using pandas
    if result.ambiguous_left:
        df_ambiguous = result.as_pandas_ambiguous()
        # Select key columns
        display_cols = []
        if "id" in df_ambiguous.columns:
            display_cols.append("id")
        if "start" in df_ambiguous.columns:
            display_cols.append("start")
        if "end" in df_ambiguous.columns:
            display_cols.append("end")

        if display_cols:
            df_display = df_ambiguous[display_cols].copy()
            df_display = df_display.rename(
                columns={
                    "id": "ID",
                    "start": "Start",
                    "end": "End",
                }
            )
        else:
            df_display = df_ambiguous

        html += f"""
        <details style="margin-bottom: 12px;">
            <summary style="cursor: pointer; font-weight: 500; margin-bottom: 6px;">
                ⚠️ Ambiguous Left Blocks ({len(result.ambiguous_left)})
            </summary>
            <div style="margin-left: 16px; max-height: 300px; overflow-y: auto; font-size: 0.85em;">
"""
        html += df_display.to_html(index=False, border=0, classes="dataframe")
        html += """
            </div>
        </details>
"""

    # Footer with hints
    html += """
        <div style="margin-top: 12px; padding-top: 8px; border-top: 1px solid var(--jp-border-color2, #e0e0e0); font-size: 0.85em; opacity: 0.7;">
            <span style="margin-right: 4px;">💡</span>
            <span>Use <code style="padding: 1px 4px; border: 1px solid var(--jp-border-color2, #e0e0e0); border-radius: 2px; font-size: 0.9em;">.report()</code>, <code style="padding: 1px 4px; border: 1px solid var(--jp-border-color2, #e0e0e0); border-radius: 2px; font-size: 0.9em;">.plot_timeline()</code>, or <code style="padding: 1px 4px; border: 1px solid var(--jp-border-color2, #e0e0e0); border-radius: 2px; font-size: 0.9em;">.to_html('file.html')</code> for analysis</span>
        </div>
    </div>
"""

    return html
