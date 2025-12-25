"""CaptureRecord エンティティ - raw.jsonl用のドメインモデル.

キャプチャログの不変性を保証し、ビジネスルールを実装する。
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, field_validator


class CaptureRecord(BaseModel):
    """キャプチャログレコードのドメインエンティティ.

    Attributes:
        ts: ISO 8601形式のタイムスタンプ
        window_title: ウィンドウタイトル（取得不可の場合はNone）
        process_name: プロセス名（オプショナル）
        keywords: 抽出されたキーワードリスト
        urls: 抽出されたURL/ドメインリスト
        files: 抽出されたファイルパスリスト
        numbers: 抽出された数値リスト
    """

    ts: Annotated[
        str,
        Field(
            description="ISO 8601形式のタイムスタンプ",
            examples=["2025-01-15T14:30:00+09:00"],
        ),
    ]
    window_title: Annotated[
        str | None,
        Field(
            default=None,
            description="ウィンドウタイトル",
            examples=["Chrome - Google"],
        ),
    ]
    process_name: Annotated[
        str | None,
        Field(
            default=None,
            description="プロセス名",
            examples=["chrome.exe", "code.exe"],
        ),
    ]
    keywords: Annotated[
        list[str],
        Field(
            default_factory=list,
            description="抽出されたキーワード",
            examples=[["login", "authentication", "OAuth"]],
        ),
    ]
    urls: Annotated[
        list[str],
        Field(
            default_factory=list,
            description="抽出されたURL/ドメイン",
            examples=[["https://github.com", "google.com"]],
        ),
    ]
    files: Annotated[
        list[str],
        Field(
            default_factory=list,
            description="抽出されたファイルパス",
            examples=[["C:\\Users\\okira\\report.xlsx"]],
        ),
    ]
    numbers: Annotated[
        list[str],
        Field(
            default_factory=list,
            description="抽出された数値",
            examples=[["123", "45.6"]],
        ),
    ]

    model_config = {
        "frozen": False,  # 集計処理で一時的に変更可能にする
        "str_strip_whitespace": True,
        "validate_assignment": True,
    }

    @field_validator("ts")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """タイムスタンプがISO 8601形式として解析可能か検証."""
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except (ValueError, AttributeError) as e:
            msg = f"無効なISO 8601タイムスタンプ: {v}"
            raise ValueError(msg) from e
        return v

    @field_validator("window_title", "process_name")
    @classmethod
    def validate_optional_string(cls, v: str | None) -> str | None:
        """空文字列をNoneに正規化."""
        if v is not None and v.strip() == "":
            return None
        return v

    @field_validator("keywords", "urls", "files", "numbers")
    @classmethod
    def validate_string_list(cls, v: list[str]) -> list[str]:
        """リスト内の空文字列と重複を除去."""
        return list(dict.fromkeys(s for s in v if s.strip()))

    @property
    def timestamp(self) -> datetime:
        """タイムスタンプをdatetimeオブジェクトとして取得."""
        return datetime.fromisoformat(self.ts.replace("Z", "+00:00"))

    @property
    def has_content(self) -> bool:
        """有効なコンテンツを持つかチェック."""
        return bool(
            self.window_title
            or self.process_name
            or self.keywords
            or self.urls
            or self.files
        )

    @property
    def app_identifier(self) -> str:
        """アプリケーション識別子（process_name優先、なければwindow_titleから推定）."""
        if self.process_name:
            return self.process_name.lower().replace(".exe", "")

        if self.window_title:
            # ウィンドウタイトルからアプリ名推定（例: "Chrome - Google" -> "chrome"）
            parts = self.window_title.lower().split("-")
            return parts[-1].strip() if len(parts) > 1 else "unknown"

        return "unknown"

    def merge_features(self, other: CaptureRecord) -> None:
        """他のレコードの特徴量を現在のレコードにマージ（重複排除）.

        Args:
            other: マージ元のCaptureRecord

        Note:
            タイムスタンプは変更されない。キーワード等のみ結合。
        """
        self.keywords = list(dict.fromkeys(self.keywords + other.keywords))
        self.urls = list(dict.fromkeys(self.urls + other.urls))
        self.files = list(dict.fromkeys(self.files + other.files))
        self.numbers = list(dict.fromkeys(self.numbers + other.numbers))

    def __str__(self) -> str:
        """人間が読みやすい文字列表現."""
        app = self.app_identifier
        title = self.window_title or "(タイトルなし)"
        return f"[{self.ts}] {app}: {title}"

    def __repr__(self) -> str:
        """デバッグ用の詳細表現."""
        return (
            f"CaptureRecord(ts={self.ts!r}, "
            f"window_title={self.window_title!r}, "
            f"process_name={self.process_name!r})"
        )
