"""Tests for text_utils module

テキスト処理ユーティリティのテストケース。
"""

import pytest

from src.utils.text_utils import (
    PROCESS_TO_APP_NAME,
    calculate_rank,
    merge_keywords,
    normalize_app_name,
)


class TestMergeKeywords:
    """merge_keywords関数のテスト"""

    def test_merge_with_duplicates(self):
        """大文字小文字を無視して重複排除"""
        records = [
            {"keywords": ["Python", "API"]},
            {"keywords": ["python", "Testing"]},
            {"keywords": ["API", "python", "Docker"]},
        ]

        result = merge_keywords(records)

        # pythonが3回、APIが2回、Testingが1回、Dockerが1回
        assert result[0].lower() == "python"  # 最頻出
        assert result[1].lower() == "api"  # 2番目
        assert len(result) == 4  # ユニーク数

    def test_merge_preserves_first_case(self):
        """最初に出現した表記を保持"""
        records = [
            {"keywords": ["Python"]},
            {"keywords": ["PYTHON"]},
            {"keywords": ["python"]},
        ]

        result = merge_keywords(records)

        assert result[0] == "Python"  # 最初の表記
        assert len(result) == 1

    def test_merge_sorts_by_frequency(self):
        """出現頻度順にソート"""
        records = [
            {"keywords": ["A"]},
            {"keywords": ["B", "B"]},
            {"keywords": ["C", "C", "C"]},
            {"keywords": ["A"]},
        ]

        result = merge_keywords(records)

        assert result[0] == "C"  # 3回
        assert result[1] in ["A", "B"]  # 2回（順序不定）
        assert len(result) == 3

    def test_merge_empty_records(self):
        """空レコードを処理"""
        result = merge_keywords([])
        assert result == []

    def test_merge_with_no_keywords_field(self):
        """keywordsフィールドがないレコード"""
        records = [
            {"other_field": "value"},
            {"keywords": ["Python"]},
        ]

        result = merge_keywords(records)

        assert result == ["Python"]

    def test_merge_with_empty_strings(self):
        """空文字列を除外"""
        records = [
            {"keywords": ["", "Python", ""]},
            {"keywords": ["API", ""]},
        ]

        result = merge_keywords(records)

        assert "" not in result
        assert len(result) == 2

    def test_merge_custom_field(self):
        """カスタムフィールド名を使用"""
        records = [
            {"tags": ["Docker", "CI/CD"]},
            {"tags": ["docker", "Testing"]},
        ]

        result = merge_keywords(records, field="tags")

        assert result[0].lower() == "docker"
        assert len(result) == 3


class TestCalculateRank:
    """calculate_rank関数のテスト"""

    def test_rank_high(self):
        """30%以上でhigh"""
        assert calculate_rank(35, 100) == "high"
        assert calculate_rank(30, 100) == "high"
        assert calculate_rank(50, 100) == "high"

    def test_rank_medium(self):
        """10-30%でmedium"""
        assert calculate_rank(20, 100) == "medium"
        assert calculate_rank(10, 100) == "medium"
        assert calculate_rank(29, 100) == "medium"

    def test_rank_low(self):
        """10%未満でlow"""
        assert calculate_rank(5, 100) == "low"
        assert calculate_rank(9, 100) == "low"
        assert calculate_rank(1, 100) == "low"

    def test_rank_zero_count(self):
        """カウント0でlow"""
        assert calculate_rank(0, 100) == "low"

    def test_rank_zero_total(self):
        """総カウント0でlow（ゼロ除算対策）"""
        assert calculate_rank(10, 0) == "low"

    def test_rank_edge_cases(self):
        """境界値テスト"""
        assert calculate_rank(30, 100) == "high"  # ちょうど30%
        assert calculate_rank(10, 100) == "medium"  # ちょうど10%
        assert calculate_rank(9, 100) == "low"  # 9%

    def test_rank_small_numbers(self):
        """小さい数値でも正確に計算"""
        assert calculate_rank(3, 10) == "high"  # 30%
        assert calculate_rank(2, 10) == "medium"  # 20%
        assert calculate_rank(1, 20) == "low"  # 5%


class TestNormalizeAppName:
    """normalize_app_name関数のテスト"""

    def test_normalize_known_processes(self):
        """既知のプロセス名を正規化"""
        assert normalize_app_name("Code.exe") == "Visual Studio Code"
        assert normalize_app_name("chrome.exe") == "Google Chrome"
        assert normalize_app_name("EXCEL.EXE") == "Microsoft Excel"
        assert normalize_app_name("slack.exe") == "Slack"

    def test_normalize_unknown_process(self):
        """未知のプロセス名はそのまま返す"""
        assert normalize_app_name("unknown.exe") == "unknown.exe"
        assert normalize_app_name("custom_app.exe") == "custom_app.exe"

    def test_normalize_none(self):
        """Noneを処理"""
        assert normalize_app_name(None) == "Unknown"

    def test_process_to_app_name_coverage(self):
        """PROCESS_TO_APP_NAMEマッピングの内容確認"""
        # 主要なアプリケーションが含まれることを確認
        assert "Code.exe" in PROCESS_TO_APP_NAME
        assert "chrome.exe" in PROCESS_TO_APP_NAME
        assert "EXCEL.EXE" in PROCESS_TO_APP_NAME
        assert "slack.exe" in PROCESS_TO_APP_NAME
        assert "Teams.exe" in PROCESS_TO_APP_NAME

        # マッピングの値が空でないことを確認
        for process, app_name in PROCESS_TO_APP_NAME.items():
            assert app_name  # 空文字列でない
            assert isinstance(app_name, str)
            assert len(app_name) > 0

    def test_normalize_case_sensitive(self):
        """大文字小文字を区別"""
        # マッピングは完全一致のみ
        assert normalize_app_name("code.exe") == "code.exe"  # 小文字は未登録
        assert normalize_app_name("Code.exe") == "Visual Studio Code"  # 大文字一致
