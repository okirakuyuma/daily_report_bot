# Notion Gateway API

## 概要

Notion APIと連携し、日報レポートをNotionデータベースに出力するゲートウェイ。

## クラス

### NotionGateway

Notion API連携の低レベルインターフェース。

#### 初期化

```python
from src.gateways.notion import NotionGateway

gateway = NotionGateway(
    token="secret_xxxxx",           # Notion Integration Token
    database_id="xxxxx-xxxx-...",   # データベースID
    retry_count=3,                   # リトライ回数
    retry_delay_sec=5                # リトライ間隔（秒）
)
```

環境変数から自動取得する場合:

```python
# NOTION_TOKEN, NOTION_DATABASE_IDが設定されていること
gateway = NotionGateway()
```

#### メソッド

##### query_page_by_date

指定日付のページを検索。

```python
page = gateway.query_page_by_date("2025-01-15")
if page:
    print(f"Found page: {page['id']}")
else:
    print("Page not found")
```

**引数:**
- `date` (str): 検索対象日付 (YYYY-MM-DD)

**戻り値:**
- `dict | None`: ページデータ（存在しない場合はNone）

**例外:**
- `Exception`: API呼び出しが全てのリトライで失敗した場合

##### create_page

新規ページを作成。

```python
properties = {
    "名前": {"title": [{"text": {"content": "2025-01-15 日報"}}]},
    "日付": {"date": {"start": "2025-01-15"}},
}

blocks = [
    {"type": "heading_2", "heading_2": {"rich_text": [...]}},
    {"type": "paragraph", "paragraph": {"rich_text": [...]}}
]

page = gateway.create_page(properties, blocks)
print(f"Created: {page['url']}")
```

**引数:**
- `properties` (dict): ページプロパティ
- `children` (list[dict]): ページ本文ブロック

**戻り値:**
- `dict`: 作成されたページデータ

**例外:**
- `Exception`: API呼び出しが全てのリトライで失敗した場合

##### update_page

ページプロパティを更新。

```python
properties = {
    "ステータス": {"select": {"name": "手動編集"}},
    "キャプチャ数": {"number": 240}
}

page = gateway.update_page("page_id_here", properties)
```

**引数:**
- `page_id` (str): ページID
- `properties` (dict): 更新するプロパティ

**戻り値:**
- `dict`: 更新されたページデータ

**例外:**
- `Exception`: API呼び出しが全てのリトライで失敗した場合

##### replace_blocks

ページの本文ブロックを置換。

既存ブロックを全て削除してから新規ブロックを追加します。

```python
new_blocks = [
    {"type": "heading_2", "heading_2": {"rich_text": [...]}},
    {"type": "paragraph", "paragraph": {"rich_text": [...]}}
]

blocks = gateway.replace_blocks("page_id_here", new_blocks)
print(f"Replaced with {len(blocks)} blocks")
```

**引数:**
- `page_id` (str): ページID
- `blocks` (list[dict]): 新規ブロックリスト

**戻り値:**
- `list[dict]`: 追加されたブロックリスト

**例外:**
- `Exception`: API呼び出しが全てのリトライで失敗した場合

## ヘルパー関数

### ブロック生成

#### heading_2

```python
from src.gateways.notion import heading_2

block = heading_2("📊 基本情報")
```

#### paragraph

```python
from src.gateways.notion import paragraph

block = paragraph("本日の作業内容")
```

#### numbered_list_item

```python
from src.gateways.notion import numbered_list_item

block = numbered_list_item("タスク1")
```

#### bulleted_list_item

```python
from src.gateways.notion import bulleted_list_item

block = bulleted_list_item("ポイント1")
```

#### divider

```python
from src.gateways.notion import divider

block = divider()
```

#### build_app_table

アプリ使用状況テーブルを生成。

```python
from src.gateways.notion import build_app_table

app_usage = [
    {
        "name": "Visual Studio Code",
        "duration_min": 240,
        "rank": "high",
        "purpose": "Python開発"
    },
    {
        "name": "Google Chrome",
        "duration_min": 120,
        "rank": "medium",
        "purpose": "調査"
    }
]

table_block = build_app_table(app_usage)
```

### レポート処理

#### build_report_blocks

レポートから本文ブロックを生成。

```python
from src.domain.report import Report
from src.gateways.notion import build_report_blocks

blocks = build_report_blocks(report)
```

**引数:**
- `report` (Report): 日報レポート

**戻り値:**
- `list[dict]`: ブロックリスト

#### build_page_properties

レポートからページプロパティを生成。

```python
from src.gateways.notion import build_page_properties

properties = build_page_properties(
    report=report,
    capture_count=240,
    total_duration_min=478
)
```

**引数:**
- `report` (Report): 日報レポート
- `capture_count` (int): キャプチャ数
- `total_duration_min` (int): 総作業時間（分）

**戻り値:**
- `dict`: プロパティ辞書

#### publish_report

日報をNotionに出力（高レベルAPI）。

既存ページがある場合は更新、ない場合は新規作成します。

```python
from src.domain.report import Report
from src.gateways.notion import publish_report

page_id, page_url = publish_report(
    report=report,
    capture_count=240,
    total_duration_min=478
)

print(f"Published: {page_url}")
```

