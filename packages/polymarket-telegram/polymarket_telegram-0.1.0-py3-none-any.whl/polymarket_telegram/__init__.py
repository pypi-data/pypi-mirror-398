"""Polymarket Telegram Sender - Telegram推送模块.

提供 Telegram 消息推送、定时调度和数据处理功能.
"""

__version__ = "0.1.0"

from .config import MarketSyncConfig
from .processor import DataProcessor, DefaultMarkdownProcessor
from .sender import TelegramSender
from .scheduler import APScheduler, SimpleScheduler

__all__ = [
    "__version__",
    "MarketSyncConfig",
    "DataProcessor",
    "DefaultMarkdownProcessor",
    "TelegramSender",
    "APScheduler",
    "SimpleScheduler",
]
