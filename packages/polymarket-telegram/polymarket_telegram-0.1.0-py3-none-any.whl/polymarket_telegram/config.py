"""Configuration classes for Telegram sender."""

from datetime import datetime
from typing import TYPE_CHECKING, Awaitable, Callable, List, Optional

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from typing_extensions import TypeAlias


# Define the data processor type for type hints
DataProcessorFunc: "TypeAlias" = Callable[[List[dict]], Awaitable[str]]


class MarketSyncConfig(BaseModel):
    """Market synchronization configuration for Telegram notifications.

    This config controls:
    - Telegram bot and chat settings
    - Market filtering criteria
    - Scheduling
    - Data processing callbacks
    """

    # -------------------------------------------------------------------------
    # Telegram Configuration
    # -------------------------------------------------------------------------
    bot_token: str = Field(..., description="Telegram Bot API token")
    chat_ids: List[str] = Field(..., description="Telegram chat IDs to send messages to")
    parse_mode: str = Field(
        default="",
        description="Message parse mode: MarkdownV2, HTML, or plain (empty for plain text)",
    )

    # -------------------------------------------------------------------------
    # Market Filtering Configuration
    # -------------------------------------------------------------------------
    category: Optional[str] = Field(
        default=None,
        description="Filter markets by category name (fuzzy match, case-insensitive)",
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Filter markets by tag ID(s)",
    )
    keywords: Optional[List[str]] = Field(
        default=None,
        description="Filter markets by keywords in question",
    )
    min_volume: float = Field(
        default=1000.0,
        ge=0,
        description="Minimum trading volume to include",
    )
    min_liquidity: float = Field(
        default=500.0,
        ge=0,
        description="Minimum liquidity to include",
    )
    only_active: bool = Field(
        default=True,
        description="Only include active markets",
    )

    # -------------------------------------------------------------------------
    # Scheduling Configuration
    # -------------------------------------------------------------------------
    cron: str = Field(
        default="0 */1 * * *",
        description="Cron expression for scheduled execution (default: every hour)",
    )
    timezone: str = Field(
        default="UTC",
        description="Timezone for cron scheduling",
    )

    # -------------------------------------------------------------------------
    # Data Processing Configuration
    # -------------------------------------------------------------------------
    data_processor: Optional[DataProcessorFunc] = Field(
        default=None,
        description="Custom async function to process market data and return message text",
    )

    # -------------------------------------------------------------------------
    # Message Settings
    # -------------------------------------------------------------------------
    max_markets_per_message: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of markets to include in a single message",
    )
    enable_preview: bool = Field(
        default=True,
        description="Enable link preview for URLs in messages",
    )

    class Config:
        """Pydantic model configuration."""

        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
