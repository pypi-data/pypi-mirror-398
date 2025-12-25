"""
Simplified Timeline Differ - Detects and classifies changes in matched pairs.

Fast implementation that checks equality and classifies specific types of changes
using a simple, extensible checker system.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd
from attrs import define, field
from loguru import logger as log

if TYPE_CHECKING:
    from ptr_editor.diffing.matcher import Match, MatchResult


# ============================================================================
# Utility Functions
# ============================================================================


def _format_delta_time(delta: pd.Timedelta) -> str:
    """
    Format a time delta as HH:MM:SS with sign.
    Used in html diff report.

    Args:
        delta: Time delta as pd.Timedelta

    Returns:
        Formatted string like "+00:00:04" or "-00:01:30", or empty string if 0 seconds.
    """
    seconds = delta.total_seconds()
    if abs(seconds) ==  0:
        return ""

    sign = "+" if seconds >= 0 else "-"
    abs_seconds = abs(seconds)

    hours = int(abs_seconds // 3600)
    minutes = int((abs_seconds % 3600) // 60)
    secs = int(abs_seconds % 60)

    return f"{sign}{hours:02d}:{minutes:02d}:{secs:02d}"


# ============================================================================
# Change Detection
# ============================================================================


@dataclass(frozen=True)
class ChangeDetail:
    """
    Details about a specific type of change detected.

    Attributes:
        detected: Whether this change was detected
        description: Human-readable description of the change
    """

    detected: bool
    description: str = ""


# ============================================================================
# Update Record
# ============================================================================


@define
class UpdateRecord:
    """
    A matched pair that has changed, with detailed change classification.

    Attributes:
        match: The Match object from the matcher
        change_details: Dict mapping change type names to ChangeDetail objects

    Unpacking:
        Supports tuple unpacking to access the block pair directly:

        ```python
        (
            current,
            incoming,
        ) = update_record
        ```

        This is equivalent to:

        ```python
        current = update_record.current_block
        incoming = update_record.incoming_block
        ```
    """

    match: Match
    change_details: dict[str, ChangeDetail] = field(factory=dict)

    @property
    def current_block(self):
        """The current (left) block."""
        return self.match.left_block

    @property
    def incoming_block(self):
        """The incoming (right) block."""
        return self.match.right_block

    def has_change(self, change_type: str) -> bool:
        """Check if a specific change type was detected."""
        detail = self.change_details.get(change_type)
        return detail.detected if detail else False

    def get_changes(self) -> list[str]:
        """Get list of all detected change types."""
        return [name for name, detail in self.change_details.items() if detail.detected]

    def changes_tags(self) -> list[str]:
        """Get list of all detected change types as tags."""
        return [name for name, detail in self.change_details.items() if detail.detected]

    def tags(self) -> str:
        """Get comma-separated string of all detected change types as tags."""
        return ", ".join(self.changes_tags())

    def describe_changes(self) -> str:
        """Get human-readable description of all changes."""
        if not self.change_details:
            return "changed (no checkers configured)"

        descriptions = [
            detail.description
            for detail in self.change_details.values()
            if detail.detected and detail.description
        ]
        return "; ".join(descriptions) if descriptions else "changed"

    def xml_diff(self) -> str:
        """Generate XML diff between current and incoming blocks if supported."""
        if hasattr(self.current_block, "xml_diff") and callable(
            self.current_block.xml_diff,
        ):
            return self.current_block.xml_diff(self.incoming_block)
        return "XML diff not supported for this block type."

    def _repr_html_(self) -> str:
        diff = self.current_block.xml_diff(self.incoming_block)
        return diff._repr_html_()

    def __iter__(self):
        """
        Allow tuple unpacking for convenient access to block pairs.

        Enables convenient unpacking syntax:
        ```python
        (
            current,
            incoming,
        ) = update_record
        ```

        Returns:
        - current_block: The current (left) block
        - incoming_block: The incoming (right) block

        Example:
            >>> for update in diff_result.changes:
            ...     (
            ...         current,
            ...         incoming,
            ...     ) = update
            ...     print(
            ...         f"{current.id} changed"
            ...     )
        """
        return iter([self.current_block, self.incoming_block])


# ============================================================================
# Diff Result
# ============================================================================


@define
class DiffResult:
    """
    Complete changeset between current and incoming timelines.

    Attributes:
        additions: New blocks in incoming timeline
        deletions: Blocks removed from current timeline
        changes: Matched pairs that differ (list of UpdateRecord)
        unchanged: Matched pairs that are identical

    Unpacking:
        Supports tuple unpacking for convenient access:

        ```python
        (
            additions,
            deletions,
            changes,
        ) = diff_result
        ```

        This is equivalent to:

        ```python
        additions = diff_result.additions
        deletions = diff_result.deletions
        changes = diff_result.changed_blocks  # Note: unwrapped tuples
        ```

        The `changes` from unpacking are `(current, incoming)` tuples,
        not `UpdateRecord` objects. Use `diff_result.changes` directly
        if you need access to `UpdateRecord` metadata.
    """

    additions: list[Any] = field(factory=list)
    deletions: list[Any] = field(factory=list)
    changes: list[UpdateRecord] = field(factory=list)
    unchanged: list[Match] = field(factory=list)

    @property
    def changed_blocks(self) -> list[tuple[object, object]]:
        """
        Get list of changed block pairs as tuples.

        Returns unwrapped blocks without UpdateRecord metadata.
        Each tuple is (current_block, incoming_block).

        Returns:
            List of (current_block, incoming_block) tuples

        Example:
            >>> for (
            ...     current,
            ...     incoming,
            ... ) in result.changed_blocks:
            ...     print(
            ...         f"{current.id} changed"
            ...     )
        """
        return [(c.current_block, c.incoming_block) for c in self.changes]

    def __iter__(self):
        """
        Allow tuple unpacking for convenient access to diff components.

        Enables convenient unpacking syntax:
        ```python
        (
            additions,
            deletions,
            changes,
        ) = differ.diff(
            match_result
        )
        ```

        Returns:
        - additions: List of new blocks in incoming timeline
        - deletions: List of blocks removed from current timeline
        - changes: List of (current_block, incoming_block) tuples for modified pairs

        This is equivalent to:
        ```python
        result = (
            differ.diff(
                match_result
            )
        )
        additions = (
            result.additions
        )
        deletions = (
            result.deletions
        )
        changes = result.changed_blocks
        ```

        Example:
            >>> (
            ...     additions,
            ...     deletions,
            ...     changes,
            ... ) = differ.diff(
            ...     match_result
            ... )
            >>> print(
            ...     f"Added: {len(additions)}, Removed: {len(deletions)}"
            ... )
            >>> for (
            ...     current,
            ...     incoming,
            ... ) in changes:
            ...     print(
            ...         f"{current.id} changed"
            ...     )
        """
        return iter([self.additions, self.deletions, self.changed_blocks])

    def __getitem__(self, block_id: str) -> Any:
        """
        Look up a block by ID across all diff categories.

        Args:
            block_id: The ID of the block to find

        Returns:
            - Single item (Block, UpdateRecord, or Match) if only one match found
            - List of items if multiple matches found
            - None if not found

        Example:
            >>> result = (
            ...     differ.diff(
            ...         match_result
            ...     )
            ... )
            >>> change = result[
            ...     "BLOCK_001"
            ... ]  # Returns UpdateRecord if changed
            >>> items = result[
            ...     "BLOCK_002"
            ... ]  # Returns list if multiple matches
        """
        found_items = []

        block_id = str(block_id).strip()

        # Search in changes (check either side of the matched pair)
        for change in self.changes:
            if (
                getattr(change.current_block, "id", None) == block_id
                or getattr(change.incoming_block, "id", None) == block_id
            ):
                found_items.append(change)

        # Search in additions
        for block in self.additions:
            if getattr(block, "id", None) == block_id:
                found_items.append(block)

        # Search in deletions
        for block in self.deletions:
            if getattr(block, "id", None) == block_id:
                found_items.append(block)

        # Search in unchanged (check either side of the matched pair)
        for match in self.unchanged:
            if (
                getattr(match.left_block, "id", None) == block_id
                or getattr(match.right_block, "id", None) == block_id
            ):
                found_items.append(match)

        # Return based on number of matches
        if len(found_items) == 0:
            return None
        if len(found_items) == 1:
            return found_items[0]
        return found_items

    def get_update_by_id(self, block_id: str) -> UpdateRecord | None:
        """
        Look up an UpdateRecord by block ID in the changes.

        Args:
            block_id: The ID of the block to find

        Returns:
            - UpdateRecord if found
            - None if not found

        Example:
            >>> result = (
            ...     differ.diff(
            ...         match_result
            ...     )
            ... )
            >>> change = result.record_by_id(
            ...     "BLOCK_001"
            ... )
        """
        for change in self.changes:
            if (
                getattr(change.current_block, "id", None) == block_id
                or getattr(change.incoming_block, "id", None) == block_id
            ):
                return change
        return None

    def summary(self) -> str:
        """Human-readable summary of changes with detailed breakdown."""
        lines = [
            "Diff Summary",
            "=" * 70,
        ]

        # Overall counts
        lines.extend(
            [
                f"Total matched pairs: {len(self.changes) + len(self.unchanged)}",
                f"  - Unchanged: {len(self.unchanged)}",
                f"  - Changed: {len(self.changes)}",
                f"Additions: {len(self.additions)} (new in incoming)",
                f"Deletions: {len(self.deletions)} (removed from current)",
                "",
                f"Total changes: {len(self.additions) + len(self.deletions) + len(self.changes)}",
            ],
        )

        # All changes
        if self.changes:
            lines.extend(["", "Changes:", "-" * 70])
            for i, change in enumerate(self.changes, 1):
                change_id = getattr(change.current_block, "id", f"#{i}")
                lines.append(f"  [{change_id}] {change.tags()}")

        lines.append("=" * 70)
        return "\n".join(lines)

    def as_pandas(self, *, sorted_changes: bool = False) -> pd.DataFrame:
        """
        Convert changes to a pandas DataFrame with change matrix.

        Returns:
            DataFrame with block IDs as rows and change types as columns,
            with 'X' marking detected changes.
        """

        if not self.changes:
            # Return empty DataFrame with appropriate structure
            return pd.DataFrame()

        # Collect all unique change types across all changes
        all_change_types = set()
        for change in self.changes:
            all_change_types.update(change.change_details.keys())

        # Sort change types for consistent ordering
        if sorted_changes:
            change_types = sorted(all_change_types)
        else:
            change_types = list(all_change_types)

        # Build the matrix
        data = {}
        ids = []

        for change in self.changes:
            change_id = getattr(change.current_block, "id", f"#{len(ids) + 1}")
            ids.append(change_id)

            detected_changes = set(change.get_changes())
            for change_type in change_types:
                if change_type not in data:
                    data[change_type] = []
                data[change_type].append("X" if change_type in detected_changes else "")

        df = pd.DataFrame(data, index=ids)
        df.index.name = "Block ID"

        return df

    def to_pandas_full(self) -> pd.DataFrame:
        """
        Convert diff result to a comprehensive DataFrame with all information needed for reporting.

        Returns a DataFrame with one row per block, including:
        - Block ID
        - Status (changed/added/removed/unchanged)
        - Designer
        - Start time
        - End time
        - Duration (minutes)
        - Change types (for changed blocks)
        - Current XML (for changed/unchanged)
        - Incoming XML (for all)
        - Description

        Returns:
            DataFrame with all diff information, indexed by block ID
        """
        rows = []

        # Process changed blocks
        for change in self.changes:
            block_id = getattr(change.current_block, "id", "N/A")
            designer = getattr(change.current_block, "designer", "N/A")
            start = getattr(change.current_block, "start", None)
            end = getattr(change.current_block, "end", None)
            duration = None
            if start and end:
                duration = (end - start).total_seconds() / 60

            current_xml = "N/A"
            try:
                if hasattr(change.current_block, "xml"):
                    current_xml = change.current_block.xml
            except Exception:
                pass

            incoming_xml = "N/A"
            try:
                if hasattr(change.incoming_block, "xml"):
                    incoming_xml = change.incoming_block.xml
            except Exception:
                pass

            change_types = ", ".join(change.get_changes()) if change.get_changes() else "N/A"
            description = change.describe_changes()

            rows.append({
                "Block ID": block_id,
                "Status": "changed",
                "Designer": designer,
                "Start": start,
                "End": end,
                "Duration (min)": duration,
                "Change Types": change_types,
                "Description": description,
                "Current XML": current_xml,
                "Incoming XML": incoming_xml,
            })

        # Process additions
        for block in self.additions:
            block_id = getattr(block, "id", "N/A")
            designer = getattr(block, "designer", "N/A")
            start = getattr(block, "start", None)
            end = getattr(block, "end", None)
            duration = None
            if start and end:
                duration = (end - start).total_seconds() / 60

            incoming_xml = "N/A"
            try:
                if hasattr(block, "xml"):
                    incoming_xml = block.xml
            except Exception:
                pass

            rows.append({
                "Block ID": block_id,
                "Status": "added",
                "Designer": designer,
                "Start": start,
                "End": end,
                "Duration (min)": duration,
                "Change Types": "N/A",
                "Description": "Block added",
                "Current XML": "N/A",
                "Incoming XML": incoming_xml,
            })

        # Process deletions
        for block in self.deletions:
            block_id = getattr(block, "id", "N/A")
            designer = getattr(block, "designer", "N/A")
            start = getattr(block, "start", None)
            end = getattr(block, "end", None)
            duration = None
            if start and end:
                duration = (end - start).total_seconds() / 60

            current_xml = "N/A"
            try:
                if hasattr(block, "xml"):
                    current_xml = block.xml
            except Exception:
                pass

            rows.append({
                "Block ID": block_id,
                "Status": "removed",
                "Designer": designer,
                "Start": start,
                "End": end,
                "Duration (min)": duration,
                "Change Types": "N/A",
                "Description": "Block removed",
                "Current XML": current_xml,
                "Incoming XML": "N/A",
            })

        # Process unchanged blocks
        for match in self.unchanged:
            block_id = getattr(match.left_block, "id", "N/A")
            designer = getattr(match.left_block, "designer", "N/A")
            start = getattr(match.left_block, "start", None)
            end = getattr(match.left_block, "end", None)
            duration = None
            if start and end:
                duration = (end - start).total_seconds() / 60

            current_xml = "N/A"
            try:
                if hasattr(match.left_block, "xml"):
                    current_xml = match.left_block.xml
            except Exception:
                pass

            incoming_xml = "N/A"
            try:
                if hasattr(match.right_block, "xml"):
                    incoming_xml = match.right_block.xml
            except Exception:
                pass

            rows.append({
                "Block ID": block_id,
                "Status": "unchanged",
                "Designer": designer,
                "Start": start,
                "End": end,
                "Duration (min)": duration,
                "Change Types": "N/A",
                "Description": "No changes",
                "Current XML": current_xml,
                "Incoming XML": incoming_xml,
            })

        df = pd.DataFrame(rows)
        return df

    def report(self):
        """Print summary with rich formatted table."""

        # Fallback to simple text output
        sys.stdout.write(self.summary() + "\n")

    def _repr_html_(self):
        """
        Uses CSS variables with fallbacks and minimal styling to respect
        the notebook theme.
        """
        # Helper to generate ID cell with copy button (left-aligned, button before ID)
        def id_cell(block_id: str) -> str:
            escaped_id = str(block_id).replace("'", "\\'")
            return f'''<td style="text-align: left; padding: 6px; white-space: nowrap;">
                <button onclick="navigator.clipboard.writeText('{escaped_id}').then(() => {{ this.textContent='✓'; setTimeout(() => this.textContent='📋', 1000); }})" 
                    style="margin-right: 4px; padding: 0; font-size: 0.85em; cursor: pointer; border: none; background: transparent; opacity: 0.6;" 
                    title="Copy ID to clipboard">📋</button>
                <strong>{block_id}</strong>
            </td>'''

        html = """
    <div style="border: 1px solid var(--jp-border-color2, #e0e0e0); border-radius: 4px; padding: 12px; margin: 8px 0; font-size: 0.9em;">
        <div style="margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid var(--jp-border-color2, #e0e0e0);">
            <strong style="font-size: 1.1em;">📊 Diff Results</strong>
        </div>
