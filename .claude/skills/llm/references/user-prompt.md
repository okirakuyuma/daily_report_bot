# ユーザープロンプトテンプレート

```python
def build_user_prompt(features: dict) -> str:
    meta = features["meta"]

    time_blocks_text = "\n".join([
        f"- {b['start']}〜{b['end']}: {', '.join([a['name'] for a in b['apps'][:2]])}"
        for b in features.get("time_blocks", [])[:8]
    ])

    app_text = "\n".join([
        f"- {a['name']}: {a['duration_min']}分 ({a['rank']})"
        for a in features.get("app_summary", [])[:5]
    ])

    keywords = features.get("global_keywords", {})
    keywords_text = ", ".join(keywords.get("top_keywords", [])[:10])

    return f"""以下は本日の作業ログの要約です。日報を作成してください。

## 基本情報
- 日付: {meta['date']}
- 記録期間: {meta.get('first_capture', 'N/A')} 〜 {meta.get('last_capture', 'N/A')}
- キャプチャ数: {meta['capture_count']}回
- 総作業時間: {meta['total_duration_min']}分

## 時間帯別作業
{time_blocks_text}

## アプリ使用状況
{app_text}

## 主なキーワード
{keywords_text}
"""
```
