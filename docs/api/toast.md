# Toast Gateway API リファレンス

Windows Toast通知を使った日報生成結果の通知機能。

## 概要

`ToastGateway` は Windows 10/11 のトースト通知を使用して、日報生成の成功・失敗をユーザーに通知します。

### 主な機能

- 成功通知（クリックでNotionページを開く）
- 失敗通知（クリックでログファイルを開く）
- プラットフォーム自動検出（Windows以外では無効化）
- フォールバック対応（通知失敗時もログ出力）

## クラス定義

### ToastGateway

```python
class ToastGateway:
    """Windows Toast通知ゲートウェイ"""

    def __init__(
        self,
        enabled: bool = True,
        duration_success: int = 5,
        duration_failure: int = 10,
        open_page_on_click: bool = True,
    ):
        """初期化

        Args:
            enabled: 通知有効/無効
            duration_success: 成功通知の表示秒数
            duration_failure: 失敗通知の表示秒数
            open_page_on_click: クリック時にページを開くか
        """
```

#### プロパティ

| プロパティ | 型 | 説明 |
|-----------|-----|------|
| `enabled` | `bool` | 通知有効/無効 |
| `duration_success` | `int` | 成功通知の表示秒数（デフォルト: 5） |
| `duration_failure` | `int` | 失敗通知の表示秒数（デフォルト: 10） |
| `open_page_on_click` | `bool` | クリック時にページを開くか（デフォルト: True） |
| `is_windows` | `bool` | Windows環境かどうか（自動検出） |
| `toaster` | `ToastNotifier | None` | Toast通知オブジェクト |

#### メソッド

##### notify_success

日報生成成功を通知します。

```python
def notify_success(
    self,
    page_url: str,
    date: str,
    capture_count: int,
) -> None:
    """日報生成成功通知

    Args:
        page_url: NotionページURL
        date: 対象日付
        capture_count: キャプチャ数
    """
```

**通知内容:**
- タイトル: "✅ 日報出力完了"
- メッセージ: "{date} / {capture_count}回キャプチャ"
- クリック時: Notionページを開く

**例:**
```python
gateway.notify_success(
    page_url="https://notion.so/page123",
    date="2025-01-15",
    capture_count=240,
)
```

##### notify_failure

日報生成失敗を通知します。

```python
def notify_failure(
    self,
    error: str,
    log_path: str | None = None,
) -> None:
    """日報生成失敗通知

    Args:
        error: エラーメッセージ
        log_path: ログファイルパス（クリック時に開く）
    """
```

**通知内容:**
- タイトル: "❌ 日報出力失敗"
- メッセージ: エラーメッセージ（最大50文字）
- クリック時: ログファイルを開く

**例:**
```python
gateway.notify_failure(
    error="API connection failed",
    log_path="C:/logs/error.log",
)
```

## 関数

### notify_with_fallback

フォールバック付きでToast通知を送信します（推奨）。

```python
def notify_with_fallback(
    success: bool,
    page_url: str | None = None,
    date: str | None = None,
    capture_count: int | None = None,
    error: str | None = None,
    log_path: str | None = None,
    config: dict[str, Any] | None = None,
) -> None:
    """フォールバック付きToast通知

    Args:
        success: 成功/失敗フラグ
        page_url: NotionページURL（成功時）
        date: 対象日付（成功時）
        capture_count: キャプチャ数（成功時）
        error: エラーメッセージ（失敗時）
        log_path: ログファイルパス（失敗時）
        config: Toast設定（オプション）
    """
```

**設定項目（config）:**
```python
config = {
    "enabled": True,
    "duration_success": 5,
    "duration_failure": 10,
    "open_page_on_click": True,
}
```

**例（成功時）:**
```python
notify_with_fallback(
    success=True,
    page_url="https://notion.so/page123",
    date="2025-01-15",
    capture_count=240,
    config={"enabled": True}
)
```

**例（失敗時）:**
```python
notify_with_fallback(
    success=False,
    error="Notion API returned 503",
    log_path="C:/logs/error.log",
    config={"enabled": True}
)
```

## プラットフォーム対応

### Windows 10/11

- 完全サポート
- `win10toast-click` パッケージが必要
- インストール: `pip install win10toast-click`

### Linux / macOS

- 自動的に無効化
- ログ出力のみ実行
- エラーは発生しない

## 依存関係

### 必須（Windows環境のみ）

```bash
pip install win10toast-click
```

### オプション