"""

        # Summary metrics as inline elements
        html += """
        <div style="margin-bottom: 12px;">
"""

        total_pairs = len(self.changes) + len(self.unchanged)
        total_changes = len(self.additions) + len(self.deletions) + len(self.changes)

        metrics = [
            (f"{total_pairs} pairs", "✓"),
            (f"{len(self.unchanged)} unchanged", "═"),
            (f"{len(self.changes)} changed", "≠"),
            (f"{len(self.additions)} additions", "+"),
            (f"{len(self.deletions)} deletions", "−"),
            (f"{total_changes} total changes", "Σ"),
        ]

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

        if not self.changes and not self.additions and not self.deletions:
            html += """
        <div style="background: #d4edda; color: #155724; padding: 12px; border-radius: 4px; border: 1px solid #c3e6cb; text-align: center; font-weight: 500;">
            ✅ No changes detected - all blocks are identical!
        </div>
    </div>
            """
            return html

        # Changed blocks - unified table with time deltas and change type markers
        if self.changes:
            df = self.as_pandas()
            change_types = list(df.columns)

            html += f"""
        <details style="margin-bottom: 12px;" open>
            <summary style="cursor: pointer; font-weight: 500; margin-bottom: 6px; color: #fd7e14;">
                ≠ Changed ({len(self.changes)} blocks)
            </summary>
            <div style="margin-left: 16px; max-height: 600px; overflow-y: auto; font-size: 0.85em;">
                <table style="border-collapse: collapse; font-size: 0.9em;">
                    <thead>
                        <tr style="border-bottom: 2px solid var(--jp-border-color2, #e0e0e0);">
                            <th style="text-align: left; padding: 6px;">Block ID</th>
                            <th style="text-align: right; padding: 6px;">Start Δt</th>
                            <th style="text-align: right; padding: 6px;">End Δt</th>
                            <th style="text-align: right; padding: 6px;">Dur Δt</th>
