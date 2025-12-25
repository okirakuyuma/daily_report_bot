# Utils API Documentation

Daily Report Botの共通ユーティリティモジュール。

## 概要

`src/utils/` には、時間計算とテキスト処理の汎用ヘルパー関数が含まれています。

## モジュール構成

```
src/utils/
├── __init__.py         # エクスポート定義
├── time_utils.py       # 時間計算ヘルパー
└── text_utils.py       # テキスト処理ヘルパー
```

---

## time_utils - 時間計算ヘルパー

### 定数

#### `JST`
```python
JST: timezone  # Asia/Tokyo タイムゾーン
```

---

### 関数

#### `parse_ts(ts: str) -> datetime`

ISO 8601タイムスタンプをパース。

**引数:**
- `ts` (str): ISO 8601形式のタイムスタンプ
  - 例: `"2024-01-15T09:30:45+09:00"`

**戻り値:**
- `datetime`: パースされたdatetimeオブジェクト

**例外:**
- `ValueError`: パース失敗時

**使用例:**
```python
from src.utils import parse_ts

ts_str = "2024-01-15T09:30:45+09:00"
dt = parse_ts(ts_str)
# -> datetime.datetime(2024, 1, 15, 9, 30, 45, tzinfo=...)
```

---

#### `filter_recent_records(records: list[dict], exclude_sec: int = 120) -> list[dict]`

直近N秒のレコードを除外（ロガー記録中の不完全データを排除）。

**引数:**
- `records` (list[dict]): タイムスタンプを含むレコードリスト
- `exclude_sec` (int): 除外する秒数（デフォルト: 120秒）

**戻り値:**
- `list[dict]`: フィルタリング後のレコード

**使用例:**
```python
from src.utils import filter_recent_records

records = [
    {"timestamp": "2024-01-15T09:00:00+09:00", "app": "Code.exe"},
    {"timestamp": "2024-01-15T14:58:00+09:00", "app": "Chrome.exe"},  # 直近 -> 除外
]

# 直近2分を除外
stable_records = filter_recent_records(records, exclude_sec=120)
```

---

#### `get_time_block(ts: datetime, block_min: int = 30) -> tuple[str, str]`

時刻から時間ブロック（開始・終了）を取得。

**引数:**
- `ts` (datetime): 対象の時刻
- `block_min` (int): ブロックの長さ（分）、デフォルト: 30

**戻り値:**
- `tuple[str, str]`: (開始時刻, 終了時刻) の "HH:MM" 形式

**使用例:**
```python
from datetime import datetime
from src.utils import get_time_block

ts = datetime(2024, 1, 15, 9, 15)
start, end = get_time_block(ts, block_min=30)
# -> ("09:00", "09:30")

ts = datetime(2024, 1, 15, 14, 45)
start, end = get_time_block(ts, block_min=30)
# -> ("14:30", "15:00")
```

---

#### `calculate_duration_min(first_ts: str, last_ts: str, sampling_interval_sec: int = 120) -> int`

総記録時間を計算（分単位）。

サンプリング間隔を考慮して、最後のサンプルの時間も含めた総時間を返す。

**引数:**
- `first_ts` (str): 最初のタイムスタンプ（ISO 8601）
- `last_ts` (str): 最後のタイムスタンプ（ISO 8601）
- `sampling_interval_sec` (int): サンプリング間隔（秒）、デフォルト: 120

**戻り値:**
- `int`: 総記録時間（分）、最小値1分

**使用例:**
```python
from src.utils import calculate_duration_min

first = "2024-01-15T09:00:00+09:00"
last = "2024-01-15T09:10:00+09:00"

duration = calculate_duration_min(first, last)
# -> 12分 (10分 + 2分サンプリング間隔)
```

---

## text_utils - テキスト処理ヘルパー

### 定数

#### `PROCESS_TO_APP_NAME`
```python
PROCESS_TO_APP_NAME: dict[str, str]
```

プロセス名からアプリケーション表示名へのマッピング辞書。

