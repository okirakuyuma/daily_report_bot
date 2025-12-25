"""LogRepository - ログファイルの読み書き処理

JSONL形式の生ログファイルとJSON形式の特徴量ファイルを管理。
Windows環境の %LOCALAPPDATA%/DailyReportBot/logs/ を基準とする。
"""

from __future__ import annotations

import json
import logging
import os
from datetime import date
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class LogFileNotFoundError(FileNotFoundError):
    """ログファイルが存在しない"""

    def __init__(self, file_path: Path) -> None:
        super().__init__(f"Log file not found: {file_path}")
        self.file_path = file_path


class LogFileEmptyError(ValueError):
    """ログファイルが空"""

    def __init__(self, file_path: Path) -> None:
        super().__init__(f"Log file is empty: {file_path}")
        self.file_path = file_path


class LogParseError(ValueError):
    """ログファイルの全行が解析エラー"""

    def __init__(self, file_path: Path, total_lines: int) -> None:
        super().__init__(
            f"All {total_lines} lines failed to parse in: {file_path}"
        )
        self.file_path = file_path
        self.total_lines = total_lines


class LogRepository:
    """ログファイルの読み書きを担当するリポジトリ

    ファイル配置:
    - raw.jsonl: %LOCALAPPDATA%/DailyReportBot/logs/YYYY-MM-DD.jsonl
    - features.json: %LOCALAPPDATA%/DailyReportBot/logs/YYYY-MM-DD_features.json
    """

    DEFAULT_BASE_PATH = Path(os.getenv("LOCALAPPDATA", "~")) / "DailyReportBot" / "logs"

    def __init__(self, base_path: Path | None = None) -> None:
        """リポジトリを初期化

        Args:
            base_path: ログ保存ディレクトリ。
                      Noneの場合は %LOCALAPPDATA%/DailyReportBot/logs/
        """
        if base_path is None:
            base_path = self.DEFAULT_BASE_PATH.expanduser()

        self.base_path = Path(base_path)
        logger.debug(f"LogRepository initialized with base_path: {self.base_path}")

    def get_log_path(self, target_date: date) -> Path:
        """対象日のログファイルパスを取得

        Args:
            target_date: 対象日

        Returns:
            ログファイルの絶対パス (YYYY-MM-DD.jsonl)
        """
        filename = f"{target_date.isoformat()}.jsonl"
        return self.base_path / filename

    def get_features_path(self, target_date: date) -> Path:
        """対象日の特徴量ファイルパスを取得

        Args:
            target_date: 対象日

        Returns:
            特徴量ファイルの絶対パス (YYYY-MM-DD_features.json)
        """
        filename = f"{target_date.isoformat()}_features.json"
        return self.base_path / filename

    def read_raw_logs(self, target_date: date) -> list[dict[str, Any]]:
        """raw.jsonlを読み込み

        JSON Lines形式（1行1レコード）で記録された生ログを読み込む。
        解析エラー行はwarningログを出力してスキップ。

        Args:
            target_date: 対象日

        Returns:
            解析成功したレコードのリスト

        Raises:
            LogFileNotFoundError: ファイルが存在しない
            LogFileEmptyError: ファイルが空または有効なレコードが0件
            LogParseError: 全行が解析エラー
        """
        log_path = self.get_log_path(target_date)

        if not log_path.exists():
            logger.error(f"Log file not found: {log_path}")
            raise LogFileNotFoundError(log_path)

        if log_path.stat().st_size == 0:
            logger.error(f"Log file is empty: {log_path}")
            raise LogFileEmptyError(log_path)

        records: list[dict[str, Any]] = []
        total_lines = 0
        error_lines = 0

        logger.info(f"Reading raw logs from: {log_path}")

        with open(log_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, start=1):
                total_lines += 1
                line = line.strip()

                if not line:
                    # 空行はスキップ（エラーカウントに含めない）
                    continue

                try:
                    record = json.loads(line)
                    records.append(record)
                except json.JSONDecodeError as e:
                    error_lines += 1
                    logger.warning(
                        f"Failed to parse line {line_num} in {log_path}: {e}"
                    )
                    logger.debug(f"Invalid line content: {line[:100]}")

        logger.info(
            f"Read {len(records)} records from {log_path} "
            f"(total_lines={total_lines}, errors={error_lines})"
        )

        # 有効なレコードが0件の場合
        if len(records) == 0:
            # エラー行が存在する場合は全行解析エラー
            if error_lines > 0:
                logger.error(f"All {error_lines} lines failed to parse: {log_path}")
                raise LogParseError(log_path, error_lines)
            # エラー行がない場合は空ファイル（空行のみ）
            else:
                logger.error(f"No valid records found in: {log_path}")
                raise LogFileEmptyError(log_path)

        return records

    def save_features(
        self, target_date: date, features: dict[str, Any]
    ) -> Path:
        """features.jsonを保存

        Args:
            target_date: 対象日
            features: 特徴量データ（Featuresモデルのdict表現）

        Returns:
            保存したファイルの絶対パス

        Note:
            - ディレクトリが存在しない場合は自動作成
            - UTF-8エンコーディング、BOMなし、インデント2スペース
        """
        features_path = self.get_features_path(target_date)

        # ディレクトリが存在しない場合は作成
        features_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Saving features to: {features_path}")

        with open(features_path, "w", encoding="utf-8") as f:
            json.dump(features, f, ensure_ascii=False, indent=2)

        logger.info(f"Features saved successfully: {features_path}")

        return features_path

    def load_features(self, target_date: date) -> dict[str, Any] | None:
        """features.jsonを読み込み

        Args:
            target_date: 対象日

        Returns:
            特徴量データ。ファイルが存在しない場合はNone

        Raises:
            json.JSONDecodeError: JSONパースエラー（ファイル破損）
        """
        features_path = self.get_features_path(target_date)

        if not features_path.exists():
            logger.debug(f"Features file not found: {features_path}")
            return None

        logger.info(f"Loading features from: {features_path}")

        with open(features_path, "r", encoding="utf-8") as f:
            features: dict[str, Any] = json.load(f)

        logger.info(f"Features loaded successfully: {features_path}")

        return features
