"""Toast Gateway - Windows Toast通知連携

日報生成の成功・失敗をWindows Toast通知で表示。
クリック時にNotionページやログファイルを開く。
"""

from __future__ import annotations

import logging
import os
import platform
import webbrowser
from typing import Any

# Windows専用ライブラリ（プラットフォーム判定後にインポート）
if platform.system() == "Windows":
    try:
        from win10toast_click import ToastNotifier
    except ImportError:
        ToastNotifier = None  # type: ignore
else:
    ToastNotifier = None  # type: ignore

logger = logging.getLogger(__name__)


class ToastGateway:
    """Windows Toast通知ゲートウェイ

    Attributes:
        enabled: 通知有効/無効
        duration_success: 成功通知の表示秒数
        duration_failure: 失敗通知の表示秒数
        open_page_on_click: クリック時にページを開くか
    """

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
        self.enabled = enabled
        self.duration_success = duration_success
        self.duration_failure = duration_failure
        self.open_page_on_click = open_page_on_click

        # プラットフォームチェック
        self.is_windows = platform.system() == "Windows"
        self.toaster = None

        if self.is_windows and ToastNotifier is not None:
            try:
                self.toaster = ToastNotifier()
            except Exception as e:
                logger.warning(f"Failed to initialize ToastNotifier: {e}")
                self.enabled = False
        else:
            if not self.is_windows:
                logger.info("Toast notifications are only supported on Windows")
            else:
                logger.warning("win10toast-click is not installed. Toast notifications disabled.")
            self.enabled = False

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
        if not self.enabled:
            logger.info(f"Toast notification skipped (disabled): Success - {date}")
            return

        if self.toaster is None:
            logger.warning("ToastNotifier is not initialized")
            return

        title = "✅ 日報出力完了"
        message = f"{date} / {capture_count}回キャプチャ"

        try:
            callback = None
            if self.open_page_on_click and page_url:
                callback = lambda: webbrowser.open(page_url)

            self.toaster.show_toast(
                title=title,
                msg=message,
                duration=self.duration_success,
                callback_on_click=callback,
                threaded=True,  # 非同期実行
            )
            logger.info(f"Toast notification sent: {title} - {message}")

        except Exception as e:
            logger.error(f"Failed to show success toast: {e}")

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
        if not self.enabled:
            logger.info(f"Toast notification skipped (disabled): Failure - {error}")
            return

        if self.toaster is None:
            logger.warning("ToastNotifier is not initialized")
            return

        title = "❌ 日報出力失敗"
        # エラーメッセージは50文字に制限
        message = error[:50] if len(error) > 50 else error

        try:
            callback = None
            if self.open_page_on_click and log_path and os.path.exists(log_path):
                # Windowsのファイルエクスプローラーで開く
                callback = lambda: os.startfile(log_path)

            self.toaster.show_toast(
                title=title,
                msg=message,
                duration=self.duration_failure,
                callback_on_click=callback,
                threaded=True,  # 非同期実行
            )
            logger.info(f"Toast notification sent: {title} - {message}")

        except Exception as e:
            logger.error(f"Failed to show failure toast: {e}")


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

    通知失敗時もログ出力で情報を残す。

    Args:
        success: 成功/失敗フラグ
        page_url: NotionページURL（成功時）
        date: 対象日付（成功時）
        capture_count: キャプチャ数（成功時）
        error: エラーメッセージ（失敗時）
        log_path: ログファイルパス（失敗時）
        config: Toast設定（オプション）
    """
    # デフォルト設定
    if config is None:
        config = {}

    gateway = ToastGateway(
        enabled=config.get("enabled", True),
        duration_success=config.get("duration_success", 5),
        duration_failure=config.get("duration_failure", 10),
        open_page_on_click=config.get("open_page_on_click", True),
    )

    try:
        if success:
            if page_url and date and capture_count is not None:
                gateway.notify_success(page_url, date, capture_count)
            else:
                logger.warning("Missing parameters for success notification")
        else:
            if error:
                gateway.notify_failure(error, log_path)
            else:
                logger.warning("Missing error message for failure notification")

    except Exception as e:
        logger.error(f"Toast notification failed: {e}")
        # フォールバック: ログに詳細を出力
        if success:
            logger.info(f"[FALLBACK] Success: {date} - {capture_count} captures - {page_url}")
        else:
            logger.error(f"[FALLBACK] Failure: {error} - Log: {log_path}")
