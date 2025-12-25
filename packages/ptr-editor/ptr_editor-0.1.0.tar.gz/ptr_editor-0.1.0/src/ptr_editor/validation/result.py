"""
Validation results and issue reporting.

This module provides classes for representing validation results and issues.
It handles the reporting side of validation, keeping it separate from
validation logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pandas as pd


class Severity(Enum):
    """Severity levels for validation issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

    def __lt__(self, other: Severity) -> bool:
        """Allow severity comparison."""
        order = {
            Severity.INFO: 0,
            Severity.WARNING: 1,
            Severity.ERROR: 2,
            Severity.CRITICAL: 3,
        }
        return order[self] < order[other]


@dataclass(frozen=True)
class Issue:
    """
    A single validation issue.

    Immutable representation of a problem found during validation.
    """

    severity: Severity
    message: str
    path: str = "root"
    source: str = ""
    obj: Any = field(repr=False, default=None)

    @staticmethod
    def error(message: str, path: str = "root", source: str = "", obj: Any = None) -> Issue:
        """Create an error issue."""
        return Issue(Severity.ERROR, message, path, source, obj)

    @staticmethod
    def warning(message: str, path: str = "root", source: str = "", obj: Any = None) -> Issue:
        """Create a warning issue."""
        return Issue(Severity.WARNING, message, path, source, obj)

    @staticmethod
    def info(message: str, path: str = "root", source: str = "", obj: Any = None) -> Issue:
        """Create an info issue."""
        return Issue(Severity.INFO, message, path, source, obj)

    @staticmethod
    def critical(message: str, path: str = "root", source: str = "", obj: Any = None) -> Issue:
        """Create a critical issue."""
        return Issue(Severity.CRITICAL, message, path, source, obj)

    def __str__(self) -> str:
        parts = [f"[{self.severity.value.upper()}]"]
        if self.path and self.path != "root":
            parts.append(f"{self.path}:")
        parts.append(self.message)
        if self.source:
            parts.append(f"({self.source})")
        return " ".join(parts)


@dataclass
class Result:
    """
    Container for validation results.

    Holds all issues found during validation and provides
    convenient methods for querying them.
    """

    issues: list[Issue] = field(default_factory=list)

    def add(self, issue: Issue) -> None:
        """Add an issue to the result."""
        self.issues.append(issue)

    def extend(self, issues: list[Issue]) -> None:
        """Add multiple issues to the result."""
        self.issues.extend(issues)

    def merge(self, other: Result) -> None:
        """Merge another result into this one."""
        self.issues.extend(other.issues)

    @property
    def ok(self) -> bool:
        """Returns True if there are no errors or critical issues."""
        return not any(
            issue.severity in (Severity.ERROR, Severity.CRITICAL)
            for issue in self.issues
        )

    @property
    def has_warnings(self) -> bool:
        """Returns True if there are any warnings."""
        return any(issue.severity == Severity.WARNING for issue in self.issues)

    @property
    def has_errors(self) -> bool:
        """Returns True if there are any errors or critical issues."""
        return not self.ok

    def by_severity(self, severity: Severity) -> list[Issue]:
        """Get issues of a specific severity."""
        return [issue for issue in self.issues if issue.severity == severity]

    def errors(self) -> list[Issue]:
        """Get all error and critical issues."""
        return [
            issue
            for issue in self.issues
            if issue.severity in (Severity.ERROR, Severity.CRITICAL)
        ]

    def warnings(self) -> list[Issue]:
        """Get all warnings."""
        return self.by_severity(Severity.WARNING)

    def infos(self) -> list[Issue]:
        """Get all info issues."""
        return self.by_severity(Severity.INFO)

    def __bool__(self) -> bool:
        """Result is truthy if validation passed (no errors)."""
        return self.ok

    def __len__(self) -> int:
        """Number of issues."""
        return len(self.issues)

    def __str__(self) -> str:
        if not self.issues:
            return "✓ Validation passed"

        lines = [
            f"Validation: {len(self.errors())} errors, "
            f"{len(self.warnings())} warnings, "
            f"{len(self.infos())} info",
        ]
        for issue in self.issues:
            lines.append(f"  {issue}")
        return "\n".join(lines)

    def as_pandas(self) -> pd.DataFrame:
        """
        Convert validation results to a pandas DataFrame.

        Returns:
            DataFrame with columns: severity, path, message, source
        """
        import pandas as pd

        if not self.issues:
            return pd.DataFrame(columns=["severity", "path", "message", "source"])

        data = [
            {
                "severity": issue.severity.value,
                "path": issue.path,
                "message": issue.message,
                "source": issue.source,
            }
            for issue in self.issues
        ]
        return pd.DataFrame(data)

    def _repr_html_(self) -> str:
        """HTML representation for Jupyter notebooks."""
        from ptr_editor.validation.html import repr_html_validation_result

        return repr_html_validation_result(self)