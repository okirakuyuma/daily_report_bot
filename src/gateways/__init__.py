# gateways layer - external API integrations

from .gemini import GeminiGateway, generate_summary_with_fallback
from .notion import NotionGateway, publish_report
from .toast import ToastGateway, notify_with_fallback

__all__ = [
    "GeminiGateway",
    "generate_summary_with_fallback",
    "NotionGateway",
    "publish_report",
    "ToastGateway",
    "notify_with_fallback",
]
