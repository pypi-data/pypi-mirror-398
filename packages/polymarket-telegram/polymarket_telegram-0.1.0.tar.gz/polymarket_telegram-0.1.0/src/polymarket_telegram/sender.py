"""Telegram sender for market notifications."""

import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

import httpx

from .config import MarketSyncConfig
from .processor import DataProcessor, DefaultMarkdownProcessor

# Reuse ProxyConfig from fetcher for Telegram API proxy
from polymarket_fetcher.config import ProxyConfig

if TYPE_CHECKING:
    from typing import Any, List


logger = logging.getLogger(__name__)


class TelegramSender:
    """Telegram message sender for Polymarket notifications.

    This class handles:
    - Fetching market data from polymarket-fetcher
    - Processing data through custom or default processors
    - Sending formatted messages to Telegram

    Example:
        >>> async def custom_processor(markets):
        ...     return f"Found {len(markets)} markets!"
        >>>
        >>> config = MarketSyncConfig(
        ...     bot_token="your-bot-token",
        ...     chat_ids=["123456"],
        ...     category="Crypto",
        ... )
        >>> sender = TelegramSender(config, data_processor=custom_processor)
        >>> await sender.run_once()  # Send immediately
    """

    def __init__(
        self,
        config: MarketSyncConfig,
        data_processor: Optional[callable] = None,
    ):
        """Initialize the Telegram sender.

        Args:
            config: Market synchronization configuration.
            data_processor: Optional custom async function to process market data.
                           Should accept a list of market dicts and return a string.
        """
        self.config = config
        self.data_processor = data_processor or DefaultMarkdownProcessor(
            parse_mode=config.parse_mode,
            max_markets=config.max_markets_per_message,
        )
        self._client: Optional[httpx.AsyncClient] = None
        self._running = False

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            # Use api.proxy configuration from settings
            proxy_config = ProxyConfig()
            proxy_url = proxy_config.get_proxy_url()
            if proxy_url:
                self._client = httpx.AsyncClient(
                    timeout=30.0,
                    proxy=proxy_url,
                )
            else:
                self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    @property
    def is_running(self) -> bool:
        """Check if the sender is running."""
        return self._running

    async def start(self) -> None:
        """Start the sender (for background scheduling).

        This method starts the sender for APScheduler-based scheduling.
        For manual execution, use run_once() instead.
        """
        if self._running:
            logger.warning("TelegramSender is already running")
            return

        self._running = True
        logger.info(
            f"TelegramSender started - category={self.config.category}, "
            f"cron={self.config.cron}"
        )

    async def stop(self) -> None:
        """Stop the sender and cleanup resources."""
        if not self._running:
            return

        self._running = False
        if self._client:
            await self._client.aclose()
            self._client = None

        logger.info("TelegramSender stopped")

    async def run_once(self) -> bool:
        """Execute a single sync and send cycle.

        Returns:
            True if successful, False otherwise.
        """
        try:
            return await self._process_and_send()
        except Exception as e:
            logger.error(f"TelegramSender run_once failed: {e}", exc_info=True)
            return False

    async def _process_and_send(self) -> bool:
        """Fetch markets, process data, and send to Telegram.

        Returns:
            True if all messages sent successfully.
        """
        # Step 1: Fetch market data
        markets = await self._fetch_markets()
        logger.info(f"Fetched {len(markets)} markets")

        # Step 2: Apply filters
        filtered = self._apply_filters(markets)
        logger.info(f"After filtering: {len(filtered)} markets")

        # Step 3: Process data
        message = await self._process_data(filtered)

        # Step 4: Send to all chat IDs
        return await self._send_to_chats(message)

    async def _fetch_markets(self) -> List[dict]:
        """Fetch market data using polymarket-fetcher.

        Returns:
            List of market data dictionaries.
        """
        try:
            # Import here to avoid circular imports
            from polymarket_fetcher import MarketFetcher

            async with MarketFetcher() as fetcher:
                if self.config.category:
                    return await fetcher.fetch_markets_by_category(
                        self.config.category,
                        limit=100,
                    )
                elif self.config.tags:
                    return await fetcher.fetch_markets_by_tags(
                        self.config.tags,
                        limit=100,
                    )
                else:
                    return await fetcher.fetch_all_markets(limit=100)

        except ImportError as e:
            logger.error(f"Failed to import MarketFetcher: {e}")
            raise RuntimeError(
                "polymarket_fetcher is required. "
                "Install it with: pip install polymarket-fetcher"
            ) from e
        except Exception as e:
            logger.error(f"Failed to fetch markets: {e}")
            raise

    def _apply_filters(self, markets: List[dict]) -> List[dict]:
        """Apply configured filters to markets.

        Args:
            markets: List of market data dictionaries.

        Returns:
            Filtered list of markets.
        """
        result = []

        for m in markets:
            # Skip inactive markets if configured
            if self.config.only_active:
                is_active = m.get('active', True)
                if not is_active:
                    continue

            # Volume filter
            volume = m.get('volume_num', 0) or 0
            if volume < self.config.min_volume:
                continue

            # Liquidity filter
            liquidity = m.get('liquidity', 0) or 0
            if liquidity < self.config.min_liquidity:
                continue

            # Keywords filter
            if self.config.keywords:
                question = m.get('question', '')
                if not any(
                    k.lower() in question.lower()
                    for k in self.config.keywords
                ):
                    continue

            result.append(m)

        return result

    async def _process_data(self, markets: List[dict]) -> str:
        """Process market data into message text.

        Args:
            markets: List of market data dictionaries.

        Returns:
            Formatted message text.
        """
        if self.config.data_processor:
            # Use custom processor
            return await self.config.data_processor(markets)
        else:
            # Use default processor
            return await self.data_processor.process(markets)

    async def _send_to_chats(self, message: str) -> bool:
        """Send message to all configured chat IDs.

        Args:
            message: Message text to send.

        Returns:
            True if all messages sent successfully.
        """
        success = True
        for chat_id in self.config.chat_ids:
            try:
                sent = await self._send_message(chat_id, message)
                if not sent:
                    success = False
            except Exception as e:
                logger.error(f"Failed to send to {chat_id}: {e}")
                success = False

        return success

    async def _send_message(
        self,
        chat_id: str,
        text: str,
    ) -> bool:
        """Send a message to a Telegram chat.

        Args:
            chat_id: Telegram chat ID.
            text: Message text.

        Returns:
            True if successful.
        """
        url = f"https://api.telegram.org/bot{self.config.bot_token}/sendMessage"

        payload = {
            "chat_id": chat_id,
            "text": text,
        }

        # Add parse mode
        if self.config.parse_mode not in ("plain", "None", None):
            payload["parse_mode"] = self.config.parse_mode

        # Disable preview if configured
        if not self.config.enable_preview:
            payload["disable_web_page_preview"] = True

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()

            result = response.json()
            if result.get("ok"):
                logger.info(f"Message sent to {chat_id}")
                return True
            else:
                logger.error(
                    f"Telegram API error for {chat_id}: {result.get('description')}"
                )
                return False

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error sending to {chat_id}: {e.response.status_code} - "
                f"{e.response.text}"
            )
            return False
        except Exception as e:
            logger.error(f"Failed to send message to {chat_id}: {e}")
            return False

    async def send_custom_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: Optional[str] = None,
    ) -> bool:
        """Send a custom message (not market-related).

        Args:
            chat_id: Telegram chat ID.
            text: Message text.
            parse_mode: Override parse mode.

        Returns:
            True if successful.
        """
        url = f"https://api.telegram.org/bot{self.config.bot_token}/sendMessage"

        payload = {
            "chat_id": chat_id,
            "text": text,
        }

        mode = parse_mode or self.config.parse_mode
        if mode not in ("plain", "None", None):
            payload["parse_mode"] = mode

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to send custom message: {e}")
            return False

    def get_status(self) -> dict:
        """Get sender status.

        Returns:
            Status dictionary.
        """
        return {
            "running": self._running,
            "category": self.config.category,
            "tags": self.config.tags,
            "chat_ids_count": len(self.config.chat_ids),
            "parse_mode": self.config.parse_mode,
        }