**主要なマッピング:**
- `"Code.exe"` → `"Visual Studio Code"`
- `"chrome.exe"` → `"Google Chrome"`
- `"EXCEL.EXE"` → `"Microsoft Excel"`
- `"Teams.exe"` → `"Microsoft Teams"`
- その他20以上のアプリケーション

---

### 関数

#### `merge_keywords(records: list[dict], field: str = "keywords") -> list[str]`

大文字小文字を無視して重複排除し、出現頻度順にソート。

**引数:**
- `records` (list[dict]): キーワードフィールドを含むレコードリスト
- `field` (str): キーワードフィールド名（デフォルト: "keywords"）

**戻り値:**
- `list[str]`: 出現頻度順のユニークなキーワードリスト

**使用例:**
```python
from src.utils import merge_keywords

records = [
    {"keywords": ["Python", "API"]},
    {"keywords": ["python", "Testing"]},
    {"keywords": ["API", "python", "Docker"]},
]

merged = merge_keywords(records)
# -> ["python", "API", "Testing", "Docker"]
# pythonが3回、APIが2回、残りが1回ずつ
```

---

#### `calculate_rank(count: int, total_count: int) -> Literal["high", "medium", "low"]`

使用頻度でランクを判定。

**引数:**
- `count` (int): 個別カウント
- `total_count` (int): 総カウント

**戻り値:**
- `Literal["high", "medium", "low"]`:
  - `"high"`: 30%以上
  - `"medium"`: 10%以上30%未満
  - `"low"`: 10%未満

**使用例:**
```python
from src.utils import calculate_rank

rank = calculate_rank(35, 100)  # -> "high" (35%)
rank = calculate_rank(20, 100)  # -> "medium" (20%)
rank = calculate_rank(5, 100)   # -> "low" (5%)
```

---

#### `normalize_app_name(process_name: str | None) -> str`

プロセス名からアプリケーション表示名に正規化。

**引数:**
- `process_name` (str | None): プロセス名

**戻り値:**
- `str`: 正規化されたアプリケーション名

**使用例:**
```python
from src.utils import normalize_app_name

app = normalize_app_name("Code.exe")
# -> "Visual Studio Code"

app = normalize_app_name("chrome.exe")
# -> "Google Chrome"

app = normalize_app_name("unknown.exe")
# -> "unknown.exe" (マッピングなし)

app = normalize_app_name(None)
# -> "Unknown"
```

---

## インポート方法

### すべてをインポート
```python
from src.utils import (
    JST,
    PROCESS_TO_APP_NAME,
    calculate_duration_min,
    calculate_rank,
    filter_recent_records,
    get_time_block,
    merge_keywords,
    normalize_app_name,
    parse_ts,
)
```

### モジュール別にインポート
```python
# 時間関連のみ
from src.utils.time_utils import parse_ts, get_time_block

# テキスト関連のみ
from src.utils.text_utils import normalize_app_name, calculate_rank
```

---

## テスト

### テストファイル
- `/home/okira/job/daily_report_bot/tests/utils/test_time_utils.py`
- `/home/okira/job/daily_report_bot/tests/utils/test_text_utils.py`

### テスト実行
```bash
# すべてのutilsテストを実行
pytest tests/utils/

# 個別モジュールのテスト
pytest tests/utils/test_time_utils.py
pytest tests/utils/test_text_utils.py

# カバレッジ付き
pytest tests/utils/ --cov=src/utils --cov-report=html
```

### 動作確認スクリプト
```bash
python3 scripts/validate_utils.py
```

---

## 設計原則

### time_utils
- **タイムゾーン対応**: すべての時刻処理でJST (Asia/Tokyo) を使用
- **安定性**: 直近データ除外により不完全なログを排除
- **柔軟性**: ブロック長やサンプリング間隔をカスタマイズ可能

### text_utils
- **正規化**: 大文字小文字の違いを吸収
- **頻度重視**: 出現回数でソートし、重要なキーワードを優先
- **可読性**: プロセス名を人間が読みやすいアプリ名に変換

---

## 依存関係

- **外部依存なし**: 標準ライブラリのみ使用
- **Python 3.10+**: Type hints (Union型の `|` 記法) を使用