"""
            for col in change_types:
                html += f'                            <th style="text-align: center; padding: 6px;">{col}</th>\n'
            html += """                        </tr>
                    </thead>
                    <tbody>
"""

            for change in self.changes:
                block_id = getattr(change.current_block, "id", "N/A")
                start_drift = end_drift = duration_change = "—"

                # Calculate time deltas
                if all(
                    hasattr(b, "start") and hasattr(b, "end") and b.start and b.end
                    for b in [change.current_block, change.incoming_block]
                ):
                    start_drift = _format_delta_time(
                        change.incoming_block.start - change.current_block.start
                    )
                    end_drift = _format_delta_time(
                        change.incoming_block.end - change.current_block.end
                    )
                    duration_change = _format_delta_time(
                        (
                            change.incoming_block.end
                            - change.incoming_block.start
                        )
                        - (
                            change.current_block.end
                            - change.current_block.start
                        )
                    )

                html += f"""<tr style="border-bottom: 1px solid var(--jp-border-color2, #e0e0e0);">
                            {id_cell(block_id)}
                            <td style="text-align: right; padding: 6px;">{start_drift}</td>
                            <td style="text-align: right; padding: 6px;">{end_drift}</td>
                            <td style="text-align: right; padding: 6px;">{duration_change}</td>
