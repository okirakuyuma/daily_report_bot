"""LogAggregationService - ログ集計サービス

raw.jsonlを読み込み、LLM要約に適した形式（features.json）に変換。
設計書: docs/design/02-aggregation-flow.md
"""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.domain.features import (
    AppRank,
    AppSummary,
    AppUsage,
    Features,
    FeaturesMeta,
    GlobalKeywords,
    TimeBlock,
)
from src.repositories.log_repository import LogRepository
from src.utils.text_utils import calculate_rank, merge_keywords, normalize_app_name
from src.utils.time_utils import (
    JST,
    calculate_duration_min,
    get_time_block,
    parse_ts,
)

logger = logging.getLogger(__name__)


# 設定パラメータ（デフォルト値）
DEFAULT_CONFIG = {
    "exclude_recent_sec": 120,  # 直近除外秒数
    "time_block_min": 30,  # 時間ブロック長（分）
    "top_keywords_count": 10,  # 上位キーワード数
    "top_files_count": 5,  # 上位ファイル数
    "top_urls_count": 5,  # 上位URL数
    "sampling_interval_sec": 120,  # サンプリング間隔（秒）
    "min_captures_for_report": 5,  # レポート生成最小キャプチャ数
}


def _filter_recent(
    records: list[dict[str, Any]],
    exclude_sec: int = 120,
    ts_field: str = "ts",
) -> list[dict[str, Any]]:
    """直近N秒のレコードを除外（安定化のため）

    Args:
        records: レコードリスト
        exclude_sec: 除外する秒数
        ts_field: タイムスタンプフィールド名

    Returns:
        フィルタリング後のレコードリスト
    """
    if not records:
        return []

    from datetime import timedelta

    now = datetime.now(JST)
    threshold = now - timedelta(seconds=exclude_sec)

    filtered = []
    for record in records:
        try:
            ts_value = record.get(ts_field)
            if ts_value is None:
                continue
            ts = parse_ts(ts_value)
            if ts <= threshold:
                filtered.append(record)
        except (ValueError, TypeError):
            # タイムスタンプが無効なレコードはスキップ
            continue

    logger.debug(
        f"Filtered recent records: {len(records)} -> {len(filtered)} "
        f"(excluded {len(records) - len(filtered)} recent records)"
    )

    return filtered


def _group_by_time_block(
    records: list[dict[str, Any]],
    block_min: int = 30,
    ts_field: str = "ts",
) -> dict[tuple[str, str], list[dict[str, Any]]]:
    """レコードを時間ブロックでグループ化

    Args:
        records: レコードリスト
        block_min: ブロックの長さ（分）
        ts_field: タイムスタンプフィールド名

    Returns:
        {(start, end): [records...]} の辞書
    """
    blocks: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for record in records:
        try:
            ts_value = record.get(ts_field)
            if ts_value is None:
                continue
            ts = parse_ts(ts_value)
            block_key = get_time_block(ts, block_min)
            blocks[block_key].append(record)
        except (ValueError, TypeError):
            continue

    return dict(blocks)


def _build_time_blocks(
    grouped: dict[tuple[str, str], list[dict[str, Any]]],
    top_keywords_count: int = 10,
    top_files_count: int = 5,
) -> list[TimeBlock]:
    """グループ化されたデータから TimeBlock リストを生成

    Args:
        grouped: 時間ブロックでグループ化されたレコード
        top_keywords_count: 上位キーワード数
        top_files_count: 上位ファイル数

    Returns:
        TimeBlock リスト（時刻順）
    """
    time_blocks: list[TimeBlock] = []

    for (start, end), block_records in sorted(grouped.items()):
        if not block_records:
            continue

        # アプリ別カウント
        app_counter: Counter[str] = Counter()
        for record in block_records:
            process_name = record.get("process_name")
            app_name = normalize_app_name(process_name)
            app_counter[app_name] += 1

        total_count = sum(app_counter.values())

        # AppUsage リスト作成（上位5件）
        apps: list[AppUsage] = []
        for app_name, count in app_counter.most_common(5):
            percent = (count / total_count) * 100 if total_count > 0 else 0.0
            apps.append(AppUsage(name=app_name, percent=percent))

        # キーワード集計
        top_keywords = merge_keywords(block_records, field="keywords")[
            :top_keywords_count
        ]

        # ファイル集計
        top_files = merge_keywords(block_records, field="files")[:top_files_count]

        time_blocks.append(
            TimeBlock(
                start=start,
                end=end,
                apps=apps,
                top_keywords=top_keywords,
                top_files=top_files,
            )
        )

    return time_blocks


