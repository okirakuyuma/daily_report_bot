# Domain Layer ドキュメント

Daily Report Botのドメイン層実装。純粋なビジネスロジックを提供し、外部依存を持たない。

## 概要

ドメイン層は以下の2つの主要なモデルを提供します:

1. **CaptureRecord** - キャプチャログの生レコード（`raw.jsonl`用）
2. **Features** - 集計済み特徴量（`features.json`用）

## モデル構造

### CaptureRecord

キャプチャログの不変性を保証するエンティティ。

```python
from src.domain import CaptureRecord

record = CaptureRecord(
    ts="2025-12-25T14:30:00+09:00",
    window_title="Chrome - Google",
    process_name="chrome.exe",
    keywords=["search", "google"],
    urls=["https://google.com"],
    files=["C:\\Users\\test.txt"],
    numbers=["123"]
)
```

#### フィールド

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `ts` | `str` | ✓ | ISO 8601形式のタイムスタンプ |
| `window_title` | `str \| None` |  | ウィンドウタイトル |
| `process_name` | `str \| None` |  | プロセス名 |
| `keywords` | `list[str]` |  | 抽出キーワード |
| `urls` | `list[str]` |  | 抽出URL/ドメイン |
| `files` | `list[str]` |  | 抽出ファイルパス |
| `numbers` | `list[str]` |  | 抽出数値 |

#### プロパティ

- `timestamp: datetime` - タイムスタンプをdatetimeオブジェクトとして取得
- `has_content: bool` - 有効なコンテンツを持つかチェック
- `app_identifier: str` - アプリケーション識別子（process_name優先）

#### メソッド

- `merge_features(other: CaptureRecord)` - 他のレコードの特徴量をマージ

#### バリデーション

- タイムスタンプはISO 8601形式として検証
- 空文字列は自動的に`None`に正規化
- リスト内の空文字列と重複は自動削除
- 文字列の前後の空白は自動トリミング

### Features

日報用の集計済み特徴量を表す値オブジェクト。

```python
from src.domain import Features, FeaturesMeta, AppSummary, AppRank

features = Features(
    meta=FeaturesMeta(
        date="2025-12-25",
        generated_at="2025-12-25T18:00:00+09:00",
        capture_count=240,
        first_capture="09:00:00",
        last_capture="18:00:00",
        total_duration_min=480.0
    ),
    app_summary=[
        AppSummary(
            name="Google Chrome",
            process="chrome.exe",
            count=150,
            duration_min=120.5,
            rank=AppRank.HIGH,
            top_keywords=["search", "docs"]
        )
    ]
)
```

#### サブモデル

##### FeaturesMeta

集計のメタデータ。

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `date` | `str` | 対象日付（YYYY-MM-DD） |
| `generated_at` | `str` | 生成タイムスタンプ（ISO 8601） |
| `capture_count` | `int` | 総キャプチャ数 |
| `first_capture` | `str` | 最初のキャプチャ時刻（HH:MM:SS） |
| `last_capture` | `str` | 最後のキャプチャ時刻（HH:MM:SS） |
| `total_duration_min` | `float` | 総記録時間（分） |

##### TimeBlock

時間ブロック単位の活動サマリ。

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `start` | `str` | 開始時刻（HH:MM） |
| `end` | `str` | 終了時刻（HH:MM） |
| `apps` | `list[AppUsage]` | アプリ使用状況リスト |
| `top_keywords` | `list[str]` | 頻出キーワード |
| `top_files` | `list[str]` | 頻出ファイルパス |

プロパティ:
- `duration_minutes: int` - ブロックの長さ（分）

##### AppUsage

時間ブロック内のアプリ使用状況。

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `name` | `str` | アプリ表示名 |
| `percent` | `float` | 使用割合（0-100%） |

##### AppSummary

アプリケーション別の集計サマリ。

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `name` | `str` | 表示名 |
| `process` | `str` | プロセス名 |
| `count` | `int` | 観測回数 |
| `duration_min` | `float` | 推定使用時間（分） |
| `rank` | `AppRank` | 使用頻度ランク |
| `top_keywords` | `list[str]` | 頻出キーワード |
| `top_files` | `list[str] \| None` | 頻出ファイルパス |
| `top_urls` | `list[str] \| None` | 頻出URL/ドメイン |

##### AppRank

アプリ使用頻度ランクのEnum。

```python
class AppRank(str, Enum):
    HIGH = "high"      # 使用時間上位33%
    MEDIUM = "medium"  # 使用時間中位33%
    LOW = "low"        # 使用時間下位33%
```

##### GlobalKeywords

全体を通しての頻出特徴量。

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `top_keywords` | `list[str]` | グローバル頻出キーワード |
| `top_urls` | `list[str]` | グローバル頻出URL/ドメイン |
| `top_files` | `list[str]` | グローバル頻出ファイルパス |

