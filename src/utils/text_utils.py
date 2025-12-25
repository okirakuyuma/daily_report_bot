"""Text utilities - テキスト処理ヘルパー

キーワード抽出、アプリ名正規化、ランク計算などのテキスト関連ユーティリティ。
"""

from __future__ import annotations

from collections import Counter
from typing import Literal

# プロセス名からアプリ表示名へのマッピング
PROCESS_TO_APP_NAME: dict[str, str] = {
    "Code.exe": "Visual Studio Code",
    "chrome.exe": "Google Chrome",
    "firefox.exe": "Firefox",
    "slack.exe": "Slack",
    "WINWORD.EXE": "Microsoft Word",
    "EXCEL.EXE": "Microsoft Excel",
    "POWERPNT.EXE": "Microsoft PowerPoint",
    "Notion.exe": "Notion",
    "explorer.exe": "Explorer",
    "msedge.exe": "Microsoft Edge",
    "Teams.exe": "Microsoft Teams",
    "Outlook.exe": "Microsoft Outlook",
    "Discord.exe": "Discord",
    "WindowsTerminal.exe": "Windows Terminal",
    "cmd.exe": "Command Prompt",
    "powershell.exe": "PowerShell",
    "notepad.exe": "Notepad",
    "notepad++.exe": "Notepad++",
    "ONENOTE.EXE": "Microsoft OneNote",
    "Zoom.exe": "Zoom",
    "python.exe": "Python",
    "node.exe": "Node.js",
}


def merge_keywords(records: list[dict], field: str = "keywords") -> list[str]:
    """大文字小文字を無視して重複排除、出現頻度でソート

    複数のレコードからキーワードを抽出し、出現頻度の高い順にソートしたユニークなリストを返す。

    Args:
        records: キーワードフィールドを含むレコードのリスト
                 各レコードは {field: ["keyword1", "keyword2", ...], ...} の形式
        field: キーワードフィールド名（デフォルト: "keywords"）

    Returns:
        出現頻度順にソートされたユニークなキーワードリスト

    Examples:
        >>> records = [
        ...     {"keywords": ["Python", "API"]},
        ...     {"keywords": ["python", "Testing"]},
        ...     {"keywords": ["API", "python", "Docker"]},
        ... ]
        >>> merge_keywords(records)
        ['python', 'API', 'Testing', 'Docker']
    """
    # 全キーワードを小文字化して収集
    all_keywords: list[str] = []
    for record in records:
        keywords = record.get(field, [])
        if isinstance(keywords, list):
            all_keywords.extend(keywords)

    # 大文字小文字を無視してカウント（小文字化）
    keyword_counter: Counter[str] = Counter()
    original_case: dict[str, str] = {}  # 小文字 -> 最初に出現した元の表記

    for keyword in all_keywords:
        if not keyword:  # 空文字列をスキップ
            continue

        keyword_lower = keyword.lower()
        keyword_counter[keyword_lower] += 1

        # 最初に出現した表記を保持
        if keyword_lower not in original_case:
            original_case[keyword_lower] = keyword

    # 出現頻度順にソート（降順）、元の表記を使用
    sorted_keywords = [
        original_case[keyword] for keyword, _ in keyword_counter.most_common()
    ]

    return sorted_keywords


def calculate_rank(count: int, total_count: int) -> Literal["high", "medium", "low"]:
    """使用頻度でランク判定

    総カウントに対する割合でランクを決定。

    Args:
        count: 個別カウント
        total_count: 総カウント

    Returns:
        ランク:
            - "high": 30%以上
            - "medium": 10%以上30%未満
            - "low": 10%未満

    Examples:
        >>> calculate_rank(35, 100)
        'high'
        >>> calculate_rank(20, 100)
        'medium'
        >>> calculate_rank(5, 100)
        'low'
        >>> calculate_rank(0, 100)
        'low'
        >>> calculate_rank(10, 0)  # ゼロ除算対策
        'low'
    """
    if total_count == 0:
        return "low"

    percentage = (count / total_count) * 100

    if percentage >= 30:
        return "high"
    elif percentage >= 10:
        return "medium"
    else:
        return "low"


def normalize_app_name(process_name: str | None) -> str:
    """プロセス名からアプリ表示名に正規化

    プロセス名を人間が読みやすいアプリケーション名に変換。
    マッピングにない場合は元のプロセス名を返す。

    Args:
        process_name: プロセス名（例: "Code.exe", "chrome.exe"）

    Returns:
        正規化されたアプリケーション名

    Examples:
        >>> normalize_app_name("Code.exe")
        'Visual Studio Code'
        >>> normalize_app_name("chrome.exe")
        'Google Chrome'
        >>> normalize_app_name("unknown.exe")
        'unknown.exe'
        >>> normalize_app_name(None)
        'Unknown'
    """
    if process_name is None:
        return "Unknown"

    # マッピングに存在する場合は変換
    return PROCESS_TO_APP_NAME.get(process_name, process_name)
