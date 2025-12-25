# 集計処理フロー設計

## 1. 概要

### 1.1 目的

常駐ロガーが出力した生ログ（raw.jsonl）を読み込み、LLM要約に適した形式（features.json）に変換する。

### 1.2 トリガー

| トリガー | 説明 |
|----------|------|
| ショートカットキー | Ctrl+Alt+D 押下時 |
| 自動実行（任意） | 毎日23:59（タスクスケジューラ） |
| 手動実行 | CLI: `python generate_report.py --date 2025-01-15` |

### 1.3 実装言語

Python 3.10+

## 2. フロー詳細

### 2.1 処理ステップ

```
┌──────────────────────────────────────────────────────────────┐
│                        START                                  │
│                  (ショートカット押下)                          │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ 1. 対象日のログファイル特定                                   │
│    - デフォルト: 当日                                         │
│    - 引数指定: --date YYYY-MM-DD                              │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. raw.jsonl 読み込み                                         │
│    - 直近N秒（デフォルト120秒）を除外（安定化）                 │
│    - 空ファイル/存在しない場合はエラー                         │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. セッション化                                               │
│    - 連続する同一 (window_title, process_name) をマージ        │
│    - 開始時刻・終了時刻・継続時間を計算                        │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. 時間ブロック生成                                           │
│    - 30分単位でグルーピング                                    │
│    - 各ブロックの主要アプリ・キーワードを集計                  │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ 5. アプリ別集計                                               │
│    - プロセス名/ウィンドウタイトルでグルーピング               │
│    - 観測回数・推定使用時間を計算                              │
│    - 使用頻度でランク付け（多/中/少）                          │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ 6. キーワード集計                                             │
│    - 全レコードのkeywords/urls/filesをマージ                   │
│    - 出現頻度でソート                                          │
│    - 上位N件を抽出                                             │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ 7. features.json 出力                                         │
│    - LLM入力用の構造化データ                                   │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                         END                                   │
│                  → LLM要約フローへ                             │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 セッション化アルゴリズム

```python
def sessionize(records: list[dict]) -> list[Session]:
    """
    連続する同一状態をセッションとしてマージ

    入力例:
      [
        {"ts": "09:00", "window_title": "VSCode", ...},
        {"ts": "09:02", "window_title": "VSCode", ...},
        {"ts": "09:04", "window_title": "Chrome", ...},
        {"ts": "09:06", "window_title": "Chrome", ...},
        {"ts": "09:08", "window_title": "VSCode", ...},
      ]

    出力例:
      [
        Session(app="VSCode", start="09:00", end="09:02", duration=4min),
        Session(app="Chrome", start="09:04", end="09:06", duration=4min),
        Session(app="VSCode", start="09:08", end="09:08", duration=2min),
      ]

    ※ 最後のセッションは次の観測がないため、1サンプリング間隔分とする
    """
```

### 2.3 時間ブロック生成

```
時間軸:
  09:00 ──────────────────────────────────────── 09:30
         │ VSCode (80%) │ Chrome (20%) │
         │ keywords: Python, Flask      │

  09:30 ──────────────────────────────────────── 10:00
         │ Chrome (60%) │ Slack (40%)  │
         │ keywords: documentation      │
