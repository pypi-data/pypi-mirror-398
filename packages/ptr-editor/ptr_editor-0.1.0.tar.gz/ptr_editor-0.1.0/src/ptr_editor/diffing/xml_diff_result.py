"""XML diff result class for comparing PTR XML representations using text diff."""

from __future__ import annotations

import difflib
from typing import Literal

from attrs import define, field


@define
class XmlDiffResult:
    """
    Result of comparing two XML documents using text-based diff.

    Uses Python's difflib for simple, reliable text comparison
    with rich display support for Jupyter notebooks.

    Attributes:
        left_xml: Original XML string
        right_xml: Comparison XML string
        left_label: Label for the left/original XML
        right_label: Label for the right/comparison XML
        context_lines: Number of context lines to show around changes
    """

    left_xml: str
    right_xml: str
    left_label: str = "Left"
    right_label: str = "Right"
    context_lines: int = 3

    # Computed attributes (lazy)
    _diff_lines: list[str] | None = field(default=None, init=False, repr=False)
    _stats: dict | None = field(default=None, init=False, repr=False)

    def _compute_diff(self) -> None:
        """Compute the unified diff."""
        left_lines = self.left_xml.splitlines(keepends=True)
        right_lines = self.right_xml.splitlines(keepends=True)

        self._diff_lines = list(
            difflib.unified_diff(
                left_lines,
                right_lines,
                fromfile=self.left_label,
                tofile=self.right_label,
                n=self.context_lines,
                lineterm="",
            )
        )

        # Compute statistics
        additions = sum(1 for line in self._diff_lines if line.startswith("+") and not line.startswith("+++"))
        deletions = sum(1 for line in self._diff_lines if line.startswith("-") and not line.startswith("---"))
        
        self._stats = {
            "additions": additions,
            "deletions": deletions,
            "total_changes": additions + deletions,
        }

    @property
    def diff_lines(self) -> list[str]:
        """Get the diff lines."""
        if self._diff_lines is None:
            self._compute_diff()
        return self._diff_lines or []

    @property
    def stats(self) -> dict:
        """Get diff statistics."""
        if self._stats is None:
            self._compute_diff()
        return self._stats or {}

    @property
    def has_changes(self) -> bool:
        """Check if there are any differences."""
        return self.stats.get("total_changes", 0) > 0

    @property
    def change_count(self) -> int:
        """Number of changes detected (additions + deletions)."""
        return self.stats.get("total_changes", 0)

    def as_text(self, color: bool = False) -> str:
        """
        Get diff as formatted text.

        Args:
            color: Whether to include ANSI color codes (for terminal output)

        Returns:
            Formatted diff text
        """
        lines = self.diff_lines
        
        if not color:
            return "\n".join(lines)
        
        # Add ANSI color codes
        colored_lines = []
        for line in lines:
            if line.startswith("+++") or line.startswith("---"):
                colored_lines.append(f"\033[1m{line}\033[0m")  # Bold
            elif line.startswith("+"):
                colored_lines.append(f"\033[32m{line}\033[0m")  # Green
            elif line.startswith("-"):
                colored_lines.append(f"\033[31m{line}\033[0m")  # Red
            elif line.startswith("@@"):
                colored_lines.append(f"\033[36m{line}\033[0m")  # Cyan
            else:
                colored_lines.append(line)
        
        return "\n".join(colored_lines)

    def as_html(self, side_by_side: bool = True) -> str:
        """
        Get diff as syntax-highlighted HTML.

        Args:
            side_by_side: If True, show side-by-side comparison (default).
                         If False, show unified diff format.

        Returns:
            HTML string with color-coded diff
        """
        if side_by_side:
            return self._as_html_side_by_side()
        return self._as_html_unified()

    def _as_html_side_by_side(self) -> str:
        """Generate side-by-side HTML diff using difflib.HtmlDiff."""
        left_lines = self.left_xml.splitlines()
        right_lines = self.right_xml.splitlines()

        differ = difflib.HtmlDiff(wrapcolumn=80)
        diff_html = differ.make_table(
            left_lines,
            right_lines,
            fromdesc=self.left_label,
            todesc=self.right_label,
            context=True,
            numlines=self.context_lines,
        )

        # Override difflib's hardcoded colors with theme-aware CSS
        # difflib.HtmlDiff generates inline styles with hardcoded colors
        # that don't work in dark themes, so we need to override them
        styled_diff = f"""
        <style>
            /* Override difflib's hardcoded styles with theme-aware colors */
            .diff_header {{
                background: var(--jp-layout-color2, #e0e0e0) !important;
                color: var(--jp-content-font-color1, inherit) !important;
            }}
            .diff_next {{
                background: var(--jp-layout-color3, #d0d0d0) !important;
                color: var(--jp-content-font-color1, inherit) !important;
            }}
            .diff_add {{
                background: var(--jp-success-color3, #d4edda) !important;
                color: var(--jp-content-font-color1, inherit) !important;
            }}
            .diff_chg {{
                background: var(--jp-warn-color3, #fff3cd) !important;
                color: var(--jp-content-font-color1, inherit) !important;
            }}
            .diff_sub {{
                background: var(--jp-error-color3, #f8d7da) !important;
                color: var(--jp-content-font-color1, inherit) !important;
            }}
            table.diff {{
                width: 100% !important;
                background: var(--jp-layout-color0, #fff) !important;
                color: var(--jp-content-font-color1, inherit) !important;
                border-color: var(--jp-border-color2, #e0e0e0) !important;
            }}
            table.diff td {{
                border-color: var(--jp-border-color2, #e0e0e0) !important;
                text-align: left !important;
            }}
            table.diff th {{
                background: var(--jp-layout-color2, #e0e0e0) !important;
                color: var(--jp-content-font-color1, inherit) !important;
                border-color: var(--jp-border-color2, #e0e0e0) !important;
            }}
            table.diff td.diff_header {{
                text-align: right !important;
            }}
        </style>
        <div style="overflow-x: auto;">
            {diff_html}
        </div>
        """

        return styled_diff

    def _as_html_unified(self) -> str:
        """Generate unified diff HTML format."""
        lines = self.diff_lines

        html_lines = [
            '<pre style="font-family: monospace; font-size: 0.85em; line-height: 1.4;">'
        ]

        for line in lines:
            # Escape HTML
            escaped_line = (
                line.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )

            if line.startswith(("+++", "---")):
                # File headers
                html_lines.append(f'<span style="font-weight: bold;">{escaped_line}</span>')
            elif line.startswith("+"):
                # Additions
                html_lines.append(
                    f'<span style="color: var(--jp-success-color1, #28a745); '
                    f'background: var(--jp-success-color3, #d4edda);">{escaped_line}</span>'
                )
            elif line.startswith("-"):
                # Deletions
                html_lines.append(
                    f'<span style="color: var(--jp-error-color1, #dc3545); '
                    f'background: var(--jp-error-color3, #f8d7da);">{escaped_line}</span>'
                )
            elif line.startswith("@@"):
                # Hunk headers
                html_lines.append(
                    f'<span style="color: var(--jp-info-color1, #0dcaf0); '
                    f'font-weight: 500;">{escaped_line}</span>'
                )
            else:
                # Context lines
                html_lines.append(
                    f'<span style="color: var(--jp-content-font-color1, inherit);">'
                    f'{escaped_line}</span>'
                )

        html_lines.append("</pre>")
        return "\n".join(html_lines)

    def summary(self) -> str:
        """Generate a text summary of the differences."""
        stats = self.stats
        
        if not self.has_changes:
            return (
                f"✓ No differences found between "
                f"{self.left_label} and {self.right_label}"
            )

        lines = [
            "XML Diff Summary",
            "=" * 70,
            f"Left:  {self.left_label}",
            f"Right: {self.right_label}",
            "",
            f"Changes: {stats['total_changes']} lines",
            f"  + {stats['additions']} additions",
            f"  - {stats['deletions']} deletions",
            "",
        ]

        return "\n".join(lines)

    def _repr_html_(self) -> str:
        """Rich HTML representation for Jupyter notebooks."""
        stats = self.stats
        
        # Build HTML with theme-aware styling
        html = """
    <div style="border: 1px solid var(--jp-border-color2, #e0e0e0); 
                border-radius: 4px; 
                padding: 12px; 
                margin: 8px 0; 
                font-size: 0.9em;">
        <div style="margin-bottom: 10px; 
                    padding-bottom: 8px; 
                    border-bottom: 1px solid var(--jp-border-color2, #e0e0e0);">
            <strong style="font-size: 1.1em;">📄 XML Diff Result</strong>
        </div>
"""

        # Status indicator
        if not self.has_changes:
            status_color = "var(--jp-success-color1, #28a745)"
            status_text = "✓ No differences"
            status_emoji = "✓"
        else:
            status_color = "var(--jp-warn-color1, #ff9800)"
            status_text = f"{self.change_count} change(s) found"
            status_emoji = "⚠"

        html += f"""
        <div style="margin-bottom: 12px;">
            <span style="margin-right: 16px; white-space: nowrap;">
                <span style="margin-right: 4px;">{status_emoji}</span>
                <span style="color: {status_color}; 
                             font-weight: 500;">{status_text}</span>
            </span>
        </div>
"""

        # Labels
        html += f"""
        <div style="margin-bottom: 12px; font-size: 0.85em; opacity: 0.8;">
            <div><strong>Left:</strong> {self.left_label}</div>
            <div><strong>Right:</strong> {self.right_label}</div>
        </div>
"""

        # Changes breakdown
        if self.has_changes:
            html += f"""
        <div style="margin-bottom: 12px;">
            <span style="margin-right: 16px; white-space: nowrap;">
                <span style="margin-right: 4px;">+</span>
                <span>{stats['additions']} additions</span>
            </span>
            <span style="margin-right: 16px; white-space: nowrap;">
                <span style="margin-right: 4px;">-</span>
                <span>{stats['deletions']} deletions</span>
            </span>
        </div>
"""

            # Detailed diff (collapsible)
            html += """
        <details style="margin-bottom: 12px;" open>
            <summary style="cursor: pointer;
                           font-weight: 500;
                           margin-bottom: 6px;">
                📋 Side-by-Side Diff
            </summary>
            <div style="margin-left: 0px;
                       font-size: 0.85em;
                       max-height: 600px;
                       overflow: auto;
                       border: 1px solid var(--jp-border-color2, #e0e0e0);
                       border-radius: 3px;
                       padding: 8px;">
"""
            html += self.as_html(side_by_side=True)
            html += """
            </div>
        </details>
"""

        # Footer with usage hints
        html += """
        <div style="margin-top: 12px; 
                    padding-top: 8px; 
                    border-top: 1px solid var(--jp-border-color2, #e0e0e0); 
                    font-size: 0.85em; 
                    opacity: 0.7;">
            <span>Use <code style="padding: 1px 4px; 
                                  border: 1px solid var(--jp-border-color2, #e0e0e0); 
                                  border-radius: 2px; 
                                  font-size: 0.9em;">.summary()</code> for text summary or <code style="padding: 1px 4px; 
                                  border: 1px solid var(--jp-border-color2, #e0e0e0); 
                                  border-radius: 2px; 
                                  font-size: 0.9em;">.as_text()</code> for plain diff</span>
        </div>
    </div>
"""

        return html

    def __str__(self) -> str:
        """String representation."""
        return self.as_text()

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"XmlDiffResult(changes={self.change_count}, "
            f"has_changes={self.has_changes})"
        )
