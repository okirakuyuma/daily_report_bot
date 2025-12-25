# Notion API Skill

Notion APIを使用してページ、データベース、ブロックを操作するためのスキル。

## Triggers

- Notion連携、Notionページ作成、データベース操作、Notion API使用時
- ユーザーが「Notionに...」「Notionから...」と言及した場合

## 基本情報

| 項目 | 値 |
|------|-----|
| ベースURL | `https://api.notion.com/v1` |
| APIバージョン | `2022-06-28` |
| 認証 | Bearer Token (`Authorization: Bearer {token}`) |
| 必須ヘッダー | `Notion-Version: 2022-06-28` |

## 認証設定

```javascript
const { Client } = require('@notionhq/client');
const notion = new Client({ auth: process.env.NOTION_API_KEY });
```

```bash
curl 'https://api.notion.com/v1/...' \
  -H 'Authorization: Bearer '$NOTION_API_KEY'' \
  -H 'Notion-Version: 2022-06-28'
```

---

## 主要エンドポイント

### データベース

| メソッド | エンドポイント | 説明 |
|----------|---------------|------|
| GET | `/v1/databases/{id}` | データベース情報取得 |
| POST | `/v1/databases` | データベース作成 |
| PATCH | `/v1/databases/{id}` | データベース更新 |
| POST | `/v1/databases/{id}/query` | データベースクエリ |

### ページ

| メソッド | エンドポイント | 説明 |
|----------|---------------|------|
| GET | `/v1/pages/{id}` | ページ取得 |
| POST | `/v1/pages` | ページ作成 |
| PATCH | `/v1/pages/{id}` | ページ更新 |
| GET | `/v1/pages/{id}/properties/{property_id}` | プロパティ取得 |

### ブロック

| メソッド | エンドポイント | 説明 |
|----------|---------------|------|
| GET | `/v1/blocks/{id}` | ブロック取得 |
| GET | `/v1/blocks/{id}/children` | 子ブロック取得 |
| POST | `/v1/blocks/{id}/children` | ブロック追加 |
| PATCH | `/v1/blocks/{id}` | ブロック更新 |
| DELETE | `/v1/blocks/{id}` | ブロック削除 |

### 検索・ユーザー

| メソッド | エンドポイント | 説明 |
|----------|---------------|------|
| POST | `/v1/search` | タイトル検索 |
| GET | `/v1/users` | ユーザー一覧 |
| GET | `/v1/users/me` | 現在のユーザー |

---

## コード例

### データベースクエリ

```javascript
const response = await notion.databases.query({
  database_id: databaseId,
  filter: {
    or: [
      { property: "Status", select: { equals: "Done" } },
      { property: "Priority", number: { greater_than: 3 } }
    ]
  },
  sorts: [
    { property: "Created", direction: "descending" }
  ]
});
```

### ページ作成

```javascript
const response = await notion.pages.create({
  parent: { database_id: databaseId },
  icon: { emoji: "📝" },
  properties: {
    Name: {
      title: [{ text: { content: "新しいページ" } }]
    },
    Status: { select: { name: "In Progress" } },
    Date: { date: { start: "2025-12-25" } }
  },
  children: [
    {
      object: "block",
      type: "paragraph",
      paragraph: {
        rich_text: [{ type: "text", text: { content: "本文テキスト" } }]
      }
    }
  ]
});
```

### ブロック追加

```javascript
await notion.blocks.children.append({
  block_id: pageId,
  children: [
    {
      object: "block",
      type: "heading_2",
      heading_2: {
        rich_text: [{ type: "text", text: { content: "見出し" } }]
      }
    },
    {
      object: "block",
      type: "bulleted_list_item",
      bulleted_list_item: {
        rich_text: [{ type: "text", text: { content: "リスト項目" } }]
      }
    }
  ]
});
```

---

## プロパティタイプ

| タイプ | 説明 | 値の形式 |
|--------|------|----------|
| `title` | タイトル | `{ title: [{ text: { content: "..." } }] }` |
| `rich_text` | リッチテキスト | `{ rich_text: [{ text: { content: "..." } }] }` |
| `number` | 数値 | `{ number: 123 }` |
| `select` | 単一選択 | `{ select: { name: "Option" } }` |
| `multi_select` | 複数選択 | `{ multi_select: [{ name: "A" }, { name: "B" }] }` |
| `date` | 日付 | `{ date: { start: "2025-12-25", end: null } }` |
| `checkbox` | チェック | `{ checkbox: true }` |
| `url` | URL | `{ url: "https://..." }` |
| `email` | メール | `{ email: "user@example.com" }` |
| `people` | ユーザー | `{ people: [{ id: "user-id" }] }` |
| `relation` | リレーション | `{ relation: [{ id: "page-id" }] }` |
| `status` | ステータス | `{ status: { name: "In Progress" } }` |

---

## ブロックタイプ

| タイプ | 説明 |
|--------|------|
| `paragraph` | 段落 |
| `heading_1`, `heading_2`, `heading_3` | 見出し |
| `bulleted_list_item` | 箇条書き |
| `numbered_list_item` | 番号付きリスト |
| `to_do` | ToDoリスト (`checked: true/false`) |
| `toggle` | トグル |
| `quote` | 引用 |
| `callout` | コールアウト (`icon`, `color`) |
| `code` | コードブロック (`language`) |
| `image`, `video`, `file` | メディア |
| `table`, `table_row` | テーブル |
| `divider` | 区切り線 |

---

## レート制限・サイズ制限

### レート制限
- **平均3リクエスト/秒**
- 429エラー時は `Retry-After` ヘッダーを尊重

### サイズ制限

| 項目 | 制限 |
|------|------|
| ペイロード | 500KB / 1000ブロック |
| text.content | 2000文字 |
| URL | 2000文字 |
| 配列要素 | 100要素 |
| relation | 100ページ |
| ページプロパティ参照 | 25件 |

---

## ページネーション

```javascript
// 初回リクエスト
let response = await notion.databases.query({ database_id: id });

// 次ページ取得
while (response.has_more) {
  response = await notion.databases.query({
    database_id: id,
    start_cursor: response.next_cursor
  });
}
```

---

## エラーハンドリング

| ステータス | コード | 対処 |
|-----------|--------|------|
| 400 | `validation_error` | リクエスト内容を修正 |
| 401 | `unauthorized` | トークン確認 |
| 403 | `restricted_resource` | 権限設定を確認 |
| 404 | `object_not_found` | ID確認、共有設定確認 |
| 429 | `rate_limited` | Retry-After待機 |

```javascript
try {
  await notion.pages.create({...});
} catch (error) {
  if (error.code === 'rate_limited') {
    await sleep(error.headers['retry-after'] * 1000);
    // リトライ
  }
}
```

---

## 制限事項

- `status` プロパティはAPI経由で作成不可
- rollupプロパティの値は更新不可
- ページの `parent` は変更不可
- formula/rollupでrelationが25件超の場合、25件のみ評価
- 同期ブロックのコンテンツはAPI更新不可