"""
                for col in change_types:
                    val = df.loc[block_id, col] if block_id in df.index else ""
                    html += f'                            <td style="text-align: center; padding: 6px;">{val}</td>\n'
                html += "                        </tr>\n"

            html += """                    </tbody>
                </table>
            </div>
        </details>
"""

        # Additions - detailed table
        if self.additions:
            html += f"""
        <details style="margin-bottom: 12px;">
            <summary style="cursor: pointer; font-weight: 500; margin-bottom: 6px; color: #007bff;">
                + Added ({len(self.additions)} blocks)
            </summary>
            <div style="margin-left: 16px; max-height: 500px; overflow-y: auto; font-size: 0.85em;">
                <table style="border-collapse: collapse; width: 100%; font-size: 0.9em;">
                    <thead>
                        <tr style="border-bottom: 2px solid var(--jp-border-color2, #e0e0e0);">
                            <th style="text-align: left; padding: 6px;">ID</th>
                            <th style="text-align: left; padding: 6px;">Start</th>
                            <th style="text-align: left; padding: 6px;">End</th>
                            <th style="text-align: right; padding: 6px;">Duration (min)</th>
                        </tr>
                    </thead>
                    <tbody>
"""

            for block in self.additions:
                block_id = getattr(block, "id", "N/A")
                start = getattr(block, "start", "N/A")
                end = getattr(block, "end", "N/A")
                duration = "N/A"

                if (
                    hasattr(block, "start")
                    and hasattr(block, "end")
                    and block.start
                    and block.end
                ):
                    duration_sec = (block.end - block.start).total_seconds()
                    duration = f"{duration_sec / 60:.1f}"
                    start = str(start)
                    end = str(end)

                html += f"""
                        <tr style="border-bottom: 1px solid var(--jp-border-color2, #e0e0e0);">
                            {id_cell(block_id)}
                            <td style="padding: 6px; font-size: 0.85em;">{start}</td>
                            <td style="padding: 6px; font-size: 0.85em;">{end}</td>
                            <td style="text-align: right; padding: 6px;">{duration}</td>
                        </tr>
