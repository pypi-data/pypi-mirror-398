"""Data processors for market data transformation."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from typing import Any


logger = logging.getLogger(__name__)


class DataProcessor(ABC):
    """Abstract base class for data processors.

    Data processors transform market data into message text for Telegram.
    Users can implement custom processors or use the default Markdown processor.
    """

    @abstractmethod
    async def process(self, markets: List[dict]) -> str:
        """Process market data and return formatted message text.

        Args:
            markets: List of market data dictionaries.

        Returns:
            Formatted message text (supports rich text formatting).
        """
        pass

    def format_market(self, market: dict) -> str:
        """Format a single market as text.

        Override this method in subclasses for custom formatting.

        Args:
            market: Market data dictionary.

        Returns:
            Formatted market text.
        """
        return f"• {market.get('question', 'Unknown')}"


class DefaultMarkdownProcessor(DataProcessor):
    """Default Markdown processor for Telegram messages.

    Generates Markdown-formatted market reports suitable for Telegram's
    MarkdownV2 parse mode.
    """

    def __init__(
        self,
        parse_mode: str = "MarkdownV2",
        max_markets: int = 10,
    ):
        """Initialize the processor.

        Args:
            parse_mode: Telegram parse mode (MarkdownV2, HTML, or plain).
            max_markets: Maximum number of markets to include in report.
        """
        self.parse_mode = parse_mode
        self.max_markets = max_markets

    async def process(self, markets: List[dict]) -> str:
        """Generate a Markdown-formatted market report.

        Args:
            markets: List of market data dictionaries.

        Returns:
            Markdown-formatted report string.
        """
        if not markets:
            return "📊 Polymarket 市场报告\n\n暂无市场数据"

        # Sort markets by volume (descending)
        sorted_markets = sorted(
            markets,
            key=lambda m: m.get('volume_num', 0) or 0,
            reverse=True
        )

        # Limit markets
        display_markets = sorted_markets[:self.max_markets]

        # Build header
        header = self._build_header(len(markets))

        # Build market items
        items = []
        for i, market in enumerate(display_markets, 1):
            item = self.format_market(market, index=i)
            items.append(item)

        items_text = "\n".join(items)

        # Build footer
        footer = self._build_footer(len(markets))

        return f"{header}\n{items_text}\n{footer}"

    def _build_header(self, total_count: int) -> str:
        """Build the report header.

        Args:
            total_count: Total number of markets.

        Returns:
            Header text.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        return f"📊 Polymarket 市场报告\n⏰ {timestamp}\n\n🪙 筛选出 {total_count} 个市场"

    def _build_footer(self, total_count: int) -> str:
        """Build the report footer.

        Args:
            total_count: Total number of markets.

        Returns:
            Footer text.
        """
        return f"\n—\n📈 数据来源: Polymarket"

    def format_market(
        self,
        market: dict,
        index: int | None = None,
    ) -> str:
        """Format a single market as a Markdown item.

        Args:
            market: Market data dictionary.
            index: Optional index number.

        Returns:
            Formatted market item.
        """
        question = market.get('question', 'Unknown')[:60]
        volume = market.get('volume_num', 0) or 0
        liquidity = market.get('liquidity', 0) or 0

        # Get current price if available
        outcome_prices = market.get('outcome_prices', [])
        if outcome_prices and isinstance(outcome_prices, list):
            current_price = outcome_prices[0]
            try:
                price_pct = float(current_price) * 100
                price_str = f"{price_pct:.0f}%"
            except (ValueError, TypeError):
                price_str = current_price
        else:
            price_str = "N/A"

        # Get category/tag info
        category = market.get('category', '')
        tags = market.get('tags', [])
        tag_info = ""
        if category:
            tag_info = f" | #{category}"
        elif tags and isinstance(tags, list) and tags:
            tag_info = f" | #{tags[0]}"

        # Format based on parse mode
        if self.parse_mode == "MarkdownV2":
            # Escape special characters for MarkdownV2
            escaped_question = self._escape_markdownv2(question)
            index_prefix = f"{index}. " if index else "• "
            return (
                f"{index_prefix}*{escaped_question}*\n"
                f"   💰 ${volume:,.0f} | 📈 {price_str}{tag_info}"
            )
        elif self.parse_mode == "HTML":
            return (
                f"{index}. <b>{question}</b>\n"
                f"   💰 ${volume:,.0f} | 📈 {price_str}{tag_info}"
            )
        else:
            # Plain text
            index_prefix = f"{index}. " if index else "• "
            return f"{index_prefix}{question}\n   💰 ${volume:,.0f} | 📈 {price_str}{tag_info}"

    def _escape_markdownv2(self, text: str) -> str:
        """Escape special characters for Telegram MarkdownV2 parse mode.

        Args:
            text: Input text.

        Returns:
            Escaped text.
        """
        # Characters that need escaping in MarkdownV2
        escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        result = text
        for char in escape_chars:
            result = result.replace(char, f'\\{char}')
        return result


class CompactTextProcessor(DataProcessor):
    """Compact text processor for high-volume markets.

    Generates a simple, compact list format suitable for many markets.
    """

    def __init__(self, parse_mode: str = "MarkdownV2", max_markets: int = 20):
        """Initialize the processor.

        Args:
            parse_mode: Telegram parse mode.
            max_markets: Maximum markets to include.
        """
        self.parse_mode = parse_mode
        self.max_markets = max_markets

    async def process(self, markets: List[dict]) -> str:
        """Generate a compact market list.

        Args:
            markets: List of market data dictionaries.

        Returns:
            Compact formatted text.
        """
        if not markets:
            return "No markets found"

        # Sort by volume
        sorted_markets = sorted(
            markets,
            key=lambda m: m.get('volume_num', 0) or 0,
            reverse=True
        )[:self.max_markets]

        lines = ["📊 Markets:"]
        for market in sorted_markets:
            question = market.get('question', 'Unknown')[:40]
            volume = market.get('volume_num', 0) or 0
            price = market.get('outcome_prices', ['N/A'])[0] if market.get('outcome_prices') else 'N/A'

            if self.parse_mode == "MarkdownV2":
                escaped = question.replace('_', r'\_').replace('*', r'\*')
                lines.append(f"• *{escaped}*: ${volume:,.0f} ({price})")
            else:
                lines.append(f"• {question}: ${volume:,.0f} ({price})")

        total = len(markets)
        if total > self.max_markets:
            lines.append(f"\n... and {total - self.max_markets} more")

        return "\n".join(lines)

    def format_market(self, market: dict) -> str:
        """Format a single market (not used in compact mode)."""
        return market.get('question', 'Unknown')[:40]
