"""Time utilities - 時間計算ヘルパー

ログデータの時刻パース、フィルタリング、ブロック分割などの時間関連ユーティリティ。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

# JSTタイムゾーン
JST = timezone(timedelta(hours=9))


def parse_ts(ts: str) -> datetime:
    """ISO 8601タイムスタンプをパース

    Args:
        ts: ISO 8601形式のタイムスタンプ文字列
            例: "2024-01-15T09:30:45+09:00" or "2024-01-15T09:30:45Z"

    Returns:
        パースされたdatetimeオブジェクト（タイムゾーン情報付き）

    Raises:
        ValueError: パース失敗時

    Examples:
        >>> parse_ts("2024-01-15T09:30:45+09:00")
        datetime.datetime(2024, 1, 15, 9, 30, 45, tzinfo=...)
    """
    return datetime.fromisoformat(ts)


def filter_recent_records(records: list[dict], exclude_sec: int = 120) -> list[dict]:
    """直近N秒のレコードを除外（安定化のため）

    ロガーが記録中の不完全なデータを除外し、確定したデータのみを取得。

    Args:
        records: タイムスタンプを含むレコードのリスト
                 各レコードは {"timestamp": "ISO8601文字列", ...} の形式
        exclude_sec: 除外する秒数（デフォルト: 120秒）

    Returns:
        フィルタリング後のレコードリスト

    Examples:
        >>> now = datetime.now(JST)
        >>> records = [
        ...     {"timestamp": (now - timedelta(minutes=5)).isoformat()},
        ...     {"timestamp": (now - timedelta(seconds=30)).isoformat()},
        ... ]
        >>> filtered = filter_recent_records(records, exclude_sec=120)
        >>> len(filtered)  # 最新30秒のレコードは除外される
        1
    """
    if not records:
        return []

    now = datetime.now(JST)
    threshold = now - timedelta(seconds=exclude_sec)

    filtered = []
    for record in records:
        try:
            ts = parse_ts(record["timestamp"])
            if ts <= threshold:
                filtered.append(record)
        except (KeyError, ValueError):
            # タイムスタンプが無効なレコードはスキップ
            continue

    return filtered


def get_time_block(ts: datetime, block_min: int = 30) -> tuple[str, str]:
    """時刻から時間ブロック（開始・終了）を取得

    指定された時刻を含む時間ブロックの開始・終了時刻を計算。

    Args:
        ts: 対象のdatetimeオブジェクト
        block_min: ブロックの長さ（分）、デフォルト: 30分

    Returns:
        (開始時刻, 終了時刻) のタプル、"HH:MM"形式

    Examples:
        >>> from datetime import datetime
        >>> ts = datetime(2024, 1, 15, 9, 15)
        >>> get_time_block(ts, block_min=30)
        ('09:00', '09:30')
        >>> ts = datetime(2024, 1, 15, 9, 45)
        >>> get_time_block(ts, block_min=30)
        ('09:30', '10:00')
        >>> ts = datetime(2024, 1, 15, 14, 20)
        >>> get_time_block(ts, block_min=60)
        ('14:00', '15:00')
    """
    # 分を block_min で切り捨て
    minutes_since_hour = ts.minute
    block_start_minute = (minutes_since_hour // block_min) * block_min

    # ブロック開始時刻
    block_start = ts.replace(minute=block_start_minute, second=0, microsecond=0)

    # ブロック終了時刻
    block_end = block_start + timedelta(minutes=block_min)

    return (
        block_start.strftime("%H:%M"),
        block_end.strftime("%H:%M"),
    )


def calculate_duration_min(
    first_ts: str,
    last_ts: str,
    sampling_interval_sec: int = 120,
) -> int:
    """総記録時間を計算（分）

    最初と最後のタイムスタンプから、サンプリング間隔を考慮した総記録時間を計算。

    Args:
        first_ts: 最初のタイムスタンプ（ISO 8601形式）
        last_ts: 最後のタイムスタンプ（ISO 8601形式）
        sampling_interval_sec: サンプリング間隔（秒）、デフォルト: 120秒

    Returns:
        総記録時間（分）、最小値は1分

    Examples:
        >>> # 10分間の記録
        >>> first = "2024-01-15T09:00:00+09:00"
        >>> last = "2024-01-15T09:10:00+09:00"
        >>> calculate_duration_min(first, last)
        10
        >>> # 2時間の記録
        >>> first = "2024-01-15T09:00:00+09:00"
        >>> last = "2024-01-15T11:00:00+09:00"
        >>> calculate_duration_min(first, last)
        120
    """
    try:
        start = parse_ts(first_ts)
        end = parse_ts(last_ts)

        # 差分を計算（秒）
        delta_sec = (end - start).total_seconds()

        # サンプリング間隔を加算（最後のサンプルもカウント）
        total_sec = delta_sec + sampling_interval_sec

        # 分に変換（切り上げ）
        duration_min = int((total_sec + 59) // 60)

        # 最小値は1分
        return max(duration_min, 1)

    except (ValueError, TypeError):
        # パースエラー時は1分として扱う
        return 1
