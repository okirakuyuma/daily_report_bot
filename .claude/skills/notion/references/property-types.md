# Notionプロパティタイプ

| タイプ | 値の形式 |
|--------|----------|
| `title` | `{ title: [{ text: { content: "..." } }] }` |
| `rich_text` | `{ rich_text: [{ text: { content: "..." } }] }` |
| `number` | `{ number: 123 }` |
| `select` | `{ select: { name: "Option" } }` |
| `multi_select` | `{ multi_select: [{ name: "A" }, { name: "B" }] }` |
| `date` | `{ date: { start: "2025-12-25", end: null } }` |
| `checkbox` | `{ checkbox: true }` |
| `url` | `{ url: "https://..." }` |
| `status` | `{ status: { name: "In Progress" } }` |

## 制限事項

- `status` プロパティはAPI経由で作成不可
- rollupプロパティの値は更新不可
- ページの `parent` は変更不可
