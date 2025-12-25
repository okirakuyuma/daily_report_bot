"""Toast Gateway 使用例

Windows Toast通知を使った日報生成結果の通知例。
"""

from __future__ import annotations

from src.gateways.toast import ToastGateway, notify_with_fallback


def example_basic_usage():
    """基本的な使い方"""
    # 1. インスタンス作成
    gateway = ToastGateway(
        enabled=True,
        duration_success=5,
        duration_failure=10,
        open_page_on_click=True,
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


def example_with_fallback():
    """フォールバック付き通知（推奨）"""
    # 設定
    config = {
        "enabled": True,
        "duration_success": 5,
        "duration_failure": 10,
        "open_page_on_click": True,
    }

    # 成功時
    notify_with_fallback(
        success=True,
        page_url="https://notion.so/page123",
        date="2025-01-15",
        capture_count=240,
        config=config,
    )

    # 失敗時
    notify_with_fallback(
        success=False,
        error="Notion API returned 503",
        log_path="C:/logs/error.log",
        config=config,
    )


def example_disabled_notification():
    """通知無効時の動作"""
    # 通知を無効化（ログのみ出力）
    gateway = ToastGateway(enabled=False)

    # 通知は表示されず、ログにのみ記録される
    gateway.notify_success(
        page_url="https://notion.so/page123",
        date="2025-01-15",
        capture_count=240,
    )


def example_integration_with_handler():
    """handler.py との統合例"""
    # 日報生成処理の完了後
    try:
        # ... Notion API でページ作成 ...
        page_url = "https://notion.so/page123"
        date = "2025-01-15"
        capture_count = 240

        # 成功通知
        notify_with_fallback(
            success=True,
            page_url=page_url,
            date=date,
            capture_count=capture_count,
        )

    except Exception as e:
        # 失敗通知
        notify_with_fallback(
            success=False,
            error=str(e),
            log_path="C:/logs/daily_report_bot.log",
        )


def example_custom_durations():
    """カスタム表示時間"""
    # 成功通知を3秒、失敗通知を15秒表示
    gateway = ToastGateway(
        duration_success=3,
        duration_failure=15,
    )

    gateway.notify_success(
        page_url="https://notion.so/page123",
        date="2025-01-15",
        capture_count=240,
    )


def example_without_click_action():
    """クリック時のアクション無効化"""
    # クリックしてもページやファイルを開かない
    gateway = ToastGateway(open_page_on_click=False)

    gateway.notify_success(
        page_url="https://notion.so/page123",
        date="2025-01-15",
        capture_count=240,
    )


if __name__ == "__main__":
    print("Toast Gateway Examples")
    print("=" * 50)

    print("\n1. Basic Usage")
    example_basic_usage()

    print("\n2. With Fallback (Recommended)")
    example_with_fallback()

    print("\n3. Disabled Notification")
    example_disabled_notification()

    print("\n4. Custom Durations")
    example_custom_durations()

    print("\n5. Without Click Action")
    example_without_click_action()

    print("\n✅ Examples completed!")