#### プロパティ

- `has_data: bool` - 有効なデータを持つかチェック
- `top_app: AppSummary | None` - 最も使用時間が長いアプリ
- `active_hours: float` - アクティブ時間（時間単位）

#### メソッド

- `get_apps_by_rank(rank: AppRank) -> list[AppSummary]` - 指定ランクのアプリをフィルタリング

#### 不変性

`Features`モデルは`frozen=True`に設定されており、作成後は変更できません。

```python
features.meta = new_meta  # ValidationError
```

## JSONシリアライゼーション

すべてのモデルはPydantic v2ベースで、完全なJSONサポートを提供します。

### エクスポート

```python
# dict に変換
data = record.model_dump()

# JSON 文字列に変換
json_str = record.model_dump_json(indent=2)
```

### インポート

```python
# dict から作成
record = CaptureRecord.model_validate(data)

# JSON 文字列から作成
record = CaptureRecord.model_validate_json(json_str)

# ファイルから読み込み
from pathlib import Path
json_data = Path("data.json").read_text(encoding="utf-8")
features = Features.model_validate_json(json_data)
```

## バリデーション機能

### 自動正規化

```python
# 空白トリミング
record = CaptureRecord(
    ts="2025-12-25T14:30:00+09:00",
    window_title="  Chrome  "
)
assert record.window_title == "Chrome"

# 重複削除
record = CaptureRecord(
    ts="2025-12-25T14:30:00+09:00",
    keywords=["test", "test", "python"]
)
assert record.keywords == ["test", "python"]

# 空文字列除去
record = CaptureRecord(
    ts="2025-12-25T14:30:00+09:00",
    keywords=["test", "", "  ", "python"]
)
assert record.keywords == ["test", "python"]
```

### 自動ソート

```python
# アプリは使用率降順にソート
time_block = TimeBlock(
    start="09:00",
    end="10:00",
    apps=[
        AppUsage(name="App1", percent=30.0),
        AppUsage(name="App2", percent=70.0)
    ]
)
assert time_block.apps[0].name == "App2"

# アプリサマリは使用時間降順にソート
features = Features(
    meta=meta,
    app_summary=[app1, app2, app3]
)
# app_summary は duration_min 降順
```

### 数値の丸め

```python
# パーセント値は小数点1桁に丸め
usage = AppUsage(name="Chrome", percent=45.567)
assert usage.percent == 45.6

# 使用時間も小数点1桁に丸め
summary = AppSummary(
    name="Chrome",
    process="chrome.exe",
    count=100,
    duration_min=120.567,
    rank=AppRank.HIGH
)
assert summary.duration_min == 120.6
```

## エラーハンドリング

```python
from pydantic import ValidationError

try:
    record = CaptureRecord(ts="invalid-timestamp")
except ValidationError as e:
    print(e.errors())
    # [{'type': 'value_error', 'msg': '無効なISO 8601タイムスタンプ: ...'}]
```

## 使用例

完全な使用例は `/home/okira/job/daily_report_bot/examples/domain_usage_example.py` を参照してください。

```bash
python examples/domain_usage_example.py
```

## テスト

ドメイン層は100%のテストカバレッジを持っています。

```bash
# 全テスト実行
pytest tests/unit/domain/ -v

# カバレッジ付き
pytest tests/unit/domain/ --cov=src/domain --cov-report=term-missing

# 型チェック
mypy src/domain/ --strict
```

テストは以下をカバーします:
- バリデーション機能
- プロパティとメソッド
- JSONシリアライゼーション
- エッジケース
- エラーハンドリング

## 設計原則

1. **純粋性**: 外部依存なし、Pydanticのみ使用
2. **不変性**: 重要なモデルは`frozen`で変更不可
3. **型安全性**: Python 3.10+ type hints + mypy strict mode
4. **バリデーション**: 入力データの自動検証と正規化
5. **テスタビリティ**: 高いテストカバレッジ（100%）

## アーキテクチャ位置付け

```
┌─────────────────────────────────────────┐
│ Handler (Lambda/CLI)                     │  ← エントリポイント
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│ Application Layer                        │  ← ユースケース実装
│ (aggregator, summarizer, publisher)      │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│ Domain Layer ★                           │  ← このドキュメントの対象
│ (CaptureRecord, Features)                │     純粋なビジネスロジック
└──────────────────────────────────────────┘
```

ドメイン層は:
- **依存しない**: データベース、API、ファイルシステム等に依存しない
- **使われる**: Application層から使用される
- **安定している**: 外部変更の影響を受けにくい

## 次のステップ

1. Application層の実装（Aggregator, Summarizer）
2. Infrastructure層の実装（S3, Notion API）
3. 統合テストの作成
