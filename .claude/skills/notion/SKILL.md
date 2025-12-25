---
name: notion-integration
description: Notion APIでページ・データベース・ブロックを操作。ユーザーが「Notionに...」「Notionから...」「日報をNotionに出力」と言及した場合、Notionページ作成・更新、データベースクエリ、ブロック生成時に使用。
---

# Notion Integration

Notion APIを使用した日報出力スキル。

## クイックリファレンス

| 項目 | 値 |
|------|-----|
| ベースURL | `https://api.notion.com/v1` |
| APIバージョン | `2022-06-28` |
| 認証 | `Authorization: Bearer {NOTION_TOKEN}` |
| レート制限 | 平均3リクエスト/秒 |

## セットアップ

```python
from notion_client import Client
notion = Client(auth=os.environ["NOTION_TOKEN"])
DATABASE_ID = os.environ["NOTION_DATABASE_ID"]
```

## 主要パターン

### ページ検索・作成・更新

```python
# 同日ページ検索
def find_page_by_date(date: str) -> str | None:
    response = notion.databases.query(
        database_id=DATABASE_ID,
        filter={"property": "日付", "date": {"equals": date}}
    )
    results = response.get("results", [])
    return results[0]["id"] if results else None

# ページ作成
response = notion.pages.create(
    parent={"database_id": DATABASE_ID},
    properties={
        "名前": {"title": [{"text": {"content": f"{date} 日報"}}]},
        "日付": {"date": {"start": date}},
        "ステータス": {"select": {"name": "自動生成"}}
    },
    children=blocks
)

# ページ更新（既存ブロック削除→新規追加）
existing = notion.blocks.children.list(page_id)
for block in existing["results"]:
    notion.blocks.delete(block["id"])
notion.blocks.children.append(page_id, children=new_blocks)
```

### ブロックビルダー

```python
def heading_2(text: str) -> dict:
    return {"type": "heading_2", "heading_2": {
        "rich_text": [{"type": "text", "text": {"content": text}}]
    }}

def paragraph(text: str) -> dict:
    return {"type": "paragraph", "paragraph": {
        "rich_text": [{"type": "text", "text": {"content": text}}]
    }}

def bulleted_list_item(text: str) -> dict:
    return {"type": "bulleted_list_item", "bulleted_list_item": {
        "rich_text": [{"type": "text", "text": {"content": text}}]
    }}

def divider() -> dict:
    return {"type": "divider", "divider": {}}
```

## エラーハンドリング

| ステータス | 対処 |
|-----------|------|
| 401 | トークン確認 |
| 404 | ID確認、共有設定確認 |
| 429 | `Retry-After`待機後リトライ |

## 詳細リファレンス

- [プロパティタイプ一覧](references/property-types.md)
- [ブロックタイプ一覧](references/block-types.md)
- [テーブル生成](references/table-builder.md)