"""

            html += """
                    </tbody>
                </table>
            </div>
        </details>
"""

        # Deletions - detailed table
        if self.deletions:
            html += f"""
        <details style="margin-bottom: 12px;">
            <summary style="cursor: pointer; font-weight: 500; margin-bottom: 6px; color: #dc3545;">
                - Removed ({len(self.deletions)} blocks)
            </summary>
            <div style="margin-left: 16px; max-height: 500px; overflow-y: auto; font-size: 0.85em;">
                <table style="border-collapse: collapse; width: 100%; font-size: 0.9em;">
                    <thead>
                        <tr style="border-bottom: 2px solid var(--jp-border-color2, #e0e0e0);">
                            <th style="text-align: left; padding: 6px;">ID</th>
                            <th style="text-align: left; padding: 6px;">Start</th>
                            <th style="text-align: left; padding: 6px;">End</th>
                            <th style="text-align: right; padding: 6px;">Duration (min)</th>
                        </tr>
                    </thead>
                    <tbody>
"""

            for block in self.deletions:
                block_id = getattr(block, "id", "N/A")
                start = getattr(block, "start", "N/A")
                end = getattr(block, "end", "N/A")
                duration = "N/A"

                if (
                    hasattr(block, "start")
                    and hasattr(block, "end")
                    and block.start
                    and block.end
                ):
                    duration_sec = (block.end - block.start).total_seconds()
                    duration = f"{duration_sec / 60:.1f}"
                    start = str(start)
                    end = str(end)

                html += f"""
                        <tr style="border-bottom: 1px solid var(--jp-border-color2, #e0e0e0);">
                            {id_cell(block_id)}
                            <td style="padding: 6px; font-size: 0.85em;">{start}</td>
                            <td style="padding: 6px; font-size: 0.85em;">{end}</td>
                            <td style="text-align: right; padding: 6px;">{duration}</td>
                        </tr>
