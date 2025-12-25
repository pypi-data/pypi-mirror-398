"""Diffing module for comparing PTR objects."""

from ptr_editor.diffing.diff_report import to_html
from ptr_editor.diffing.matcher import (
    AndMatcher,
    BlockMatcher,
    DurationMatcher,
    EqualityMatcher,
    IDMatcher,
    LambdaMatcher,
    Match,
    Matcher,
    MatchingRule,
    NotMatcher,
    OrMatcher,
    OverlapMatcher,
    PercentageOverlapMatcher,
    TimingMatcher,
    make_custom_matcher,
    make_duration_matcher,
    make_flexible_matcher,
    make_multi_id_matcher,
    make_overlap_matcher,
    make_progressive_matcher,
    make_robust_matcher,
    make_strict_matcher,
)
from ptr_editor.diffing.timeline_differ_simple import (
    DiffResult,
    TimelineDiffer,
    UpdateRecord,
)

__all__ = [
    # Report generation
    "to_html",
    # Timeline Differ (Step 2: Diffing)
    "TimelineDiffer",
    "DiffResult",
    "UpdateRecord",
    "ChangeType",
    # Matcher classes (Step 1: Matching)
    "Matcher",
    "IDMatcher",
    "TimingMatcher",
    "EqualityMatcher",
    "AndMatcher",
    "OrMatcher",
    "NotMatcher",
    "DurationMatcher",
    "OverlapMatcher",
    "PercentageOverlapMatcher",
    "LambdaMatcher",
    # Matcher orchestration
    "BlockMatcher",
    "MatchingRule",
    "Match",
    # Matcher factories
    "make_strict_matcher",
    "make_flexible_matcher",
    "make_robust_matcher",
    "make_multi_id_matcher",
    "make_overlap_matcher",
    "make_progressive_matcher",
    "make_duration_matcher",
    "make_custom_matcher",
]