```

## 3. データ仕様

### 3.1 入力: raw.jsonl

```json
{"ts": "2025-01-15T09:00:00+09:00", "window_title": "main.py - VSCode", "process_name": "Code.exe", "keywords": ["Python", "def"], "urls": [], "files": ["main.py"]}
{"ts": "2025-01-15T09:02:00+09:00", "window_title": "main.py - VSCode", "process_name": "Code.exe", "keywords": ["Python", "class"], "urls": [], "files": ["main.py"]}
{"ts": "2025-01-15T09:04:00+09:00", "window_title": "Stack Overflow - Chrome", "process_name": "chrome.exe", "keywords": ["Python", "error"], "urls": ["stackoverflow.com"], "files": []}
```

### 3.2 出力: features.json

```json
{
  "meta": {
    "date": "2025-01-15",
    "generated_at": "2025-01-15T18:00:00+09:00",
    "capture_count": 240,
    "first_capture": "2025-01-15T09:00:00+09:00",
    "last_capture": "2025-01-15T17:58:00+09:00",
    "total_duration_min": 478
  },
  "time_blocks": [
    {
      "start": "09:00",
      "end": "09:30",
      "apps": [
        {"name": "Visual Studio Code", "percent": 80},
        {"name": "Chrome", "percent": 20}
      ],
      "top_keywords": ["Python", "Flask", "API"],
      "top_files": ["main.py", "routes.py"]
    },
    {
      "start": "09:30",
      "end": "10:00",
      "apps": [
        {"name": "Chrome", "percent": 60},
        {"name": "Slack", "percent": 40}
      ],
      "top_keywords": ["documentation", "review"],
      "top_files": []
    }
  ],
  "app_summary": [
    {
      "name": "Visual Studio Code",
      "process": "Code.exe",
      "count": 120,
      "duration_min": 240,
      "rank": "high",
      "top_keywords": ["Python", "Flask", "import"],
      "top_files": ["main.py", "routes.py", "models.py"]
    },
    {
      "name": "Chrome",
      "process": "chrome.exe",
      "count": 80,
      "duration_min": 160,
      "rank": "high",
      "top_keywords": ["documentation", "Stack Overflow"],
      "top_urls": ["stackoverflow.com", "docs.python.org"]
    },
    {
      "name": "Slack",
      "process": "slack.exe",
      "count": 40,
      "duration_min": 80,
      "rank": "medium",
      "top_keywords": ["meeting", "review"]
    }
  ],
  "global_keywords": {
    "top_keywords": ["Python", "Flask", "API", "documentation", "review"],
    "top_urls": ["stackoverflow.com", "docs.python.org", "github.com"],
    "top_files": ["main.py", "routes.py", "models.py", "README.md"]
  }
}
```

### 3.3 フィールド定義

#### meta

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `date` | string | 対象日 (YYYY-MM-DD) |
| `generated_at` | string | 生成日時 (ISO 8601) |
| `capture_count` | number | 総キャプチャ数 |
| `first_capture` | string | 最初のキャプチャ時刻 |
| `last_capture` | string | 最後のキャプチャ時刻 |
| `total_duration_min` | number | 総記録時間（分） |

#### time_blocks[]

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `start` | string | ブロック開始時刻 (HH:MM) |
| `end` | string | ブロック終了時刻 (HH:MM) |
| `apps` | array | アプリ別使用率 |
| `top_keywords` | string[] | 上位キーワード |
| `top_files` | string[] | 上位ファイル |

#### app_summary[]

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `name` | string | アプリ名（表示用） |
| `process` | string | プロセス名 |
| `count` | number | 観測回数 |
| `duration_min` | number | 推定使用時間（分） |
| `rank` | string | 使用頻度ランク (high/medium/low) |
| `top_keywords` | string[] | アプリ内上位キーワード |

## 4. 集計ロジック詳細

### 4.1 使用時間計算

```
観測回数 × サンプリング間隔 = 推定使用時間

例: 120回 × 2分 = 240分
```

### 4.2 ランク判定

```python
def calculate_rank(count: int, total_count: int) -> str:
    ratio = count / total_count
    if ratio >= 0.3:
        return "high"    # 30%以上
    elif ratio >= 0.1:
        return "medium"  # 10-30%
    else:
        return "low"     # 10%未満