"""

            html += """
                    </tbody>
                </table>
            </div>
        </details>
"""

        html += """
    </div>
"""

        return html

    def to_html(
        self,
        output_file: str | Path | None = None,
        compact: bool = False,
        open: bool = False,
    ) -> str:
        """
        Generate interactive HTML report for this diff result.

        Creates a comprehensive HTML report including:
        - Summary statistics (matched pairs, changes, additions, deletions)
        - Changed blocks with detailed change analysis
        - Additions (new blocks)
        - Deletions (removed blocks)
        - Unchanged blocks (in collapsible section)

        Args:
            output_file: Path to save HTML file. If None, returns HTML string.
            compact: If True, uses minimal styling suitable for Jupyter notebooks.
                    If False, uses full styled report for standalone HTML files.
            open: If True, opens the report in a web browser. If output_file is None,
                  creates a temporary file first.

        Returns:
            HTML string of the generated report.

        Example:
            >>> from ptr_editor.diffing import TimelineDiffer
            >>> differ = TimelineDiffer()
            >>> diff_result = differ.diff(match_result)
            >>> # Save to file
            >>> html = diff_result.to_html("changes.html")
            >>> # Save and open in browser
            >>> html = diff_result.to_html("changes.html", open=True)
            >>> # Open in browser with temp file
            >>> html = diff_result.to_html(open=True)
            >>> # Just get HTML string
            >>> html = diff_result.to_html()
        """
        from ptr_editor.diffing.diff_report import to_html

        return to_html(self, output_file=output_file, compact=compact, open=open)


# ============================================================================
# Timeline Differ
# ============================================================================


@define
class TimelineDiffer:
    """
    Differ that detects and classifies changes in matched objects.

    Uses a list of checker instances to classify specific types of changes.
    Each checker has a check() method that returns a ChangeDetail with detection status.

    Note: If no checkers are provided, changes will be detected but not classified.
    Use make_timeline_differ() factory function to create a differ with standard checkers.
    """

    checkers: list[CheckerBase] = field(factory=list)

    def diff(self, match_result: MatchResult) -> DiffResult:
        """
        Detect and classify changes in a MatchResult.

        Args:
            match_result: Output from BlockMatcher.match()

        Returns:
            DiffResult with additions, deletions, changes, and unchanged
        """
        additions = match_result.unmatched_blocks_right
        deletions = match_result.unmatched_blocks_left

        # Separate changed from unchanged pairs
        changes = []
        unchanged = []
        for match in match_result.matches:
            if self._are_equal(match):
                unchanged.append(match)
            else:
                update = self._classify_changes(match)
                changes.append(update)

        return DiffResult(
            additions=additions,
            deletions=deletions,
            changes=changes,
            unchanged=unchanged,
        )

    def _are_equal(self, match: Match) -> bool:
        """Check if a matched pair is equal."""
        return match.left_block == match.right_block

    def _classify_changes(self, match: Match) -> UpdateRecord:
        """Classify what changed in a matched pair."""
        change_details = {}

        # Run all registered checkers
        for checker in self.checkers:
            try:
                name, detail = checker.check(match.left_block, match.right_block)
                change_details[name] = detail
            except Exception as e:
                # Log error but continue with other checkers

                checker_name = checker.__class__.__name__
                log.error(
                    f"Checker {checker_name} failed for match {match}: {e}",
                    exc_info=True,
                )

        return UpdateRecord(match=match, change_details=change_details)


# ============================================================================
# Built-in Change Checkers
# ============================================================================


class CheckerBase:
    """
    Base class for change checkers.

    Subclasses should implement the check() method to detect specific types of changes.
    """

    def check(self, current: Any, incoming: Any) -> tuple[str, ChangeDetail]:
        """
        Check for a specific type of change between current and incoming objects.

        Args:
            current: Current (left) object
            incoming: Incoming (right) object

        Returns:
            Tuple of (change_name, ChangeDetail)
        """
        raise NotImplementedError


class MoveChecker(CheckerBase):
    """Check if start and end moved together (same duration)."""

    def check(self, current: Any, incoming: Any) -> tuple[str, ChangeDetail]:
        start_changed = current.start != incoming.start
        end_changed = current.end != incoming.end
        current_duration = (current.end - current.start).total_seconds()
        incoming_duration = (incoming.end - incoming.start).total_seconds()
        duration_unchanged = abs(current_duration - incoming_duration) < 0.001

        if start_changed and end_changed and duration_unchanged:
            drift = (incoming.start - current.start).total_seconds()
            sign = "+" if drift > 0 else ""
            return (
                "move",
                ChangeDetail(detected=True, description=f"moved {sign}{drift:.1f}s"),
            )

        return ("move", ChangeDetail(detected=False))


@define
class TimeAttributeChecker(CheckerBase):
    """
    Check if a time attribute changed.

    Args:
        attr_name: Name of the time attribute to check (e.g., "start", "end")
        tag_name: Optional custom tag name (defaults to attr_name)
    """

    attr_name: str
    tag_name: str | None = field(default=None)

    def __attrs_post_init__(self):
        if self.tag_name is None:
            object.__setattr__(self, "tag_name", self.attr_name)

    def check(self, current: Any, incoming: Any) -> tuple[str, ChangeDetail]:
        current_time = getattr(current, self.attr_name)
        incoming_time = getattr(incoming, self.attr_name)

        if current_time != incoming_time:
            drift = (incoming_time - current_time).total_seconds()
            sign = "+" if drift > 0 else ""
            return (
                self.tag_name,
                ChangeDetail(
                    detected=True,
                    description=f"{self.attr_name} {sign}{drift:.1f}s",
                ),
            )
        return (self.tag_name, ChangeDetail(detected=False))


class DurationChangeChecker(CheckerBase):
    """Check if duration changed."""

    def check(self, current: Any, incoming: Any) -> tuple[str, ChangeDetail]:
        current_duration = (current.end - current.start).total_seconds()
        incoming_duration = (incoming.end - incoming.start).total_seconds()
        diff = incoming_duration - current_duration

        if abs(diff) > 0.001:  # More than 1ms difference
            sign = "+" if diff > 0 else ""
            return (
                "duration",
                ChangeDetail(detected=True, description=f"duration {sign}{diff:.1f}s"),
            )
        return ("duration", ChangeDetail(detected=False))


@define
class AttributeChangeChecker(CheckerBase):
    """
    Check for changes in a specific attribute.

    Supports nested attributes using dot notation (e.g., "attitude.phase_angle").

    Args:
        attr_name: Attribute name or path using dot notation
        tag_name: Optional custom tag name (defaults to last part of attr_name)

    Example:
        >>> checker = AttributeChangeChecker(
        ...     "attitude.phase_angle.value"
        ... )
        >>> checker.check(
        ...     block1, block2
        ... )  # Accesses block.attitude.phase_angle.value
    """

    attr_name: str
    tag_name: str | None = field(default=None)

    def __attrs_post_init__(self):
        if self.tag_name is None:
            object.__setattr__(self, "tag_name", self.attr_name.split(".")[-1])

    def check(self, current: Any, incoming: Any) -> tuple[str, ChangeDetail]:
        current_val = self._get_nested_attr(current, self.attr_name)
        incoming_val = self._get_nested_attr(incoming, self.attr_name)

        if current_val != incoming_val:
            return (
                self.tag_name,
                ChangeDetail(
                    detected=True,
                    description=f"{self.attr_name}: {current_val} → {incoming_val}",
                ),
            )
        return (self.tag_name, ChangeDetail(detected=False))

    def _get_nested_attr(self, obj: Any, attr_path: str) -> Any:
        """
        Get attribute value supporting dot notation for nested access.

        Args:
            obj: Object to get attribute from
            attr_path: Attribute path, e.g., "attitude.phase_angle.value"

        Returns:
            Attribute value or None if not found
        """
        parts = attr_path.split(".")
        current = obj

        for part in parts:
            if not hasattr(current, part):
                return None
            current = getattr(current, part)

        return current


# ============================================================================
# Factory Functions
# ============================================================================


def make_timeline_differ(
    *,
    include_temporal: bool = True,
    include_attributes: list[str] | None = None,
    custom_checkers: list[CheckerBase] | None = None,
) -> TimelineDiffer:
    """
    Create a TimelineDiffer with standard checkers.

    Args:
        include_temporal: Include temporal change checkers (move, start, end, duration)
        include_attributes: List of attribute names to check for changes
        custom_checkers: Additional custom checker instances

    Returns:
        Configured TimelineDiffer instance

    Example:
        >>> differ = make_timeline_differ(
        ...     include_temporal=True,
        ...     include_attributes=[
        ...         "name",
        ...         "priority",
        ...     ],
        ... )
        >>> diff_result = (
        ...     differ.diff(
        ...         match_result
        ...     )
        ... )
        >>> for change in diff_result.changes:
        ...     print(
        ...         change.describe_changes()
        ...     )
    """
    checkers = []

    if include_temporal:
        checkers.extend(
            [
                MoveChecker(),
                TimeAttributeChecker("start"),
                TimeAttributeChecker("end"),
                TimeAttributeChecker("duration"),
            ],
        )

    if include_attributes:
        checkers.extend([AttributeChangeChecker(attr) for attr in include_attributes])

    if custom_checkers:
        checkers.extend(custom_checkers)

    return TimelineDiffer(checkers=checkers)
