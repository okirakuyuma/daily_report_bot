# Notionテーブル生成

```python
def build_app_table(app_usage: list) -> dict:
    """アプリ使用状況テーブルを生成"""
    RANK_EMOJI = {"high": "🔴 多", "medium": "🟡 中", "low": "🟢 少"}

    rows = [table_row(["アプリ", "時間", "頻度", "主な用途"])]  # ヘッダー

    for app in app_usage:
        rows.append(table_row([
            app["name"],
            f"{app['duration_min']}分",
            RANK_EMOJI.get(app["rank"], "-"),
            app.get("purpose", "-")
        ]))

    return {
        "type": "table",
        "table": {
            "table_width": 4,
            "has_column_header": True,
            "has_row_header": False,
            "children": rows
        }
    }

def table_row(cells: list) -> dict:
    return {
        "type": "table_row",
        "table_row": {
            "cells": [
                [{"type": "text", "text": {"content": cell}}]
                for cell in cells
            ]
        }
    }
```
