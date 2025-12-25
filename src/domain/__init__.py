"""Domain layer - entities and business rules.

このモジュールは純粋なドメインロジックを提供し、外部依存を持たない。
"""

from .capture import CaptureRecord
from .features import (
    AppRank,
    AppSummary,
    AppUsage,
    Features,
    FeaturesMeta,
    GlobalKeywords,
    TimeBlock,
)

__all__ = [
    # capture.py
    "CaptureRecord",
    # features.py
    "AppRank",
    "AppSummary",
    "AppUsage",
    "Features",
    "FeaturesMeta",
    "GlobalKeywords",
    "TimeBlock",
]