```toml
[project.optional-dependencies]
windows = [
    "win10toast-click>=0.1.0",
]
```

## エラーハンドリング

### ライブラリ未インストール

```python
# win10toast-click が未インストールの場合
gateway = ToastGateway()
# gateway.enabled == False
# ログに警告が出力される
```

### 通知失敗時

```python
try:
    gateway.notify_success(...)
except Exception as e:
    # エラーをログに記録
    logger.error(f"Toast notification failed: {e}")
    # 処理は継続
```

### フォールバック動作

```python
# 通知失敗時でも例外は発生しない
notify_with_fallback(
    success=True,
    page_url="https://notion.so/page123",
    date="2025-01-15",
    capture_count=240,
)
# ログに詳細が記録される
```

## 使用例

### 基本的な使い方

```python
from src.gateways.toast import ToastGateway

# 1. インスタンス作成
gateway = ToastGateway(
    enabled=True,
    duration_success=5,
    duration_failure=10,
)

# 2. 成功通知
gateway.notify_success(
    page_url="https://notion.so/page123",
    date="2025-01-15",
    capture_count=240,
)

# 3. 失敗通知
gateway.notify_failure(
    error="API connection failed",
    log_path="C:/logs/error.log",
)
```

### handler.py との統合

```python
from src.gateways.toast import notify_with_fallback

def generate_daily_report(date: str):
    """日報生成処理"""
    try:
        # 1. ログ集計
        features = aggregate_logs(date)

        # 2. LLM要約
        summary = generate_summary(features)

        # 3. Notion出力
        page_url = publish_to_notion(summary)

        # 4. 成功通知
        notify_with_fallback(
            success=True,
            page_url=page_url,
            date=date,
            capture_count=features["meta"]["capture_count"],
        )

    except Exception as e:
        # 失敗通知
        notify_with_fallback(
            success=False,
            error=str(e),
            log_path="C:/logs/daily_report_bot.log",
        )
        raise
```

### カスタム設定

```python
# 設定ファイルから読み込み
config = {
    "enabled": True,
    "duration_success": 3,
    "duration_failure": 15,
    "open_page_on_click": True,
}

# 通知実行
notify_with_fallback(
    success=True,
    page_url="https://notion.so/page123",
    date="2025-01-15",
    capture_count=240,
    config=config,
)
```

### 通知を無効化

```python
# 通知を完全に無効化（開発環境など）
gateway = ToastGateway(enabled=False)

# 通知は表示されず、ログのみ出力
gateway.notify_success(
    page_url="https://notion.so/page123",
    date="2025-01-15",
    capture_count=240,
)
```

## テスト

### 単体テスト

```python
import pytest
from src.gateways.toast import ToastGateway

def test_notify_success_when_disabled(caplog):
    """通知無効時はログのみ出力"""
    gateway = ToastGateway(enabled=False)
    gateway.notify_success(
        page_url="https://notion.so/page123",
        date="2025-01-15",
        capture_count=240,
    )
    assert "Toast notification skipped" in caplog.text
```

### 統合テスト

```bash
# Windows環境でのテスト
pytest tests/gateways/test_toast.py -v

# 非Windows環境（スキップされる）
pytest tests/gateways/test_toast.py -v
```

## パフォーマンス

| 項目 | 値 |
|------|------|
| 通知表示時間 | 5秒（成功）/ 10秒（失敗） |
| 実行時間 | < 100ms（非同期） |
| メモリ使用量 | < 5MB |

## ベストプラクティス

### 推奨

- `notify_with_fallback` を使用（エラーハンドリング組み込み）
- 設定ファイルで通知の有効/無効を管理
- ログレベルを適切に設定

### 非推奨

- 通知失敗時に処理を停止する
- 長いエラーメッセージをそのまま渡す（50文字制限がある）
- 非Windows環境で例外を期待する

## トラブルシューティング

### 通知が表示されない

1. Windows環境か確認
2. `win10toast-click` がインストールされているか確認
3. `enabled=True` になっているか確認
4. Windows通知設定が有効か確認

### クリックしてもページが開かない

1. `open_page_on_click=True` か確認
2. URLが正しいか確認
3. デフォルトブラウザが設定されているか確認

### ログファイルが開かない

1. `log_path` が正しいか確認
2. ファイルが存在するか確認
3. ファイルの権限を確認

## 関連ドキュメント

- [Notion Gateway API](./notion.md)
- [Gemini Gateway API](./gemini.md)
- [設計: Notion出力フロー](../design/04-notion-flow.md)
