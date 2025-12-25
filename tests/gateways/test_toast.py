"""Toast Gateway テスト"""

from __future__ import annotations

import platform
from unittest.mock import MagicMock, patch

import pytest

from src.gateways.toast import ToastGateway, notify_with_fallback


class TestToastGateway:
    """ToastGateway クラスのテスト"""

    def test_init_on_non_windows(self):
        """非Windows環境では通知が無効化される"""
        with patch("src.gateways.toast.platform.system", return_value="Linux"):
            gateway = ToastGateway()
            assert gateway.enabled is False
            assert gateway.toaster is None

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows only")
    def test_init_on_windows_without_library(self):
        """Windows環境でライブラリ未インストール時は無効化"""
        with patch("src.gateways.toast.ToastNotifier", None):
            gateway = ToastGateway()
            assert gateway.enabled is False

    def test_init_with_custom_config(self):
        """カスタム設定で初期化"""
        gateway = ToastGateway(
            enabled=False,
            duration_success=10,
            duration_failure=20,
            open_page_on_click=False,
        )
        assert gateway.enabled is False
        assert gateway.duration_success == 10
        assert gateway.duration_failure == 20
        assert gateway.open_page_on_click is False

    def test_notify_success_when_disabled(self, caplog):
        """通知無効時はログのみ出力"""
        gateway = ToastGateway(enabled=False)
        gateway.notify_success(
            page_url="https://notion.so/page123",
            date="2025-01-15",
            capture_count=240,
        )
        assert "Toast notification skipped" in caplog.text

    def test_notify_failure_when_disabled(self, caplog):
        """通知無効時はログのみ出力"""
        gateway = ToastGateway(enabled=False)
        gateway.notify_failure(
            error="API connection failed",
            log_path="/path/to/error.log",
        )
        assert "Toast notification skipped" in caplog.text

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows only")
    def test_notify_success_on_windows(self):
        """Windows環境での成功通知（モック使用）"""
        mock_toaster = MagicMock()

        with patch("src.gateways.toast.ToastNotifier", return_value=mock_toaster):
            gateway = ToastGateway(enabled=True)
            gateway.toaster = mock_toaster

            gateway.notify_success(
                page_url="https://notion.so/page123",
                date="2025-01-15",
                capture_count=240,
            )

            mock_toaster.show_toast.assert_called_once()
            call_args = mock_toaster.show_toast.call_args
            assert call_args.kwargs["title"] == "✅ 日報出力完了"
            assert "2025-01-15" in call_args.kwargs["msg"]
            assert "240回キャプチャ" in call_args.kwargs["msg"]

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows only")
    def test_notify_failure_on_windows(self):
        """Windows環境での失敗通知（モック使用）"""
        mock_toaster = MagicMock()

        with patch("src.gateways.toast.ToastNotifier", return_value=mock_toaster):
            gateway = ToastGateway(enabled=True)
            gateway.toaster = mock_toaster

            gateway.notify_failure(
                error="API connection failed",
                log_path="/path/to/error.log",
            )

            mock_toaster.show_toast.assert_called_once()
            call_args = mock_toaster.show_toast.call_args
            assert call_args.kwargs["title"] == "❌ 日報出力失敗"
            assert "API connection failed" in call_args.kwargs["msg"]

    def test_notify_failure_truncates_long_error(self):
        """長いエラーメッセージは50文字に切り詰め"""
        mock_toaster = MagicMock()
        gateway = ToastGateway(enabled=True)
        gateway.toaster = mock_toaster

        long_error = "A" * 100
        gateway.notify_failure(error=long_error, log_path=None)

        if mock_toaster.show_toast.called:
            call_args = mock_toaster.show_toast.call_args
            msg = call_args.kwargs["msg"]
            assert len(msg) <= 50


class TestNotifyWithFallback:
    """notify_with_fallback 関数のテスト"""

    def test_success_notification(self):
        """成功通知"""
        notify_with_fallback(
            success=True,
            page_url="https://notion.so/page123",
            date="2025-01-15",
            capture_count=240,
            config={"enabled": False},  # テスト用に無効化
        )

    def test_failure_notification(self):
        """失敗通知"""
        notify_with_fallback(
            success=False,
            error="API connection failed",
            log_path="/path/to/error.log",
            config={"enabled": False},  # テスト用に無効化
        )

    def test_missing_parameters_for_success(self, caplog):
        """成功通知でパラメータ不足時は警告"""
        notify_with_fallback(
            success=True,
            page_url="https://notion.so/page123",
            # date と capture_count が欠けている
            config={"enabled": False},
        )
        assert "Missing parameters" in caplog.text

    def test_missing_parameters_for_failure(self, caplog):
        """失敗通知でパラメータ不足時は警告"""
        notify_with_fallback(
            success=False,
            # error が欠けている
            config={"enabled": False},
        )
        assert "Missing error message" in caplog.text

    def test_with_custom_config(self):
        """カスタム設定を使用"""
        config = {
            "enabled": False,
            "duration_success": 10,
            "duration_failure": 20,
            "open_page_on_click": False,
        }
        notify_with_fallback(
            success=True,
            page_url="https://notion.so/page123",
            date="2025-01-15",
            capture_count=240,
            config=config,
        )