```

### 4.3 アプリ名正規化

```python
PROCESS_TO_APP_NAME = {
    "Code.exe": "Visual Studio Code",
    "chrome.exe": "Google Chrome",
    "firefox.exe": "Firefox",
    "slack.exe": "Slack",
    "WINWORD.EXE": "Microsoft Word",
    "EXCEL.EXE": "Microsoft Excel",
    "POWERPNT.EXE": "Microsoft PowerPoint",
    "Notion.exe": "Notion",
    "explorer.exe": "Explorer",
}
```

### 4.4 キーワード重複排除

```python
def merge_keywords(records: list[dict]) -> list[str]:
    """
    大文字小文字を無視して重複排除、出現頻度でソート
    """
    counter = Counter()
    for record in records:
        for kw in record.get("keywords", []):
            counter[kw.lower()] += 1

    # 元の大文字小文字を保持しつつ頻度順で返す
    return [kw for kw, _ in counter.most_common(20)]
```

## 5. 直近除外ロジック

### 5.1 目的

ショートカット押下時点で作業中の状態が含まれると、集計が不安定になるため、直近N秒を除外する。

### 5.2 実装

```python
def filter_recent_records(
    records: list[dict],
    exclude_sec: int = 120  # デフォルト2分
) -> list[dict]:
    cutoff = datetime.now() - timedelta(seconds=exclude_sec)
    return [r for r in records if parse_ts(r["ts"]) < cutoff]
```

## 6. エラーハンドリング

| エラー | 対応 |
|--------|------|
| ログファイル不存在 | エラー終了（Toastで通知） |
| ログファイル空 | エラー終了（Toastで通知） |
| JSON解析エラー（1行） | 該当行スキップ、警告ログ |
| 全行解析エラー | エラー終了 |

## 7. 設定パラメータ

```json
{
  "aggregation": {
    "exclude_recent_sec": 120,
    "time_block_min": 30,
    "top_keywords_count": 10,
    "top_files_count": 5,
    "top_urls_count": 5,
    "min_captures_for_report": 5
  }
}
```

## 8. テスト観点

### 8.1 単体テスト

- [ ] セッション化が正しく動作
- [ ] 時間ブロックが正しく生成
- [ ] アプリ別集計が正確
- [ ] キーワード重複排除が機能
- [ ] ランク判定が正確

### 8.2 統合テスト

- [ ] 実際のログファイルで正常動作
- [ ] 大量レコード（1000件以上）で性能問題なし
- [ ] 日付跨ぎログの処理

### 8.3 エッジケース

- [ ] ログ1件のみ
- [ ] 全て同一アプリ
- [ ] キーワード/URL/ファイルが全て空
- [ ] 日本語ウィンドウタイトル

## 9. アーキテクチャ配置

軽量DDD（4レイヤー）に基づく配置:

```
src/
├── domain/
│   ├── capture.py         # CaptureRecord エンティティ
│   ├── session.py         # Session エンティティ (Phase 2)
│   └── features.py        # Features 値オブジェクト
│
├── services/
│   └── aggregator.py      # LogAggregationService (本ファイルの実装)
│
├── repositories/
│   └── log_repository.py  # JSONL読み書き
│
└── utils/
    ├── time_utils.py      # 時間計算ヘルパー
    └── text_utils.py      # キーワード抽出ヘルパー
```

### 依存関係

```
services/aggregator.py
    ↓
repositories/log_repository.py + utils/*
    ↓
domain/*
```

## 10. Phase別実装予定

| Phase | 集計処理の変更 |
|-------|--------------|
| 1 MVP | 基本集計（セッション化なし、プロセス名はウィンドウタイトルから推定） |
| 2 安定運用 | セッション化・時間ブロック・プロセス名取得追加 |
| 3 LLM導入 | 変更なし（LLM要約フローで対応） |
| 4 高精度化 | キーワード抽出精度向上、InsightCandidate追加 |
| 5 プロダクト化 | プライバシーマスキング、監査ログ連携 |

## 11. 関連ドキュメント

- [01-logger-flow.md](01-logger-flow.md) - 常駐ロガー設計
- [03-llm-flow.md](03-llm-flow.md) - LLM要約設計
- [04-notion-flow.md](04-notion-flow.md) - Notion出力設計
- [data-schema.md](../api/data-schema.md) - データスキーマ定義
