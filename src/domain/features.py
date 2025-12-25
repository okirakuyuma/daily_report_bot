"""Features 値オブジェクト - features.json用のドメインモデル.

集計結果の不変性を保証し、ビジネスルールを実装する。
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, field_validator


class AppRank(str, Enum):
    """アプリ使用頻度ランク."""

    HIGH = "high"  # 使用時間上位33%
    MEDIUM = "medium"  # 使用時間中位33%
    LOW = "low"  # 使用時間下位33%


class AppUsage(BaseModel):
    """時間ブロック内のアプリ使用状況.

    Attributes:
        name: アプリ表示名
        percent: 該当時間ブロック内での使用割合（0-100）
    """

    name: Annotated[
        str,
        Field(
            description="アプリ表示名",
            min_length=1,
            examples=["Chrome", "VSCode"],
        ),
    ]
    percent: Annotated[
        float,
        Field(
            description="使用割合（%）",
            ge=0.0,
            le=100.0,
            examples=[45.5],
        ),
    ]

    @field_validator("percent")
    @classmethod
    def round_percent(cls, v: float) -> float:
        """パーセント値を小数点1桁に丸める."""
        return round(v, 1)


class TimeBlock(BaseModel):
    """時間ブロック単位の活動サマリ.

    Attributes:
        start: 開始時刻（HH:MM形式）
        end: 終了時刻（HH:MM形式）
        apps: アプリ使用状況リスト
        top_keywords: 頻出キーワード（上位N件）
        top_files: 頻出ファイルパス（上位N件）
    """

    start: Annotated[
        str,
        Field(
            description="開始時刻（HH:MM）",
            pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$",
            examples=["09:00", "14:30"],
        ),
    ]
    end: Annotated[
        str,
        Field(
            description="終了時刻（HH:MM）",
            pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$",
            examples=["10:00", "15:30"],
        ),
    ]
    apps: Annotated[
        list[AppUsage],
        Field(
            default_factory=list,
            description="アプリ使用状況（使用率降順）",
        ),
    ]
    top_keywords: Annotated[
        list[str],
        Field(
            default_factory=list,
            description="頻出キーワード",
            max_length=20,
        ),
    ]
    top_files: Annotated[
        list[str],
        Field(
            default_factory=list,
            description="頻出ファイルパス",
            max_length=10,
        ),
    ]

    @field_validator("apps")
    @classmethod
    def validate_apps_sorted(cls, v: list[AppUsage]) -> list[AppUsage]:
        """アプリリストを使用率降順にソート."""
        return sorted(v, key=lambda app: app.percent, reverse=True)

    @property
    def duration_minutes(self) -> int:
        """ブロックの長さ（分）を計算."""
        start_h, start_m = map(int, self.start.split(":"))
        end_h, end_m = map(int, self.end.split(":"))
        return (end_h * 60 + end_m) - (start_h * 60 + start_m)


class AppSummary(BaseModel):
    """アプリケーション別の集計サマリ.

    Attributes:
        name: 表示名
        process: プロセス名
        count: 観測回数
        duration_min: 推定使用時間（分）
        rank: 使用頻度ランク
        top_keywords: 頻出キーワード
        top_files: 頻出ファイルパス（オプショナル）
        top_urls: 頻出URL/ドメイン（オプショナル）
    """

    name: Annotated[
        str,
        Field(
            description="アプリ表示名",
            min_length=1,
            examples=["Google Chrome"],
        ),
    ]
    process: Annotated[
        str,
        Field(
            description="プロセス名",
            min_length=1,
            examples=["chrome.exe"],
        ),
    ]
    count: Annotated[
        int,
        Field(
            description="観測回数",
            ge=1,
            examples=[150],
        ),
    ]
    duration_min: Annotated[
        float,
        Field(
            description="推定使用時間（分）",
            ge=0.0,
            examples=[120.5],
        ),
    ]
    rank: Annotated[
        AppRank,
        Field(
            description="使用頻度ランク",
            examples=[AppRank.HIGH],
        ),
    ]
    top_keywords: Annotated[
        list[str],
        Field(
            default_factory=list,
            description="頻出キーワード",
            max_length=15,
        ),
    ]
    top_files: Annotated[
        list[str] | None,
        Field(
            default=None,
            description="頻出ファイルパス",
            max_length=10,
        ),
    ]
    top_urls: Annotated[
        list[str] | None,
        Field(
            default=None,
            description="頻出URL/ドメイン",
            max_length=10,
        ),
    ]

    @field_validator("duration_min")
    @classmethod
    def round_duration(cls, v: float) -> float:
        """使用時間を小数点1桁に丸める."""
        return round(v, 1)


class GlobalKeywords(BaseModel):
    """全体を通しての頻出特徴量.

    Attributes:
        top_keywords: グローバル頻出キーワード
        top_urls: グローバル頻出URL/ドメイン
        top_files: グローバル頻出ファイルパス
    """

    top_keywords: Annotated[
        list[str],
        Field(
            default_factory=list,
            description="グローバル頻出キーワード",
            max_length=50,
        ),
    ]
    top_urls: Annotated[
        list[str],
        Field(
            default_factory=list,
            description="グローバル頻出URL/ドメイン",
            max_length=20,
        ),
    ]
    top_files: Annotated[
        list[str],
        Field(
            default_factory=list,
            description="グローバル頻出ファイルパス",
            max_length=20,
        ),
    ]


class FeaturesMeta(BaseModel):
    """Features集計のメタデータ.

    Attributes:
        date: 対象日付（YYYY-MM-DD）
        generated_at: 生成タイムスタンプ（ISO 8601）
        capture_count: 総キャプチャ数
        first_capture: 最初のキャプチャ時刻
        last_capture: 最後のキャプチャ時刻
        total_duration_min: 総記録時間（分）
    """

    date: Annotated[
        str,
        Field(
            description="対象日付（YYYY-MM-DD）",
            pattern=r"^\d{4}-\d{2}-\d{2}$",
            examples=["2025-12-25"],
        ),
    ]
    generated_at: Annotated[
        str,
        Field(
            description="生成タイムスタンプ（ISO 8601）",
            examples=["2025-12-25T18:00:00+09:00"],
        ),
    ]
    capture_count: Annotated[
        int,
        Field(
            description="総キャプチャ数",
            ge=0,
            examples=[240],
        ),
    ]
    first_capture: Annotated[
        str,
        Field(
            description="最初のキャプチャ時刻",
            pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$",
            examples=["09:00:00"],
        ),
    ]
    last_capture: Annotated[
        str,
        Field(
            description="最後のキャプチャ時刻",
            pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$",
            examples=["18:00:00"],
        ),
    ]
    total_duration_min: Annotated[
        float,
        Field(
            description="総記録時間（分）",
            ge=0.0,
            examples=[480.0],
        ),
    ]

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        """日付が有効なYYYY-MM-DD形式か検証."""
        try:
            date.fromisoformat(v)
        except ValueError as e:
            msg = f"無効な日付形式: {v}"
            raise ValueError(msg) from e
        return v

    @field_validator("generated_at")
    @classmethod
    def validate_generated_at(cls, v: str) -> str:
        """生成タイムスタンプが有効なISO 8601形式か検証."""
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError as e:
            msg = f"無効なISO 8601タイムスタンプ: {v}"
            raise ValueError(msg) from e
        return v

    @field_validator("total_duration_min")
    @classmethod
    def round_total_duration(cls, v: float) -> float:
        """総記録時間を小数点1桁に丸める."""
        return round(v, 1)


class Features(BaseModel):
    """日報用の集計済み特徴量（features.json）.

    Attributes:
        meta: メタデータ
        time_blocks: 時間ブロック別サマリ
        app_summary: アプリケーション別サマリ
        global_keywords: グローバル頻出特徴量
    """

    meta: Annotated[
        FeaturesMeta,
        Field(description="メタデータ"),
    ]
    time_blocks: Annotated[
        list[TimeBlock],
        Field(
            default_factory=list,
            description="時間ブロック別サマリ",
        ),
    ]
    app_summary: Annotated[
        list[AppSummary],
        Field(
            default_factory=list,
            description="アプリケーション別サマリ（使用時間降順）",
        ),
    ]
    global_keywords: Annotated[
        GlobalKeywords,
        Field(
            default_factory=GlobalKeywords,
            description="グローバル頻出特徴量",
        ),
    ]

    model_config = {
        "frozen": True,  # 集計後は変更不可
        "validate_assignment": True,
    }

    @field_validator("app_summary")
    @classmethod
    def validate_app_summary_sorted(cls, v: list[AppSummary]) -> list[AppSummary]:
        """アプリサマリを使用時間降順にソート."""
        return sorted(v, key=lambda app: app.duration_min, reverse=True)

    @property
    def has_data(self) -> bool:
        """有効なデータを持つかチェック."""
        return self.meta.capture_count > 0 and len(self.app_summary) > 0

    @property
    def top_app(self) -> AppSummary | None:
        """最も使用時間が長いアプリを取得."""
        return self.app_summary[0] if self.app_summary else None

    @property
    def active_hours(self) -> float:
        """アクティブ時間（時間単位）を計算."""
        return round(self.meta.total_duration_min / 60.0, 1)

    def get_apps_by_rank(self, rank: AppRank) -> list[AppSummary]:
        """指定ランクのアプリをフィルタリング.

        Args:
            rank: フィルタリング対象のランク

        Returns:
            指定ランクのアプリリスト
        """
        return [app for app in self.app_summary if app.rank == rank]

    def __str__(self) -> str:
        """人間が読みやすい文字列表現."""
        return (
            f"Features({self.meta.date}, "
            f"{self.meta.capture_count} captures, "
            f"{len(self.app_summary)} apps)"
        )

    def __repr__(self) -> str:
        """デバッグ用の詳細表現."""
        return (
            f"Features(meta={self.meta!r}, "
            f"time_blocks={len(self.time_blocks)}, "
            f"app_summary={len(self.app_summary)})"
        )