**引数:**
- `report` (Report): 日報レポート
- `capture_count` (int): キャプチャ数
- `total_duration_min` (int): 総作業時間（分）
- `token` (str | None): Notion Integration Token（オプション）
- `database_id` (str | None): データベースID（オプション）

**戻り値:**
- `(str, str)`: (ページID, ページURL)

**例外:**
- `Exception`: Notion API呼び出しが失敗した場合

## エラーハンドリング

### リトライロジック

以下のエラーに対して自動リトライを実行:

- **レート制限 (429)**: 60秒待機後リトライ
- **ネットワークエラー**: retry_delay_sec秒待機後リトライ
- **その他のAPIエラー**: retry_delay_sec秒待機後リトライ

デフォルトでは3回までリトライします。

### エラーログ

全てのエラーはloggingモジュールを使用してログ出力されます。

```python
import logging

logging.basicConfig(level=logging.INFO)
```

## 環境変数

### NOTION_TOKEN

Notion Integration Token。

取得方法:
1. https://www.notion.so/my-integrations にアクセス
2. "+ New integration" をクリック
3. 名前: "Daily Report Bot"
4. Capabilities: Read content, Update content, Insert content
5. "Submit" してトークンをコピー

### NOTION_DATABASE_ID

日報データベースのID。

取得方法:
1. 日報用データベースページを開く
2. URLから取得: `https://notion.so/{DATABASE_ID}?v=...`
3. データベースページの "..." → "接続" → "Daily Report Bot" を選択

## プロパティ定義

Notionデータベースには以下のプロパティが必要です:

| プロパティ名 | 型 | 説明 |
|-------------|-----|------|
| 名前 | title | ページタイトル |
| 日付 | date | 対象日付 |
| ステータス | select | "自動生成" / "手動編集" |
| キャプチャ数 | number | 総キャプチャ数 |
| 作業時間(分) | number | 総作業時間 |
| メイン作業 | multi_select | 主要タスクのタグ |
| 生成日時 | date | レポート生成日時 |

## ブロック構成

生成されるページの構造:

```
📋 {date} 日報
├── 📊 基本情報
│   └── 生成日時・LLMモデル・成功フラグ
├── 📝 作業サマリー
│   └── 1-2文の要約
├── 🎯 本日のメイン作業
│   ├── 1. タスク1
│   │   └── 詳細説明
│   ├── 2. タスク2
│   │   └── 詳細説明
│   └── 3. タスク3
│       └── 詳細説明
├── 💡 知見・メモ
│   ├── [技術] 知見1
│   ├── [プロセス] 知見2
│   └── ...
├── 📱 アプリ使用状況
│   └── テーブル（アプリ名・時間・頻度・用途）
├── 📁 作業ファイル
│   ├── ファイル1
│   ├── ファイル2
│   └── ...
└── ──────────
    └── 🤖 Generated by Daily Report Bot
```

## 使用例

### 基本的な使用

```python
from src.domain.report import Report, ReportMeta, MainTask, AppUsage
from src.gateways.notion import publish_report

# レポート作成
report = Report(
    meta=ReportMeta(date="2025-01-15"),
    main_tasks=[
        MainTask(
            title="API実装",
            description="認証エンドポイントを実装した"
        )
    ],
    work_summary="本日はAPI実装に注力した",
    app_usage=[
        AppUsage(
            name="Visual Studio Code",
            duration_min=240,
            rank="high",
            purpose="Python開発"
        )
    ],
    files=["main.py", "routes.py"]
)

# Notion出力
page_id, page_url = publish_report(report, capture_count=240, total_duration_min=478)
print(f"Published: {page_url}")
```

### 既存ページ更新

```python
# 同じ日付のレポートを再度publish_reportすると自動的に更新される
page_id, page_url = publish_report(updated_report, capture_count=260, total_duration_min=500)
print(f"Updated: {page_url}")
```

### 低レベルAPI使用

```python
from src.gateways.notion import NotionGateway, build_page_properties, build_report_blocks

gateway = NotionGateway()

# 既存ページ検索
existing = gateway.query_page_by_date("2025-01-15")

# プロパティとブロック生成
properties = build_page_properties(report, 240, 478)
blocks = build_report_blocks(report)

if existing:
    # 更新
    gateway.update_page(existing["id"], properties)
    gateway.replace_blocks(existing["id"], blocks)
else:
    # 新規作成
    gateway.create_page(properties, blocks)
```

## トラブルシューティング

### 認証エラー

```
ValueError: NOTION_TOKEN environment variable is required
```

→ 環境変数 `NOTION_TOKEN` を設定してください。

### データベースIDエラー

```
ValueError: NOTION_DATABASE_ID environment variable is required
```

→ 環境変数 `NOTION_DATABASE_ID` を設定してください。

### APIエラー

```
Notion query failed after 4 attempts: API error
```

→ ネットワーク接続とNotion Integrationの権限を確認してください。

### レート制限

```
Rate limited, waiting 60 seconds...
```

→ 自動的にリトライされます。頻繁に発生する場合はAPI呼び出し頻度を下げてください。