def _build_app_summary(
    records: list[dict[str, Any]],
    sampling_interval_sec: int = 120,
    top_keywords_count: int = 10,
    top_files_count: int = 5,
    top_urls_count: int = 5,
) -> list[AppSummary]:
    """アプリケーション別の集計サマリを生成

    Args:
        records: レコードリスト
        sampling_interval_sec: サンプリング間隔（秒）
        top_keywords_count: 上位キーワード数
        top_files_count: 上位ファイル数
        top_urls_count: 上位URL数

    Returns:
        AppSummary リスト（使用時間降順）
    """
    # プロセス名でグループ化
    app_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        process_name = record.get("process_name") or "Unknown"
        app_groups[process_name].append(record)

    total_count = len(records)
    app_summaries: list[AppSummary] = []

    for process_name, app_records in app_groups.items():
        count = len(app_records)
        duration_min = (count * sampling_interval_sec) / 60.0

        # ランク計算
        rank_str = calculate_rank(count, total_count)
        rank = AppRank(rank_str)

        # アプリ表示名
        app_name = normalize_app_name(process_name)

        # キーワード集計
        top_keywords = merge_keywords(app_records, field="keywords")[
            :top_keywords_count
        ]

        # ファイル集計
        files = merge_keywords(app_records, field="files")[:top_files_count]
        top_files = files if files else None

        # URL集計
        urls = merge_keywords(app_records, field="urls")[:top_urls_count]
        top_urls = urls if urls else None

        app_summaries.append(
            AppSummary(
                name=app_name,
                process=process_name,
                count=count,
                duration_min=duration_min,
                rank=rank,
                top_keywords=top_keywords,
                top_files=top_files,
                top_urls=top_urls,
            )
        )

    # 使用時間降順でソート（Featuresの validator でもソートされるが、明示的に）
    return sorted(app_summaries, key=lambda x: x.duration_min, reverse=True)


def _build_global_keywords(
    records: list[dict[str, Any]],
    top_keywords_count: int = 10,
    top_files_count: int = 5,
    top_urls_count: int = 5,
) -> GlobalKeywords:
    """グローバル頻出特徴量を生成

    Args:
        records: レコードリスト
        top_keywords_count: 上位キーワード数
        top_files_count: 上位ファイル数
        top_urls_count: 上位URL数

    Returns:
        GlobalKeywords オブジェクト
    """
    top_keywords = merge_keywords(records, field="keywords")[:top_keywords_count]
    top_urls = merge_keywords(records, field="urls")[:top_urls_count]
    top_files = merge_keywords(records, field="files")[:top_files_count]

    return GlobalKeywords(
        top_keywords=top_keywords,
        top_urls=top_urls,
        top_files=top_files,
    )


def _build_meta(
    target_date: date,
    records: list[dict[str, Any]],
    sampling_interval_sec: int = 120,
    ts_field: str = "ts",
) -> FeaturesMeta:
    """メタデータを生成

    Args:
        target_date: 対象日
        records: レコードリスト
        sampling_interval_sec: サンプリング間隔（秒）
        ts_field: タイムスタンプフィールド名

    Returns:
        FeaturesMeta オブジェクト
    """
    capture_count = len(records)

    # 最初と最後のキャプチャ時刻を取得
    timestamps: list[datetime] = []
    for record in records:
        try:
            ts_value = record.get(ts_field)
            if ts_value:
                timestamps.append(parse_ts(ts_value))
        except (ValueError, TypeError):
            continue

    if timestamps:
        timestamps.sort()
        first_ts = timestamps[0]
        last_ts = timestamps[-1]
        first_capture = first_ts.strftime("%H:%M:%S")
        last_capture = last_ts.strftime("%H:%M:%S")
        total_duration_min = calculate_duration_min(
            first_ts.isoformat(),
            last_ts.isoformat(),
            sampling_interval_sec,
        )
    else:
        first_capture = "00:00:00"
        last_capture = "00:00:00"
        total_duration_min = 0

    generated_at = datetime.now(JST).isoformat()

    return FeaturesMeta(
        date=target_date.isoformat(),
        generated_at=generated_at,
        capture_count=capture_count,
        first_capture=first_capture,
        last_capture=last_capture,
        total_duration_min=total_duration_min,
    )


class LogAggregationService:
    """ログ集計サービス

    raw.jsonlを読み込み、LLM要約に適したfeatures.jsonを生成。

    処理ステップ:
    1. 対象日のログファイル特定
    2. raw.jsonl 読み込み（直近N秒除外）
    3. 時間ブロック生成
    4. アプリ別集計
    5. キーワード集計
    6. features.json 出力

    Note:
        セッション化（Phase 2機能）は現在スキップ
    """

    def __init__(
        self,
        repository: LogRepository | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        """初期化

        Args:
            repository: LogRepositoryインスタンス（依存性注入）
            config: 設定パラメータ（オプション）
        """
        self.repository = repository or LogRepository()
        self.config = {**DEFAULT_CONFIG, **(config or {})}

        logger.debug(f"LogAggregationService initialized with config: {self.config}")

    def aggregate(self, target_date: date | None = None) -> Features:
        """ログを集計してFeaturesを生成

        Args:
            target_date: 対象日（Noneの場合は当日）

        Returns:
            集計結果のFeaturesオブジェクト

        Raises:
            LogFileNotFoundError: ログファイルが存在しない
            LogFileEmptyError: ログファイルが空
            LogParseError: 全行解析エラー
            ValueError: キャプチャ数が最小値未満
        """
        if target_date is None:
            target_date = date.today()

        logger.info(f"Starting aggregation for date: {target_date}")

        # 1. raw.jsonl 読み込み
        raw_records = self.repository.read_raw_logs(target_date)
        logger.info(f"Read {len(raw_records)} raw records")

        # 2. 直近N秒を除外
        records = _filter_recent(
            raw_records,
            exclude_sec=self.config["exclude_recent_sec"],
            ts_field="ts",
        )
        logger.info(f"After filtering recent: {len(records)} records")

        # 最小キャプチャ数チェック
        min_captures = self.config["min_captures_for_report"]
        if len(records) < min_captures:
            logger.warning(
                f"Not enough captures for report: {len(records)} < {min_captures}"
            )
            # 警告のみでエラーにはしない（空のFeaturesを返す）

        # 3. 時間ブロック生成
        grouped = _group_by_time_block(
            records,
            block_min=self.config["time_block_min"],
            ts_field="ts",
        )
        time_blocks = _build_time_blocks(
            grouped,
            top_keywords_count=self.config["top_keywords_count"],
            top_files_count=self.config["top_files_count"],
        )
        logger.info(f"Generated {len(time_blocks)} time blocks")

        # 4. アプリ別集計
        app_summary = _build_app_summary(
            records,
            sampling_interval_sec=self.config["sampling_interval_sec"],
            top_keywords_count=self.config["top_keywords_count"],
            top_files_count=self.config["top_files_count"],
            top_urls_count=self.config["top_urls_count"],
        )
        logger.info(f"Generated {len(app_summary)} app summaries")

        # 5. キーワード集計
        global_keywords = _build_global_keywords(
            records,
            top_keywords_count=self.config["top_keywords_count"],
            top_files_count=self.config["top_files_count"],
            top_urls_count=self.config["top_urls_count"],
        )

        # 6. メタデータ生成
        meta = _build_meta(
            target_date,
            records,
            sampling_interval_sec=self.config["sampling_interval_sec"],
            ts_field="ts",
        )

        # Features 作成
        features = Features(
            meta=meta,
            time_blocks=time_blocks,
            app_summary=app_summary,
            global_keywords=global_keywords,
        )

        logger.info(f"Aggregation completed: {features}")

        return features

    def aggregate_and_save(self, target_date: date | None = None) -> tuple[Features, Path]:
        """ログを集計してfeatures.jsonに保存

        Args:
            target_date: 対象日（Noneの場合は当日）

        Returns:
            (Features, 保存パス) のタプル

        Raises:
            LogFileNotFoundError: ログファイルが存在しない
            LogFileEmptyError: ログファイルが空
            LogParseError: 全行解析エラー
        """
        if target_date is None:
            target_date = date.today()

        # 集計実行
        features = self.aggregate(target_date)

        # JSON形式で保存
        features_dict = features.model_dump(mode="json")
        saved_path = self.repository.save_features(target_date, features_dict)

        logger.info(f"Features saved to: {saved_path}")

        return features, saved_path


# 便利関数: デフォルト設定でサービスを作成
def create_aggregator(
    base_path: Path | None = None,
    config: dict[str, Any] | None = None,
) -> LogAggregationService:
    """LogAggregationServiceインスタンスを生成

    Args:
        base_path: ログ保存ディレクトリ（オプション）
        config: 設定パラメータ（オプション）

    Returns:
        LogAggregationService インスタンス
    """
    repository = LogRepository(base_path)
    return LogAggregationService(repository=repository, config=config)
